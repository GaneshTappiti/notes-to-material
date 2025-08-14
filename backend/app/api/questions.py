from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import json
from pathlib import Path
from ..services.auth import require_role, current_user
from ..models import User, QuestionResult, get_session, create_db
from datetime import datetime

RESULTS_DIR = Path("storage/job_results")

router = APIRouter()

class QuestionPatch(BaseModel):
    question: str | None = None
    answers: dict | None = None
    page_references: list[str] | None = None
    status: str | None = None

def _load_job_items(job_id: str):
    # Prefer DB rows
    create_db()
    with get_session() as session:
        rows = session.query(QuestionResult).filter(QuestionResult.job_id == job_id).all()  # type: ignore
        if rows:
            items = []
            for r in rows:
                base = r.raw_model_output or {}
                if not base:
                    base = {
                        'id': r.question_id,
                        'question': r.question_text,
                        'answers': {str(r.mark_value): r.answer} if r.answer else {},
                        'page_references': r.page_references,
                        'status': r.status,
                    }
                if r.approved_at and 'approval' not in base:
                    base['approval'] = {'approved_at': r.approved_at, 'approver_id': r.approver_id}
                items.append(base)
            return {'items': items}, None
    # Fallback to legacy JSON file
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
    # Try DB lookup first
    create_db()
    with get_session() as session:
        qr = session.query(QuestionResult).filter(QuestionResult.question_id == qid).first()  # type: ignore
        if qr:
            if payload.question:
                qr.question_text = payload.question
            if payload.page_references is not None:
                qr.page_references = payload.page_references
            if payload.status:
                qr.status = payload.status
            # answers stored in raw_model_output for now
            rmo = qr.raw_model_output or {}
            if payload.answers:
                rmo['answers'] = payload.answers
            if payload.question:
                rmo['question'] = payload.question
            if payload.page_references is not None:
                rmo['page_references'] = payload.page_references
            qr.raw_model_output = rmo
            session.commit()
            return {"job_id": qr.job_id, "question": rmo}
    raise HTTPException(status_code=404, detail="Question not found")

@router.delete('/questions/{qid}')
async def delete_question(qid: str):
    create_db()
    with get_session() as session:
        qr = session.query(QuestionResult).filter(QuestionResult.question_id == qid).first()  # type: ignore
        if qr:
            job_id = qr.job_id
            session.delete(qr)
            session.commit()
            return {"job_id": job_id, "deleted": qid}
    raise HTTPException(status_code=404, detail="Question not found")


@router.patch('/questions/{qid}/approve')
async def approve_question(qid: str, user: User = Depends(require_role('faculty','admin'))):
    create_db()
    with get_session() as session:
        qr = session.query(QuestionResult).filter(QuestionResult.question_id == qid).first()  # type: ignore
        if qr:
            qr.approved_at = datetime.utcnow().isoformat()
            qr.approver_id = user.id
            rmo = qr.raw_model_output or {}
            rmo['approval'] = { 'approved_at': qr.approved_at, 'approver_id': user.id, 'approver_role': user.role }
            qr.raw_model_output = rmo
            session.commit()
            return {"job_id": qr.job_id, "question": rmo}
    raise HTTPException(status_code=404, detail="Question not found")
