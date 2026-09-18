"""
Process-wide RAG engine singleton: owns the fitted embedder and the FAISS
vector store, with disk persistence so the index survives restarts without
needing a full reindex every time.
"""
from __future__ import annotations

import threading

from app.services.rag.embeddings import TFIDF_DENSE_DIM, get_embedder
from app.services.rag.vector_store import FaissVectorStore

_lock = threading.Lock()
_engine_instance: "RagEngine | None" = None


class RagEngine:
    def __init__(self) -> None:
        self.embedder = get_embedder()
        # Use the embedder's target dim once fit; until then, use the TF-IDF default
        # so the FAISS index has a stable dimensionality to initialize with.
        initial_dim = getattr(self.embedder, "DIM", None) or TFIDF_DENSE_DIM
        self.store = FaissVectorStore(dim=initial_dim)
        self._ready = False
        self._try_load_persisted()

    def _try_load_persisted(self) -> None:
        import pickle
        from pathlib import Path

        from app.core.config import settings

        embedder_path = Path(settings.FAISS_INDEX_DIR) / "embedder.pkl"
        if self.store.load() and embedder_path.exists() and self.embedder.name == "tfidf":
            try:
                self.embedder.load(embedder_path)
                self._ready = True
            except Exception:
                self._ready = False

    def rebuild(self, id_text_pairs: list[tuple[str, str]]) -> None:
        """Full rebuild: refit embedder on all texts, re-embed everything, replace the index."""
        from pathlib import Path

        from app.core.config import settings

        ids = [pair[0] for pair in id_text_pairs]
        texts = [pair[1] for pair in id_text_pairs]

        self.embedder.fit(texts)
        vectors = self.embedder.transform(texts)

        self.store = FaissVectorStore(dim=vectors.shape[1])
        self.store.add(vectors, ids)
        self.store.save()

        if self.embedder.name == "tfidf":
            self.embedder.save(Path(settings.FAISS_INDEX_DIR) / "embedder.pkl")

        self._ready = True

    def clear(self) -> None:
        self.store.reset()
        self._ready = False

    def search(self, query: str, top_k: int = 5) -> list[tuple[str, float]]:
        if not self._ready or self.store.total_vectors == 0:
            return []
        query_vector = self.embedder.embed_query(query)
        return self.store.search(query_vector, top_k=top_k)

    @property
    def is_ready(self) -> bool:
        return self._ready and self.store.total_vectors > 0


def get_rag_engine() -> RagEngine:
    global _engine_instance
    with _lock:
        if _engine_instance is None:
            _engine_instance = RagEngine()
        return _engine_instance
