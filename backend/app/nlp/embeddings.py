"""Thin wrapper around sentence-transformers so the rest of the app never
touches the model directly.

Model choice: all-MiniLM-L6-v2 — 80MB, runs fine on a CPU-only free-tier
dyno, and is the standard baseline for semantic-similarity tasks like this
one. Swap it for a bigger model later if match quality needs it; nothing
outside this file would need to change.

IMPORTANT — lazy loading
------------------------
`sentence_transformers` drags in torch and transformers: ~4 seconds of import
on a fast machine, and far longer on a throttled free-tier instance.

uvicorn must finish importing the app BEFORE it can bind a port, and hosts
like Render kill a deploy that hasn't opened a port in time. Importing torch
at module scope therefore risks the deploy failing outright with
"No open ports detected". So the heavy import happens inside `_get_model()`,
on the first request that actually needs an embedding — long after the port
is open.

Embedding cache
---------------
Encoding is the expensive part of matching, and job descriptions basically
never change once ingested, so every embedding we compute is remembered:

  - warm_cache(texts) encodes anything new in ONE batch call, which is far
    faster than one call per text. The match router calls it before scoring.
  - embed(text) / embed_cached(text) are cache lookups that fall back to a
    single encode.

Before the cache existed, every /match request re-encoded the whole jobs table
one job at a time: ~57 seconds per page load on a free-tier instance. Now
repeat loads do no model work at all.

If the model can't be loaded — interrupted download, out of memory, no
network — the failure is remembered so we don't retry (and stall) 85 times in
one request, and callers fall back to a neutral score instead of 500ing.
"""

import hashlib
import threading
import traceback

import numpy as np

_MODEL_NAME = "all-MiniLM-L6-v2"

# Roughly 4x the number of jobs you'd have before moving to a real vector store.
_CACHE_LIMIT = 20_000

_cache: dict[str, np.ndarray] = {}
_hits = 0
_misses = 0

# Guards model loading and every encode call. FastAPI runs sync endpoints in a
# threadpool and the tokenizer underneath is not safe from two threads at once.
_lock = threading.RLock()

_model = None
_load_error: str | None = None
_load_failed = False


def _get_model():
    """
    Load the model on first use. Raises if it can't be loaded.

    On failure the state is remembered: later calls raise immediately instead
    of re-running the import (which would otherwise be retried once per job,
    turning one failure into 85 slow failures).
    """
    global _model, _load_error, _load_failed

    if _model is not None:
        return _model
    if _load_failed:
        raise RuntimeError(f"Embedding model unavailable: {_load_error}")

    with _lock:
        if _model is not None:
            return _model
        try:
            from sentence_transformers import SentenceTransformer

            _model = SentenceTransformer(_MODEL_NAME)
        except Exception:
            _load_failed = True
            _load_error = traceback.format_exc()
            raise
    return _model


def is_available() -> bool:
    """True if the embedding model can be used right now."""
    try:
        _get_model()
        return True
    except Exception:
        return False


def load_error() -> str | None:
    """Traceback from the failed model load, or None if it's fine."""
    try:
        _get_model()
        return None
    except Exception:
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
        "model_loaded": _model is not None,
        "model_failed": _load_failed,
    }


def cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    # Vectors are already L2-normalized (normalize_embeddings=True above),
    # so cosine similarity is just the dot product.
    return float(np.dot(vec_a, vec_b))


def preload() -> None:
    """
    Load the model now. Called from a background thread at startup so the
    first user request doesn't pay the import + model-load cost. Safe to call
    more than once.
    """
    try:
        _get_model()
    except Exception:
        pass
