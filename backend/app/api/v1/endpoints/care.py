from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.db.session import get_db
from app.models.care import CareConnection, ConnectionStatus, DirectConversation, DirectMessage
from app.models.user import DoctorProfile, User, UserRole
from app.schemas.extended import (
    CareConnectionOut,
    DirectConversationOut,
    DirectMessageCreate,
    DirectMessageOut,
    DoctorPublicOut,
)
from app.services.notify import notify

router = APIRouter(tags=["Care Connections & Messaging"])


@router.get("/doctors", response_model=list[DoctorPublicOut])
def list_doctors(db: Session = Depends(get_db)):
    rows = db.query(DoctorProfile, User).join(User, DoctorProfile.user_id == User.id).filter(User.is_active.is_(True)).all()
    return [
        DoctorPublicOut(
            user_id=profile.user_id,
            full_name=user.full_name,
            specialty=profile.specialty,
            years_experience=profile.years_experience,
            is_verified=profile.is_verified,
        )
        for profile, user in rows
    ]


@router.post("/care-connections/{doctor_id}", response_model=CareConnectionOut, status_code=status.HTTP_201_CREATED)
def request_connection(
    doctor_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_role(UserRole.PATIENT))
):
    existing = (
        db.query(CareConnection)
        .filter(CareConnection.patient_id == current_user.id, CareConnection.doctor_id == doctor_id)
        .first()
    )
    if existing:
        return existing

    doctor = db.get(User, doctor_id)
    if doctor is None or doctor.role != UserRole.DOCTOR:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Doctor not found")

    connection = CareConnection(patient_id=current_user.id, doctor_id=doctor_id, status=ConnectionStatus.PENDING)
    db.add(connection)
    db.commit()
    db.refresh(connection)

    notify(
        db,
        user_id=doctor_id,
        title="New patient connection request",
        message=f"{current_user.full_name} would like to connect with you.",
        category="info",
    )
    return connection


@router.get("/care-connections/my", response_model=list[CareConnectionOut])
def my_connections(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role == UserRole.DOCTOR:
        return db.query(CareConnection).filter(CareConnection.doctor_id == current_user.id).all()
    return db.query(CareConnection).filter(CareConnection.patient_id == current_user.id).all()


@router.put("/care-connections/{connection_id}/accept", response_model=CareConnectionOut)
def accept_connection(
    connection_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_role(UserRole.DOCTOR))
):
    connection = db.get(CareConnection, connection_id)
    if connection is None or connection.doctor_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Connection request not found")
    connection.status = ConnectionStatus.ACTIVE
    db.commit()
    db.refresh(connection)
    notify(db, user_id=connection.patient_id, title="Connection accepted", message=f"Dr. {current_user.full_name} accepted your request.")
    return connection


def _get_or_create_conversation(db: Session, patient_id: str, doctor_id: str) -> DirectConversation:
    convo = (
        db.query(DirectConversation)
        .filter(DirectConversation.patient_id == patient_id, DirectConversation.doctor_id == doctor_id)
        .first()
    )
    if convo is None:
        convo = DirectConversation(patient_id=patient_id, doctor_id=doctor_id)
        db.add(convo)
        db.commit()
        db.refresh(convo)
    return convo


@router.get("/messages/conversations", response_model=list[DirectConversationOut])
def list_conversations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role == UserRole.DOCTOR:
        rows = db.query(DirectConversation).filter(DirectConversation.doctor_id == current_user.id).all()
    else:
        rows = db.query(DirectConversation).filter(DirectConversation.patient_id == current_user.id).all()

    results = []
    for convo in rows:
        other_id = convo.doctor_id if current_user.role != UserRole.DOCTOR else convo.patient_id
        other_user = db.get(User, other_id)
        last_msg = (
            db.query(DirectMessage)
            .filter(DirectMessage.conversation_id == convo.id)
            .order_by(DirectMessage.created_at.desc())
            .first()
        )
        results.append(
            DirectConversationOut(
                id=convo.id,
                patient_id=convo.patient_id,
                doctor_id=convo.doctor_id,
                other_party_name=other_user.full_name if other_user else None,
                last_message=last_msg.content if last_msg else None,
                created_at=convo.created_at,
            )
        )
    return results


@router.post("/messages/with/{other_user_id}", response_model=DirectMessageOut)
def send_message(
    other_user_id: str,
    payload: DirectMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.DOCTOR:
        patient_id, doctor_id = other_user_id, current_user.id
    elif current_user.role == UserRole.PATIENT:
        patient_id, doctor_id = current_user.id, other_user_id
    else:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only doctors and patients can message each other")

    convo = _get_or_create_conversation(db, patient_id, doctor_id)
    message = DirectMessage(conversation_id=convo.id, sender_id=current_user.id, content=payload.content)
    db.add(message)
    db.commit()
    db.refresh(message)

    notify(db, user_id=other_user_id, title=f"New message from {current_user.full_name}", message=payload.content[:120])
    return message


@router.get("/messages/conversations/{conversation_id}", response_model=list[DirectMessageOut])
def get_messages(
    conversation_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    convo = db.get(DirectConversation, conversation_id)
    if convo is None or current_user.id not in (convo.patient_id, convo.doctor_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found")

    messages = (
        db.query(DirectMessage).filter(DirectMessage.conversation_id == conversation_id).order_by(DirectMessage.created_at).all()
    )
    for m in messages:
        if m.sender_id != current_user.id:
            m.is_read = True
    db.commit()
    return messages
