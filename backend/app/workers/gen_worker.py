from ..services.gemini_client import CLIENT
from ..services.vector_store import VECTOR_STORE
import json

QUESTION_SCHEMA = {
    "type": "object",
    "properties": {
        "items": {"type": "array"}
    },
    "required": ["items"]
}


def generate_questions(prompt: str, k: int = 5):
    # TODO: retrieve top-k context
    dummy_context = VECTOR_STORE.items[:k]
    # Build simple prompt (replace with strict JSON instruction)
    full_prompt = f"Context: {dummy_context}\n\nInstruction: {prompt}\nReturn JSON with items."
    raw = CLIENT.generate(full_prompt)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {"items": []}
    return data
