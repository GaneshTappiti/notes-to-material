from fastapi.testclient import TestClient
from app.main import app
from app.api.exports import _background_build, ExportRequest, EXPORTS
import time

def test_export_queue(monkeypatch):
    client = TestClient(app)
    # Seed a simple job results file
    job_id = 'gen-exportjob-queued'
    import json, uuid, os
    from pathlib import Path
    results_dir = Path('storage/job_results')
    results_dir.mkdir(parents=True, exist_ok=True)
    payload = {'job_id': job_id, 'items':[{'question':'Q1','answers':{'2':'A2'}, 'page_references': []}]}
    (results_dir / f'{job_id}.json').write_text(json.dumps(payload))
    r = client.post('/api/exports', json={'job_id': job_id})
    assert r.status_code == 200
    export_id = r.json()['export_id']
    assert EXPORTS[export_id]['status'] == 'pending'
    # run background manually
    _background_build(export_id, ExportRequest(job_id=job_id))
    assert EXPORTS[export_id]['status'] == 'ready'
    dr = client.get(f'/api/exports/{export_id}/download')
    assert dr.status_code == 200
    assert dr.headers['content-type'] == 'application/pdf'
