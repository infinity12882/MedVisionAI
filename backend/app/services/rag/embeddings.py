"""
Embedding layer for RAG.

Two backends, selected by `settings.EMBEDDING_BACKEND`:

* "tfidf" (default) — a scikit-learn TF-IDF vectorizer fit over the
  knowledge base text. Fully offline, deterministic, zero external cost,
  and good enough for keyword-heavy medical text (symptom names, disease
  names) where exact/near-exact term overlap is exactly what we want to
  match on. This is what makes the RAG pipeline fully testable and
  demoable without any API key.

* "gemini" — uses Google's `text-embedding-004` model via the Gemini API
  for genuine semantic embeddings. Requires GEMINI_API_KEY and outbound
  internet access to Google's endpoints.

Both implement the same tiny interface: `fit(texts)`, `transform(texts)`,
`embed_query(text)`, all returning dense numpy float32 vectors so FAISS
can index them interchangeably.
"""
from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD

from app.core.config import settings

# Fixed dense dimensionality so the FAISS index size is stable regardless of
# vocabulary growth as the knowledge base expands.
TFIDF_DENSE_DIM = 256


class TfidfEmbedder:
    """Offline embedder: TF-IDF -> TruncatedSVD (LSA) -> fixed-size dense vector."""

    name = "tfidf"

    def __init__(self) -> None:
        self.vectorizer = TfidfVectorizer(max_features=20000, ngram_range=(1, 2), stop_words="english")
        self.svd: TruncatedSVD | None = None
        self._fitted = False

    def fit(self, texts: list[str]) -> None:
        if not texts:
            raise ValueError("Cannot fit embedder on an empty corpus")
        sparse = self.vectorizer.fit_transform(texts)
        n_components = min(TFIDF_DENSE_DIM, max(2, sparse.shape[1] - 1), max(2, sparse.shape[0] - 1))
        self.svd = TruncatedSVD(n_components=n_components, random_state=42)
        self.svd.fit(sparse)
        self._fitted = True

    def transform(self, texts: list[str]) -> np.ndarray:
        if not self._fitted or self.svd is None:
            raise RuntimeError("Embedder must be fit() before transform()")
        sparse = self.vectorizer.transform(texts)
        dense = self.svd.transform(sparse).astype("float32")
        return _l2_normalize(dense)

    def embed_query(self, text: str) -> np.ndarray:
        return self.transform([text])[0]

    @property
    def dim(self) -> int:
        if self.svd is None:
            raise RuntimeError("Embedder not fit yet")
        return self.svd.n_components

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump({"vectorizer": self.vectorizer, "svd": self.svd}, f)

    def load(self, path: Path) -> None:
        with open(path, "rb") as f:
            data = pickle.load(f)
        self.vectorizer = data["vectorizer"]
        self.svd = data["svd"]
        self._fitted = True


class GeminiEmbedder:
    """Online embedder using Google's text-embedding-004 via the Gemini API."""

    name = "gemini"
    EMBED_MODEL = "text-embedding-004"
    DIM = 768

    def __init__(self) -> None:
        if not settings.GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY is not set; cannot use the Gemini embedding backend")
        from google import genai

        self._client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def fit(self, texts: list[str]) -> None:
        pass  # nothing to fit — embeddings come straight from the hosted model

    def transform(self, texts: list[str]) -> np.ndarray:
        vectors = []
        for text in texts:
            result = self._client.models.embed_content(model=self.EMBED_MODEL, contents=text)
            vectors.append(result.embeddings[0].values)
        return _l2_normalize(np.array(vectors, dtype="float32"))

    def embed_query(self, text: str) -> np.ndarray:
        return self.transform([text])[0]

    @property
    def dim(self) -> int:
        return self.DIM

    def save(self, path: Path) -> None:
        pass  # stateless — nothing to persist

    def load(self, path: Path) -> None:
        pass


def _l2_normalize(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return matrix / norms


def get_embedder():
    if settings.EMBEDDING_BACKEND == "gemini":
        try:
            return GeminiEmbedder()
        except Exception:
            # Graceful degradation: fall back to offline embeddings rather than crash the app.
            return TfidfEmbedder()
    return TfidfEmbedder()
