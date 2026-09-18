"""
Family accounts: a patient can register dependents (children, elderly
parents, etc.) and run any diagnosis flow "on behalf of" them. Dependents
are lightweight profiles, not full User accounts — no login of their own.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class FamilyMember(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "family_members"

    guardian_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    relationship: Mapped[str] = mapped_column(String(50), nullable=False)  # child, parent, spouse, sibling, other
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    sex: Mapped[str | None] = mapped_column(String(20), nullable=True)
    chronic_conditions: Mapped[str | None] = mapped_column(Text, nullable=True)
    allergies: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
