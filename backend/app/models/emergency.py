"""
Location-based emergency features. Hospital/Pharmacy are a seeded
directory (see scripts/seed_data.py) searched by Haversine distance from
the user's coordinates — no external maps API required, though
`google_place_id`-style fields are left available for a production
deployment to enrich with live data later.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Hospital(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "hospitals"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    address: Mapped[str] = mapped_column(String(400), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    specialties: Mapped[str | None] = mapped_column(String(400), nullable=True)
    has_emergency_room: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Pharmacy(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "pharmacies"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    address: Mapped[str] = mapped_column(String(400), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_24h: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class EmergencyContact(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "emergency_contacts"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    relationship: Mapped[str | None] = mapped_column(String(50), nullable=True)
    phone: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)


class EmergencyAlert(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "emergency_alerts"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    notified_contacts_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
