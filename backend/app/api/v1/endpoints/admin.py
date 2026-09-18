from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.article import MedicalArticle
from app.models.disease import Disease, Symptom
from app.models.medication import Medication
from app.models.prediction import Prediction
from app.models.system import AuditLog
from app.models.upload import ImageRecord, LabReport, VoiceRecord
from app.models.user import DoctorProfile, User, UserRole
from app.schemas.auth import UserOut
from app.schemas.misc import DatasetAnalyticsOut
from app.services.rag.indexer import reindex_all

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/analytics", response_model=DatasetAnalyticsOut)
def get_analytics(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)

    def _daily_counts(model, date_field):
        rows = (
            db.query(func.date(date_field), func.count())
            .filter(date_field >= seven_days_ago)
            .group_by(func.date(date_field))
            .all()
        )
        return [{"date": str(d), "count": c} for d, c in rows]

    return DatasetAnalyticsOut(
        total_diseases=db.query(Disease).count(),
        total_symptoms=db.query(Symptom).count(),
        total_medications=db.query(Medication).count(),
        total_articles=db.query(MedicalArticle).count(),
        total_images=db.query(ImageRecord).count(),
        total_voice_records=db.query(VoiceRecord).count(),
        total_lab_reports=db.query(LabReport).count(),
        total_verified_cases=db.query(ImageRecord).filter(ImageRecord.is_verified.is_(True)).count()
        + db.query(VoiceRecord).filter(VoiceRecord.is_verified.is_(True)).count(),
        total_users=db.query(User).count(),
        total_doctors=db.query(User).filter(User.role == UserRole.DOCTOR).count(),
        total_patients=db.query(User).filter(User.role == UserRole.PATIENT).count(),
        predictions_last_7_days=_daily_counts(Prediction, Prediction.created_at),
        uploads_last_7_days=_daily_counts(ImageRecord, ImageRecord.created_at),
    )


@router.get("/analytics/trending-conditions", response_model=list[dict])
def trending_conditions(
    db: Session = Depends(get_db), admin: User = Depends(require_admin), days: int = 30, limit: int = 10
):
    """
    Anonymized, aggregate-only view of which conditions are trending
    across the whole platform — no individual patient data is exposed,
    only disease name + case count. Useful as an early "outbreak radar"
    signal for an admin or public-health partner.
    """
    since = datetime.now(timezone.utc) - timedelta(days=days)
    rows = (
        db.query(Prediction.top_disease, Prediction.risk_level, func.count(Prediction.id).label("case_count"))
        .filter(Prediction.created_at >= since, Prediction.top_disease.isnot(None))
        .group_by(Prediction.top_disease, Prediction.risk_level)
        .order_by(func.count(Prediction.id).desc())
        .limit(limit)
        .all()
    )
    return [{"disease_name": name, "case_count": count, "risk_level": risk.value} for name, risk, count in rows]


@router.get("/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), admin: User = Depends(require_admin), role: UserRole | None = None):
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    return query.order_by(User.created_at.desc()).all()


@router.put("/users/{user_id}/role", response_model=UserOut)
def change_user_role(
    user_id: str, new_role: UserRole, db: Session = Depends(get_db), admin: User = Depends(require_admin)
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    user.role = new_role
    if new_role == UserRole.DOCTOR and not db.query(DoctorProfile).filter(DoctorProfile.user_id == user.id).first():
        db.add(DoctorProfile(user_id=user.id))
    db.commit()
    db.refresh(user)
    return user


@router.put("/users/{user_id}/deactivate", response_model=UserOut)
def deactivate_user(user_id: str, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    user.is_active = False
    db.commit()
    db.refresh(user)
    return user


@router.put("/users/{user_id}/activate", response_model=UserOut)
def activate_user(user_id: str, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    user.is_active = True
    db.commit()
    db.refresh(user)
    return user


@router.put("/doctors/{user_id}/verify", response_model=UserOut)
def verify_doctor(user_id: str, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    profile = db.query(DoctorProfile).filter(DoctorProfile.user_id == user_id).first()
    if profile is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Doctor profile not found")
    profile.is_verified = True
    db.commit()
    return db.get(User, user_id)


@router.post("/knowledge-base/reindex")
def trigger_reindex(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    count = reindex_all(db)
    return {"detail": f"Knowledge base reindexed: {count} chunks now searchable via RAG."}


@router.get("/audit-logs", response_model=list[dict])
def get_audit_logs(db: Session = Depends(get_db), admin: User = Depends(require_admin), limit: int = 100):
    rows = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()
    return [
        {
            "id": r.id,
            "user_id": r.user_id,
            "action": r.action,
            "resource_type": r.resource_type,
            "resource_id": r.resource_id,
            "ip_address": r.ip_address,
            "created_at": r.created_at,
        }
        for r in rows
    ]


@router.post("/images/{image_id}/verify")
def verify_image_label(
    image_id: str,
    verified_label: str,
    severity: str | None = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Expert validation step for the Image Dataset Builder / Active Learning pipeline."""
    record = db.get(ImageRecord, image_id)
    if record is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Image record not found")
    record.verified_label = verified_label
    record.severity = severity
    record.is_verified = True
    record.expert_approved_by = admin.id
    db.commit()
    return {"detail": "Image verified and added to the training dataset for the next model retrain."}


@router.post("/models/retrain-vision")
def retrain_vision_model(admin: User = Depends(require_admin)):
    """Kicks off vision model retraining as a background Celery task."""
    from app.tasks.training_tasks import retrain_vision_model_task

    task = retrain_vision_model_task.delay()
    return {"detail": "Vision model retraining started.", "task_id": task.id}
