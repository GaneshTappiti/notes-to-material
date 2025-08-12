# Placeholder ingestion worker (would be Celery / RQ in production)
from pathlib import Path
from ..services import pdf_extract


def ingest_pdf(path: Path, file_id: str, original_name: str):
    pages = pdf_extract.extract_pages(path)
    # TODO: persist pages to DB
    return pages
