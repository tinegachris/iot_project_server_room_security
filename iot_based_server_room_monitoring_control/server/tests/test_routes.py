from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_trigger_alert():
    # Prepare a valid alert payload based on the Alert model
    alert_data = {
        "message": "Test alert from API",
        "video_url": "http://example.com/video.h264",
        "event_timestamp": "2025-03-13T21:00:00",  # ISO 8601 format
        "channels": ["sms", "email"]
    }
    response = client.post("/api/alert", json=alert_data)
    # Our endpoint returns status code 201 Created on success
    assert response.status_code == 201
    data = response.json()
    assert "message" in data
    assert data["message"] == "Alert processed"
    assert "log_id" in data

def test_manual_control_valid():
    # Test valid control command "lock"
    response = client.post("/api/control", params={"command": "lock_door"})
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "lock" in data["message"].lower()

    # Test valid control command "unlock"
    response = client.post("/api/control", params={"command": "unlock_window"})
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "unlock" in data["message"].lower()

def test_manual_control_invalid():
    # Test an invalid command should return HTTP 400
    response = client.post("/api/control", params={"command": "invalid"})
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
