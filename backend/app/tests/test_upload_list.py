from fastapi.testclient import TestClient
from app.main import app
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

client = TestClient(app)

def _make_pdf(texts):
    buff = io.BytesIO()
    c = canvas.Canvas(buff, pagesize=letter)
    for t in texts:
        c.drawString(72, 720, t)
        c.showPage()
    c.save()
    buff.seek(0)
    return buff.getvalue()

def test_upload_list_endpoint():
    pdf_bytes = _make_pdf(["Listing test page 1"])
    files = {"file": ("listfile.pdf", pdf_bytes, "application/pdf")}
    r = client.post('/api/uploads', files=files)
    assert r.status_code == 200, r.text
    fid = r.json()['file_id']
    r2 = client.get('/api/uploads')
    assert r2.status_code == 200, r2.text
    data = r2.json()
    assert any(u['file_id'] == fid for u in data.get('uploads', []))
    r3 = client.delete(f'/api/uploads/{fid}')
    assert r3.status_code == 200
