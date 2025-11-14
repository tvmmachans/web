import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


@pytest.mark.asyncio
async def test_full_content_creation_flow():
    # Test the complete flow from content generation to scheduling
    # This would require mocking external services

    # 1. Generate content
    generate_response = client.post(
        "/generate", json={"prompt": "Create a video about AI"}
    )
    assert generate_response.status_code in [200, 401]  # 401 if auth required

    # 2. Upload video (mock)
    # This would require file upload mocking

    # 3. Schedule post
    schedule_data = {
        "content": "AI is transforming our world",
        "platform": "youtube",
        "schedule_time": "2024-12-01T10:00:00Z",
    }
    schedule_response = client.post("/schedule", json=schedule_data)
    assert schedule_response.status_code in [200, 401]


def test_rate_limiting():
    # Test rate limiting middleware
    for i in range(10):
        response = client.get("/health")
        if i < 5:  # Assuming 5 requests per minute limit
            assert response.status_code == 200
        else:
            assert response.status_code == 429  # Too Many Requests


def test_cors_headers():
    response = client.options("/health")
    assert "access-control-allow-origin" in response.headers
    assert "access-control-allow-methods" in response.headers
