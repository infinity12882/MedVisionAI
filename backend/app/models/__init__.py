"""
Import every ORM model here so that `Base.metadata` is fully populated.
This module is imported by Alembic's `env.py` and by `init_db.py` —
without it, autogenerate / create_all would silently miss tables.
"""
from app.db.base import Base  # noqa: F401

from app.models.user import User, DoctorProfile, PatientProfile  # noqa: F401
from app.models.disease import Disease, Symptom, DiseaseSymptom  # noqa: F401
from app.models.medication import Medication  # noqa: F401
from app.models.article import MedicalArticle, KnowledgeChunk  # noqa: F401
from app.models.upload import ImageRecord, VoiceRecord, LabReport  # noqa: F401
from app.models.prediction import Prediction, MedicalHistory  # noqa: F401
from app.models.chat import ChatConversation, ChatMessage  # noqa: F401
from app.models.system import Notification, AuditLog  # noqa: F401
from app.models.family import FamilyMember  # noqa: F401
from app.models.care import (  # noqa: F401
    CareConnection,
    DirectConversation,
    DirectMessage,
    DoctorTimeSlot,
    Appointment,
)
from app.models.health_tracking import (  # noqa: F401
    PatientMedication,
    MedicationLog,
    SymptomDiaryEntry,
    Vaccination,
    WearableDataPoint,
)
from app.models.emergency import Hospital, Pharmacy, EmergencyContact, EmergencyAlert  # noqa: F401
from app.models.platform import (  # noqa: F401
    ApiKey,
    ReferralCode,
    Referral,
    Subscription,
    UsageCounter,
    TwoFactorAuth,
)

__all__ = [
    "Base",
    "User",
    "DoctorProfile",
    "PatientProfile",
    "Disease",
    "Symptom",
    "DiseaseSymptom",
    "Medication",
    "MedicalArticle",
    "KnowledgeChunk",
    "ImageRecord",
    "VoiceRecord",
    "LabReport",
    "Prediction",
    "MedicalHistory",
    "ChatConversation",
    "ChatMessage",
    "Notification",
    "AuditLog",
    "FamilyMember",
    "CareConnection",
    "DirectConversation",
    "DirectMessage",
    "DoctorTimeSlot",
    "Appointment",
    "PatientMedication",
    "MedicationLog",
    "SymptomDiaryEntry",
    "Vaccination",
    "WearableDataPoint",
    "Hospital",
    "Pharmacy",
    "EmergencyContact",
    "EmergencyAlert",
    "ApiKey",
    "ReferralCode",
    "Referral",
    "Subscription",
    "UsageCounter",
    "TwoFactorAuth",
]
