import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_upload_endpoint():
    # Test upload endpoint with mock file
    files = {"file": ("test.mp4", b"fake video content", "video/mp4")}
    data = {"title": "Test Video", "description": "Test Description"}
    response = client.post("/upload", files=files, data=data)
    # Assuming authentication is required, this should return 401 or similar
    assert response.status_code in [401, 403]  # Unauthorized

def test_generate_endpoint():
    data = {"prompt": "Test prompt"}
    response = client.post("/generate", json=data)
    assert response.status_code in [401, 403]  # Unauthorized

def test_schedule_endpoint():
    data = {"content": "Test content", "platform": "youtube", "schedule_time": "2024-01-01T00:00:00Z"}
    response = client.post("/schedule", json=data)
    assert response.status_code in [401, 403]  # Unauthorized

def test_analytics_endpoint():
    response = client.get("/analytics")
    assert response.status_code in [401, 403]  # Unauthorized

def test_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    # Check if response contains Prometheus metrics format
    assert "HELP" in response.text or "TYPE" in response.text
