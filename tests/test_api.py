from fastapi.testclient import TestClient
from app.api import app

def test_liveness():
    assert TestClient(app).get('/health/live').json()=={'status':'ok'}
def test_invalid_upload():
    response=TestClient(app).post('/ingest',files={'file':('bad.txt',b'hello','text/plain')})
    assert response.status_code==400
