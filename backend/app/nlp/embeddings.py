"""Thin wrapper around sentence-transformers so the rest of the app never
touches the model directly.

Model choice: all-MiniLM-L6-v2 — 80MB, runs fine on a CPU-only free-tier
dyno, and is the standard baseline for semantic-similarity tasks like this
one. Swap it for a bigger model later if match quality needs it; nothing
outside this file would need to change.

What changed from the first version, and why
--------------------------------------------
The original code called model.encode() once per job inside the scoring loop.
On a free-tier instance (512MB RAM) with 85 jobs in the database that meant 85
separate encodes per page load: minutes of work, heavy memory churn, and a
very good chance of the request being killed or the process running out of
memory. Repeat loads re-did all of it from scratch.

Now:
  - warm_cache(texts) encodes everything new in ONE batch, which is far faster
    and much gentler on memory. The match router calls it before scoring.
  - embed(text) / embed_cached(text) are cache lookups keyed by a hash of the
    text, so repeat loads do no model work at all.
  - A lock guards the model, because FastAPI runs sync endpoints in a
    threadpool and the underlying Rust tokenizer is not safe to hit from two
    threads at once ("Already borrowed" errors).
  - is_available() / load_error() let callers degrade gracefully instead of
    returning a 500 when the model can't be loaded.

Caveats, so this isn't oversold: the cache lives in the process, so it's empty
after each deploy and isn't shared between workers. The real long-term fix is
to precompute job embeddings at ingestion time and store them on the Job row.
"""

import hashlib
import threading
import traceback
from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer

_MODEL_NAME = "all-MiniLM-L6-v2"

# Roughly 4x the number of jobs you'd have before moving to a real vector store.
_CACHE_LIMIT = 20_000

_cache: dict[str, np.ndarray] = {}
_hits = 0
_misses = 0

# Guards model loading and every encode call. See the module docstring.
_lock = threading.RLock()

# Set if the model could not be loaded, so callers can fall back instead of
# failing the whole request. Reset by a successful load.
_load_error: str | None = None


@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    # Loaded once per process (first request pays the cost, ~a few seconds;
    # every request after is fast).
    return SentenceTransformer(_MODEL_NAME)


def is_available() -> bool:
    """True if the embedding model can be used right now."""
    global _load_error
    with _lock:
        try:
            _get_model()
            _load_error = None
            return True
        except Exception:
            _load_error = traceback.format_exc()
            return False


def load_error() -> str | None:
    """The traceback from the last failed model load, or None."""
    is_available()
    return _load_error


def _key(text: str) -> str:
    return hashlib.blake2b((text or "").encode("utf-8"), digest_size=16).hexdigest()


def _store(text: str, vector: np.ndarray) -> None:
    if len(_cache) >= _CACHE_LIMIT:
        # Crude eviction: drop everything rather than tracking LRU order.
        # Only reachable at tens of thousands of distinct texts.
        _cache.clear()
    _cache[_key(text)] = vector


def warm_cache(texts: list[str]) -> None:
    """Batch-encode every text that isn't cached yet, in a single model call."""
    global _misses

    missing: list[str] = []
    seen: set[str] = set()
    for text in texts:
        key = _key(text)
        if key in _cache or key in seen:
            continue
        seen.add(key)
        missing.append(text or "")

    if not missing:
        return

    with _lock:
        vectors = _get_model().encode(missing, normalize_embeddings=True)

    if len(missing) == 1:
        vectors = vectors.reshape(1, -1)

    for text, vector in zip(missing, vectors):
        _store(text, vector)
    _misses += len(missing)


def embed(text: str) -> np.ndarray:
    """Embedding for `text` — computed once, then served from the cache."""
    return embed_cached(text)


def embed_cached(text: str) -> np.ndarray:
    global _hits, _misses

    text = text or ""
    cached = _cache.get(_key(text))
    if cached is not None:
        _hits += 1
        return cached

    with _lock:
        vector = _get_model().encode(text, normalize_embeddings=True)

    _store(text, vector)
    _misses += 1
    return vector


def embed_batch(texts: list[str]) -> np.ndarray:
    with _lock:
        return _get_model().encode(texts, normalize_embeddings=True)


def cache_stats() -> dict:
    total = _hits + _misses
    return {
        "size": len(_cache),
        "limit": _CACHE_LIMIT,
        "hits": _hits,
        "misses": _misses,
        "hit_rate": round(_hits / total, 3) if total else 0.0,
    }


def cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    # Vectors are already L2-normalized (normalize_embeddings=True above),
    # so cosine similarity is just the dot product.
    return float(np.dot(vec_a, vec_b))
