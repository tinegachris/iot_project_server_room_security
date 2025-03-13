from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_trigger_alert():
    response = client.post("/alert")
    assert response.status_code == 200
    assert response.json() == {"alert": "Alert triggered"}
