import pytest
from services.ai_service import AIService
from services.video_service import VideoService


def test_ai_service_generate_content():
    ai_service = AIService()
    # Mock the OpenAI API call
    result = ai_service.generate_content("Test prompt")
    assert isinstance(result, str)
    assert len(result) > 0


def test_video_service_upload():
    video_service = VideoService()
    # Mock S3 upload
    result = video_service.upload_video("fake_video.mp4", "test-bucket")
    assert "url" in result or "signed_url" in result


def test_video_service_generate_signed_url():
    video_service = VideoService()
    # Test signed URL generation
    signed_url = video_service.generate_signed_url("test-bucket", "test-key")
    assert signed_url.startswith("https://")
    assert "test-bucket" in signed_url
