import io
import os, glob
from fastapi.testclient import TestClient
from app.main import app
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from pathlib import Path
from app.models import get_pages_for_file

client = TestClient(app)

def _make_pdf(bytes_io: io.BytesIO):
    c = canvas.Canvas(bytes_io, pagesize=letter)
    c.drawString(72, 720, "Page 1 sample text for testing.")
    c.showPage()
    c.drawString(72, 720, "Page 2 sample text for testing.")
    c.showPage()  # Need showPage() for the last page too
    c.save()
    bytes_io.seek(0)


def test_pdf_upload_and_ingest(tmp_path):
    # Clear any existing sample files to ensure fresh test
    import os, glob
    storage_pages = Path("storage/pages")
    if storage_pages.exists():
        for f in glob.glob(str(storage_pages / "sample-p*.txt")):
            try:
                os.remove(f)
            except:
                pass

    # create in-memory PDF
    buff = io.BytesIO()
    _make_pdf(buff)
    files = {"file": ("sample.pdf", buff.getvalue(), "application/pdf")}
    r = client.post("/api/uploads", files=files)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["page_count"] == 2
    assert len(data["pages"]) == 2
    # text files exist
    for p in data["pages"]:
        tp = Path(p["stored_text_path"])
        assert tp.exists()
        content = tp.read_text(encoding='utf-8')
        assert len(content) > 0
    # DB rows
    pages = get_pages_for_file("sample.pdf")
    assert len(pages) == 2
