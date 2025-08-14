from fastapi.testclient import TestClient
from app.main import app
from pathlib import Path
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from uuid import uuid4

client = TestClient(app)

def _make_pdf():
    buff = io.BytesIO()
    c = canvas.Canvas(buff, pagesize=letter)
    c.drawString(72, 720, "Sample page for approval test")
    c.save()
    buff.seek(0)
    return buff.getvalue()

def _register(email: str, password: str, role: str | None = None):
    payload = {"email": email, "password": password}
    if role:
        payload['role'] = role
    r = client.post('/api/auth/register', json=payload)
    assert r.status_code == 200, r.text
    return r.json()['token']

def _login(email: str, password: str):
    r = client.post('/api/auth/login', json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()['token']

def test_role_based_approval_flow(tmp_path):
    suffix = uuid4().hex[:6]
    admin_token = _register(f'admin_{suffix}@example.com','pass123','admin')
    student_token = _register(f'stud_{suffix}@example.com','pass123')
    faculty_token = _register(f'fac_{suffix}@example.com','pass123','faculty')

    # Upload PDF (no auth required yet) -> create job via generate? simplest just craft a fake question record
    # We'll simulate by creating a job result file directly
    job_id = 'job123'
    results_dir = Path('storage/job_results')
    results_dir.mkdir(parents=True, exist_ok=True)
    qid = 'q1'
    results_dir.joinpath(f'{job_id}.json').write_text('{"items": [{"id": "q1", "question": "What?", "answers": {"1": "Ans"}}]}')

    # Create test database record for the question-job relationship
    from app.models import create_db, get_session, QuestionResult as QuestionResultModel
    create_db()
    with get_session() as session:
        question_result = QuestionResultModel(
            question_id=qid,
            job_id=job_id,
            mark_value=10,
            question_text="What?",
            answer="Sample answer",
            answer_format="text",
            page_references=[],
            approved=False
        )
        session.add(question_result)
        session.commit()

    # Student tries approval -> 403
    r = client.patch(f'/api/questions/{qid}/approve', headers={'Authorization': f'Bearer {student_token}'})
    assert r.status_code == 403, r.text

    # Faculty approves -> success
    r = client.patch(f'/api/questions/{qid}/approve', headers={'Authorization': f'Bearer {faculty_token}'})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data['question']['approval']['approver_id'] is not None

    # Admin can also approve (second approval overwrites)
    r = client.patch(f'/api/questions/{qid}/approve', headers={'Authorization': f'Bearer {admin_token}'})
    assert r.status_code == 200
