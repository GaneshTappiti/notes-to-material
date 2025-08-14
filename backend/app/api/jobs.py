from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
import uuid
import json
from datetime import datetime
from typing import List, Optional, Dict
from pathlib import Path
from pydantic import BaseModel
from ..services.vector_store import VECTOR_STORE
from ..services.gemini_client import CLIENT
from ..services.vector_store_faiss import FAISS_STORE
from jsonschema import validate as json_validate
from ..services.generator import generate as strict_generate
from ..models import Job as JobModel, QuestionResult, get_session, create_db, add_question_results, create_job_row
import random
import difflib

GEN_SCHEMA = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                    "answers": {
                        "type": "object",
                        "properties": {
                            "2": {"type": "string"},
                            "5": {"type": "string"},
                            "10": {"type": "string"}
                        },
                        "minProperties": 1
                    },
                    "page_references": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["question", "answers", "page_references"]
            }
        }
    },
    "required": ["items"]
}

from ..services.auth import require_role

router = APIRouter()

class JobCreate(BaseModel):
    job_name: str
    course_id: Optional[str] = None
    files: List[str] = []
    mode: str = "qbank"  # or auto-generate
    marks: List[int] = []
    per_chapter: bool = False
    questions_per_mark: Dict[str, int] | None = None
    options: dict | None = None

# Legacy in-memory stores have been removed - using DB as single source of truth
RESULTS_DIR = Path("storage/job_results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

class EmbedRequest(BaseModel):
    file_id: str
    pages: List[dict]  # each: {page_no, text, ...}

class RetrieveRequest(BaseModel):
    query: str
    top_k: int = 5

class GenerateRequest(BaseModel):
    prompt: str
    top_k: int = 5
    marks: List[int] | None = None  # subset of [2,5,10]; if None generate all

class GenerateItemRequest(BaseModel):
    question: str
    top_k: int = 5
    marks: List[int] | None = None

class UpdateItemRequest(BaseModel):
    job_id: str
    index: int
    question: str | None = None
    answers: dict | None = None
    page_references: List[str] | None = None
    status: str | None = None  # e.g., approved, draft

def _retrieve_embeddings(query: str, top_k: int, file_ids: List[str] | None = None):
    emb = CLIENT.embed([query])[0]
    base_results = VECTOR_STORE.query(emb, top_k=top_k)
    if FAISS_STORE.available():
        faiss_results = FAISS_STORE.query(emb, top_k=top_k)
    else:
        faiss_results = []
    # merge simple (unique by metadata signature)
    seen = set()
    merged = []
    for r in base_results + faiss_results:
        md = r.get('metadata', {})

        # Apply file_ids filter if specified
        if file_ids and md.get('file_id') not in file_ids:
            continue

        sig = tuple(sorted(md.items()))
        if sig in seen:
            continue
        seen.add(sig)
        merged.append(r)
    merged.sort(key=lambda x: x.get('score',0), reverse=True)
    return emb, merged[:top_k]

def _calc_total_expected(qpm: Dict[str,int] | None) -> int:
    if not qpm:
        return 0
    return sum(qpm.values())


def _is_duplicate(candidate: str, existing: List[str]) -> bool:
    for e in existing:
        if difflib.SequenceMatcher(None, candidate, e).ratio() > 0.9:
            return True
    return False


def _auto_generate_job(job_id: str):  # background
    create_db()
    with get_session() as session:
        job_row = session.query(JobModel).filter(JobModel.job_id == job_id).first()  # type: ignore
        if not job_row:
            return
        payload = job_row.payload_json
        file_ids = job_row.file_ids  # Get file_ids for scoped retrieval
        qpm = payload.get('questions_per_mark') or {}
        marks = sorted({int(m) for m in (payload.get('marks') or qpm.keys())})
        generated_questions: List[str] = []
        for mark in marks:
            target = int(qpm.get(str(mark), 0))
            count = 0
            attempts = 0
            while count < target and attempts < target * 5:
                attempts += 1
                task = f"Generate a {mark}-mark question"  # simple placeholder; could use notes context
                result = strict_generate(task, mark, top_k=6, file_ids=file_ids)
                qtext = result.data.get('question_text','')
                if not qtext or _is_duplicate(qtext, generated_questions):
                    continue
                generated_questions.append(qtext)
                retrieval_scores = [p.get('score',0.0) for p in result.pages]
                qr = QuestionResult(
                    job_id=job_id,
                    question_id=result.data.get('question_id','q'+uuid.uuid4().hex[:6]),
                    mark_value=mark,
                    question_text=qtext,
                    answer=result.data.get('answer',''),
                    answer_format=result.data.get('answer_format','text'),
                    page_references=result.data.get('page_references',[]),
                    verbatim_quotes=result.data.get('verbatim_quotes',[]),
                    diagram_images=result.data.get('diagram_images',[]),
                    status=result.data.get('status','NOT_FOUND'),
                    retrieval_scores=retrieval_scores,
                    raw_model_output=result.data,
                )
                session.add(qr)
                count += 1
                job_row.generated_count += 1
                if result.data.get('status') == 'NOT_FOUND':
                    job_row.not_found_count += 1
                else:
                    job_row.found_count += 1
                session.commit()
        job_row.status = 'completed'
        session.commit()

@router.post('/jobs', dependencies=[Depends(require_role('faculty','admin'))])
async def create_job(payload: JobCreate, background: BackgroundTasks):
    job_id = str(uuid.uuid4())
    create_db()
    total_expected = _calc_total_expected(payload.questions_per_mark)
    # Persist job row immediately
    with get_session() as session:
        row = JobModel(
            job_id=job_id,
            job_name=payload.job_name,
            course_id=payload.course_id,
            mode=payload.mode,
            payload_json=payload.model_dump(),
            file_ids=payload.files,  # Store file_ids from payload
            status='running' if payload.mode == 'auto-generate' else 'created',
            total_expected=total_expected
        )
        session.add(row)
        session.commit()
    if payload.mode == 'auto-generate':
        background.add_task(_auto_generate_job, job_id)
    return {"job_id": job_id, "status": 'running' if payload.mode == 'auto-generate' else 'created'}

@router.get('/jobs/{job_id}/status')
async def job_status(job_id: str):
    with get_session() as session:
        db_row = session.query(JobModel).filter(JobModel.job_id == job_id).first()  # type: ignore
        if not db_row:
            return {"error": "not_found"}
        return {
            'job_id': job_id,
            'status': db_row.status,
            'generated_count': db_row.generated_count,
            'found_count': db_row.found_count,
            'not_found_count': db_row.not_found_count,
            'total_expected': db_row.total_expected,
        }

@router.post('/embeddings', dependencies=[Depends(require_role('faculty','admin'))])
async def create_embeddings(payload: EmbedRequest):
    if not payload.pages:
        raise HTTPException(status_code=400, detail="No pages provided")
    texts = [p.get('text','') for p in payload.pages]
    embeddings = CLIENT.embed(texts)
    VECTOR_STORE.add_batch(embeddings, [{"file_id": payload.file_id, **p} for p in payload.pages])
    return {"count": len(embeddings)}

@router.post('/retrieve')
async def retrieve(payload: RetrieveRequest):
    _emb, results = _retrieve_embeddings(payload.query, payload.top_k)
    return {"query": payload.query, "results": results}

def _build_generation_prompt(user_prompt: str, ctx: List[dict], marks: List[int] | None):
    context_block = "\n\n".join([
        f"[Score={round(c.get('score',0),3)}] {c['metadata'].get('text','')[:500]}" if 'text' in c['metadata'] else str(c['metadata'])
        for c in ctx
    ])
    if not marks:
        marks = [2,5,10]
    marks_list = ",".join(str(m) for m in marks)
    instruction = (
        "You are a strict assistant. Use ONLY the supplied context. Generate exam questions and multi-mark answer variants. "
        "Return STRICT JSON: {\"items\": [ {\"question\": string, \"answers\": { '2'?: string, '5'?: string, '10'?: string }, \"page_references\": [string]} ] }. "
        "Each answer variant must be appropriate in depth for its mark value. Only generate marks in: " + marks_list + "."
    )
    return f"Context:\n{context_block}\n\nUser Prompt: {user_prompt}\n{instruction}\nJSON:"

def _run_generation(prompt: str):
    attempts = []
    data = {"items": []}
    for attempt in range(3):
        raw = CLIENT.generate(prompt)
        try:
            candidate = json.loads(raw)
            json_validate(candidate, GEN_SCHEMA)
            data = candidate
            break
        except Exception as e:
            attempts.append(str(e))
            prompt += "\n# Retry: STRICT VALID JSON ONLY."
    # Structured fallback: if model returned no items, synthesize one question from prompt context
    if not data.get('items'):
        # Very lightweight heuristic extraction of a concept phrase
        import re
        lines = [l.strip() for l in prompt.splitlines() if l.strip()]
        subject = 'the provided material'
        for l in lines:
            if len(l.split()) >= 2 and not l.lower().startswith('return strict json'):
                subject = ' '.join(l.split()[:6])
                break
        def _answer(mark: int) -> str:
            return (f"Definition: Brief definition of {subject}.\n"
                    f"Key Points: • Point 1 • Point 2 (mark depth {mark}).\n"
                    f"Diagram: Textual description (no external facts).\n"
                    f"Example: Simple example based on {subject}.\n"
                    f"Marking Scheme: {mark} discrete scoring elements clearly stated.")
        answers = {str(m): _answer(m) for m in (2,5,10)}
        data = {"items": [{"question": f"Explain {subject}?", "answers": answers, "page_references": []}]}
    else:
        # Ensure each answer variant contains required labeled sections (idempotent augmentation)
        required_labels = ["Definition:", "Key Points:", "Diagram:", "Example:", "Marking Scheme:"]
        for item in data.get('items', []):
            ans_obj = item.get('answers') or {}
            for k,v in list(ans_obj.items()):
                if v is None:
                    continue
                missing = [lab for lab in required_labels if lab not in v]
                if missing:
                    # Append minimally
                    ans_obj[k] = v.rstrip() + "\n" + "\n".join(f"{lab} TBD" for lab in missing)
    return data, attempts

def _apply_citations(data: dict, ctx: List[dict]):
    if isinstance(data.get("items"), list):
        for item in data["items"]:
            if not item.get("page_references"):
                refs = []
                for c in ctx[:3]:
                    md = c.get("metadata", {})
                    file_id = md.get("file_id")
                    page_no = md.get("page_no")
                    if file_id and page_no:
                        refs.append(f"{file_id}:{page_no}")
                item["page_references"] = refs

@router.post('/generate', dependencies=[Depends(require_role('faculty','admin'))])
async def generate(payload: GenerateRequest):
    _emb, ctx = _retrieve_embeddings(payload.prompt, payload.top_k)
    prompt = _build_generation_prompt(payload.prompt, ctx, payload.marks)
    data, attempts = _run_generation(prompt)
    _apply_citations(data, ctx)
    items = data.get("items", [])
    job_id = f"gen-{uuid.uuid4().hex[:8]}"
    # Assign stable ids for items that don't have them
    for it in items:
        if 'id' not in it:
            it['id'] = uuid.uuid4().hex[:8]
    # Persist Job + QuestionResults
    create_db()
    with get_session() as session:
        job_row = JobModel(job_id=job_id, job_name=f"Adhoc-{job_id}", mode='adhoc', payload_json={'prompt': payload.prompt}, status='completed', total_expected=len(items), generated_count=len(items), found_count=sum(1 for _ in items))
        session.add(job_row)
        session.commit()
    add_question_results(job_id, items)
    # Legacy JSON file for exports/tests
    (RESULTS_DIR / f"{job_id}.json").write_text(json.dumps({"job_id": job_id, "items": items}, ensure_ascii=False, indent=2))
    return {"job_id": job_id, "prompt": payload.prompt, "context_count": len(ctx), "output": {"items": items}, "attempt_errors": attempts}

@router.post('/generate_item', dependencies=[Depends(require_role('faculty','admin'))])
async def generate_item(payload: GenerateItemRequest):
    # Regenerate answers for a single question text
    _emb, ctx = _retrieve_embeddings(payload.question, payload.top_k)
    prompt = _build_generation_prompt(payload.question, ctx, payload.marks)
    data, attempts = _run_generation(prompt)
    _apply_citations(data, ctx)
    item = data.get("items", [{}])[0]
    if 'id' not in item:
        item['id'] = uuid.uuid4().hex[:8]
    return {"question": payload.question, "item": item, "attempt_errors": attempts}

@router.delete('/jobs/{job_id}', dependencies=[Depends(require_role('faculty','admin'))])
async def delete_job(job_id: str):
    # Remove DB rows
    create_db()
    with get_session() as session:
        # delete question results first
        session.query(QuestionResult).filter(QuestionResult.job_id == job_id).delete()  # type: ignore
        session.query(JobModel).filter(JobModel.job_id == job_id).delete()  # type: ignore
        session.commit()
    fp = RESULTS_DIR / f"{job_id}.json"
    if fp.exists():
        try:
            fp.unlink()
        except Exception:
            pass
    return {"deleted": job_id}

@router.post('/jobs/update_item', dependencies=[Depends(require_role('faculty','admin'))])
async def update_item(payload: UpdateItemRequest):
    # DEPRECATED: index-based updates retained for backward compatibility. Prefer PATCH /jobs/{job_id}/items/{item_id}
    fp = RESULTS_DIR / f"{payload.job_id}.json"
    items = []
    if fp.exists():
        try:
            data = json.loads(fp.read_text())
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Corrupt job file: {e}")
        items = data.get('items', [])
    if not items:
        # fallback: load from DB
        with get_session() as session:
            db_items = session.query(QuestionResult).filter(QuestionResult.job_id == payload.job_id).all()  # type: ignore
            items = [qr.raw_model_output or {"id": qr.question_id, "question": qr.question_text, "answers": {str(qr.mark_value): qr.answer}, "page_references": qr.page_references} for qr in db_items]
    if payload.index < 0 or payload.index >= len(items):
        raise HTTPException(status_code=400, detail="Index out of range")
    item = items[payload.index]
    if payload.question:
        item['question'] = payload.question
    if payload.answers:
        item['answers'] = payload.answers
    if payload.page_references is not None:
        item['page_references'] = payload.page_references
    if payload.status is not None:
        item['status'] = payload.status
    # persist JSON for compatibility
    if fp.parent.exists():
        fp.write_text(json.dumps({"job_id": payload.job_id, "items": items}, ensure_ascii=False, indent=2))
    # update DB row if exists
    try:
        with get_session() as session:
            qr = session.query(QuestionResult).filter(QuestionResult.job_id == payload.job_id, QuestionResult.question_id == item.get('id')).first()  # type: ignore
            if qr:
                qr.question_text = item.get('question', qr.question_text)
                if isinstance(item.get('answers'), dict):
                    # choose answer for smallest mark
                    try:
                        smallest_mark = sorted(int(k) for k in item['answers'].keys())[0]
                        qr.mark_value = smallest_mark
                        qr.answer = item['answers'][str(smallest_mark)]
                    except Exception:
                        pass
                qr.page_references = item.get('page_references', qr.page_references)
                qr.status = item.get('status', qr.status)
                qr.raw_model_output = item
                session.commit()
    except Exception:
        pass
    return {"status": "updated", "item": item}

from fastapi import Path as FPath, Body

@router.patch('/jobs/{job_id}/items/{item_id}', dependencies=[Depends(require_role('faculty','admin'))])
async def patch_job_item(
    job_id: str,
    item_id: str,
    question: str | None = Body(default=None),
    answers: dict | None = Body(default=None),
    page_references: List[str] | None = Body(default=None),
    status: str | None = Body(default=None),
):
    """Update a single question result by its stable id (race-safe).

    Fields omitted are left unchanged.
    """
    fp = RESULTS_DIR / f"{job_id}.json"
    items: List[dict] = []
    if fp.exists():
        try:
            data = json.loads(fp.read_text())
            items = data.get('items', [])
        except Exception:
            items = []
    if not items:
        with get_session() as session:
            db_items = session.query(QuestionResult).filter(QuestionResult.job_id == job_id).all()  # type: ignore
            items = [qr.raw_model_output or {"id": qr.question_id, "question": qr.question_text, "answers": {str(qr.mark_value): qr.answer}, "page_references": qr.page_references, "status": qr.status} for qr in db_items]
    # Locate
    idx = None
    for i, it in enumerate(items):
        if it.get('id') == item_id:
            idx = i
            break
    if idx is None:
        raise HTTPException(status_code=404, detail="Item not found")
    item = items[idx]
    if question is not None:
        item['question'] = question
    if answers is not None:
        item['answers'] = answers
    if page_references is not None:
        item['page_references'] = page_references
    if status is not None:
        item['status'] = status
    # Persist JSON
    if fp.parent.exists():
        fp.write_text(json.dumps({"job_id": job_id, "items": items}, ensure_ascii=False, indent=2))
    # Update DB
    try:
        with get_session() as session:
            qr = session.query(QuestionResult).filter(QuestionResult.job_id == job_id, QuestionResult.question_id == item_id).first()  # type: ignore
            if qr:
                if question is not None:
                    qr.question_text = question
                if answers and isinstance(answers, dict):
                    try:
                        smallest_mark = sorted(int(k) for k in answers.keys())[0]
                        qr.mark_value = smallest_mark
                        qr.answer = answers[str(smallest_mark)]
                    except Exception:
                        pass
                if page_references is not None:
                    qr.page_references = page_references
                if status is not None:
                    qr.status = status
                qr.raw_model_output = item
                session.commit()
    except Exception:
        pass
    return {"status": "updated", "item": item}

@router.get('/jobs')
async def list_jobs(page: int = 1, limit: int = 50):
    # stable ordering by created_at desc
    # Prefer DB listing
    create_db()
    with get_session() as session:
        rows = session.query(JobModel).order_by(JobModel.created_at.desc()).offset((page-1)*limit).limit(limit).all()  # type: ignore
        total = session.query(JobModel).count()  # type: ignore
        items = [
            {"job_id": r.job_id, "status": r.status, "count": r.generated_count, "created_at": r.created_at}
            for r in rows
        ]
    return {"jobs": items, "page": page, "limit": limit, "total": total}
