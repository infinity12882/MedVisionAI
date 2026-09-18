from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.prediction import MedicalHistory, Prediction
from app.models.system import Notification
from app.models.user import User
from app.schemas.misc import NotificationOut
from app.services.pdf_report import generate_prediction_report_pdf

router = APIRouter(tags=["History & Reports"])


@router.get("/history", response_model=list[dict])
def get_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = (
        db.query(MedicalHistory)
        .filter(MedicalHistory.user_id == current_user.id)
        .order_by(MedicalHistory.created_at.desc())
        .all()
    )
    return [
        {
            "id": r.id,
            "event_type": r.event_type,
            "title": r.title,
            "detail": r.detail,
            "prediction_id": r.prediction_id,
            "created_at": r.created_at,
        }
        for r in rows
    ]


@router.get("/reports/{prediction_id}/pdf")
def download_pdf_report(
    prediction_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    prediction = db.get(Prediction, prediction_id)
    if prediction is None or (prediction.user_id != current_user.id and current_user.role.value != "admin"):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Prediction not found")

    pdf_path = generate_prediction_report_pdf(current_user, prediction)
    return FileResponse(pdf_path, media_type="application/pdf", filename=f"medvision_report_{prediction_id}.pdf")


@router.get("/notifications", response_model=list[NotificationOut])
def get_notifications(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .all()
    )


@router.put("/notifications/{notification_id}/read", response_model=NotificationOut)
def mark_notification_read(
    notification_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    notification = db.get(Notification, notification_id)
    if notification is None or notification.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Notification not found")
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification
