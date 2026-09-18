"""
Upload records for the three modalities the platform accepts: images,
voice recordings, and laboratory reports (PDF/image).

Each upload row doubles as a "dataset builder" record: admin/doctor users
can attach a verified disease label, severity, body part, and approval
status, which is exactly what `app/services/ml/active_learning.py` and the
retraining scripts consume later.
"""
from __future__ import annotations

import enum

from sqlalchemy import Boolean, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ImageBodyPart(str, enum.Enum):
    SKIN = "skin"
    EYE = "eye"
    TONGUE = "tongue"
    NAILS = "nails"
    THROAT = "throat"
    WOUND = "wound"
    OTHER = "other"


class ImageRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "image_records"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    body_part: Mapped[ImageBodyPart] = mapped_column(Enum(ImageBodyPart), nullable=False)

    # AI analysis quality gate + predictions
    quality_ok: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    quality_note: Mapped[str | None] = mapped_column(String(300), nullable=True)
    predicted_disease: Mapped[str | None] = mapped_column(String(200), nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Dataset-builder / active-learning metadata
    series_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)  # groups multi-image series
    verified_label: Mapped[str | None] = mapped_column(String(200), nullable=True)
    severity: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    expert_approved_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)


class VoiceRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "voice_records"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_symptoms: Mapped[str | None] = mapped_column(Text, nullable=True)  # comma separated

    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verified_label: Mapped[str | None] = mapped_column(String(200), nullable=True)


class LabReport(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "lab_reports"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    ocr_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_values_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON string
    abnormal_findings_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON string
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
