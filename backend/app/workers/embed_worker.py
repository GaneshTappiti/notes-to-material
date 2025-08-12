from ..services.gemini_client import CLIENT
from ..services.vector_store import VECTOR_STORE


def embed_pages(pages):
    texts = [p['text'] for p in pages]
    embeddings = CLIENT.embed(texts)
    for emb, page in zip(embeddings, pages):
        VECTOR_STORE.add(emb, {"page_no": page['page_no']})
