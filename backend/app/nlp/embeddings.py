"""
Thin wrapper around sentence-transformers so the rest of the app never
touches the model directly.

Model choice: all-MiniLM-L6-v2 — 80MB, runs fine on a CPU-only free-tier
dyno, and is the standard baseline for semantic-similarity tasks like
this one. Swap it for a bigger model later if match quality needs it;
nothing outside this file would need to change.
"""

from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer

_MODEL_NAME = "all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    # Loaded once per process (first request pays the cost, ~a few
    # seconds; every request after is fast). lru_cache gives us a
    # simple singleton without extra state-management code.
    return SentenceTransformer(_MODEL_NAME)


def embed(text: str) -> np.ndarray:
    model = _get_model()
    return model.encode(text or "", normalize_embeddings=True)


def embed_batch(texts: list[str]) -> np.ndarray:
    model = _get_model()
    return model.encode(texts, normalize_embeddings=True)


def cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    # Vectors are already L2-normalized (normalize_embeddings=True above),
    # so cosine similarity is just the dot product.
    return float(np.dot(vec_a, vec_b))
