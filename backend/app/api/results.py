from fastapi import APIRouter, Query
from pathlib import Path
import json
from ..models import QuestionResult, get_session, create_db
from sqlmodel import select

RESULTS_DIR = Path("storage/job_results")

router = APIRouter()

@router.get('/jobs/{job_id}/results')
async def job_results(
    job_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    approved_only: bool = Query(False)
):
    """Get job results with pagination and filtering.

    Args:
        job_id: The job ID to get results for
        limit: Maximum number of results (1-200, default 50)
        offset: Number of results to skip (default 0)
        approved_only: If true, only return approved questions
    """
    create_db()
    with get_session() as session:
        # Base query
        query = select(QuestionResult).where(QuestionResult.job_id == job_id)

        # Apply approved_only filter
        if approved_only:
            query = query.where(QuestionResult.approved_at != None)

        # Get total count before pagination
        total_query = query
        total = len(list(session.exec(total_query)))

        # Apply pagination
        query = query.offset(offset).limit(limit)
        rows = list(session.exec(query))

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
            return {
                "job_id": job_id,
                "results": items,
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": (offset + len(items)) < total
            }

    # Fallback legacy JSON
    fp = RESULTS_DIR / f"{job_id}.json"
    if not fp.exists():
        return {
            "job_id": job_id,
            "results": [],
            "total": 0,
            "limit": limit,
            "offset": offset,
            "has_more": False
        }
    try:
        payload = json.loads(fp.read_text())
        items = payload.get("items", [])

        # Apply approved_only filter for legacy data
        if approved_only:
            items = [item for item in items if item.get('approval')]

        total = len(items)
        paginated_items = items[offset:offset + limit]

        return {
            "job_id": job_id,
            "results": paginated_items,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + len(paginated_items)) < total
        }
    except Exception:
        return {
            "job_id": job_id,
            "results": [],
            "total": 0,
            "limit": limit,
            "offset": offset,
            "has_more": False
        }
