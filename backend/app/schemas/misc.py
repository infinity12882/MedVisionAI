from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.chat import ChatRole


# ---------- Chat ----------
class ChatSendRequest(BaseModel):
    conversation_id: str | None = None
    message: str = Field(min_length=1, max_length=4000)


class RetrievedSource(BaseModel):
    source_type: str
    source_id: str
    title: str
    snippet: str
    score: float


class ChatMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    role: ChatRole
    content: str
    retrieved_sources: list[RetrievedSource] = Field(default_factory=list)
    used_fallback: bool
    created_at: datetime


class ChatConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    created_at: datetime


class ChatSendResponse(BaseModel):
    conversation_id: str
    user_message: ChatMessageOut
    assistant_message: ChatMessageOut


# ---------- Notifications ----------
class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    message: str
    category: str
    is_read: bool
    created_at: datetime


# ---------- Health score ----------
class HealthScoreOut(BaseModel):
    overall_score: float = Field(ge=0, le=100)
    bmi: float | None
    bmi_category: str | None
    sleep_score: float
    stress_score: float
    water_intake_score: float
    exercise_score: float
    lifestyle_risk: str  # low | moderate | high
    recommendations: list[str]


# ---------- Admin analytics ----------
class DatasetAnalyticsOut(BaseModel):
    total_diseases: int
    total_symptoms: int
    total_medications: int
    total_articles: int
    total_images: int
    total_voice_records: int
    total_lab_reports: int
    total_verified_cases: int
    total_users: int
    total_doctors: int
    total_patients: int
    predictions_last_7_days: list[dict]
    uploads_last_7_days: list[dict]
