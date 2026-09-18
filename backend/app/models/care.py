"""
Doctor portal infrastructure: care connections (a patient "follows" /
is accepted by a doctor), secure direct messaging between a connected
doctor and patient, doctor-defined availability slots, and appointment
booking against those slots (including telemedicine video calls, which
reuse the appointment id as the WebRTC signaling room id — see
app/api/v1/endpoints/telemedicine.py).
"""
from __future__ import annotations

import enum

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


from datetime import datetime

class ConnectionStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    ENDED = "ended"


class CareConnection(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "care_connections"

    patient_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    doctor_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    status: Mapped[ConnectionStatus] = mapped_column(Enum(ConnectionStatus), default=ConnectionStatus.PENDING, nullable=False)


class DirectConversation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "direct_conversations"

    patient_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    doctor_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)


class DirectMessage(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "direct_messages"

    conversation_id: Mapped[str] = mapped_column(ForeignKey("direct_conversations.id"), nullable=False, index=True)
    sender_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(default=False, nullable=False)


class DoctorTimeSlot(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "doctor_time_slots"

    doctor_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_booked: Mapped[bool] = mapped_column(default=False, nullable=False)


class AppointmentStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Appointment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "appointments"

    patient_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    doctor_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    slot_id: Mapped[str | None] = mapped_column(ForeignKey("doctor_time_slots.id"), nullable=True)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[AppointmentStatus] = mapped_column(Enum(AppointmentStatus), default=AppointmentStatus.PENDING, nullable=False)
    doctor_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
