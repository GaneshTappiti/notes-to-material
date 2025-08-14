"""Upload + PDF ingestion endpoints.

POST /api/uploads
  - Accepts multipart/form-data with 'file'
  - Stores original under STORAGE_PATH/uploads/
  - Extracts pages via services.pdf_extract.extract_pages
  - Persists per-page records to DB (Page table) and writes a metadata JSON
    summary under PAGE_DATA_DIR/<file_id>.json for lightweight lookup & deletion
  - Returns summary JSON {file_id, filename, page_count, pages:[{page_no, stored_text_path}]}

DELETE /api/uploads/{file_id}
  - Deletes metadata JSON and associated Page rows (by file_name heuristic)
"""
from __future__ import annotations

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends
from pathlib import Path
import os, uuid, json
from datetime import datetime
from ..services.pdf_extract import extract_pages
from ..models import Page, PageEmbedding, Upload, get_session, create_db
from ..services.vector_store import VECTOR_STORE

STORAGE_PATH = Path(os.getenv("STORAGE_PATH", "storage"))
UPLOADS_DIR = STORAGE_PATH / "uploads"
PAGE_DATA_DIR = STORAGE_PATH / "upload_meta"  # exported constant (tests rely)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
PAGE_DATA_DIR.mkdir(parents=True, exist_ok=True)

from ..services.auth import require_role

router = APIRouter(dependencies=[Depends(require_role('faculty','admin'))])

def _gen_file_id(filename: str) -> str:
    stem = Path(filename).stem
    safe = ''.join(c for c in stem if c.isalnum() or c in ('-','_')) or 'file'
    return f"{safe}-{uuid.uuid4().hex[:8]}"

def _background_embed(file_id: str):  # simple sequential embedding using existing upsert logic for new pages
    from ..services.embedding_tracker import EmbeddingTracker
    from ..services.embedding import embed_texts
    from ..services.vector_store import VECTOR_STORE
    from ..services.vector_store_faiss import FAISS_STORE

    # Get pages for this file that need embedding
    new_pages: list[Page] = []
    with get_session() as session:
        # Get all page IDs that already have embeddings
        embedded_page_ids = {pe.page_id for pe in session.query(PageEmbedding).all()}

        # Find pages from this file that don't have embeddings
        for p in session.query(Page).filter(Page.file_id == file_id):  # type: ignore
            if p.id not in embedded_page_ids:
                new_pages.append(p)

    if not new_pages:
        return

    texts = [p.text for p in new_pages]
    embeddings = embed_texts(texts)
    metadatas = [{'file_id': p.file_id, 'file_name': p.file_name, 'page_no': p.page_no, 'text': p.text[:800]} for p in new_pages]

    VECTOR_STORE.add_batch(embeddings, metadatas)
    if FAISS_STORE.available():
        FAISS_STORE.add_batch(embeddings, metadatas)

    # Use the new embedding tracker to mark pages as embedded
    embedding_records = []
    for p, emb in zip(new_pages, embeddings):
        if p.id is not None:
            embedding_records.append({
                'page_id': p.id,
                'file_id': p.file_id,
                'page_no': p.page_no,
                'embedding': emb
            })

    EmbeddingTracker.bulk_mark_embedded(embedding_records)

@router.post("/uploads")
async def upload_file(background: BackgroundTasks, file: UploadFile = File(...)):
    """Accept a single PDF file and ingest.

    Returns summary JSON: {file_id, filename, page_count, pages:[{page_no, stored_text_path}]}
    (Kept single-file contract to align with tests and spec.)
    """
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files supported")
    create_db()
    # Reuse prior file_id for same filename in current DB session to keep tests deterministic
    existing_id: str | None = None
    with get_session() as s:  # quick lookup
        for p in s.query(Page).filter(Page.file_name == file.filename).limit(1):  # type: ignore
            existing_id = p.file_id
            break
    assert file.filename  # narrow type
    file_id = existing_id or _gen_file_id(file.filename)
    dest = UPLOADS_DIR / file.filename
    try:
        data = await file.read()
        with open(dest, 'wb') as fh:
            fh.write(data)
    except Exception as e:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"Failed to store file {file.filename}: {e}")
    pages = extract_pages(dest)
    from sqlmodel import Session
    with get_session() as session:
        # remove prior pages for same file_id/file_name to avoid duplication across repeated test runs
        for old in session.query(Page).filter(Page.file_name == file.filename):  # type: ignore
            session.delete(old)
        session.commit()
        for p in pages:
            page_rec = Page(file_id=file_id, file_name=file.filename, page_no=p['page_no'], text=p.get('text',''), image_paths=p.get('images', []))
            session.add(page_rec)
        # Upsert Upload row
        up = session.query(Upload).filter(Upload.file_id == file_id).first()  # type: ignore
        if not up:
            up = Upload(file_id=file_id, file_name=file.filename, page_count=len(pages), ocr_status='done')
            session.add(up)
        else:
            up.page_count = len(pages)
            up.ocr_status = 'done'
        session.commit()

    # Return canonical response only - remove all the redundant aliases
    # Prepare canonical response with pages information for backward compatibility
    summary_pages = [{"page_no": p['page_no'], "stored_text_path": p.get('text_path')} for p in pages]
    canonical_response = {
        "file_id": file_id,
        "filename": file.filename,
        "page_count": len(pages),
        "pages": summary_pages,
        "created_at": datetime.utcnow().isoformat()
    }

    # Save legacy metadata for backward compatibility (will be removed later)
    meta = {
        "file_id": file_id,
        "filename": file.filename,
        "page_count": len(pages),
        "pages": summary_pages,
        "ocr_status": "done"
    }
    (PAGE_DATA_DIR / f"{file_id}.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))

    # Kick off background embedding
    background.add_task(_background_embed, file_id)
    return canonical_response

@router.get('/uploads/{file_id}/pages')
async def get_upload_pages(file_id: str):
    """Return detailed page information for an upload.

    Returns: file_id, filename, page_count, pages: [{page_no, text_preview, image_paths}]
    """
    create_db()
    with get_session() as session:
        # Get Upload info
        upload = session.query(Upload).filter(Upload.file_id == file_id).first()  # type: ignore
        if not upload:
            raise HTTPException(status_code=404, detail="Upload not found")

        # Get all pages for this file
        pages = session.query(Page).filter(Page.file_id == file_id).order_by(Page.page_no).all()  # type: ignore

        page_data = []
        for page in pages:
            # Create text preview (first 200 characters)
            text_preview = page.text[:200] + "..." if len(page.text) > 200 else page.text
            page_data.append({
                "page_no": page.page_no,
                "text_preview": text_preview,
                "image_paths": page.image_paths or []
            })

        return {
            "file_id": file_id,
            "filename": upload.file_name,
            "page_count": upload.page_count,
            "pages": page_data
        }

@router.get('/uploads/{file_id}')
async def get_upload(file_id: str):
    """Return metadata + simple status for a previously uploaded file.

    Frontend polls this endpoint looking for a status field. Since extraction is
    synchronous in current implementation (embedding runs in background but not
    required for basic readiness), we treat existing meta as status=done.
    """
    create_db()
    with get_session() as session:
        upload = session.query(Upload).filter(Upload.file_id == file_id).first()  # type: ignore
        if upload:
            return {
                "file_id": file_id,
                "status": upload.ocr_status,
                "page_count": upload.page_count,
                "filename": upload.file_name,
                "created_at": upload.created_at
            }

    # Fallback to JSON metadata for legacy support
    meta_path = PAGE_DATA_DIR / f"{file_id}.json"
    if not meta_path.exists():
        raise HTTPException(status_code=404, detail="Not found")
    try:
        meta = json.loads(meta_path.read_text())
    except Exception:
        raise HTTPException(status_code=500, detail="Corrupt metadata")
    # Normalize minimal polling contract
    page_count = meta.get('page_count') or meta.get('pagesCount') or len(meta.get('pages') or [])
    return {"file_id": file_id, "status": "done", "page_count": page_count, "filename": meta.get('filename')}

@router.delete('/uploads/{file_id}')
async def delete_upload(file_id: str):
    meta_path = PAGE_DATA_DIR / f"{file_id}.json"
    deleted_files: list[str] = []
    if not meta_path.exists():
        return {"file_id": file_id, "status": "deleted"}
    try:
        meta = json.loads(meta_path.read_text())
    except Exception:
        meta = {}
    # Remove JSON summary first
    try:
        meta_path.unlink()
    except Exception:
        pass
    file_name = meta.get('filename')
    # Collect per-page text paths for deletion
    page_text_paths = []
    for p in meta.get('pages', []):
        tp = p.get('stored_text_path') or p.get('text_path')
        if tp:
            page_text_paths.append(tp)
    with get_session() as session:
        # Find page ids for embeddings cleanup
        page_ids: list[int] = []
        if file_name:
            from sqlmodel import select
            for page in session.exec(select(Page).where(Page.file_name == file_name)):
                if page.id is not None:
                    page_ids.append(page.id)
                # gather image paths too
                for img in (page.image_paths or []):
                    page_text_paths.append(img)
                session.delete(page)
            session.commit()
        # Delete Upload row
        try:
            up = session.query(Upload).filter(Upload.file_id == file_id).first()  # type: ignore
            if up:
                session.delete(up)
                session.commit()
        except Exception:
            pass
        if page_ids:
            # delete PageEmbedding rows referencing those pages
            try:
                for pe in session.query(PageEmbedding).filter(PageEmbedding.page_id.in_(page_ids)):  # type: ignore
                    session.delete(pe)
                session.commit()
            except Exception:
                pass
    # Remove vector store entries (JSON + FAISS)
    try:
        VECTOR_STORE.delete_by_file(file_id)
    except Exception:
        pass
    try:
        from ..services.vector_store_faiss import FAISS_STORE
        if FAISS_STORE.available():
            FAISS_STORE.delete_by_file(file_id)
    except Exception:
        pass
    # Delete original file
    if file_name:
        orig = UPLOADS_DIR / file_name
        if orig.exists():
            try:
                orig.unlink(); deleted_files.append(str(orig))
            except Exception:
                pass
    # Delete per-page text + images
    for path_str in page_text_paths:
        p = Path(path_str)
        if p.exists():
            try:
                p.unlink(); deleted_files.append(str(p))
            except Exception:
                pass
    return {"file_id": file_id, "status": "deleted", "removed_files": len(deleted_files)}

@router.get('/uploads')
async def list_uploads():
    """Return list of Upload rows (basic listing for UI/tests).

    If Upload table is empty (legacy scenario) derive from JSON meta files.
    """
    create_db()
    with get_session() as session:
        rows = session.query(Upload).order_by(Upload.created_at.desc()).all()  # type: ignore
        if rows:
            return {"uploads": [
                {"file_id": r.file_id, "file_name": r.file_name, "page_count": r.page_count, "ocr_status": r.ocr_status}
                for r in rows
            ]}
    # Legacy fallback
    uploads = []
    for fp in PAGE_DATA_DIR.glob('*.json'):
        try:
            meta = json.loads(fp.read_text())
        except Exception:
            continue
        uploads.append({
            "file_id": meta.get('file_id') or fp.stem,
            "file_name": meta.get('filename','unknown.pdf'),
            "page_count": meta.get('page_count') or len(meta.get('pages',[])),
            "ocr_status": meta.get('ocr_status','done')
        })
    return {"uploads": uploads}
