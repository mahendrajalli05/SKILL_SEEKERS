"""Embedding backends for Overlap Intelligence V1.

Production prefers Sentence Transformers (`all-MiniLM-L6-v2`) when the
package is installed. Tests and machines without model weights use a
deterministic hashed-token + character n-gram backend. Cosine scoring is
the same in both cases. Scenario labels are never embedded.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from typing import Protocol

from app.engines.overlap.constants import (
    HASHED_EMBEDDER_NAME,
    HASHED_EMBEDDING_DIM,
    SENTENCE_TRANSFORMER_MODEL,
)
from app.engines.overlap.text import compact_embedding_text, overlap_tokens


class EmbeddingBackend(Protocol):
    name: str

    def embed(self, texts: Sequence[str]) -> list[tuple[float, ...] | None]:
        """Return one L2-normalised vector per text. Empty text → None."""


def _accumulate(vector: list[float], key: str, weight: float) -> None:
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    dim = len(vector)
    for offset in (0, 4, 8, 12):
        index = int.from_bytes(digest[offset : offset + 2], "little") % dim
        sign = 1.0 if digest[offset + 2] % 2 == 0 else -1.0
        vector[index] += sign * weight


def _l2_normalize(vector: list[float]) -> tuple[float, ...]:
    norm_sq = sum(value * value for value in vector)
    if norm_sq <= 0.0:
        return tuple(vector)
    norm = norm_sq**0.5
    return tuple(value / norm for value in vector)


class HashedTokenEmbedder:
    """Deterministic lexical embedding. Not a neural sentence model."""

    name = HASHED_EMBEDDER_NAME

    def __init__(self, dim: int = HASHED_EMBEDDING_DIM) -> None:
        self.dim = dim
        self._cache: dict[str, tuple[float, ...]] = {}

    def embed_one(self, text: str) -> tuple[float, ...] | None:
        cleaned = (text or "").strip()
        if not cleaned:
            return None
        cached = self._cache.get(cleaned)
        if cached is not None:
            return cached
        vector = [0.0] * self.dim
        tokens = overlap_tokens(cleaned)
        if not tokens:
            for char in cleaned.casefold():
                if char.isalnum():
                    _accumulate(vector, f"ch:{char}", 1.0)
        for token in sorted(tokens):
            _accumulate(vector, f"tok:{token}", 1.0)
        compact = compact_embedding_text(cleaned)
        if len(compact) >= 4:
            for index in range(len(compact) - 3):
                _accumulate(vector, f"ng:{compact[index:index + 4]}", 0.35)
        result = _l2_normalize(vector)
        self._cache[cleaned] = result
        return result

    def embed(self, texts: Sequence[str]) -> list[tuple[float, ...] | None]:
        return [self.embed_one(text) for text in texts]


class SentenceTransformerEmbedder:
    """Neural semantic embeddings. Requires ``sentence-transformers``."""

    def __init__(self, model_name: str = SENTENCE_TRANSFORMER_MODEL) -> None:
        from sentence_transformers import SentenceTransformer

        self.model_name = model_name
        self.name = f"sentence-transformers/{model_name}"
        self._model = SentenceTransformer(model_name)
        self._cache: dict[str, tuple[float, ...]] = {}

    def embed(self, texts: Sequence[str]) -> list[tuple[float, ...] | None]:
        pending: list[str] = []
        for text in texts:
            cleaned = (text or "").strip()
            if cleaned and cleaned not in self._cache:
                pending.append(cleaned)
        unique_pending = list(dict.fromkeys(pending))
        if unique_pending:
            vectors = self._model.encode(
                unique_pending,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            for text, row in zip(unique_pending, vectors, strict=True):
                self._cache[text] = tuple(float(value) for value in row)
        out: list[tuple[float, ...] | None] = []
        for text in texts:
            cleaned = (text or "").strip()
            if not cleaned:
                out.append(None)
            else:
                out.append(self._cache[cleaned])
        return out


def try_sentence_transformer_embedder() -> SentenceTransformerEmbedder | None:
    try:
        return SentenceTransformerEmbedder()
    except Exception:
        return None


def get_default_embedder() -> EmbeddingBackend:
    """Prefer Sentence Transformers; fall back to the hashed embedder."""
    neural = try_sentence_transformer_embedder()
    if neural is not None:
        return neural
    return HashedTokenEmbedder()
