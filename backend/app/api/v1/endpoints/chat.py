from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.chat import ChatConversation, ChatMessage, ChatRole
from app.models.platform import Subscription, SubscriptionTier, UsageCounter
from app.models.user import User
from app.schemas.misc import (
    ChatConversationOut,
    ChatMessageOut,
    ChatSendRequest,
    ChatSendResponse,
    RetrievedSource,
)
from app.services.llm.gemini_client import generate_grounded_reply
from app.services.rag.retriever import retrieve

router = APIRouter(prefix="/chat", tags=["Medical Chatbot"])


def _message_to_out(message: ChatMessage) -> ChatMessageOut:
    sources_raw = json.loads(message.retrieved_context_json or "[]")
    return ChatMessageOut(
        id=message.id,
        role=message.role,
        content=message.content,
        retrieved_sources=[RetrievedSource(**s) for s in sources_raw],
        used_fallback=message.used_fallback,
        created_at=message.created_at,
    )


@router.get("/conversations", response_model=list[ChatConversationOut])
def list_conversations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return (
        db.query(ChatConversation)
        .filter(ChatConversation.user_id == current_user.id)
        .order_by(ChatConversation.created_at.desc())
        .all()
    )


@router.get("/conversations/{conversation_id}/messages", response_model=list[ChatMessageOut])
def list_messages(
    conversation_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    convo = db.get(ChatConversation, conversation_id)
    if convo is None or convo.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found")
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.conversation_id == conversation_id)
        .order_by(ChatMessage.created_at)
        .all()
    )
    return [_message_to_out(m) for m in messages]


@router.post("/send", response_model=ChatSendResponse)
def send_message(
    payload: ChatSendRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    from datetime import date

    subscription = db.query(Subscription).filter(Subscription.user_id == current_user.id).first()
    is_premium = subscription is not None and subscription.tier == SubscriptionTier.PREMIUM

    if not is_premium:
        today = date.today()
        counter = (
            db.query(UsageCounter)
            .filter(UsageCounter.user_id == current_user.id, UsageCounter.usage_date == today)
            .first()
        )
        if counter is None:
            counter = UsageCounter(user_id=current_user.id, usage_date=today, chat_messages_count=0)
            db.add(counter)
            db.flush()
        if counter.chat_messages_count >= settings.FREE_TIER_DAILY_CHAT_LIMIT:
            raise HTTPException(
                status.HTTP_429_TOO_MANY_REQUESTS,
                f"You've reached today's free-tier limit of {settings.FREE_TIER_DAILY_CHAT_LIMIT} AI chat "
                "messages. Upgrade to Premium for unlimited chat, or try again tomorrow.",
            )
        counter.chat_messages_count += 1

    if payload.conversation_id:
        convo = db.get(ChatConversation, payload.conversation_id)
        if convo is None or convo.user_id != current_user.id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found")
    else:
        title = payload.message[:60] + ("..." if len(payload.message) > 60 else "")
        convo = ChatConversation(user_id=current_user.id, title=title)
        db.add(convo)
        db.flush()

    # Conversation memory: pull recent prior turns for context.
    history_rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.conversation_id == convo.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(10)
        .all()
    )
    history = [{"role": m.role.value, "content": m.content} for m in reversed(history_rows)]

    user_message = ChatMessage(conversation_id=convo.id, role=ChatRole.USER, content=payload.message)
    db.add(user_message)
    db.flush()

    retrieved = retrieve(db, payload.message, top_k=5)
    reply_text, used_fallback = generate_grounded_reply(payload.message, retrieved, history)

    assistant_message = ChatMessage(
        conversation_id=convo.id,
        role=ChatRole.ASSISTANT,
        content=reply_text,
        retrieved_context_json=json.dumps(retrieved),
        used_fallback=used_fallback,
    )
    db.add(assistant_message)
    db.commit()
    db.refresh(user_message)
    db.refresh(assistant_message)

    return ChatSendResponse(
        conversation_id=convo.id,
        user_message=_message_to_out(user_message),
        assistant_message=_message_to_out(assistant_message),
    )
