# Placeholder vector store abstraction for Chroma / FAISS
from typing import List, Dict, Any
import json, math, os
from pathlib import Path

STORAGE_PATH = Path("storage/vector_store.json")

class VectorStore:
    def __init__(self):
        self.items: List[Dict[str, Any]] = []
        self._loaded = False

    def _ensure_loaded(self):
        if self._loaded:
            return
        if STORAGE_PATH.exists():
            try:
                data = json.loads(STORAGE_PATH.read_text())
                self.items = data.get("items", [])
            except Exception:
                self.items = []
        self._loaded = True

    def _persist(self):
        STORAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
        STORAGE_PATH.write_text(json.dumps({"items": self.items}))

    def add(self, embedding: list[float], metadata: dict):
        self._ensure_loaded()
        self.items.append({"embedding": embedding, "metadata": metadata})
        self._persist()

    def add_batch(self, embeddings: List[list[float]], metadatas: List[dict]):
        self._ensure_loaded()
        for emb, md in zip(embeddings, metadatas):
            self.items.append({"embedding": emb, "metadata": md})
        self._persist()

    @staticmethod
    def _cosine(a: list[float], b: list[float]) -> float:
        dot = sum(x*y for x, y in zip(a, b))
        na = math.sqrt(sum(x*x for x in a)) or 1e-9
        nb = math.sqrt(sum(y*y for y in b)) or 1e-9
        return dot / (na * nb)

    def query(self, embedding: list[float], top_k: int = 5):
        self._ensure_loaded()
        scored = []
        for item in self.items:
            score = self._cosine(embedding, item["embedding"])
            scored.append({"score": score, **item})
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    def delete_by_file(self, file_id: str):
        """Remove all embeddings whose metadata.file_id matches.

        Returns count removed.
        """
        self._ensure_loaded()
        before = len(self.items)
        self.items = [it for it in self.items if it.get('metadata', {}).get('file_id') != file_id]
        removed = before - len(self.items)
        if removed:
            self._persist()
        return removed

VECTOR_STORE = VectorStore()
