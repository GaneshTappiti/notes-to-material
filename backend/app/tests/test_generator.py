import json
from app.services import generator

class DummyClient:
    def __init__(self, payload):
        self.payload = payload
    def embed(self, texts):
        return [[0.1]*128 for _ in texts]
    def generate(self, prompt: str):
        return json.dumps(self.payload)


def test_generator_success(monkeypatch):
    payload = {
        'question_id': 'q1',
        'question_text': 'What is X?',
        'marks': 2,
        'answer': 'X is Y',
        'answer_format': 'text',
        'page_references': ['f1:1'],
        'diagram_images': [],
        'verbatim_quotes': [],
        'status': 'FOUND'
    }
    dummy = DummyClient(payload)
    monkeypatch.setattr(generator, 'CLIENT', dummy)
    # also patch vector store query to return deterministic pages
    from app.services import vector_store
    monkeypatch.setattr(vector_store.VECTOR_STORE, 'query', lambda emb, top_k=6: [
        {'score':0.9,'metadata':{'file_id':'f1','file_name':'file1.pdf','page_no':1,'text':'Content about X'}},
    ])
    result = generator.generate('Explain X', 2, top_k=1)
    assert result.data['status'] == 'FOUND'
    assert result.data['question_text'] == 'What is X?'
    assert result.error is None or 'validation' not in (result.error or '')


def test_generator_not_found(monkeypatch):
    # return invalid payload -> service should coerce to NOT_FOUND
    dummy = DummyClient({'foo':'bar'})
    monkeypatch.setattr(generator, 'CLIENT', dummy)
    from app.services import vector_store
    monkeypatch.setattr(vector_store.VECTOR_STORE, 'query', lambda emb, top_k=6: [])
    result = generator.generate('Unanswerable question', 5, top_k=1)
    assert result.data['status'] == 'NOT_FOUND'
    assert result.data['answer'] == ''
