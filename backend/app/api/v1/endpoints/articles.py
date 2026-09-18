from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.article import ArticleFileType, MedicalArticle
from app.models.user import User
from app.schemas.knowledge import ArticleOut
from app.services.article_text import extract_article_text
from app.services.audit import write_audit_log
from app.services.rag.indexer import reindex_all
from app.services.uploads import save_article

router = APIRouter(prefix="/articles", tags=["Medical Articles"])

_EXT_TO_TYPE = {
    ".pdf": ArticleFileType.PDF,
    ".docx": ArticleFileType.DOCX,
    ".md": ArticleFileType.MARKDOWN,
    ".txt": ArticleFileType.TEXT,
}


@router.get("", response_model=list[ArticleOut])
def list_articles(db: Session = Depends(get_db), search: str | None = None):
    query = db.query(MedicalArticle)
    if search:
        query = query.filter(MedicalArticle.title.ilike(f"%{search}%"))
    return query.order_by(MedicalArticle.created_at.desc()).all()


@router.post("", response_model=ArticleOut, status_code=status.HTTP_201_CREATED)
def upload_article(
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
    title: str = Form(...),
    author: str | None = Form(default=None),
    tags: str | None = Form(default=None),
    file: UploadFile = File(...),
):
    file_path = save_article(file)
    suffix = Path(file_path).suffix.lower()
    file_type = _EXT_TO_TYPE.get(suffix)
    if file_type is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unsupported article file type")

    try:
        raw_text = extract_article_text(file_path, file_type.value)
    except Exception as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Could not extract text from this file: {exc}")

    article = MedicalArticle(
        title=title, author=author, file_type=file_type, file_path=file_path, raw_text=raw_text, tags=tags
    )
    db.add(article)
    db.commit()
    db.refresh(article)

    reindex_all(db)  # makes the article instantly searchable via RAG — no retraining step
    write_audit_log(
        db, user_id=admin.id, action="article.upload", resource_type="article", resource_id=article.id,
        ip_address=request.client.host if request.client else None,
    )
    return article


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_article(
    article_id: str, request: Request, db: Session = Depends(get_db), admin: User = Depends(require_admin)
):
    article = db.get(MedicalArticle, article_id)
    if article is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Article not found")
    db.delete(article)
    db.commit()
    reindex_all(db)
    write_audit_log(
        db, user_id=admin.id, action="article.delete", resource_type="article", resource_id=article_id,
        ip_address=request.client.host if request.client else None,
    )
