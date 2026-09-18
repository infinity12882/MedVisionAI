from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import verify_password
from app.db.session import get_db
from app.models.chat import ChatConversation, ChatMessage
from app.models.prediction import MedicalHistory, Prediction
from app.models.upload import ImageRecord, LabReport, VoiceRecord
from app.models.user import User

router = APIRouter(prefix="/privacy", tags=["Privacy & Data Rights"])


def _serialize_row(row) -> dict:
    result = {}
    for column in row.__table__.columns:
        value = getattr(row, column.name)
        result[column.name] = value.isoformat() if hasattr(value, "isoformat") else value
    return result


@router.get("/export")
def export_my_data(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Returns every record tied to the current user as a single JSON document (GDPR Art. 20 style)."""
    data = {
        "user": _serialize_row(current_user),
        "predictions": [_serialize_row(p) for p in db.query(Prediction).filter(Prediction.user_id == current_user.id).all()],
        "medical_history": [
            _serialize_row(h) for h in db.query(MedicalHistory).filter(MedicalHistory.user_id == current_user.id).all()
        ],
        "image_records": [
            _serialize_row(i) for i in db.query(ImageRecord).filter(ImageRecord.user_id == current_user.id).all()
        ],
        "voice_records": [
            _serialize_row(v) for v in db.query(VoiceRecord).filter(VoiceRecord.user_id == current_user.id).all()
        ],
        "lab_reports": [
            _serialize_row(l) for l in db.query(LabReport).filter(LabReport.user_id == current_user.id).all()
        ],
        "chat_conversations": [],
    }

    conversations = db.query(ChatConversation).filter(ChatConversation.user_id == current_user.id).all()
    for convo in conversations:
        messages = db.query(ChatMessage).filter(ChatMessage.conversation_id == convo.id).all()
        data["chat_conversations"].append(
            {"conversation": _serialize_row(convo), "messages": [_serialize_row(m) for m in messages]}
        )

    headers = {"Content-Disposition": f"attachment; filename=medvision_data_export_{current_user.id[:8]}.json"}
    return JSONResponse(content=json.loads(json.dumps(data, default=str)), headers=headers)


from pydantic import BaseModel

class DeleteAccountRequest(BaseModel):
    password: str

@router.post("/delete-account")
def delete_my_account(
    request: DeleteAccountRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    Anonymizes and deactivates the account rather than hard-deleting rows,
    so referential integrity (predictions, audit logs, etc.) is preserved
    for any other party's records (e.g. a doctor's appointment history)
    while the requesting user's personal data is scrubbed.
    """
    if not verify_password(request.password, current_user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect password")

    current_user.email = f"deleted-{current_user.id[:8]}@deleted.medvision.ai"
    current_user.full_name = "Deleted User"
    current_user.hashed_password = "!"  # un-loginable hash
    current_user.is_active = False
    db.commit()
    return {"detail": "Your account has been deactivated and personal data anonymized."}
