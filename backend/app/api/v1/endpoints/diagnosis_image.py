from __future__ import annotations

import uuid

import cv2
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.disease import Disease
from app.models.prediction import MedicalHistory
from app.models.upload import ImageBodyPart, ImageRecord
from app.models.user import User
from app.schemas.diagnosis import ImageDiagnosisOut, ProgressionOut, ProgressionPoint
from app.services.uploads import save_image
from app.services.vision.classifier import is_model_available, predict
from app.services.vision.quality_check import check_image_quality

router = APIRouter(prefix="/diagnosis/image", tags=["Image Diagnosis"])

# Healthy-looking labels never warrant emergency/high risk; anything else maps by keyword.
_RISK_KEYWORDS = {
    "healthy": "low",
    "healing": "low",
    "fresh wound": "moderate",
    "infected": "high",
    "strep": "high",
    "fungal": "moderate",
}


def _infer_risk(label: str) -> str:
    lowered = label.lower()
    for keyword, risk in _RISK_KEYWORDS.items():
        if keyword in lowered:
            return risk
    return "moderate"


def _record_to_out(record: ImageRecord) -> ImageDiagnosisOut:
    return ImageDiagnosisOut.model_validate(record)


@router.post("", response_model=ImageDiagnosisOut)
def diagnose_image(
    body_part: ImageBodyPart = Form(...),
    series_id: str | None = Form(default=None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not is_model_available():
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "The image-analysis model isn't trained yet. Run scripts/train_vision_model.py first.",
        )

    file_path = save_image(file)
    image_bgr = cv2.imread(file_path)

    quality_ok, quality_note = check_image_quality(image_bgr)

    record = ImageRecord(
        user_id=current_user.id,
        file_path=file_path,
        body_part=body_part,
        quality_ok=quality_ok,
        quality_note=quality_note,
        series_id=series_id or None,
    )

    if not quality_ok:
        db.add(record)
        db.commit()
        db.refresh(record)
        return _record_to_out(record)

    try:
        result = predict(body_part.value, image_bgr)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))

    label = result["predicted_label"]
    confidence = result["confidence"]
    risk = _infer_risk(label)

    # Pull educational context from the knowledge base if a disease with a matching name exists.
    disease = db.query(Disease).filter(Disease.name.ilike(f"%{label}%")).first()
    explanation_parts = [
        f"The image was classified as '{label}' with {round(confidence * 100)}% model confidence, "
        f"based on color and texture patterns typical of this category."
    ]
    if disease and disease.description:
        explanation_parts.append(disease.description)
    explanation = " ".join(explanation_parts)

    record.predicted_disease = label
    record.confidence_score = confidence
    record.risk_level = risk
    record.explanation = explanation

    db.add(record)
    db.flush()

    db.add(
        MedicalHistory(
            user_id=current_user.id,
            event_type="image",
            title=f"Image analysis ({body_part.value}): {label}",
            detail=explanation,
        )
    )
    db.commit()
    db.refresh(record)
    return _record_to_out(record)


@router.get("/{image_id}", response_model=ImageDiagnosisOut)
def get_image_result(image_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    record = db.get(ImageRecord, image_id)
    if record is None or (record.user_id != current_user.id and current_user.role.value != "admin"):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Image record not found")
    return _record_to_out(record)


@router.get("/series/{series_id}/progression", response_model=ProgressionOut)
def get_progression(series_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    records = (
        db.query(ImageRecord)
        .filter(ImageRecord.series_id == series_id, ImageRecord.user_id == current_user.id)
        .order_by(ImageRecord.created_at)
        .all()
    )
    if not records:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No image series found with this ID")

    points = [
        ProgressionPoint(
            image_id=r.id,
            created_at=r.created_at,
            predicted_disease=r.predicted_disease,
            confidence_score=r.confidence_score,
            risk_level=r.risk_level,
        )
        for r in records
    ]

    risk_order = {"low": 0, "moderate": 1, "high": 2, "emergency": 3}
    trend = "insufficient_data"
    if len(points) >= 2:
        first_risk = risk_order.get((points[0].risk_level or "moderate"), 1)
        last_risk = risk_order.get((points[-1].risk_level or "moderate"), 1)
        if last_risk < first_risk:
            trend = "improving"
        elif last_risk > first_risk:
            trend = "worsening"
        else:
            trend = "stable"

    return ProgressionOut(series_id=series_id, body_part=records[0].body_part.value, points=points, trend=trend)
