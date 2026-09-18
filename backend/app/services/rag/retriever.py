from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.article import KnowledgeChunk
from app.services.rag.engine import get_rag_engine
from app.services.nlp.uzbek_medical import get_medical_extractor


def retrieve(db: Session, query: str, top_k: int = 5) -> list[dict]:
    """Search the knowledge base and return resolved, ready-to-display results.
    
    For Uzbek queries, automatically translates medical terms to English
    to improve RAG retrieval accuracy.
    """
    engine = get_rag_engine()
    
    # Expand Uzbek query with English translations for better matching
    extractor = get_medical_extractor()
    expanded_query = extractor.expand_query_with_translations(query)
    
    hits = engine.search(expanded_query, top_k=top_k)
    if not hits:
        return []

    chunk_ids = [chunk_id for chunk_id, _ in hits]
    chunks_by_id = {c.id: c for c in db.query(KnowledgeChunk).filter(KnowledgeChunk.id.in_(chunk_ids)).all()}

    results = []
    for chunk_id, score in hits:
        chunk = chunks_by_id.get(chunk_id)
        if chunk is None:
            continue  # stale vector pointing at a since-deleted chunk; skip
        snippet = chunk.content if len(chunk.content) <= 400 else chunk.content[:400] + "..."
        results.append(
            {
                "source_type": chunk.source_type.value,
                "source_id": chunk.source_id,
                "title": chunk.title,
                "snippet": snippet,
                "score": round(score, 4),
            }
        )
    return results
