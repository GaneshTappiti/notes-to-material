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

import json, re
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


def _retrieve(query: str, k: int, file_ids: List[str] | None = None) -> List[dict]:
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

        # Apply file_ids filter if specified
        if file_ids and md.get('file_id') not in file_ids:
            continue

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


def _repair_json(text: str) -> str | None:
    """Attempt lightweight JSON repair (truncate to last balanced brace, quote keys)."""
    # Balance braces
    open_count = 0
    last_good = -1
    for i, ch in enumerate(text):
        if ch == '{':
            open_count += 1
        elif ch == '}':
            open_count -= 1
            if open_count == 0:
                last_good = i
    if last_good != -1:
        candidate = text[: last_good + 1]
        # naive key quoting fix: replace unquoted keys at start of line
        candidate = re.sub(r'([,{]\s*)([A-Za-z_][A-Za-z0-9_]*)(\s*:)','\1"\2"\3', candidate)
        return candidate
    return None


def generate(task: str, mark: int, top_k: int = 6, file_ids: List[str] | None = None) -> GenerationResult:
    pages = _retrieve(task, top_k, file_ids)
    file_blocks = assemble_context(pages)
    user_message = build_user_message(file_blocks, task, mark)
    base_prompt = SYSTEM_MESSAGE + "\n" + user_message + "\nJSON only:"
    attempts: list[str] = []
    raw = ''
    parsed: dict[str, Any] = {}
    error: str | None = None
    for attempt in range(3):
        prompt = base_prompt
        if attempt > 0:
            prompt += f"\n# Retry {attempt}: STRICT VALID JSON with fields {OUTPUT_FIELDS}."
        raw = CLIENT.generate(prompt)
        try:
            parsed = json.loads(raw)
            valid, verr = _validate_json(parsed)
            if valid:
                error = None
                break
            else:
                error = verr or 'validation_failed'
        except Exception as e:
            # try repair
            repaired = _repair_json(raw)
            if repaired:
                try:
                    parsed = json.loads(repaired)
                    valid, verr = _validate_json(parsed)
                    if valid:
                        raw = repaired  # use repaired version
                        error = None
                        break
                    else:
                        error = verr or f'validation_failed_after_repair'
                except Exception as e2:  # pragma: no cover
                    error = f"json_parse_error: {e2}"  # keep last
            else:
                error = f"json_parse_error: {e}"
        attempts.append(error or 'unknown_error')
    if error:
        # fallback NOT_FOUND object
        base_id = parsed.get('question_id') if isinstance(parsed, dict) else 'NA'
        parsed = {
            'question_id': base_id or 'NA',
            'question_text': task,
            'marks': mark,
            'answer': '',
            'answer_format': 'text',
            'page_references': [],
            'diagram_images': [],
            'verbatim_quotes': [],
            'status': 'NOT_FOUND'
        }
    # ensure page references present when FOUND
    if parsed.get('status') != 'NOT_FOUND' and not parsed.get('page_references'):
        refs = []
        for p in pages[:3]:
            if p.get('file_id') and p.get('page_no') is not None:
                refs.append(f"{p['file_id']}:{p['page_no']}")
        parsed['page_references'] = refs
    return GenerationResult(data=parsed, raw=raw, pages=pages, error=error)
