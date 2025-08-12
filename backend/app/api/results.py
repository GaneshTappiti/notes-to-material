from fastapi import APIRouter
from pathlib import Path
import json

RESULTS_DIR = Path("storage/job_results")

router = APIRouter()

@router.get('/jobs/{job_id}/results')
async def job_results(job_id: str, page: int = 1):
    fp = RESULTS_DIR / f"{job_id}.json"
    if not fp.exists():
        return {"job_id": job_id, "page": page, "results": []}
    try:
        payload = json.loads(fp.read_text())
        items = payload.get("items", [])
    except Exception:
        items = []
    # Simple pagination size 50
    start = (page-1)*50
    end = start + 50
    return {"job_id": job_id, "page": page, "results": items[start:end], "total": len(items)}
