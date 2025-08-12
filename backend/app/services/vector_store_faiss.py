"""Optional FAISS-backed vector store.

If FAISS is installed (faiss-cpu) this module provides a lightweight index
as an alternative to the JSON persistence vector_store. Use via:

    from .vector_store_faiss import FAISS_STORE
    FAISS_STORE.add_batch(embeddings, metadatas)

Dimensions are inferred from the first embedding added. Data is stored in
memory only (local-first dev). You can extend with on-disk serialization
using faiss.write_index / read_index.
"""
from __future__ import annotations
from typing import List, Dict, Any

try:  # pragma: no cover
    import faiss  # type: ignore
except ImportError:  # pragma: no cover
    faiss = None


class _FaissStore:
    def __init__(self):
        self.index = None
        self.dim = None
        self.metadatas: List[Dict[str, Any]] = []

    def available(self) -> bool:
        return faiss is not None

    def add_batch(self, embeddings: List[List[float]], metadatas: List[dict]):
        if not embeddings:
            return
        if not self.available():
            return
        import numpy as np
        arr = np.array(embeddings, dtype='float32')
        if self.index is None:
            self.dim = arr.shape[1]
            self.index = faiss.IndexFlatIP(self.dim)
        self.index.add(arr)
        self.metadatas.extend(metadatas)

    def query(self, embedding: List[float], top_k: int = 5):
        if not self.available() or self.index is None:
            return []
        import numpy as np
        q = np.array([embedding], dtype='float32')
        scores, idxs = self.index.search(q, top_k)
        out = []
        for score, i in zip(scores[0], idxs[0]):
            if i == -1:
                continue
            md = self.metadatas[i]
            out.append({"score": float(score), "metadata": md})
        return out


FAISS_STORE = _FaissStore()
