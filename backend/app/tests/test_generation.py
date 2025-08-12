import json
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

def test_generate_empty(monkeypatch):
    client = TestClient(app)
    # Force embed + generate minimal fallbacks
    r = client.post('/api/generate', json={'prompt':'Test prompt','top_k':1})
    assert r.status_code == 200
    data = r.json()
    assert 'job_id' in data
    assert 'output' in data
    assert 'items' in data['output']

def test_update_item(monkeypatch, tmp_path):
    client = TestClient(app)
    # create a fake job file
    job_id = 'gen-testjob'
    results_dir = Path('storage/job_results')
    results_dir.mkdir(parents=True, exist_ok=True)
    payload = {'job_id': job_id, 'items':[{'question':'Q1','answers':{'2':'A2'}, 'page_references': []}]}
    (results_dir / f'{job_id}.json').write_text(json.dumps(payload))
    # update
    r = client.post('/api/jobs/update_item', json={'job_id':job_id,'index':0,'question':'Q1 edited','answers':{'2':'A2 edited'}, 'status':'approved'})
    assert r.status_code == 200
    updated = r.json()['item']
    assert updated['question'] == 'Q1 edited'
    assert updated['answers']['2'] == 'A2 edited'
    assert updated['status'] == 'approved'

def test_export(monkeypatch):
    client = TestClient(app)
    # Prepare job
    job_id = 'gen-exportjob'
    results_dir = Path('storage/job_results')
    results_dir.mkdir(parents=True, exist_ok=True)
    payload = {'job_id': job_id, 'items':[{'question':'Q1','answers':{'2':'A2'}, 'page_references': []}]}
    (results_dir / f'{job_id}.json').write_text(json.dumps(payload))
    r = client.post('/api/export/'+job_id)
    assert r.status_code == 200
    export_id = r.json()['export_id']
    dr = client.get(f'/api/exports/{export_id}/download')
    assert dr.status_code == 200
    assert dr.headers['content-type'] == 'application/pdf'
