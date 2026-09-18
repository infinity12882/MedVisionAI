"""
Knowledge-base indexing for RAG.

Every Disease, Symptom, Medication and MedicalArticle becomes one or more
`KnowledgeChunk` rows, which is what actually gets embedded and searched.
This means an admin adding a single new disease makes that disease
*immediately* searchable through chat/diagnosis RAG — no LLM retraining,
no separate "build dataset" step.

Strategy: full reindex on every knowledge-base write. For a startup-scale
knowledge base (hundreds to low tens-of-thousands of records) a full
TF-IDF refit + FAISS rebuild completes in well under a second to a few
seconds, which is simpler and far less bug-prone than incremental FAISS
mutation (FAISS's flat index has no in-place delete/update). At larger
scale this should move behind the Celery task in
`app/tasks/rag_tasks.py` and be debounced — the synchronous call below
already exists as `reindex_all`, swap the call site only.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.article import KnowledgeChunk, KnowledgeSourceType, MedicalArticle
from app.models.disease import Disease
from app.models.medication import Medication
from app.services.rag.engine import get_rag_engine


def _disease_chunk_text(d: Disease) -> str:
    parts = [
        f"Disease: {d.name}",
        f"Also known as: {d.alternative_names}" if d.alternative_names else "",
        f"ICD code: {d.icd_code}" if d.icd_code else "",
        f"Description: {d.description}" if d.description else "",
        f"Causes: {d.causes}" if d.causes else "",
        f"Risk factors: {d.risk_factors}" if d.risk_factors else "",
        f"Symptoms: {', '.join(link.symptom.name for link in d.symptom_links)}" if d.symptom_links else "",
        f"Complications: {d.complications}" if d.complications else "",
        f"Treatment overview: {d.treatment_overview}" if d.treatment_overview else "",
        f"Prevention: {d.prevention}" if d.prevention else "",
        f"Nutrition advice: {d.nutrition_advice}" if d.nutrition_advice else "",
        f"Recommended specialist: {d.recommended_specialist}" if d.recommended_specialist else "",
        f"Emergency warning signs: {d.emergency_warning_signs}" if d.emergency_warning_signs else "",
        f"Tags: {d.tags}" if d.tags else "",
    ]
    return "\n".join(p for p in parts if p)


def _symptom_chunk_text(symptom) -> str:
    parts = [
        f"Symptom: {symptom.name}",
        f"Body system: {symptom.body_system}" if symptom.body_system else "",
        f"Description: {symptom.description}" if symptom.description else "",
    ]
    return "\n".join(p for p in parts if p)


def _medication_chunk_text(m: Medication) -> str:
    parts = [
        f"Medication: {m.name}",
        f"Active ingredient: {m.active_ingredient}" if m.active_ingredient else "",
        f"Category: {m.drug_category}" if m.drug_category else "",
        f"General indications: {m.general_indications}" if m.general_indications else "",
        f"Contraindications: {m.contraindications}" if m.contraindications else "",
        f"Side effects: {m.possible_side_effects}" if m.possible_side_effects else "",
        f"Drug interactions: {m.drug_interactions}" if m.drug_interactions else "",
        f"Pregnancy considerations: {m.pregnancy_considerations}" if m.pregnancy_considerations else "",
        f"Educational notes: {m.educational_notes}" if m.educational_notes else "",
    ]
    return "\n".join(p for p in parts if p)


def _article_chunks(article: MedicalArticle, chunk_size: int = 1200) -> list[str]:
    text = article.raw_text or ""
    if not text.strip():
        return [f"Article: {article.title}"]
    chunks = []
    for i in range(0, len(text), chunk_size):
        snippet = text[i : i + chunk_size]
        chunks.append(f"Article: {article.title}\n{snippet}")
    return chunks


def reindex_all(db: Session) -> int:
    """Rebuild KnowledgeChunk rows + the FAISS index from the current DB state.
    Returns the number of chunks indexed."""
    from app.models.disease import Symptom

    db.query(KnowledgeChunk).delete()

    chunks: list[KnowledgeChunk] = []

    for disease in db.query(Disease).all():
        chunks.append(
            KnowledgeChunk(
                source_type=KnowledgeSourceType.DISEASE,
                source_id=disease.id,
                title=disease.name,
                content=_disease_chunk_text(disease),
            )
        )

    for symptom in db.query(Symptom).all():
        chunks.append(
            KnowledgeChunk(
                source_type=KnowledgeSourceType.SYMPTOM,
                source_id=symptom.id,
                title=symptom.name,
                content=_symptom_chunk_text(symptom),
            )
        )

    for med in db.query(Medication).all():
        chunks.append(
            KnowledgeChunk(
                source_type=KnowledgeSourceType.MEDICATION,
                source_id=med.id,
                title=med.name,
                content=_medication_chunk_text(med),
            )
        )

    for article in db.query(MedicalArticle).all():
        for text in _article_chunks(article):
            chunks.append(
                KnowledgeChunk(
                    source_type=KnowledgeSourceType.ARTICLE,
                    source_id=article.id,
                    title=article.title,
                    content=text,
                )
            )
        article.is_indexed = True

    db.add_all(chunks)
    db.flush()

    engine = get_rag_engine()
    if chunks:
        engine.rebuild([(c.id, c.content) for c in chunks])
    else:
        engine.clear()

    db.commit()
    return len(chunks)
