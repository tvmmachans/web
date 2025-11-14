import logging
import os
import subprocess
import sys
import tempfile
from typing import Any, Dict, Optional

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

import requests

from agent.config.settings import (CLIP_DURATION_SECONDS,
                                   CLIP_START_OFFSET_SECONDS)
from agent.services.decision_engine import DecisionEngine

logger = logging.getLogger(__name__)


class ContentRepurposer:
    """
    Handles content repurposing for different social media platforms.
    Creates Instagram clips from YouTube videos, optimizes thumbnails, etc.
    """

    def __init__(self):
        self.decision_engine = DecisionEngine()

    async def repurpose_content(
        self, post, decision: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Repurpose content based on the platform decision.
        """
        try:
            platform = decision.get("platform", "youtube")

            if platform == "instagram":
                return await self._create_instagram_clip(post)
            elif platform == "youtube":
                # For YouTube, we might want to create shorts or optimize existing content
                return await self._optimize_for_youtube(post)

            return None

        except Exception as e:
            logger.error(f"Error repurposing content for post {post.id}: {e}")
            return None

    async def _create_instagram_clip(self, post) -> Optional[Dict[str, Any]]:
        """
        Create a short clip from YouTube video for Instagram.
        """
        try:
            # Download the original video
            video_path = await self._download_video(post.video_url)
            if not video_path:
                return None

            # Create clip
            clip_path = await self._extract_clip(
                video_path, CLIP_START_OFFSET_SECONDS, CLIP_DURATION_SECONDS
            )

            # Generate new thumbnail for clip
            thumbnail_path = await self._generate_thumbnail(clip_path)

            # Generate new caption optimized for Instagram
            caption = await self._generate_instagram_caption(post)

            # Upload clip to storage (would need to implement this)
            # For now, return local paths
            repurposed = {
                "video_url": clip_path,  # In production, this would be uploaded URL
                "thumbnail_url": thumbnail_path,
                "caption": caption,
                "platform": "instagram",
                "duration": CLIP_DURATION_SECONDS,
            }

            logger.info(f"Created Instagram clip for post {post.id}")
            return repurposed

        except Exception as e:
            logger.error(f"Error creating Instagram clip: {e}")
            return None
        finally:
            # Cleanup temp files
            await self._cleanup_temp_files()

    async def _optimize_for_youtube(self, post) -> Optional[Dict[str, Any]]:
        """
        Optimize content for YouTube (create Shorts, improve thumbnails, etc.)
        """
        try:
            # For YouTube, we might create a Short version alongside the main video
            if post.duration and post.duration <= 60:
                # Already short, just optimize caption
                caption = await self._generate_youtube_caption(post)
                return {"caption": caption, "platform": "youtube"}

            # Create a YouTube Short
            video_path = await self._download_video(post.video_url)
            if not video_path:
                return None

            short_path = await self._extract_clip(
                video_path, 0, 60
            )  # 60 seconds for Shorts
            thumbnail_path = await self._generate_thumbnail(short_path)
            caption = await self._generate_youtube_caption(post)

            return {
                "short_video_url": short_path,
                "thumbnail_url": thumbnail_path,
                "caption": caption,
                "platform": "youtube",
            }

        except Exception as e:
            logger.error(f"Error optimizing for YouTube: {e}")
            return None

    async def _download_video(self, video_url: str) -> Optional[str]:
        """
        Download video from storage URL.
        """
        try:
            response = requests.get(video_url, stream=True)
            if response.status_code != 200:
                logger.error(f"Failed to download video: {response.status_code}")
                return None

            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
                for chunk in response.iter_content(chunk_size=8192):
                    temp_file.write(chunk)
                return temp_file.name

        except Exception as e:
            logger.error(f"Error downloading video: {e}")
            return None

    async def _extract_clip(
        self, video_path: str, start_time: int, duration: int
    ) -> Optional[str]:
        """
        Extract a clip from video using ffmpeg.
        """
        try:
            output_path = tempfile.mktemp(suffix=".mp4")

            # ffmpeg command to extract clip
            cmd = [
                "ffmpeg",
                "-i",
                video_path,
                "-ss",
                str(start_time),
                "-t",
                str(duration),
                "-c:v",
                "libx264",
                "-c:a",
                "aac",
                "-strict",
                "experimental",
                "-y",
                output_path,
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                logger.error(f"FFmpeg error: {result.stderr}")
                return None

            return output_path

        except Exception as e:
            logger.error(f"Error extracting clip: {e}")
            return None

    async def _generate_thumbnail(self, video_path: str) -> Optional[str]:
        """
        Generate thumbnail from video at 5-second mark.
        """
        try:
            thumbnail_path = tempfile.mktemp(suffix=".jpg")

            # ffmpeg command to extract thumbnail
            cmd = [
                "ffmpeg",
                "-i",
                video_path,
                "-ss",
                "5",  # 5 seconds in
                "-vframes",
                "1",
                "-q:v",
                "2",
                "-y",
                thumbnail_path,
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                logger.error(f"FFmpeg thumbnail error: {result.stderr}")
                return None

            return thumbnail_path

        except Exception as e:
            logger.error(f"Error generating thumbnail: {e}")
            return None

    async def _generate_instagram_caption(self, post) -> str:
        """
        Generate Instagram-optimized caption.
        """
        try:
            base_caption = (
                post.ai_caption or post.description or f"Check out: {post.title}"
            )

            # Use decision engine to optimize for Instagram
            decision = {"platform": "instagram", "content_category": "entertainment"}
            optimized = await self.decision_engine.optimize_caption(
                base_caption, decision
            )

            return optimized

        except Exception as e:
            logger.error(f"Error generating Instagram caption: {e}")
            return base_caption

    async def _generate_youtube_caption(self, post) -> str:
        """
        Generate YouTube-optimized caption.
        """
        try:
            base_caption = (
                post.ai_caption or post.description or f"Check out: {post.title}"
            )

            # Use decision engine to optimize for YouTube
            decision = {"platform": "youtube", "content_category": "entertainment"}
            optimized = await self.decision_engine.optimize_caption(
                base_caption, decision
            )

            return optimized

        except Exception as e:
            logger.error(f"Error generating YouTube caption: {e}")
            return base_caption

    async def _cleanup_temp_files(self):
        """
        Clean up temporary files created during processing.
        """
        try:
            # This would clean up files from a temp directory
            # For now, we'll rely on system cleanup
            pass
        except Exception as e:
            logger.error(f"Error cleaning up temp files: {e}")

    async def get_repurposing_status(self) -> Dict[str, Any]:
        """
        Get current repurposing service status.
        """
        return {
            "service": "content_repurposer",
            "clip_duration": CLIP_DURATION_SECONDS,
            "start_offset": CLIP_START_OFFSET_SECONDS,
            "supported_platforms": ["instagram", "youtube"],
        }
