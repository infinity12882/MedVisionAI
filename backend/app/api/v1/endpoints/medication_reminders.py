from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.health_tracking import MedicationLog, PatientMedication
from app.models.user import User
from app.schemas.extended import PatientMedicationCreate, PatientMedicationOut

router = APIRouter(prefix="/medication-reminders", tags=["Medication Reminders"])


@router.get("", response_model=list[PatientMedicationOut])
def list_medications(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return (
        db.query(PatientMedication)
        .filter(PatientMedication.user_id == current_user.id, PatientMedication.is_active.is_(True))
        .order_by(PatientMedication.created_at.desc())
        .all()
    )


@router.post("", response_model=PatientMedicationOut, status_code=status.HTTP_201_CREATED)
def add_medication(
    payload: PatientMedicationCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    med = PatientMedication(user_id=current_user.id, **payload.model_dump())
    db.add(med)
    db.commit()
    db.refresh(med)
    return med


@router.put("/{medication_id}/log")
def log_dose_taken(
    medication_id: str,
    was_taken: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    med = db.get(PatientMedication, medication_id)
    if med is None or med.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Medication not found")
    db.add(MedicationLog(patient_medication_id=medication_id, taken_at=date.today(), was_taken=was_taken))
    db.commit()
    return {"detail": "Logged"}


@router.delete("/{medication_id}", status_code=status.HTTP_204_NO_CONTENT)
def stop_medication(medication_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    med = db.get(PatientMedication, medication_id)
    if med is None or med.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Medication not found")
    med.is_active = False
    db.commit()
