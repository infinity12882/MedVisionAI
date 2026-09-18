"""
Chat history for the RAG + Gemini medical chatbot. Conversations group
messages so the assistant has memory across turns within a session.
"""
from __future__ import annotations

import enum

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ChatRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"


class ChatConversation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "chat_conversations"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), default="New conversation", nullable=False)


class ChatMessage(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "chat_messages"

    conversation_id: Mapped[str] = mapped_column(ForeignKey("chat_conversations.id"), nullable=False, index=True)
    role: Mapped[ChatRole] = mapped_column(Enum(ChatRole), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # JSON list of {source_type, source_id, title, snippet} — what RAG retrieved for this turn.
    retrieved_context_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    used_fallback: Mapped[bool] = mapped_column(default=False, nullable=False)  # true if Gemini was unavailable
