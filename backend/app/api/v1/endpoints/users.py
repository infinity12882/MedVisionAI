from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import DoctorProfile, PatientProfile, User, UserRole
from app.schemas.auth import (
    DoctorProfileOut,
    DoctorProfileUpdate,
    PatientProfileOut,
    PatientProfileUpdate,
    UserOut,
    UserUpdate,
)
from app.schemas.misc import HealthScoreOut
from app.services.health_score import calculate_health_score

router = APIRouter(prefix="/users", tags=["Users"])


@router.put("/me", response_model=UserOut)
def update_me(payload: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/me/patient-profile", response_model=PatientProfileOut)
def get_patient_profile(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.PATIENT:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only patients have a patient profile")
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == current_user.id).first()
    if profile is None:
        profile = PatientProfile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


@router.put("/me/patient-profile", response_model=PatientProfileOut)
def update_patient_profile(
    payload: PatientProfileUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    if current_user.role != UserRole.PATIENT:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only patients have a patient profile")
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == current_user.id).first()
    if profile is None:
        profile = PatientProfile(user_id=current_user.id)
        db.add(profile)
        db.flush()
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/me/doctor-profile", response_model=DoctorProfileOut)
def get_doctor_profile(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.DOCTOR:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only doctors have a doctor profile")
    profile = db.query(DoctorProfile).filter(DoctorProfile.user_id == current_user.id).first()
    if profile is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Doctor profile not found")
    return profile


@router.put("/me/doctor-profile", response_model=DoctorProfileOut)
def update_doctor_profile(
    payload: DoctorProfileUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    if current_user.role != UserRole.DOCTOR:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only doctors have a doctor profile")
    profile = db.query(DoctorProfile).filter(DoctorProfile.user_id == current_user.id).first()
    if profile is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Doctor profile not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/me/health-score", response_model=HealthScoreOut)
def get_health_score(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.PATIENT:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Health score is available for patient accounts only")
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == current_user.id).first()
    return calculate_health_score(profile)
