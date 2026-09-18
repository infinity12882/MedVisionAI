"""
User accounts and role-specific profiles (Doctor / Patient).

Role-based access control is implemented via the `UserRole` enum on `User`;
`app/api/deps.py` exposes dependency helpers (`require_role`) that endpoints
use to restrict access (e.g. only ADMIN can manage the knowledge base).
"""
from __future__ import annotations

import enum
from datetime import date, datetime

from sqlalchemy import Boolean, Date, Enum, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    DOCTOR = "doctor"
    PATIENT = "patient"


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.PATIENT, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_verification_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    password_reset_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    password_reset_expires: Mapped[datetime | None] = mapped_column(nullable=True)

    preferred_language: Mapped[str] = mapped_column(String(5), default="en", nullable=False)  # en | uz | ru
    dark_mode: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    doctor_profile: Mapped["DoctorProfile | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    patient_profile: Mapped["PatientProfile | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User {self.email} role={self.role}>"


class DoctorProfile(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "doctors"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    specialty: Mapped[str] = mapped_column(String(120), nullable=False, default="General Medicine")
    license_number: Mapped[str | None] = mapped_column(String(120), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    years_experience: Mapped[int] = mapped_column(default=0, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped["User"] = relationship(back_populates="doctor_profile")


class PatientProfile(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "patients"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    sex: Mapped[str | None] = mapped_column(String(20), nullable=True)
    height_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    chronic_conditions: Mapped[str | None] = mapped_column(Text, nullable=True)  # comma separated, simple by design
    allergies: Mapped[str | None] = mapped_column(Text, nullable=True)
    sleep_hours_avg: Mapped[float | None] = mapped_column(Float, nullable=True)
    water_intake_liters_avg: Mapped[float | None] = mapped_column(Float, nullable=True)
    exercise_minutes_per_week: Mapped[int | None] = mapped_column(nullable=True)
    stress_level: Mapped[int | None] = mapped_column(nullable=True)  # 1-10 self reported

    user: Mapped["User"] = relationship(back_populates="patient_profile")
