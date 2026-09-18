"""
Medication educational database. The AI uses this strictly to surface
*general educational information* about medicine categories relevant to a
retrieved condition — never as a personalized prescription.
"""
from __future__ import annotations

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Medication(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "medications"

    name: Mapped[str] = mapped_column(String(200), unique=True, index=True, nullable=False)
    active_ingredient: Mapped[str | None] = mapped_column(String(200), nullable=True)
    drug_category: Mapped[str | None] = mapped_column(String(150), nullable=True)

    general_indications: Mapped[str | None] = mapped_column(Text, nullable=True)
    contraindications: Mapped[str | None] = mapped_column(Text, nullable=True)
    possible_side_effects: Mapped[str | None] = mapped_column(Text, nullable=True)
    drug_interactions: Mapped[str | None] = mapped_column(Text, nullable=True)
    age_restrictions: Mapped[str | None] = mapped_column(Text, nullable=True)
    pregnancy_considerations: Mapped[str | None] = mapped_column(Text, nullable=True)
    storage_information: Mapped[str | None] = mapped_column(Text, nullable=True)
    educational_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    prescription_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    linked_disease_tags: Mapped[str | None] = mapped_column(String(500), nullable=True)  # comma separated disease tags
