from fastapi.testclient import TestClient
from app.main import app
from pathlib import Path
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

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
    # First user becomes admin
    admin_token = _register('admin@example.com','pass123')
    # Second user student
    student_token = _register('stud@example.com','pass123')
    # Third user faculty (allowed to set role because an admin exists)
    faculty_token = _register('fac@example.com','pass123','faculty')

    # Upload PDF (no auth required yet) -> create job via generate? simplest just craft a fake question record
    # We'll simulate by creating a job result file directly
    job_id = 'job123'
    results_dir = Path('storage/job_results')
    results_dir.mkdir(parents=True, exist_ok=True)
    qid = 'q1'
    results_dir.joinpath(f'{job_id}.json').write_text('{"items": [{"id": "q1", "question": "What?", "answers": {"1": "Ans"}}]}')
    # map qid to job id for in-memory structure
    from app.api.jobs import QUESTION_TO_JOB
    QUESTION_TO_JOB[qid] = job_id

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
