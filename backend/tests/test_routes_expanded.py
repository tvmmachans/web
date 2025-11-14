import json

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_upload_endpoint():
    # Test upload endpoint with mock file
    files = {"file": ("test.mp4", b"fake video content", "video/mp4")}
    data = {"title": "Test Video", "description": "Test Description"}
    response = client.post("/upload", files=files, data=data)
    # Assuming authentication is required, this should return 401 or similar
    assert response.status_code in [401, 403]  # Unauthorized


def test_generate_caption_endpoint():
    data = {"content": "Test video content", "language": "ml"}
    response = client.post("/generate/caption", json=data)
    assert response.status_code in [200, 401]  # 200 if no auth, 401 if auth required
    if response.status_code == 200:
        response_data = response.json()
        assert "caption" in response_data
        assert isinstance(response_data["caption"], str)


def test_generate_subtitles_endpoint():
    data = {"video_path": "/path/to/video.mp4", "language": "ml"}
    response = client.post("/generate/subtitles", json=data)
    assert response.status_code in [200, 401]
    if response.status_code == 200:
        response_data = response.json()
        assert "subtitles" in response_data
        assert isinstance(response_data["subtitles"], list)


def test_schedule_post_endpoint():
    data = {
        "post_id": 1,
        "platform": "youtube",
        "scheduled_at": "2024-12-01T10:00:00Z",
        "title": "Test Post",
        "description": "Test Description",
    }
    response = client.post("/schedule/post", json=data)
    assert response.status_code in [200, 401, 404]  # 404 if post doesn't exist


def test_get_scheduled_jobs_endpoint():
    response = client.get("/schedule/jobs")
    assert response.status_code in [200, 401]
    if response.status_code == 200:
        response_data = response.json()
        assert "jobs" in response_data
        assert isinstance(response_data["jobs"], list)


def test_analytics_endpoint():
    response = client.get("/analytics")
    assert response.status_code in [200, 401]
    if response.status_code == 200:
        response_data = response.json()
        assert isinstance(response_data, list)
        if len(response_data) > 0:
            assert "platform" in response_data[0]
            assert "total_posts" in response_data[0]


def test_analytics_insights_endpoint():
    response = client.get("/analytics/insights")
    assert response.status_code in [200, 401]
    if response.status_code == 200:
        response_data = response.json()
        assert "best_posting_times" in response_data
        assert "top_topics" in response_data


def test_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    # Check if response contains Prometheus metrics format
    assert "HELP" in response.text or "TYPE" in response.text


def test_invalid_endpoints():
    # Test 404 for invalid endpoints
    response = client.get("/invalid-endpoint")
    assert response.status_code == 404


def test_method_not_allowed():
    # Test 405 for wrong HTTP method
    response = client.post("/health")
    assert response.status_code == 405


def test_upload_invalid_file_type():
    # Test upload with invalid file type
    files = {"file": ("test.txt", b"fake text content", "text/plain")}
    data = {"title": "Test Video", "description": "Test Description"}
    response = client.post("/upload", files=files, data=data)
    assert response.status_code in [400, 401, 403]


def test_generate_caption_missing_content():
    data = {"language": "ml"}  # Missing content
    response = client.post("/generate/caption", json=data)
    assert response.status_code in [422, 401]  # 422 for validation error


def test_schedule_invalid_platform():
    data = {
        "post_id": 1,
        "platform": "invalid_platform",
        "scheduled_at": "2024-12-01T10:00:00Z",
    }
    response = client.post("/schedule/post", json=data)
    assert response.status_code in [422, 401, 404]


def test_analytics_with_platform_filter():
    response = client.get("/analytics?platform=youtube")
    assert response.status_code in [200, 401]
    if response.status_code == 200:
        response_data = response.json()
        assert isinstance(response_data, list)


def test_analytics_with_date_filter():
    response = client.get("/analytics?days=7")
    assert response.status_code in [200, 401]
    if response.status_code == 200:
        response_data = response.json()
        assert isinstance(response_data, list)
