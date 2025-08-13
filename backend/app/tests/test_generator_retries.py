from fastapi.testclient import TestClient
from app.main import app

def test_strict_generator_retry(monkeypatch):
    # Force model to emit malformed JSON first then valid
    calls = {'n':0}
    import json
    from app.services import gemini_client
    def fake_generate(prompt: str):
        calls['n'] += 1
        if calls['n'] == 1:
            return '{"question_id":"q1", "question_text": "Q?", "marks": 2, '  # truncated
        return json.dumps({
            'question_id':'q1','question_text':'Q?','marks':2,'answer':'A','answer_format':'text','page_references':[],'diagram_images':[],'verbatim_quotes':[],'status':'FOUND'
        })
    monkeypatch.setattr(gemini_client.CLIENT, 'generate', fake_generate)
    from app.services.generator import generate
    res = generate('What is?', 2, top_k=0)
    assert res.data['status'] in ('FOUND','NOT_FOUND')
    assert res.data['question_text']
