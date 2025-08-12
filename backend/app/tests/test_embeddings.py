from fastapi.testclient import TestClient
from app.main import app
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

client = TestClient(app)

def _make_pdf(bytes_io: io.BytesIO, texts):
    c = canvas.Canvas(bytes_io, pagesize=letter)
    for t in texts:
        c.drawString(72, 720, t)
        c.showPage()
    c.save()
    bytes_io.seek(0)

def test_embedding_upsert_and_query():
    # upload PDF
    buff = io.BytesIO()
    _make_pdf(buff, ["Alpha page text", "Beta page text"])
    files = {"file": ("embedsample.pdf", buff.getvalue(), "application/pdf")}
    r = client.post('/api/uploads', files=files)
    assert r.status_code == 200
    # upsert
    r2 = client.post('/api/embeddings/upsert')
    assert r2.status_code == 200
    # query
    r3 = client.get('/api/embeddings/query', params={"q":"Alpha", "k":5})
    assert r3.status_code == 200
    data = r3.json()
    assert data['count'] >= 1
    assert any('Alpha' in (res.get('metadata', {}).get('text','')) for res in data['results'])
