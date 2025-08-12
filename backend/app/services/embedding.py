"""Embedding service abstraction.

Provides embed_texts(texts) -> list[list[float]] with retry/backoff using
Gemini client (google-generativeai) falling back to deterministic hash-based
embeddings when remote API unavailable (for tests / offline dev).
"""
from __future__ import annotations

from typing import List
import time, random
from .gemini_client import CLIENT

def embed_texts(texts: List[str], max_retries: int = 3, base_delay: float = 0.5) -> List[List[float]]:
    vectors: List[List[float]] = []
    for t in texts:
        attempt = 0
        while True:
            try:
                vec = CLIENT.embed([t])[0]
                vectors.append(vec)
                break
            except Exception:  # pragma: no cover - network failures
                attempt += 1
                if attempt > max_retries:
                    # fallback deterministic embedding
                    vectors.append(CLIENT._fallback_embed([t])[0])
                    break
                time.sleep(base_delay * (2 ** (attempt-1)) + random.random()*0.1)
    return vectors
