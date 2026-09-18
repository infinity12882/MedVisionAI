from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.medication import Medication
from app.models.user import User
from app.schemas.knowledge import MedicationCreate, MedicationOut, MedicationUpdate
from app.services.audit import write_audit_log
from app.services.rag.indexer import reindex_all

router = APIRouter(prefix="/medications", tags=["Medications"])


@router.get("", response_model=list[MedicationOut])
def list_medications(db: Session = Depends(get_db), search: str | None = None):
    query = db.query(Medication)
    if search:
        query = query.filter(Medication.name.ilike(f"%{search}%"))
    return query.order_by(Medication.name).all()


@router.get("/{medication_id}", response_model=MedicationOut)
def get_medication(medication_id: str, db: Session = Depends(get_db)):
    med = db.get(Medication, medication_id)
    if med is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Medication not found")
    return med


@router.post("", response_model=MedicationOut, status_code=status.HTTP_201_CREATED)
def create_medication(
    payload: MedicationCreate, request: Request, db: Session = Depends(get_db), admin: User = Depends(require_admin)
):
    if db.query(Medication).filter(Medication.name == payload.name).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "A medication with this name already exists")
    med = Medication(**payload.model_dump())
    db.add(med)
    db.commit()
    db.refresh(med)
    reindex_all(db)
    write_audit_log(
        db, user_id=admin.id, action="medication.create", resource_type="medication", resource_id=med.id,
        ip_address=request.client.host if request.client else None,
    )
    return med


@router.put("/{medication_id}", response_model=MedicationOut)
def update_medication(
    medication_id: str,
    payload: MedicationUpdate,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    med = db.get(Medication, medication_id)
    if med is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Medication not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(med, field, value)
    db.commit()
    reindex_all(db)
    write_audit_log(
        db, user_id=admin.id, action="medication.update", resource_type="medication", resource_id=med.id,
        ip_address=request.client.host if request.client else None,
    )
    return med


@router.delete("/{medication_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_medication(
    medication_id: str, request: Request, db: Session = Depends(get_db), admin: User = Depends(require_admin)
):
    med = db.get(Medication, medication_id)
    if med is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Medication not found")
    db.delete(med)
    db.commit()
    reindex_all(db)
    write_audit_log(
        db, user_id=admin.id, action="medication.delete", resource_type="medication", resource_id=medication_id,
        ip_address=request.client.host if request.client else None,
    )
