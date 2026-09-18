"""
Thin wrapper around a FAISS index, persisted to disk alongside a sidecar
JSON mapping vector positions back to KnowledgeChunk IDs.
"""
from __future__ import annotations

import json
from pathlib import Path

import faiss
import numpy as np

from app.core.config import settings


class FaissVectorStore:
    def __init__(self, dim: int, index_dir: str | None = None) -> None:
        self.dim = dim
        self.index_dir = Path(index_dir or settings.FAISS_INDEX_DIR)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.index_dir / "index.faiss"
        self.meta_path = self.index_dir / "meta.json"

        # Inner-product search over L2-normalized vectors == cosine similarity.
        self.index = faiss.IndexFlatIP(dim)
        self.chunk_ids: list[str] = []  # position -> KnowledgeChunk.id

    def add(self, vectors: np.ndarray, chunk_ids: list[str]) -> list[int]:
        assert vectors.shape[0] == len(chunk_ids)
        start_pos = self.index.ntotal
        self.index.add(vectors.astype("float32"))
        self.chunk_ids.extend(chunk_ids)
        return list(range(start_pos, start_pos + len(chunk_ids)))

    def search(self, query_vector: np.ndarray, top_k: int = 5) -> list[tuple[str, float]]:
        if self.index.ntotal == 0:
            return []
        query = query_vector.reshape(1, -1).astype("float32")
        scores, positions = self.index.search(query, min(top_k, self.index.ntotal))
        results = []
        for pos, score in zip(positions[0], scores[0]):
            if pos == -1:
                continue
            results.append((self.chunk_ids[pos], float(score)))
        return results

    def reset(self) -> None:
        self.index = faiss.IndexFlatIP(self.dim)
        self.chunk_ids = []

    def save(self) -> None:
        faiss.write_index(self.index, str(self.index_path))
        self.meta_path.write_text(json.dumps({"dim": self.dim, "chunk_ids": self.chunk_ids}))

    def load(self) -> bool:
        """Returns True if a persisted index was found and loaded."""
        if not self.index_path.exists() or not self.meta_path.exists():
            return False
        self.index = faiss.read_index(str(self.index_path))
        meta = json.loads(self.meta_path.read_text())
        self.dim = meta["dim"]
        self.chunk_ids = meta["chunk_ids"]
        return True

    @property
    def total_vectors(self) -> int:
        return self.index.ntotal
