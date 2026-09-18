from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.disease import Symptom
from app.models.user import User
from app.schemas.knowledge import SymptomCreate, SymptomOut, SymptomUpdate
from app.services.audit import write_audit_log
from app.services.rag.indexer import reindex_all

router = APIRouter(prefix="/symptoms", tags=["Symptoms"])


@router.get("", response_model=list[SymptomOut])
def list_symptoms(db: Session = Depends(get_db), search: str | None = None):
    query = db.query(Symptom)
    if search:
        query = query.filter(Symptom.name.ilike(f"%{search}%"))
    return query.order_by(Symptom.name).all()


@router.post("", response_model=SymptomOut, status_code=status.HTTP_201_CREATED)
def create_symptom(
    payload: SymptomCreate, request: Request, db: Session = Depends(get_db), admin: User = Depends(require_admin)
):
    if db.query(Symptom).filter(Symptom.name == payload.name).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "A symptom with this name already exists")
    symptom = Symptom(**payload.model_dump())
    db.add(symptom)
    db.commit()
    db.refresh(symptom)
    reindex_all(db)
    write_audit_log(
        db, user_id=admin.id, action="symptom.create", resource_type="symptom", resource_id=symptom.id,
        ip_address=request.client.host if request.client else None,
    )
    return symptom


@router.put("/{symptom_id}", response_model=SymptomOut)
def update_symptom(
    symptom_id: str,
    payload: SymptomUpdate,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    symptom = db.get(Symptom, symptom_id)
    if symptom is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Symptom not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(symptom, field, value)
    db.commit()
    reindex_all(db)
    write_audit_log(
        db, user_id=admin.id, action="symptom.update", resource_type="symptom", resource_id=symptom.id,
        ip_address=request.client.host if request.client else None,
    )
    return symptom


@router.delete("/{symptom_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_symptom(
    symptom_id: str, request: Request, db: Session = Depends(get_db), admin: User = Depends(require_admin)
):
    symptom = db.get(Symptom, symptom_id)
    if symptom is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Symptom not found")
    db.delete(symptom)
    db.commit()
    reindex_all(db)
    write_audit_log(
        db, user_id=admin.id, action="symptom.delete", resource_type="symptom", resource_id=symptom_id,
        ip_address=request.client.host if request.client else None,
    )
