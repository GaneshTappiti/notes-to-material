"""PDF extraction utilities.

Implements page-wise extraction using PyMuPDF (fitz). For each page we try
native text extraction; if the text looks empty (<20 chars ignoring
whitespace) we fallback to a rasterized image + Tesseract OCR (if available).
All extracted artifacts are persisted under STORAGE_PATH:
  pages/<filename>-p{n}.txt  (UTF-8 text)
  images/<filename>-p{n}-{i}.png  (page embedded images)

Returns list of dicts: {page_no, text, images} where images is a list of
saved image relative paths.
"""
from __future__ import annotations

from pathlib import Path
import os
from typing import List, Dict

try:  # runtime optional dependencies
    import fitz  # type: ignore
except ImportError:  # pragma: no cover
    fitz = None

try:  # OCR optional
    import pytesseract  # type: ignore
    from PIL import Image
except ImportError:  # pragma: no cover
    pytesseract = None
    Image = None  # type: ignore

STORAGE_PATH = Path(os.getenv("STORAGE_PATH", "storage"))
PAGES_DIR = STORAGE_PATH / "pages"
IMAGES_DIR = STORAGE_PATH / "images"
PAGES_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

def _sanitize_stem(name: str) -> str:
    keep = [c for c in name if c.isalnum() or c in ('-','_')]
    return ''.join(keep) or 'file'

def extract_pages(filepath: str | Path) -> List[Dict]:
    filepath = Path(filepath)
    if not filepath.exists():  # pragma: no cover - defensive
        raise FileNotFoundError(filepath)
    if fitz is None:  # Fallback if PyMuPDF not installed
        text = filepath.read_bytes()[:200].decode(errors='ignore')
        return [{"page_no": 1, "text": text, "images": []}]

    doc = fitz.open(str(filepath))
    results: List[Dict] = []
    stem = _sanitize_stem(filepath.stem)
    for page_index in range(doc.page_count):
        page = doc.load_page(page_index)
        page_no = page_index + 1
        text = (page.get_text("text") or '').strip()
        if len(text.replace('\n','').strip()) < 20 and pytesseract and Image:  # OCR fallback
            try:  # pragma: no branch
                pix = page.get_pixmap(dpi=200)
                img_path = IMAGES_DIR / f"{stem}-p{page_no}-ocr.png"
                pix.save(str(img_path))
                img = Image.open(img_path)
                ocr_text = pytesseract.image_to_string(img)
                if ocr_text and len(ocr_text.strip()) > len(text):
                    text = ocr_text.strip()
            except Exception:
                pass
        # Save text file
        text_path = PAGES_DIR / f"{stem}-p{page_no}.txt"
        try:
            text_path.write_text(text, encoding='utf-8')
        except Exception:  # pragma: no cover
            pass
        # Extract embedded images
        image_paths: List[str] = []
        try:
            for i, img in enumerate(page.get_images(full=True)):
                xref = img[0]
                try:
                    base = doc.extract_image(xref)
                except Exception:
                    continue
                img_bytes = base.get('image')
                if not img_bytes:
                    continue
                img_ext = (base.get('ext') or 'png').lower()
                out_path = IMAGES_DIR / f"{stem}-p{page_no}-{i}.{ 'png' if img_ext not in ('png','jpg','jpeg') else img_ext}"
                try:
                    with open(out_path, 'wb') as f:
                        f.write(img_bytes)
                    image_paths.append(str(out_path))
                except Exception:
                    continue
        except Exception:  # pragma: no cover
            pass
        results.append({"page_no": page_no, "text": text, "images": image_paths, "text_path": str(text_path)})
    return results

