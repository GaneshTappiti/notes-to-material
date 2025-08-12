"""Generation endpoint aligned with spec.

POST /api/generate
  Body: {"job_id": str, "marks_type": str}
  - Loads job info from JOBS (created via /api/jobs) to discover associated file_ids
  - Fetches text from Page rows for those file_ids
  - Builds a prompt and queries Google Generative AI (via services.gemini_client.CLIENT)
  - Persists output JSON to storage/jobs/<job_id>.json
  - Returns {questions: [...]} where each question has id, question, answers, page_references

If job_id not found, 404.
If no file_ids, returns empty list.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
import json, uuid, textwrap
from ..models import get_pages_for_files
from .jobs import JOBS  # reuse in-memory store
from ..services.gemini_client import CLIENT

router = APIRouter()

JOBS_DIR = Path("storage/jobs")
JOBS_DIR.mkdir(parents=True, exist_ok=True)

class GenerateSpec(BaseModel):
    job_id: str
    marks_type: str = "all"  # one of: all, 2,5,10 or comma list
    max_questions: int = 10

def _parse_marks(marks_type: str) -> list[int]:
    if marks_type == 'all':
        return [2,5,10]
    parts = [p.strip() for p in marks_type.split(',') if p.strip().isdigit()]
    vals = sorted({int(p) for p in parts if int(p) in (2,5,10)})
    return vals or [2,5,10]

@router.post('/generate')
async def generate(spec: GenerateSpec):
    job = JOBS.get(spec.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    file_ids = job.get('payload', {}).get('files') or []
    if not file_ids:
        return {"questions": []}
    pages = get_pages_for_files(file_ids)
    if not pages:
        return {"questions": []}
    # Build corpus (truncate per page for prompt size)
    corpus_blocks = []
    for p in pages[:200]:  # safety limit
        snippet = p.text.strip()
        if len(snippet) > 800:
            snippet = snippet[:800] + '…'
        corpus_blocks.append(f"[File={p.file_id} Pg={p.page_no}] {snippet}")
    corpus = "\n".join(corpus_blocks)
    marks = _parse_marks(spec.marks_type)
    marks_list = ",".join(str(m) for m in marks)
    instruction = textwrap.dedent(f"""
    You are an educational content assistant. Using ONLY the supplied corpus, generate up to {spec.max_questions} exam-style questions.
    For each question produce answer variants appropriate for mark values: {marks_list}.
    Return STRICT JSON: {{"items":[{{"question":str,"answers":{{"2"?:str,"5"?:str,"10"?:str}},"page_references":[str] }}]}}.
    Do not include any commentary.
    """)
    prompt = f"Corpus:\n{corpus}\n\n{instruction}\nJSON:"
    raw = CLIENT.generate(prompt)
    try:
        data = json.loads(raw)
    except Exception:
        # fallback minimal structure
        data = {"items": []}
    items = data.get('items', [])
    for it in items:
        it.setdefault('id', uuid.uuid4().hex[:8])
        it.setdefault('page_references', [])
    # Persist
    out_path = JOBS_DIR / f"{spec.job_id}.json"
    out_path.write_text(json.dumps({"job_id": spec.job_id, "items": items}, ensure_ascii=False, indent=2))
    # Mirror into JOBS
    job['results'] = items
    return {"questions": items, "count": len(items)}
