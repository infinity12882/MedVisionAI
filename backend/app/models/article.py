"""
Medical articles (uploaded PDFs/DOCX/Markdown/research papers) and the
KnowledgeChunk table, which is the atomic unit indexed into the FAISS
vector store for Retrieval-Augmented Generation.

Design note: rather than only embedding raw article text, we also generate
one KnowledgeChunk per Disease / Symptom / Medication record whenever those
are created or updated (see app/services/rag/indexer.py). This means the
*entire* structured knowledge base — not just uploaded articles — is
searchable through RAG immediately, with no retraining step, exactly as
specified.
"""
from __future__ import annotations

import enum

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ArticleFileType(str, enum.Enum):
    PDF = "pdf"
    DOCX = "docx"
    MARKDOWN = "markdown"
    TEXT = "text"


class MedicalArticle(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "medical_articles"

    title: Mapped[str] = mapped_column(String(300), nullable=False)
    author: Mapped[str | None] = mapped_column(String(200), nullable=True)
    file_type: Mapped[ArticleFileType] = mapped_column(Enum(ArticleFileType), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[str | None] = mapped_column(String(400), nullable=True)
    is_indexed: Mapped[bool] = mapped_column(default=False, nullable=False)


class KnowledgeSourceType(str, enum.Enum):
    DISEASE = "disease"
    SYMPTOM = "symptom"
    MEDICATION = "medication"
    ARTICLE = "article"
    VERIFIED_CASE = "verified_case"


class KnowledgeChunk(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """One retrievable, embeddable unit of knowledge-base text."""

    __tablename__ = "knowledge_chunks"

    source_type: Mapped[KnowledgeSourceType] = mapped_column(Enum(KnowledgeSourceType), nullable=False, index=True)
    source_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)  # id of Disease/Article/etc.
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # Position of this chunk's embedding vector inside the FAISS index file.
    vector_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
