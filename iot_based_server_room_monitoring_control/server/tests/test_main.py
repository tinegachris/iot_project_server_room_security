from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_status():
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    # Ensure the response contains a "status" key with value "normal" and a "timestamp"
    assert "status" in data
    assert data["status"] == "normal"
    assert "timestamp" in data
