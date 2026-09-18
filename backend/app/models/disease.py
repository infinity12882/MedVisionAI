"""
Core medical knowledge base: Disease and Symptom entities and their
many-to-many relationship (each link carries an importance score so the
symptom checker can weigh which symptoms matter most for a given disease).
"""
from __future__ import annotations

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Symptom(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "symptoms"

    name: Mapped[str] = mapped_column(String(150), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    body_system: Mapped[str | None] = mapped_column(String(80), nullable=True)  # e.g. respiratory, skin, GI

    disease_links: Mapped[list["DiseaseSymptom"]] = relationship(
        back_populates="symptom", cascade="all, delete-orphan"
    )


class Disease(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "diseases"

    name: Mapped[str] = mapped_column(String(200), unique=True, index=True, nullable=False)
    alternative_names: Mapped[str | None] = mapped_column(Text, nullable=True)  # comma separated
    icd_code: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)

    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    causes: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_factors: Mapped[str | None] = mapped_column(Text, nullable=True)
    stages: Mapped[str | None] = mapped_column(Text, nullable=True)
    complications: Mapped[str | None] = mapped_column(Text, nullable=True)
    treatment_overview: Mapped[str | None] = mapped_column(Text, nullable=True)
    prevention: Mapped[str | None] = mapped_column(Text, nullable=True)
    nutrition_advice: Mapped[str | None] = mapped_column(Text, nullable=True)
    foods_to_eat: Mapped[str | None] = mapped_column(Text, nullable=True)
    foods_to_avoid: Mapped[str | None] = mapped_column(Text, nullable=True)
    lifestyle_advice: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommended_specialist: Mapped[str | None] = mapped_column(String(150), nullable=True)
    emergency_warning_signs: Mapped[str | None] = mapped_column(Text, nullable=True)
    references: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[str | None] = mapped_column(String(400), nullable=True)  # comma separated

    severity: Mapped[str] = mapped_column(String(20), default="moderate", nullable=False)  # mild/moderate/severe/critical
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # admin sort/feature priority
    avg_recovery_days: Mapped[int | None] = mapped_column(Integer, nullable=True)

    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    video_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    pdf_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    symptom_links: Mapped[list["DiseaseSymptom"]] = relationship(
        back_populates="disease", cascade="all, delete-orphan"
    )


class DiseaseSymptom(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "disease_symptoms"

    disease_id: Mapped[str] = mapped_column(ForeignKey("diseases.id"), nullable=False, index=True)
    symptom_id: Mapped[str] = mapped_column(ForeignKey("symptoms.id"), nullable=False, index=True)
    importance_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)  # 0.0 - 1.0

    disease: Mapped["Disease"] = relationship(back_populates="symptom_links")
    symptom: Mapped["Symptom"] = relationship(back_populates="disease_links")
