"""Embeddings upsert + query endpoints.

POST /api/embeddings/upsert
  - Embeds pages from DB that lack vectors (tracked via simple local cache file)

GET /api/embeddings/query?q=...&k=5
  - Embeds query and returns top-k results from vector store
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi import Query as Q
from pathlib import Path
import json
from ..models import get_session, Page
from ..services.embedding import embed_texts
from ..services.vector_store import VECTOR_STORE
from ..services.vector_store_faiss import FAISS_STORE
from ..services.gemini_client import CLIENT

router = APIRouter()

EMBED_TRACK_PATH = Path('storage/embed_tracking.json')

def _load_tracking():
    if EMBED_TRACK_PATH.exists():
        try:
            return json.loads(EMBED_TRACK_PATH.read_text())
        except Exception:  # pragma: no cover
            return {}
    return {}

def _save_tracking(data):  # pragma: no cover - trivial
    EMBED_TRACK_PATH.parent.mkdir(parents=True, exist_ok=True)
    EMBED_TRACK_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2))

@router.post('/embeddings/upsert')
async def upsert_embeddings(limit: int = 200):
    tracking = _load_tracking()
    done_ids = set(tracking.get('page_ids', []))
    to_process: list[Page] = []
    with get_session() as session:
        # manual select because SQLModel select helper used earlier; fallback to ORM rows
        for p in session.query(Page).order_by(Page.id):  # type: ignore
            if p.id not in done_ids:
                to_process.append(p)
                if len(to_process) >= limit:
                    break
    if not to_process:
        return {'processed': 0, 'message': 'nothing to do'}
    texts = [p.text for p in to_process]
    embeddings = embed_texts(texts)
    metadatas = [{'file_id': p.file_id, 'file_name': p.file_name, 'page_no': p.page_no, 'text': p.text[:800]} for p in to_process]
    VECTOR_STORE.add_batch(embeddings, metadatas)
    if FAISS_STORE.available():
        FAISS_STORE.add_batch(embeddings, metadatas)
    done_ids.update(p.id for p in to_process if p.id is not None)
    tracking['page_ids'] = list(done_ids)
    _save_tracking(tracking)
    return {'processed': len(to_process)}

@router.get('/embeddings/query')
async def query_embeddings(q: str = Q(...), k: int = Q(5, ge=1, le=50)):
    if not q.strip():
        raise HTTPException(status_code=400, detail='Empty query')
    emb = CLIENT.embed([q])[0]
    base = VECTOR_STORE.query(emb, top_k=k)
    faiss_results = FAISS_STORE.query(emb, top_k=k) if FAISS_STORE.available() else []
    merged = base + faiss_results
    # simple dedupe by metadata signature
    out = []
    seen = set()
    for r in merged:
        sig = tuple(sorted((r.get('metadata') or {}).items()))
        if sig in seen:
            continue
        seen.add(sig)
        out.append(r)
    out.sort(key=lambda x: x.get('score',0), reverse=True)
    return {'query': q, 'count': len(out[:k]), 'results': out[:k]}
