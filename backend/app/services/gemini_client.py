# Placeholder Gemini client (use google generative AI SDK or Vertex AI SDK in production)
import os, hashlib, json, threading, time
from typing import List

try:
    import google.generativeai as genai  # type: ignore
except ImportError:  # pragma: no cover
    genai = None

API_KEY = os.getenv("GOOGLE_API_KEY", "")
if genai and API_KEY:
    genai.configure(api_key=API_KEY)

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
            for t in texts:
                try:
                    resp = genai.embed_content(model=self.embed_model, content=t)
                    emb = resp.get("embedding") or resp.get("embeddings", [None])[0]
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
                model = genai.GenerativeModel(self.gen_model)
                resp = model.generate_content(prompt)
                return resp.text or '{"items": []}'
            except Exception:
                pass
        # fallback stub
        return json.dumps({"items": []})

CLIENT = GeminiClient()
