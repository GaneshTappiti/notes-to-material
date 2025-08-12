from fastapi import APIRouter, HTTPException, BackgroundTasks
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
from ..models import Job as JobModel, QuestionResult, get_session, create_db
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

# In-memory stores (replace with DB)
JOBS: dict = {}
QUESTION_TO_JOB: dict[str, str] = {}
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

def _retrieve_embeddings(query: str, top_k: int):
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
        sig = tuple(sorted(r.get('metadata', {}).items()))
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
                result = strict_generate(task, mark, top_k=6)
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

@router.post('/jobs')
async def create_job(payload: JobCreate, background: BackgroundTasks):
    job_id = str(uuid.uuid4())
    JOBS[job_id] = {"status": "created", "payload": payload.model_dump(), "progress": 0, "results": [], "created_at": datetime.utcnow().isoformat()}
    if payload.mode == 'auto-generate':
        create_db()
        with get_session() as session:
            row = JobModel(job_id=job_id, job_name=payload.job_name, course_id=payload.course_id, mode=payload.mode, payload_json=payload.model_dump(), status='running', total_expected=_calc_total_expected(payload.questions_per_mark))
            session.add(row)
            session.commit()
        background.add_task(_auto_generate_job, job_id)
    return {"job_id": job_id, "status": "created"}

@router.get('/jobs/{job_id}/status')
async def job_status(job_id: str):
    job = JOBS.get(job_id)
    db_row = None
    with get_session() as session:
        db_row = session.query(JobModel).filter(JobModel.job_id == job_id).first()  # type: ignore
    if not job and not db_row:
        return {"error": "not_found"}
    if db_row:
        return {
            'job_id': job_id,
            'status': db_row.status,
            'generated_count': db_row.generated_count,
            'found_count': db_row.found_count,
            'not_found_count': db_row.not_found_count,
            'total_expected': db_row.total_expected,
        }
    return {"job_id": job_id, "status": job["status"], "progress": job.get("progress",0)}

@router.post('/embeddings')
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

@router.post('/generate')
async def generate(payload: GenerateRequest):
    _emb, ctx = _retrieve_embeddings(payload.prompt, payload.top_k)
    prompt = _build_generation_prompt(payload.prompt, ctx, payload.marks)
    data, attempts = _run_generation(prompt)
    _apply_citations(data, ctx)
    items = data.get("items", [])
    # Assign stable ids to each item
    for it in items:
        if 'id' not in it:
            it['id'] = uuid.uuid4().hex[:8]
    job_id = f"gen-{uuid.uuid4().hex[:8]}"
    for it in items:
        QUESTION_TO_JOB[it['id']] = job_id
    JOBS[job_id] = {"status": "completed", "payload": {"prompt": payload.prompt}, "progress": 100, "results": items, "created_at": datetime.utcnow().isoformat()}
    (RESULTS_DIR / f"{job_id}.json").write_text(json.dumps({"job_id": job_id, "items": items}, ensure_ascii=False, indent=2))
    return {"job_id": job_id, "prompt": payload.prompt, "context_count": len(ctx), "output": {"items": items}, "attempt_errors": attempts}

@router.post('/generate_item')
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

@router.delete('/jobs/{job_id}')
async def delete_job(job_id: str):
    JOBS.pop(job_id, None)
    fp = RESULTS_DIR / f"{job_id}.json"
    if fp.exists():
        try:
            fp.unlink()
        except Exception:
            pass
    return {"deleted": job_id}

@router.post('/jobs/update_item')
async def update_item(payload: UpdateItemRequest):
    # Persist item modifications into job_results json file and in-memory JOBS
    fp = RESULTS_DIR / f"{payload.job_id}.json"
    if not fp.exists():
        raise HTTPException(status_code=404, detail="Job not found")
    try:
        data = json.loads(fp.read_text())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Corrupt job file: {e}")
    items = data.get('items', [])
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
    data['items'] = items
    fp.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    # update in-memory store if present
    job = JOBS.get(payload.job_id)
    if job:
        job['results'] = items
    return {"status": "updated", "item": item}

@router.get('/jobs')
async def list_jobs(page: int = 1, limit: int = 50):
    # stable ordering by created_at desc
    items = [
        {"job_id": jid, "status": meta.get('status'), "count": len(meta.get('results', [])), "created_at": meta.get('created_at')}
        for jid, meta in JOBS.items()
    ]
    items.sort(key=lambda x: x.get('created_at') or '', reverse=True)
    total = len(items)
    start = (page-1)*limit
    end = start + limit
    return {"jobs": items[start:end], "page": page, "limit": limit, "total": total}
