from fastapi.testclient import TestClient
from app.main import app
from pathlib import Path
import json

client = TestClient(app)

def test_delete_job():
    job_id = 'gen-deljob'
    results_dir = Path('storage/job_results')
    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir / f'{job_id}.json').write_text(json.dumps({'job_id':job_id,'items':[]}))
    r = client.delete(f'/api/jobs/{job_id}')
    assert r.status_code == 200
    assert r.json()['deleted'] == job_id

def test_delete_upload(tmp_path):
    # simulate stored upload
    from app.api.uploads import PAGE_DATA_DIR
    file_id = 'upl-del'
    fp = PAGE_DATA_DIR / f'{file_id}.json'
    fp.write_text(json.dumps({'file_id':file_id,'pages':[]}))
    r = client.delete(f'/api/uploads/{file_id}')
    assert r.status_code == 200
    assert r.json()['file_id'] == file_id
