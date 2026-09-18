from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.article import ArticleFileType


# ---------- Symptom ----------
class SymptomBase(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    description: str | None = None
    body_system: str | None = None


class SymptomCreate(SymptomBase):
    pass


class SymptomUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    body_system: str | None = None


class SymptomOut(SymptomBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: datetime


# ---------- Disease ----------
class DiseaseSymptomLink(BaseModel):
    symptom_id: str
    importance_score: float = Field(default=1.0, ge=0, le=1)


class DiseaseBase(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    alternative_names: str | None = None
    icd_code: str | None = None
    description: str | None = None
    causes: str | None = None
    risk_factors: str | None = None
    stages: str | None = None
    complications: str | None = None
    treatment_overview: str | None = None
    prevention: str | None = None
    nutrition_advice: str | None = None
    foods_to_eat: str | None = None
    foods_to_avoid: str | None = None
    lifestyle_advice: str | None = None
    recommended_specialist: str | None = None
    emergency_warning_signs: str | None = None
    references: str | None = None
    tags: str | None = None
    severity: str = "moderate"
    priority: int = 0
    avg_recovery_days: int | None = None
    image_url: str | None = None
    video_url: str | None = None
    pdf_url: str | None = None


class DiseaseCreate(DiseaseBase):
    symptoms: list[DiseaseSymptomLink] = Field(default_factory=list)


class DiseaseUpdate(BaseModel):
    """All fields optional for PATCH-style partial updates."""

    name: str | None = None
    alternative_names: str | None = None
    icd_code: str | None = None
    description: str | None = None
    causes: str | None = None
    risk_factors: str | None = None
    stages: str | None = None
    complications: str | None = None
    treatment_overview: str | None = None
    prevention: str | None = None
    nutrition_advice: str | None = None
    foods_to_eat: str | None = None
    foods_to_avoid: str | None = None
    lifestyle_advice: str | None = None
    recommended_specialist: str | None = None
    emergency_warning_signs: str | None = None
    references: str | None = None
    tags: str | None = None
    severity: str | None = None
    priority: int | None = None
    avg_recovery_days: int | None = None
    image_url: str | None = None
    video_url: str | None = None
    pdf_url: str | None = None
    symptoms: list[DiseaseSymptomLink] | None = None


class DiseaseSymptomOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    symptom_id: str
    importance_score: float
    symptom: SymptomOut


class DiseaseOut(DiseaseBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: datetime
    symptom_links: list[DiseaseSymptomOut] = Field(default_factory=list)


class DiseaseListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    severity: str
    recommended_specialist: str | None = None
    tags: str | None = None


# ---------- Medication ----------
class MedicationBase(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    active_ingredient: str | None = None
    drug_category: str | None = None
    general_indications: str | None = None
    contraindications: str | None = None
    possible_side_effects: str | None = None
    drug_interactions: str | None = None
    age_restrictions: str | None = None
    pregnancy_considerations: str | None = None
    storage_information: str | None = None
    educational_notes: str | None = None
    prescription_required: bool = True
    linked_disease_tags: str | None = None


class MedicationCreate(MedicationBase):
    pass


class MedicationUpdate(BaseModel):
    name: str | None = None
    active_ingredient: str | None = None
    drug_category: str | None = None
    general_indications: str | None = None
    contraindications: str | None = None
    possible_side_effects: str | None = None
    drug_interactions: str | None = None
    age_restrictions: str | None = None
    pregnancy_considerations: str | None = None
    storage_information: str | None = None
    educational_notes: str | None = None
    prescription_required: bool | None = None
    linked_disease_tags: str | None = None


class MedicationOut(MedicationBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: datetime


# ---------- Article ----------
class ArticleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    author: str | None
    file_type: ArticleFileType
    tags: str | None
    is_indexed: bool
    created_at: datetime
