"""Retrieval endpoints.

GET /api/retrieval/topk?q=...&k=6
  Returns top-k pages ordered by descending score from available vector stores.
  Response shape:
    {"query": str, "count": int, "pages": [
        {"file_id": str, "file_name": str, "page_no": int, "text": str, "score": float}
    ]}

Also exposes assemble_context(pages) utility used by generator service.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi import Query as Q
from ..services.gemini_client import CLIENT
from ..services.vector_store import VECTOR_STORE
from ..services.vector_store_faiss import FAISS_STORE

router = APIRouter()


def _merge_results(base, extra, k: int):
    seen = set()
    out = []
    for r in base + extra:
        md = r.get('metadata', {})
        sig = (md.get('file_id'), md.get('file_name'), md.get('page_no'))
        if sig in seen:
            continue
        seen.add(sig)
        out.append(r)
    out.sort(key=lambda x: x.get('score', 0), reverse=True)
    return out[:k]


@router.get('/retrieval/topk')
async def topk(q: str = Q(...), k: int = Q(6, ge=1, le=50), file_ids: str = Q(None)):
    """Retrieve top-k pages, optionally filtered by file_ids.

    Args:
        q: Query string
        k: Number of results to return
        file_ids: Optional comma-separated list of file_ids to filter by
    """
    if not q.strip():
        raise HTTPException(status_code=400, detail='Empty query')

    # Parse file_ids filter if provided
    filter_file_ids = None
    if file_ids:
        filter_file_ids = set(fid.strip() for fid in file_ids.split(',') if fid.strip())

    emb = CLIENT.embed([q])[0]
    base = VECTOR_STORE.query(emb, top_k=k)
    faiss = FAISS_STORE.query(emb, top_k=k) if FAISS_STORE.available() else []
    merged = _merge_results(base, faiss, k)

    pages = []
    for r in merged:
        md = r.get('metadata', {})

        # Apply file_ids filter if specified
        if filter_file_ids and md.get('file_id') not in filter_file_ids:
            continue

        text = md.get('text', '')
        if len(text) > 800:
            text = text[:800] + '…'
        pages.append({
            'file_id': md.get('file_id'),
            'file_name': md.get('file_name'),
            'page_no': md.get('page_no'),
            'text': text,
            'score': r.get('score', 0.0)
        })

    # Return only the top k after filtering
    return {'query': q, 'count': len(pages[:k]), 'pages': pages[:k]}


def assemble_context(pages: list[dict]) -> str:
    """Format retrieved pages into strict FILE blocks for prompting.

    Each page dict must contain file_name (or file_id fallback), page_no, text.
    Format per spec:
        FILE:<filename>:<page_no>\n<text>\n\n
    Pages assumed already sorted by descending score.
    """
    blocks = []
    for p in pages:
        filename = p.get('file_name') or p.get('file_id') or 'file'
        page_no = p.get('page_no')
        text = (p.get('text') or '').strip()
        blocks.append(f"FILE:{filename}:{page_no}\n{text}\n")
    return "\n".join(blocks).strip() + ("\n" if blocks else "")
