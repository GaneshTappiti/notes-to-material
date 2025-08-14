import io, json, uuid
from fastapi.testclient import TestClient
from app.main import app
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from app.models import get_session, Job as JobModel, create_db

client = TestClient(app)

def _make_pdf(texts):
    buff = io.BytesIO()
    c = canvas.Canvas(buff, pagesize=letter)
    for t in texts:
        c.drawString(72, 720, t)
        c.showPage()
    c.save(); buff.seek(0)
    return buff.getvalue()

def test_generate_from_job_flow():
    # Upload PDF to create pages
    pdf_bytes = _make_pdf(["Alpha concept text", "Beta concept second page"])
    r = client.post('/api/uploads', files={'file': ('jobgen.pdf', pdf_bytes, 'application/pdf')})
    assert r.status_code == 200, r.text
    file_id = r.json()['file_id']
    # Create job row directly (simulate /api/jobs future payload with files list)
    create_db()
    payload = { 'files': [file_id] }
    job_id = f'job-gen-test-{uuid.uuid4().hex[:8]}'  # Make unique
    with get_session() as session:
        # Clean up any existing job with similar ID to avoid conflicts
        try:
            existing = session.query(JobModel).filter(JobModel.job_id.like('job-gen-test%')).all()
            for j in existing:
                session.delete(j)
            session.commit()
        except Exception:
            session.rollback()  # Handle any constraint errors

        job = JobModel(job_id=job_id, job_name='Generation Job', mode='manual', payload_json=payload, status='created')
        session.add(job)
        session.commit()
    # Call generation from job endpoint
    gr = client.post('/api/generate/from_job', json={'job_id': job_id, 'marks_type': '2,5', 'max_questions': 3})
    assert gr.status_code == 200, gr.text
    data = gr.json()
    assert data['job_id'] == job_id
    assert data['count'] >= 1
    # Each question should have answers object with at least one mark variant
    for q in data['questions']:
        assert 'answers' in q and isinstance(q['answers'], dict)
        # ensure required labeled sections present (Definition, etc.) appended by endpoint logic
        for ans in q['answers'].values():
            assert 'Definition:' in ans
            assert 'Marking Scheme:' in ans
