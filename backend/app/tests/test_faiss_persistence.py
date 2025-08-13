import os, json
from pathlib import Path
import pytest

os.environ['PYTHONPATH'] = 'backend'
os.environ['TEST_MODE'] = '1'

def test_faiss_delete_by_file(monkeypatch):
    from app.services.vector_store_faiss import FAISS_STORE, STORE_PATH
    if not FAISS_STORE.available():
        pytest.skip('faiss not available')
    # reset store file
    if STORE_PATH.exists():
        STORE_PATH.unlink()
    emb1 = [[0.1,0.2,0.3],[0.2,0.1,0.0]]
    meta1 = [{'file_id':'f1','file_name':'a.pdf','page_no':1},{'file_id':'f2','file_name':'b.pdf','page_no':1}]
    FAISS_STORE.add_batch(emb1, meta1)
    assert STORE_PATH.exists()
    # delete file f1
    removed = FAISS_STORE.delete_by_file('f1')
    assert removed == 1
    # ensure remaining metadata doesn't have f1
    from app.services.vector_store_faiss import json as _json  # reuse module json
    data = _json.loads(STORE_PATH.read_text())
    left = [m for m in data['metadatas'] if m.get('file_id')=='f1']
    assert not left
