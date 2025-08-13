from fastapi import APIRouter
from pathlib import Path
import json
from ..models import QuestionResult, get_session, create_db

RESULTS_DIR = Path("storage/job_results")

router = APIRouter()

@router.get('/jobs/{job_id}/results')
async def job_results(job_id: str, page: int = 1):
    create_db()
    with get_session() as session:
        q = session.query(QuestionResult).filter(QuestionResult.job_id == job_id)  # type: ignore
        total = q.count()  # type: ignore
        rows = q.offset((page-1)*50).limit(50).all()  # type: ignore
        if rows:
            items = []
            for r in rows:
                base = r.raw_model_output or {
                    'id': r.question_id,
                    'question': r.question_text,
                    'answers': {str(r.mark_value): r.answer} if r.answer else {},
                    'page_references': r.page_references,
                    'status': r.status
                }
                if r.approved_at and 'approval' not in base:
                    base['approval'] = {'approved_at': r.approved_at, 'approver_id': r.approver_id}
                items.append(base)
            return {"job_id": job_id, "page": page, "results": items, "total": total}
    # Fallback legacy JSON
    fp = RESULTS_DIR / f"{job_id}.json"
    if not fp.exists():
        return {"job_id": job_id, "page": page, "results": []}
    try:
        payload = json.loads(fp.read_text())
        items = payload.get("items", [])
    except Exception:
        items = []
    start = (page-1)*50
    end = start + 50
    return {"job_id": job_id, "page": page, "results": items[start:end], "total": len(items)}
