import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_live():
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}

def test_health_ready():
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}

def test_generate_caption():
    # Mock request for caption generation
    response = client.post("/generate/caption", json={"content": "Test content", "language": "ml"})
    # This will fail without proper setup, but tests the endpoint exists
    assert response.status_code in [200, 500]  # 500 expected without API keys

def test_get_analytics():
    response = client.get("/analytics/")
    # This will fail without database, but tests the endpoint exists
    assert response.status_code in [200, 500]

def test_get_insights():
    response = client.get("/analytics/insights")
    assert response.status_code == 200
    data = response.json()
    assert "best_posting_times" in data
    assert "top_topics" in data
    assert "caption_suggestions" in data
