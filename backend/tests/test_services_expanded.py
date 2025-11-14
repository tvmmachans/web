import pytest
from unittest.mock import Mock, patch, AsyncMock
from backend.services.ai_service import AIService
from backend.services.video_service import VideoService
from backend.services.youtube_service import upload_to_youtube
from backend.services.instagram_service import upload_to_instagram
import tempfile
import os


class TestAIService:
    def setup_method(self):
        self.ai_service = AIService()

    @patch("backend.services.ai_service.OpenAI")
    def test_generate_content_success(self, mock_openai):
        # Mock OpenAI response
        mock_client = Mock()
        mock_openai.return_value = mock_client
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Generated content"
        mock_client.chat.completions.create.return_value = mock_response

        result = self.ai_service.generate_content("Test prompt")
        assert result == "Generated content"
        mock_client.chat.completions.create.assert_called_once()

    @patch("backend.services.ai_service.OpenAI")
    def test_generate_caption_malayalam(self, mock_openai):
        mock_client = Mock()
        mock_openai.return_value = mock_client
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "മലയാളം ക്യാപ്ഷൻ"
        mock_client.chat.completions.create.return_value = mock_response

        result = self.ai_service.generate_caption("Test content", "ml")
        assert "മലയാളം" in result

    @patch("backend.services.ai_service.OpenAI")
    def test_generate_subtitles(self, mock_openai):
        mock_client = Mock()
        mock_openai.return_value = mock_client
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = (
            "00:00:01,000 --> 00:00:05,000\nസബ്ടൈറ്റിൽ ടെക്സ്റ്റ്"
        )
        mock_client.audio.transcriptions.create.return_value = mock_response

        result = self.ai_service.generate_subtitles("fake_video.mp4", "ml")
        assert isinstance(result, list)
        assert len(result) > 0

    def test_generate_content_error_handling(self):
        # Test error handling when OpenAI fails
        with patch("backend.services.ai_service.OpenAI") as mock_openai:
            mock_openai.side_effect = Exception("API Error")

            result = self.ai_service.generate_content("Test prompt")
            assert "Error generating content" in result


class TestVideoService:
    def setup_method(self):
        self.video_service = VideoService()

    @patch("backend.services.video_service.boto3.client")
    def test_upload_video_success(self, mock_boto3):
        mock_s3 = Mock()
        mock_boto3.return_value = mock_s3
        mock_s3.upload_file.return_value = None
        mock_s3.generate_presigned_url.return_value = "https://signed-url.com"

        result = self.video_service.upload_video("test.mp4", "test-bucket")
        assert "signed_url" in result
        assert result["signed_url"] == "https://signed-url.com"

    @patch("backend.services.video_service.boto3.client")
    def test_generate_signed_url(self, mock_boto3):
        mock_s3 = Mock()
        mock_boto3.return_value = mock_s3
        mock_s3.generate_presigned_url.return_value = "https://signed-url.com"

        result = self.video_service.generate_signed_url("test-bucket", "test-key")
        assert result == "https://signed-url.com"

    def test_upload_video_invalid_file(self):
        result = self.video_service.upload_video("nonexistent.mp4", "test-bucket")
        assert "error" in result


class TestYouTubeService:
    @patch("backend.services.youtube_service.googleapiclient.discovery.build")
    @patch("backend.services.youtube_service.get_authenticated_service")
    @pytest.mark.asyncio
    async def test_upload_to_youtube_success(self, mock_auth, mock_build):
        mock_youtube = Mock()
        mock_build.return_value = mock_youtube

        mock_response = {"id": "test_video_id"}
        mock_request = Mock()
        mock_request.next_chunk.return_value = (None, mock_response)
        mock_youtube.videos.return_value.insert.return_value = mock_request

        result = await upload_to_youtube("test.mp4", "Test Title", "Test Description")
        assert result == "test_video_id"

    @patch("backend.services.youtube_service.get_authenticated_service")
    @pytest.mark.asyncio
    async def test_upload_to_youtube_error(self, mock_auth):
        mock_auth.side_effect = Exception("Authentication failed")

        result = await upload_to_youtube("test.mp4", "Test Title", "Test Description")
        assert result is None


class TestInstagramService:
    @patch("backend.services.instagram_service.requests.post")
    @pytest.mark.asyncio
    async def test_upload_to_instagram_success(self, mock_post):
        # Mock container creation
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"id": "container_id"}

        # Mock publish response
        mock_publish_response = Mock()
        mock_publish_response.status_code = 200
        mock_publish_response.json.return_value = {"id": "media_id"}

        def side_effect(*args, **kwargs):
            if "media_publish" in args[0]:
                return mock_publish_response
            return Mock(status_code=200, json=lambda: {"id": "container_id"})

        mock_post.side_effect = side_effect

        result = await upload_to_instagram("https://video-url.com", "Test caption")
        assert result["id"] == "media_id"

    @patch("backend.services.instagram_service.requests.post")
    @pytest.mark.asyncio
    async def test_upload_to_instagram_container_error(self, mock_post):
        mock_post.return_value.status_code = 400

        result = await upload_to_instagram("https://video-url.com", "Test caption")
        assert result is None


class TestSchedulerService:
    def setup_method(self):
        from backend.scheduler import scheduler

        self.scheduler = scheduler

    def test_schedule_upload(self):
        from datetime import datetime

        scheduled_time = datetime.utcnow()

        job_id = self.scheduler.schedule_upload(
            post_id=1,
            platform="youtube",
            scheduled_time=scheduled_time,
            title="Test",
            description="Test desc",
        )

        assert job_id is not None
        assert "youtube_1_" in job_id

    def test_get_scheduled_jobs(self):
        jobs = self.scheduler.get_scheduled_jobs()
        assert isinstance(jobs, list)

    def test_cancel_job(self):
        # First schedule a job
        from datetime import datetime

        scheduled_time = datetime.utcnow()
        job_id = self.scheduler.schedule_upload(
            1, "youtube", scheduled_time, "Test", "Test"
        )

        # Then cancel it
        result = self.scheduler.cancel_job(job_id)
        assert result is True

        # Try to cancel non-existent job
        result = self.scheduler.cancel_job("nonexistent")
        assert result is False
