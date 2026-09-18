"""
Day-to-day health management tools: medication reminders, a daily
symptom/mood diary, vaccination history, and wearable device data
(manually entered or CSV-imported — see app/api/v1/endpoints/wearables.py
for the real OAuth integration points a production deployment would add
for Fitbit/Apple Health/Google Fit).
"""
from __future__ import annotations

from datetime import date, time

from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class PatientMedication(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "patient_medications"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    medication_name: Mapped[str] = mapped_column(String(200), nullable=False)
    dosage: Mapped[str | None] = mapped_column(String(100), nullable=True)
    frequency_per_day: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    reminder_times: Mapped[str] = mapped_column(String(200), default="09:00", nullable=False)  # comma-separated HH:MM
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class MedicationLog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "medication_logs"

    patient_medication_id: Mapped[str] = mapped_column(ForeignKey("patient_medications.id"), nullable=False, index=True)
    taken_at: Mapped[date] = mapped_column(nullable=False)
    was_taken: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class SymptomDiaryEntry(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "symptom_diary_entries"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    entry_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    mood_score: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1-5
    energy_level: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1-5
    pain_level: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 0-10
    symptoms_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class Vaccination(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "vaccinations"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    vaccine_name: Mapped[str] = mapped_column(String(150), nullable=False)
    dose_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    date_administered: Mapped[date] = mapped_column(Date, nullable=False)
    next_due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    administered_at: Mapped[str | None] = mapped_column(String(200), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class WearableDataPoint(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "wearable_data_points"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    metric_type: Mapped[str] = mapped_column(String(30), nullable=False)  # steps|heart_rate|sleep_hours|calories|weight_kg
    value: Mapped[float] = mapped_column(Float, nullable=False)
    recorded_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(30), default="manual", nullable=False)  # manual|csv_import
