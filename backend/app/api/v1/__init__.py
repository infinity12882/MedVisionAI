from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin,
    api_keys,
    appointments,
    articles,
    auth,
    billing,
    care,
    chat,
    coach,
    diagnosis_image,
    diagnosis_lab,
    diagnosis_text,
    diagnosis_voice,
    diseases,
    emergency,
    family,
    health_tracking,
    history,
    medication_reminders,
    medications,
    privacy,
    public_api,
    referrals,
    symptoms,
    telemedicine,
    two_factor,
    users,
    ws,
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(diseases.router)
api_router.include_router(symptoms.router)
api_router.include_router(medications.router)
api_router.include_router(articles.router)
api_router.include_router(diagnosis_text.router)
api_router.include_router(diagnosis_image.router)
api_router.include_router(diagnosis_voice.router)
api_router.include_router(diagnosis_lab.router)
api_router.include_router(chat.router)
api_router.include_router(history.router)
api_router.include_router(admin.router)

# --- Newly added startup-grade features ---
api_router.include_router(family.router)
api_router.include_router(care.router)
api_router.include_router(appointments.router)
api_router.include_router(telemedicine.router)
api_router.include_router(medication_reminders.router)
api_router.include_router(health_tracking.router)
api_router.include_router(coach.router)
api_router.include_router(emergency.router)
api_router.include_router(api_keys.router)
api_router.include_router(referrals.router)
api_router.include_router(billing.router)
api_router.include_router(two_factor.router)
api_router.include_router(ws.router)
api_router.include_router(public_api.router)
api_router.include_router(privacy.router)
