from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.prediction import PredictionSource, RiskLevel
from app.models.upload import ImageBodyPart


# ---------- Text symptom checker ----------
class SymptomCheckRequest(BaseModel):
    symptoms_text: str = Field(min_length=3, max_length=4000, description="Free-text symptom description")
    family_member_id: str | None = Field(default=None, description="Run this check on behalf of a dependent")


class DiseasePredictionItem(BaseModel):
    disease_id: str | None = None
    disease_name: str
    probability: float
    explanation: str
    risk_level: RiskLevel
    recommended_specialist: str | None = None
    medicine_category: str | None = None
    home_care_tips: str | None = None
    foods_to_eat: str | None = None
    foods_to_avoid: str | None = None
    recovery_time_days: int | None = None
    when_to_visit_hospital: str | None = None
    emergency_signs: str | None = None


class ExplainabilityInfo(BaseModel):
    matched_symptoms: list[str] = Field(default_factory=list)
    feature_importance: dict[str, float] = Field(default_factory=dict)
    confidence_note: str | None = None


class PredictionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source: PredictionSource
    family_member_id: str | None = None
    input_summary: str
    results: list[DiseasePredictionItem]
    top_disease: str | None
    top_probability: float | None
    risk_level: RiskLevel
    recommended_specialist: str | None
    recovery_estimate_days: int | None
    explainability: ExplainabilityInfo
    created_at: datetime


# ---------- Image diagnosis ----------
class ImageDiagnosisOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    body_part: ImageBodyPart
    quality_ok: bool
    quality_note: str | None
    predicted_disease: str | None
    confidence_score: float | None
    risk_level: str | None
    explanation: str | None
    created_at: datetime


# ---------- Voice diagnosis ----------
class VoiceDiagnosisOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    transcript: str | None
    extracted_symptoms: list[str] = Field(default_factory=list)
    prediction: PredictionOut | None = None
    created_at: datetime


# ---------- Lab report ----------
class LabReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    ocr_text: str | None
    extracted_values: dict | None = None
    abnormal_findings: list[dict] | None = None
    summary: str | None
    created_at: datetime


# ---------- Multi-image progression ----------
class ProgressionPoint(BaseModel):
    image_id: str
    created_at: datetime
    predicted_disease: str | None
    confidence_score: float | None
    risk_level: str | None


class ProgressionOut(BaseModel):
    series_id: str
    body_part: str
    points: list[ProgressionPoint]
    trend: str  # "improving" | "worsening" | "stable" | "insufficient_data"
