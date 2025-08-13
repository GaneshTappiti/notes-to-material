"""Gemini client wrapper.

Loads API key from environment (use backend/.env for local dev). Provides
embedding + text generation with graceful fallback when the SDK or key are
missing so tests and local offline flows still work deterministically.
"""
import os, hashlib, json, threading, time
from typing import List

try:  # load .env if present (local dev)
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:  # pragma: no cover
    pass

try:
    import google.generativeai as genai  # type: ignore
except ImportError:  # pragma: no cover
    genai = None

API_KEY = os.getenv("GOOGLE_API_KEY", "")
if genai and API_KEY:
    try:  # tolerate SDK version drift by getattr indirection
        _configure = getattr(genai, 'configure', None)
        if callable(_configure):
            _configure(api_key=API_KEY)
    except Exception:  # pragma: no cover
        pass

EMBED_MODEL_CANDIDATES = [
    "text-embedding-004",
    "gemini-embedding-001",
]

GEN_MODEL_CANDIDATES = [
    "gemini-1.5-flash",
    "gemini-pro",
]

class GeminiClient:
    def __init__(self):
        self.embed_model = EMBED_MODEL_CANDIDATES[0]
        self.gen_model = GEN_MODEL_CANDIDATES[0]
        self._lock = threading.Lock()
        self.calls_today = 0
        self._day = time.strftime('%Y-%m-%d')
        self.daily_limit = int(os.getenv('DAILY_CALL_LIMIT', '0'))  # 0 = unlimited

    def _fallback_embed(self, texts: List[str]) -> list[list[float]]:
        out = []
        for t in texts:
            h = hashlib.sha256(t.encode("utf-8")).digest()[:128]
            out.append([b/255.0 for b in h])
        return out

    def embed(self, texts: List[str]) -> list[list[float]]:
        if genai and API_KEY:
            vectors: list[list[float]] = []
            _embed_content = getattr(genai, 'embed_content', None)
            for t in texts:
                if not callable(_embed_content):
                    vectors.append(self._fallback_embed([t])[0])
                    continue
                try:
                    resp = _embed_content(model=self.embed_model, content=t)
                    emb = None
                    if isinstance(resp, dict):
                        emb = resp.get("embedding") or resp.get("embeddings", [None])[0]
                    else:  # SDK object variant
                        emb = getattr(resp, 'embedding', None) or getattr(resp, 'embeddings', [None])[0]
                    if emb is None:
                        raise ValueError("No embedding returned")
                    vectors.append(emb)
                except Exception:
                    vectors.append(self._fallback_embed([t])[0])
            return vectors
        return self._fallback_embed(texts)

    def generate(self, prompt: str) -> str:
        with self._lock:
            today = time.strftime('%Y-%m-%d')
            if today != self._day:
                self._day = today
                self.calls_today = 0
            if self.daily_limit and self.calls_today >= self.daily_limit:
                return json.dumps({"items": [], "error": "daily_limit_reached"})
            self.calls_today += 1
        if genai and API_KEY:
            try:
                _GenerativeModel = getattr(genai, 'GenerativeModel', None)
                if _GenerativeModel:
                    model = _GenerativeModel(self.gen_model)
                    resp = model.generate_content(prompt)
                    text = getattr(resp, 'text', None)
                    return text or '{"items": []}'
            except Exception:
                pass
        # fallback stub
        return json.dumps({"items": []})

CLIENT = GeminiClient()
