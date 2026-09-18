"""
Predictions (one row per AI analysis run, any modality) and MedicalHistory
(a denormalized timeline used to drive the patient's progress charts and
the PDF report generator).
"""
from __future__ import annotations

import enum

from sqlalchemy import Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class PredictionSource(str, enum.Enum):
    TEXT = "text"
    VOICE = "voice"
    IMAGE = "image"
    LAB_REPORT = "lab_report"


class RiskLevel(str, enum.Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    EMERGENCY = "emergency"


class Prediction(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "predictions"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    family_member_id: Mapped[str | None] = mapped_column(ForeignKey("family_members.id"), nullable=True, index=True)
    source: Mapped[PredictionSource] = mapped_column(Enum(PredictionSource), nullable=False)
    source_record_id: Mapped[str | None] = mapped_column(String(36), nullable=True)  # FK to image/voice/lab record

    input_summary: Mapped[str] = mapped_column(Text, nullable=False)  # symptoms text / transcript / etc.
    # JSON-encoded list of {disease, probability, explanation, risk_level, specialist, ...}
    results_json: Mapped[str] = mapped_column(Text, nullable=False)
    top_disease: Mapped[str | None] = mapped_column(String(200), nullable=True)
    top_probability: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_level: Mapped[RiskLevel] = mapped_column(Enum(RiskLevel), default=RiskLevel.LOW, nullable=False)
    recommended_specialist: Mapped[str | None] = mapped_column(String(150), nullable=True)
    recovery_estimate_days: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Explainable AI fields
    detected_symptoms_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # which symptoms drove it
    feature_importance_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class MedicalHistory(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "medical_history"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    prediction_id: Mapped[str | None] = mapped_column(ForeignKey("predictions.id"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)  # prediction|image|voice|lab_report|note
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    health_score_snapshot: Mapped[float | None] = mapped_column(Float, nullable=True)
