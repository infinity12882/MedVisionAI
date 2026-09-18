from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.care import AppointmentStatus, ConnectionStatus
from app.models.platform import SubscriptionTier


# ---------- Family ----------
class FamilyMemberBase(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    relationship: str
    date_of_birth: date | None = None
    sex: str | None = None
    chronic_conditions: str | None = None
    allergies: str | None = None
    notes: str | None = None


class FamilyMemberCreate(FamilyMemberBase):
    pass


class FamilyMemberOut(FamilyMemberBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: datetime


# ---------- Care connections ----------
class CareConnectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    patient_id: str
    doctor_id: str
    status: ConnectionStatus
    created_at: datetime


class DoctorPublicOut(BaseModel):
    user_id: str
    full_name: str
    specialty: str
    years_experience: int
    is_verified: bool


# ---------- Messaging ----------
class DirectMessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=4000)


class DirectMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    sender_id: str
    content: str
    is_read: bool
    created_at: datetime


class DirectConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    patient_id: str
    doctor_id: str
    other_party_name: str | None = None
    last_message: str | None = None
    created_at: datetime


# ---------- Appointments ----------
class TimeSlotCreate(BaseModel):
    start_time: datetime
    end_time: datetime


class TimeSlotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    doctor_id: str
    start_time: datetime
    end_time: datetime
    is_booked: bool


class AppointmentCreate(BaseModel):
    doctor_id: str
    slot_id: str
    reason: str | None = None


class AppointmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    patient_id: str
    doctor_id: str
    scheduled_at: datetime
    duration_minutes: int
    reason: str | None
    status: AppointmentStatus
    doctor_notes: str | None
    created_at: datetime


class AppointmentStatusUpdate(BaseModel):
    status: AppointmentStatus
    doctor_notes: str | None = None


# ---------- Health tracking ----------
class PatientMedicationCreate(BaseModel):
    medication_name: str
    dosage: str | None = None
    frequency_per_day: int = 1
    reminder_times: str = "09:00"
    start_date: date
    end_date: date | None = None
    notes: str | None = None


class PatientMedicationOut(PatientMedicationCreate):
    model_config = ConfigDict(from_attributes=True)
    id: str
    is_active: bool
    created_at: datetime


class SymptomDiaryCreate(BaseModel):
    entry_date: date
    mood_score: int | None = Field(default=None, ge=1, le=5)
    energy_level: int | None = Field(default=None, ge=1, le=5)
    pain_level: int | None = Field(default=None, ge=0, le=10)
    symptoms_text: str | None = None
    notes: str | None = None


class SymptomDiaryOut(SymptomDiaryCreate):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: datetime


class VaccinationCreate(BaseModel):
    vaccine_name: str
    dose_number: int = 1
    date_administered: date
    next_due_date: date | None = None
    administered_at: str | None = None
    notes: str | None = None


class VaccinationOut(VaccinationCreate):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: datetime


class WearableDataPointCreate(BaseModel):
    metric_type: str
    value: float
    recorded_date: date


class WearableDataPointOut(WearableDataPointCreate):
    model_config = ConfigDict(from_attributes=True)
    id: str
    source: str
    created_at: datetime


# ---------- Emergency ----------
class RouteInfo(BaseModel):
    """Route information from user to destination using Yandex Maps."""
    distance_km: float
    duration_minutes: float
    map_image_url: str | None = None
    polyline: list[tuple[float, float]] | None = None


class HospitalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    address: str
    latitude: float
    longitude: float
    phone: str | None
    specialties: str | None
    has_emergency_room: bool
    distance_km: float | None = None
    route_info: RouteInfo | None = None


class PharmacyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    address: str
    latitude: float
    longitude: float
    phone: str | None
    is_24h: bool
    distance_km: float | None = None
    route_info: RouteInfo | None = None


class EmergencyContactCreate(BaseModel):
    name: str
    relationship: str | None = None
    phone: str
    email: EmailStr | None = None


class EmergencyContactOut(EmergencyContactCreate):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: datetime


class EmergencyAlertCreate(BaseModel):
    latitude: float | None = None
    longitude: float | None = None
    message: str | None = None


class EmergencyAlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    latitude: float | None
    longitude: float | None
    message: str | None
    resolved: bool
    created_at: datetime


# ---------- Platform: API keys ----------
class ApiKeyCreate(BaseModel):
    name: str


class ApiKeyCreatedOut(BaseModel):
    id: str
    name: str
    key_prefix: str
    full_key: str  # shown once only


class ApiKeyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    key_prefix: str
    is_active: bool
    total_requests: int
    last_used_at: datetime | None
    created_at: datetime


# ---------- Platform: referrals ----------
class ReferralCodeOut(BaseModel):
    code: str
    uses_count: int


# ---------- Platform: billing ----------
class SubscriptionOut(BaseModel):
    tier: SubscriptionTier
    current_period_end: datetime | None
    is_stripe_configured: bool


class CheckoutSessionOut(BaseModel):
    preview_mode: bool
    checkout_url: str | None
    message: str | None = None


# ---------- Platform: 2FA ----------
class TwoFactorSetupOut(BaseModel):
    secret: str
    qr_code_data_url: str
    backup_codes: list[str]


class TwoFactorVerifyRequest(BaseModel):
    code: str


class TwoFactorStatusOut(BaseModel):
    is_enabled: bool


# ---------- Population health ----------
class TrendingConditionOut(BaseModel):
    disease_name: str
    case_count: int
    risk_level: str
