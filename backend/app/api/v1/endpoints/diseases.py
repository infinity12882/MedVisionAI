from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user, require_admin
from app.db.session import get_db
from app.models.disease import Disease, DiseaseSymptom, Symptom
from app.models.user import User
from app.schemas.knowledge import DiseaseCreate, DiseaseListItem, DiseaseOut, DiseaseUpdate
from app.services.audit import write_audit_log
from app.services.rag.indexer import reindex_all

router = APIRouter(prefix="/diseases", tags=["Diseases"])


def _apply_symptom_links(db: Session, disease: Disease, symptom_links) -> None:
    db.query(DiseaseSymptom).filter(DiseaseSymptom.disease_id == disease.id).delete()
    for link in symptom_links:
        symptom = db.get(Symptom, link.symptom_id)
        if symptom is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Symptom {link.symptom_id} does not exist")
        db.add(DiseaseSymptom(disease_id=disease.id, symptom_id=link.symptom_id, importance_score=link.importance_score))


@router.get("", response_model=list[DiseaseListItem])
def list_diseases(
    db: Session = Depends(get_db),
    search: str | None = Query(default=None, description="Search by name or tag"),
    limit: int = Query(default=50, le=200),
    offset: int = 0,
):
    query = db.query(Disease)
    if search:
        like = f"%{search}%"
        query = query.filter((Disease.name.ilike(like)) | (Disease.tags.ilike(like)))
    return query.order_by(Disease.priority.desc(), Disease.name).offset(offset).limit(limit).all()


@router.get("/{disease_id}", response_model=DiseaseOut)
def get_disease(disease_id: str, db: Session = Depends(get_db)):
    disease = (
        db.query(Disease)
        .options(selectinload(Disease.symptom_links).selectinload(DiseaseSymptom.symptom))
        .filter(Disease.id == disease_id)
        .first()
    )
    if disease is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Disease not found")
    return disease


@router.post("", response_model=DiseaseOut, status_code=status.HTTP_201_CREATED)
def create_disease(
    payload: DiseaseCreate, request: Request, db: Session = Depends(get_db), admin: User = Depends(require_admin)
):
    if db.query(Disease).filter(Disease.name == payload.name).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "A disease with this name already exists")

    data = payload.model_dump(exclude={"symptoms"})
    disease = Disease(**data)
    db.add(disease)
    db.flush()

    _apply_symptom_links(db, disease, payload.symptoms)
    db.commit()
    db.refresh(disease)

    reindex_all(db)
    write_audit_log(
        db, user_id=admin.id, action="disease.create", resource_type="disease", resource_id=disease.id,
        ip_address=request.client.host if request.client else None,
    )
    return get_disease(disease.id, db)


@router.put("/{disease_id}", response_model=DiseaseOut)
def update_disease(
    disease_id: str,
    payload: DiseaseUpdate,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    disease = db.get(Disease, disease_id)
    if disease is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Disease not found")

    update_data = payload.model_dump(exclude={"symptoms"}, exclude_unset=True)
    for field, value in update_data.items():
        setattr(disease, field, value)

    if payload.symptoms is not None:
        _apply_symptom_links(db, disease, payload.symptoms)

    db.commit()
    reindex_all(db)
    write_audit_log(
        db, user_id=admin.id, action="disease.update", resource_type="disease", resource_id=disease.id,
        ip_address=request.client.host if request.client else None,
    )
    return get_disease(disease.id, db)


@router.delete("/{disease_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_disease(
    disease_id: str, request: Request, db: Session = Depends(get_db), admin: User = Depends(require_admin)
):
    disease = db.get(Disease, disease_id)
    if disease is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Disease not found")
    db.delete(disease)
    db.commit()
    reindex_all(db)
    write_audit_log(
        db, user_id=admin.id, action="disease.delete", resource_type="disease", resource_id=disease_id,
        ip_address=request.client.host if request.client else None,
    )
