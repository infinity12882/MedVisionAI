from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


# ---------- Auth ----------
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=255)
    role: UserRole = UserRole.PATIENT  # admins are promoted manually, not self-registered as admin
    referral_code: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    totp_code: str | None = None


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class EmailVerifyRequest(BaseModel):
    token: str


# ---------- User ----------
class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    is_email_verified: bool
    preferred_language: str
    dark_mode: bool
    created_at: datetime


class UserUpdate(BaseModel):
    full_name: str | None = None
    preferred_language: str | None = Field(default=None, pattern="^(en|uz|ru)$")
    dark_mode: bool | None = None


class PatientProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date_of_birth: date | None = None
    sex: str | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    chronic_conditions: str | None = None
    allergies: str | None = None
    sleep_hours_avg: float | None = None
    water_intake_liters_avg: float | None = None
    exercise_minutes_per_week: int | None = None
    stress_level: int | None = None


class PatientProfileUpdate(BaseModel):
    date_of_birth: date | None = None
    sex: str | None = None
    height_cm: float | None = Field(default=None, ge=30, le=272)
    weight_kg: float | None = Field(default=None, ge=1, le=500)
    chronic_conditions: str | None = None
    allergies: str | None = None
    sleep_hours_avg: float | None = Field(default=None, ge=0, le=24)
    water_intake_liters_avg: float | None = Field(default=None, ge=0, le=20)
    exercise_minutes_per_week: int | None = Field(default=None, ge=0, le=2000)
    stress_level: int | None = Field(default=None, ge=1, le=10)


class DoctorProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    specialty: str
    license_number: str | None = None
    bio: str | None = None
    years_experience: int
    is_verified: bool


class DoctorProfileUpdate(BaseModel):
    specialty: str | None = None
    license_number: str | None = None
    bio: str | None = None
    years_experience: int | None = Field(default=None, ge=0, le=70)
