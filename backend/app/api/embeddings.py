"""Embeddings upsert + query endpoints.

POST /api/embeddings/upsert
  - Embeds pages from DB that lack vectors (using database as authoritative source)

GET /api/embeddings/query?q=...&k=5
  - Embeds query and returns top-k results from vector store
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Depends
from fastapi import Query as Q
from ..models import get_session, Page, PageEmbedding
from ..services.embedding import embed_texts
from ..services.vector_store import VECTOR_STORE
from ..services.vector_store_faiss import FAISS_STORE
from ..services.gemini_client import CLIENT
from ..services.embedding_tracker import EmbeddingTracker

from ..services.auth import require_role

router = APIRouter(dependencies=[Depends(require_role('faculty','admin'))])

@router.post('/embeddings/upsert')
async def upsert_embeddings(limit: int = 200):
    """Embed all Page rows missing a PageEmbedding.

    Uses the database as the single source of truth for tracking which pages
    have been embedded, eliminating the need for external tracking files.
    """
    # Get pages that need embedding
    to_process = EmbeddingTracker.get_pending_pages(limit)

    if not to_process:
        return {'processed': 0, 'message': 'All pages have embeddings'}

    # Generate embeddings for new pages
    texts = [p.text for p in to_process]
    embeddings = embed_texts(texts)
    metadatas = [
        {
            'file_id': getattr(p, 'file_id', None),
            'file_name': p.file_name,
            'page_no': p.page_no,
            'text': p.text[:800]
        }
        for p in to_process
    ]

    # Add to vector stores
    VECTOR_STORE.add_batch(embeddings, metadatas)
    if FAISS_STORE.available():
        FAISS_STORE.add_batch(embeddings, metadatas)

    # Bulk mark as embedded in database
    embedding_records = []
    for p, emb in zip(to_process, embeddings):
        if p.id is not None:
            embedding_records.append({
                'page_id': p.id,
                'file_id': getattr(p, 'file_id', None),
                'page_no': p.page_no,
                'embedding': emb
            })

    created_count = EmbeddingTracker.bulk_mark_embedded(embedding_records)

    return {
        'processed': len(to_process),
        'stored': created_count,
        'message': f'Successfully embedded {len(to_process)} pages'
    }

@router.get('/embeddings/status')
async def get_embedding_status():
    """Get statistics about current embedding status."""
    return EmbeddingTracker.get_embedding_status()

@router.delete('/embeddings/reset')
async def reset_embeddings():
    """Reset all embeddings - useful for development/testing."""
    deleted_count = EmbeddingTracker.reset_all_embeddings()

    return {
        'deleted_embeddings': deleted_count,
        'message': 'All embedding database records have been reset'
    }

@router.post('/embeddings/cleanup')
async def cleanup_orphaned_embeddings():
    """Remove embedding records for pages that no longer exist."""
    cleaned_count = EmbeddingTracker.cleanup_orphaned_embeddings()

    return {
        'cleaned_records': cleaned_count,
        'message': f'Removed {cleaned_count} orphaned embedding records'
    }

@router.get('/embeddings/query')
async def query_embeddings(q: str = Q(...), k: int = Q(5, ge=1, le=50)):
    if not q.strip():
        raise HTTPException(status_code=400, detail='Empty query')
    emb = CLIENT.embed([q])[0]
    # Query a wider pool to allow lexical fallback injection if needed
    internal_k = max(k*4, k+5)
    base = VECTOR_STORE.query(emb, top_k=internal_k)
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
    top = out[:k]
    # Lexical fallback: ensure at least one result contains raw query token(s)
    q_lower = q.lower()
    if not any(q_lower in (r.get('metadata',{}).get('text','').lower()) for r in top):
        # scan entire list for lexical matches
        lex_matches = [r for r in out if q_lower in (r.get('metadata',{}).get('text','').lower())]
        if lex_matches:
            # prepend first lexical match
            top = lex_matches[:1] + top[:-1] if len(top) == k and k>0 else lex_matches[:1] + top
    return {'query': q, 'count': len(top), 'results': top}
