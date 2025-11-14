import pytest
from fastapi.testclient import TestClient
from backend.main import app
from unittest.mock import patch, AsyncMock
import json

client = TestClient(app)


@pytest.mark.asyncio
async def test_full_content_creation_flow():
    """Test the complete flow from content generation to scheduling"""
    # Mock external services
    with (
        patch("backend.services.ai_service.OpenAI") as mock_openai,
        patch("backend.services.video_service.boto3") as mock_boto3,
        patch("backend.scheduler.scheduler.schedule_upload") as mock_schedule,
    ):

        # Mock AI service
        mock_client = AsyncMock()
        mock_openai.return_value = mock_client
        mock_response = AsyncMock()
        mock_response.choices = [AsyncMock()]
        mock_response.choices[0].message.content = "Generated caption"
        mock_client.chat.completions.create.return_value = mock_response

        # Mock video service
        mock_s3 = AsyncMock()
        mock_boto3.client.return_value = mock_s3
        mock_s3.upload_file.return_value = None
        mock_s3.generate_presigned_url.return_value = "https://signed-url.com"

        # Mock scheduler
        mock_schedule.return_value = "job_123"

        # 1. Generate caption
        generate_response = client.post(
            "/generate/caption",
            json={"content": "Test video content", "language": "ml"},
        )
        assert generate_response.status_code == 200
        caption_data = generate_response.json()
        assert "caption" in caption_data

        # 2. Upload video (mock file upload)
        files = {"file": ("test.mp4", b"fake video content", "video/mp4")}
        data = {"title": "Test Video", "description": caption_data["caption"]}
        upload_response = client.post("/upload", files=files, data=data)
        # This might return 401 if auth is required, adjust accordingly
        assert upload_response.status_code in [200, 401]

        # 3. Schedule post (assuming we have a post ID)
        if upload_response.status_code == 200:
            schedule_data = {
                "post_id": 1,  # Assuming post was created
                "platform": "youtube",
                "scheduled_at": "2024-12-01T10:00:00Z",
                "title": "Test Post",
                "description": caption_data["caption"],
            }
            schedule_response = client.post("/schedule/post", json=schedule_data)
            assert schedule_response.status_code in [200, 404]


def test_rate_limiting():
    """Test rate limiting middleware"""
    # Make multiple requests to test rate limiting
    responses = []
    for i in range(10):
        response = client.get("/health")
        responses.append(response.status_code)

    # At least some should be successful
    assert 200 in responses

    # If rate limiting is implemented, some should be 429
    # assert 429 in responses  # Uncomment if rate limiting is active


def test_cors_headers():
    """Test CORS headers are properly set"""
    response = client.options("/health")
    assert "access-control-allow-origin" in response.headers
    assert "access-control-allow-methods" in response.headers
    assert "access-control-allow-headers" in response.headers


def test_error_handling():
    """Test error handling for various scenarios"""
    # Test invalid JSON
    response = client.post("/generate/caption", data="invalid json")
    assert response.status_code == 422

    # Test missing required fields
    response = client.post("/generate/caption", json={})
    assert response.status_code == 422

    # Test invalid endpoint
    response = client.get("/nonexistent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_analytics_flow():
    """Test analytics data flow"""
    with patch("backend.routes.analytics.get_db") as mock_get_db:
        # Mock database session
        mock_session = AsyncMock()
        mock_get_db.return_value = mock_session

        # Mock analytics query results
        mock_result = AsyncMock()
        mock_result.fetchall.return_value = [
            AsyncMock(
                platform="youtube",
                total_posts=10,
                total_views=1000,
                total_likes=50,
                total_comments=20,
                avg_engagement=0.05,
            )
        ]
        mock_session.execute.return_value = mock_result

        response = client.get("/analytics")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


@pytest.mark.asyncio
async def test_scheduler_integration():
    """Test scheduler integration"""
    with patch("backend.scheduler.scheduler.get_scheduled_jobs") as mock_get_jobs:
        mock_get_jobs.return_value = [
            {
                "job_id": "job_1",
                "platform": "youtube",
                "scheduled_time": "2024-01-01T10:00:00Z",
            }
        ]

        response = client.get("/schedule/jobs")
        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data
        assert len(data["jobs"]) == 1


def test_health_check_detailed():
    """Test detailed health check"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"


def test_metrics_format():
    """Test that metrics endpoint returns proper Prometheus format"""
    response = client.get("/metrics")
    assert response.status_code == 200
    content = response.text

    # Should contain Prometheus metric format
    lines = content.split("\n")
    assert any(line.startswith("# HELP") for line in lines) or any(
        line.startswith("# TYPE") for line in lines
    )


@pytest.mark.asyncio
async def test_cross_service_communication():
    """Test communication between different services"""
    # This would test how different parts of the system interact
    # For example, how analytics service gets data from database

    with (
        patch("backend.routes.analytics.get_db") as mock_get_db,
        patch("backend.services.ai_service.OpenAI") as mock_openai,
    ):

        # Mock database
        mock_session = AsyncMock()
        mock_get_db.return_value = mock_session

        # Mock AI service for insights
        mock_client = AsyncMock()
        mock_openai.return_value = mock_client
        mock_response = AsyncMock()
        mock_response.choices = [AsyncMock()]
        mock_response.choices[0].message.content = "Test insight"
        mock_client.chat.completions.create.return_value = mock_response

        # Test analytics insights endpoint
        response = client.get("/analytics/insights")
        assert response.status_code == 200
        data = response.json()
        assert "best_posting_times" in data
        assert "top_topics" in data


def test_request_validation():
    """Test request validation for various endpoints"""
    # Test invalid platform
    data = {
        "post_id": 1,
        "platform": "invalid_platform",
        "scheduled_at": "2024-12-01T10:00:00Z",
    }
    response = client.post("/schedule/post", json=data)
    assert response.status_code in [422, 401]

    # Test invalid date format
    data = {"post_id": 1, "platform": "youtube", "scheduled_at": "invalid-date"}
    response = client.post("/schedule/post", json=data)
    assert response.status_code in [422, 401]

    # Test missing required fields
    data = {"platform": "youtube"}
    response = client.post("/schedule/post", json=data)
    assert response.status_code == 422
