"""Strict RAG generator service.

Responsibilities:
  - retrieve top-k pages (using in-process vector stores)
  - assemble FILE blocks
  - build strict system + user messages
  - call Gemini client (single text prompt fallback interface)
  - parse + validate JSON output against schema
  - surface NOT_FOUND status when no answer derivable
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import List, Dict, Any
from .gemini_client import CLIENT
from .vector_store import VECTOR_STORE
from .vector_store_faiss import FAISS_STORE
from ..api.retrieval import assemble_context

SYSTEM_MESSAGE = (
    'SYSTEM:\n"You are an JNTUV AR23 academic expert. You MUST ONLY use the exact text and images present in the FILE blocks. '
    'Do not use outside knowledge. If the answer is not present in the provided files, return status: NOT_FOUND. '
    'Return output only in the exact JSON schema provided."'
)

OUTPUT_FIELDS = ["question_id","question_text","marks","answer","answer_format","page_references","diagram_images","verbatim_quotes","status"]

JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "question_id": {"type": "string"},
        "question_text": {"type": "string"},
        "marks": {"type": "integer"},
        "answer": {"type": "string"},
        "answer_format": {"type": "string"},
        "page_references": {"type": "array", "items": {"type": "string"}},
        "diagram_images": {"type": "array", "items": {"type": "string"}},
        "verbatim_quotes": {"type": "array", "items": {"type": "string"}},
        "status": {"type": "string"},
    },
    "required": OUTPUT_FIELDS,
    "additionalProperties": False,
}

@dataclass
class GenerationResult:
    data: Dict[str, Any]
    raw: str
    pages: List[dict]
    error: str | None = None


def _retrieve(query: str, k: int) -> List[dict]:
    emb = CLIENT.embed([query])[0]
    base = VECTOR_STORE.query(emb, top_k=k)
    extra = []
    if FAISS_STORE.available():  # protect against dim mismatch exceptions in tests
        try:  # pragma: no cover - defensive
            extra = FAISS_STORE.query(emb, top_k=k)
        except Exception:
            extra = []
    # merge
    seen = set()
    merged = []
    for r in base + extra:
        md = r.get('metadata', {})
        sig = (md.get('file_id'), md.get('file_name'), md.get('page_no'))
        if sig in seen:
            continue
        seen.add(sig)
        merged.append(r)
    merged.sort(key=lambda x: x.get('score',0), reverse=True)
    pages = []
    for r in merged:
        md = r.get('metadata', {})
        pages.append({
            'file_id': md.get('file_id'),
            'file_name': md.get('file_name'),
            'page_no': md.get('page_no'),
            'text': md.get('text',''),
            'score': r.get('score',0.0)
        })
    return pages


def build_user_message(file_blocks: str, task: str, mark: int) -> str:
    return (
        f"FILES:\n{file_blocks}\n\nTask: {task} marks={mark}. Return JSON following schema: "
        "{question_id,question_text,marks,answer,answer_format,page_references,diagram_images,verbatim_quotes,status}"
    )


def _validate_json(obj: dict) -> tuple[bool, str | None]:
    # minimal manual validation to avoid heavy jsonschema dependency reuse
    for field in OUTPUT_FIELDS:
        if field not in obj:
            return False, f"Missing field: {field}"
    if not isinstance(obj.get('marks'), int):
        return False, 'marks must be integer'
    return True, None


def generate(task: str, mark: int, top_k: int = 6) -> GenerationResult:
    pages = _retrieve(task, top_k)
    file_blocks = assemble_context(pages)
    user_message = build_user_message(file_blocks, task, mark)
    prompt = SYSTEM_MESSAGE + "\n" + user_message + "\nJSON only:"  # single text prompt interface
    raw = CLIENT.generate(prompt)
    error = None
    parsed: dict[str, Any] = {}
    try:
        parsed = json.loads(raw)
    except Exception as e:
        error = f"json_parse_error: {e}"
        parsed = {}
    valid, verr = _validate_json(parsed) if not error else (False, error)
    if not valid:
        # attempt NOT_FOUND fallback if no answer content
        status = parsed.get('status') if isinstance(parsed, dict) else None
        if status != 'NOT_FOUND':
            parsed = {
                'question_id': parsed.get('question_id') if isinstance(parsed, dict) else 'NA',
                'question_text': task,
                'marks': mark,
                'answer': '',
                'answer_format': 'text',
                'page_references': [],
                'diagram_images': [],
                'verbatim_quotes': [],
                'status': 'NOT_FOUND'
            }
        error = verr or error or 'validation_failed'
    # ensure page references present when FOUND
    if parsed.get('status') != 'NOT_FOUND' and not parsed.get('page_references'):
        refs = []
        for p in pages[:3]:
            if p.get('file_id') and p.get('page_no') is not None:
                refs.append(f"{p['file_id']}:{p['page_no']}")
        parsed['page_references'] = refs
    return GenerationResult(data=parsed, raw=raw, pages=pages, error=error)
