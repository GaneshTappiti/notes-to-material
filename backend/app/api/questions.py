from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import json
from pathlib import Path
from .jobs import QUESTION_TO_JOB, JOBS, RESULTS_DIR

router = APIRouter()

class QuestionPatch(BaseModel):
    question: str | None = None
    answers: dict | None = None
    page_references: list[str] | None = None
    status: str | None = None

def _load_job_items(job_id: str):
    fp = RESULTS_DIR / f"{job_id}.json"
    if not fp.exists():
        raise HTTPException(status_code=404, detail="Job not found")
    try:
        data = json.loads(fp.read_text())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed reading job file: {e}")
    return data, fp

@router.patch('/questions/{qid}')
async def patch_question(qid: str, payload: QuestionPatch):
    job_id = QUESTION_TO_JOB.get(qid)
    if not job_id:
        raise HTTPException(status_code=404, detail="Question not found")
    data, fp = _load_job_items(job_id)
    items = data.get('items', [])
    target = next((it for it in items if it.get('id') == qid), None)
    if not target:
        raise HTTPException(status_code=404, detail="Question missing in job")
    patch = payload.model_dump(exclude_unset=True)
    target.update(patch)
    data['items'] = items
    fp.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    # sync JOBS
    job = JOBS.get(job_id)
    if job:
        job['results'] = items
    return {"job_id": job_id, "question": target}

@router.delete('/questions/{qid}')
async def delete_question(qid: str):
    job_id = QUESTION_TO_JOB.pop(qid, None)
    if not job_id:
        raise HTTPException(status_code=404, detail="Question not found")
    data, fp = _load_job_items(job_id)
    items = [it for it in data.get('items', []) if it.get('id') != qid]
    data['items'] = items
    fp.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    job = JOBS.get(job_id)
    if job:
        job['results'] = items
    return {"job_id": job_id, "deleted": qid, "remaining": len(items)}
