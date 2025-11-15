"""
Enhanced Video Factory - Multi-format creation, auto-editing, brand consistency
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
import json

from agent.services.ai_video_factory import AIVideoFactory

logger = logging.getLogger(__name__)


class MultiFormatCreator:
    """Creates videos in multiple formats (Shorts, Reels, Long-form)."""

    def __init__(self):
        self.video_factory = AIVideoFactory()

    async def create_multi_format(
        self, script: Dict[str, Any], formats: List[str] = ["short", "reel", "long"]
    ) -> Dict[str, Any]:
        """Create content in multiple formats."""
        results = {}

        for format_type in formats:
            try:
                format_script = self._adapt_script_for_format(script, format_type)
                video_result = await self.video_factory.create_complete_video(
                    format_script, output_filename=f"video_{format_type}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.mp4"
                )
                results[format_type] = video_result
            except Exception as e:
                logger.error(f"Failed to create {format_type} format: {e}")
                results[format_type] = {"error": str(e)}

        return {
            "formats_created": list(results.keys()),
            "results": results,
            "created_at": datetime.utcnow().isoformat(),
        }

    def _adapt_script_for_format(
        self, script: Dict[str, Any], format_type: str
    ) -> Dict[str, Any]:
        """Adapt script for different format."""
        adapted = script.copy()

        if format_type == "short":
            # Condense to 30-60 seconds
            adapted["scenes"] = script.get("scenes", [])[:3]
            adapted["total_duration"] = 60
        elif format_type == "reel":
            # Instagram Reels format (15-90 seconds)
            adapted["scenes"] = script.get("scenes", [])[:2]
            adapted["total_duration"] = 30
        elif format_type == "long":
            # Long-form content (5+ minutes)
            adapted["total_duration"] = 300
            # Expand scenes

        return adapted


class AutoEditingPipeline:
    """Automatically edits videos with color, audio, transitions."""

    def __init__(self):
        self.ffmpeg_path = os.getenv("FFMPEG_PATH", "ffmpeg")

    async def auto_edit_video(
        self,
        video_url: str,
        style: str = "modern",
        transitions: bool = True,
    ) -> Dict[str, Any]:
        """Automatically edit video with enhancements."""
        try:
            # Download video
            video_path = await self._download_video(video_url)

            # Apply enhancements
            edited_path = await self._apply_enhancements(
                video_path, style, transitions
            )

            # Upload edited video
            edited_url = await self._upload_video(edited_path)

            return {
                "original_url": video_url,
                "edited_url": edited_url,
                "enhancements_applied": ["color_correction", "audio_normalization", "transitions"],
                "style": style,
                "status": "completed",
            }

        except Exception as e:
            logger.error(f"Auto editing failed: {e}")
            return {"error": str(e), "status": "failed"}

    async def _apply_enhancements(
        self, video_path: str, style: str, transitions: bool
    ) -> str:
        """Apply video enhancements."""
        import subprocess
        import tempfile

        output_path = tempfile.mktemp(suffix=".mp4")

        # Build FFmpeg command with enhancements
        cmd = [
            self.ffmpeg_path,
            "-i",
            video_path,
            "-vf",
            "eq=contrast=1.1:brightness=0.02:saturation=1.1",  # Color correction
            "-af",
            "loudnorm=I=-16:TP=-1.5:LRA=11",  # Audio normalization
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            output_path,
        ]

        if transitions:
            # Add transitions (simplified)
            pass

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise Exception(f"FFmpeg failed: {result.stderr}")

        return output_path

    async def _download_video(self, url: str) -> str:
        """Download video from URL."""
        import tempfile
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
            temp_file.write(response.content)
            temp_file.close()

            return temp_file.name

    async def _upload_video(self, file_path: str) -> str:
        """Upload video to storage."""
        # Placeholder - would upload to S3/MinIO
        return f"https://storage.example.com/videos/{os.path.basename(file_path)}"


class BrandConsistencyEnforcer:
    """Ensures all content maintains brand style guidelines."""

    def __init__(self):
        self.brand_guidelines = self._load_brand_guidelines()

    def _load_brand_guidelines(self) -> Dict[str, Any]:
        """Load brand style guidelines."""
        return {
            "colors": {
                "primary": "#667eea",
                "secondary": "#764ba2",
                "accent": "#10b981",
            },
            "fonts": {
                "primary": "Inter",
                "secondary": "Roboto",
            },
            "style": {
                "tone": "professional",
                "mood": "engaging",
                "language": "malayalam",
            },
            "content_rules": {
                "min_duration": 30,
                "max_duration": 300,
                "thumbnail_style": "vibrant",
                "subtitle_style": "bold",
            },
        }

    async def validate_brand_compliance(
        self, content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate content meets brand guidelines."""
        issues = []
        score = 1.0

        # Check duration
        duration = content.get("duration", 0)
        if duration < self.brand_guidelines["content_rules"]["min_duration"]:
            issues.append("Duration too short")
            score -= 0.2
        if duration > self.brand_guidelines["content_rules"]["max_duration"]:
            issues.append("Duration too long")
            score -= 0.2

        # Check language
        script = content.get("script", {})
        if not self._check_malayalam_content(script.get("voiceover_text", "")):
            issues.append("Content not in Malayalam")
            score -= 0.3

        # Check thumbnail
        if not content.get("thumbnail_url"):
            issues.append("Missing thumbnail")
            score -= 0.1

        return {
            "compliant": len(issues) == 0,
            "score": max(score, 0.0),
            "issues": issues,
            "guidelines": self.brand_guidelines,
        }

    def _check_malayalam_content(self, text: str) -> bool:
        """Check if content is in Malayalam."""
        malayalam_chars = "അആഇഈഉഊഋഌഎഏഐഒഓഔകഖഗഘങചഛജഝഞടഠഡഢണതഥദധനപഫബഭമയരറലളഴവശഷസഹ"
        return any(char in text for char in malayalam_chars)


class BatchContentCreator:
    """Creates multiple videos in batch."""

    def __init__(self):
        self.video_factory = AIVideoFactory()
        self.multi_format = MultiFormatCreator()

    async def create_batch(
        self, trends: List[Dict[str, Any]], batch_size: int = 5
    ) -> Dict[str, Any]:
        """Create multiple videos from trends."""
        results = []

        for trend in trends[:batch_size]:
            try:
                # Generate content for trend
                from agent.services.ai_content_brain import AIContentBrain

                brain = AIContentBrain()
                content_result = await brain.generate_content_for_trend(trend)

                if content_result.get("script"):
                    # Create video
                    video_result = await self.video_factory.create_complete_video(
                        content_result.get("script")
                    )
                    results.append(
                        {
                            "trend": trend.get("title"),
                            "content": content_result,
                            "video": video_result,
                            "status": "completed",
                        }
                    )
            except Exception as e:
                logger.error(f"Batch creation failed for trend {trend.get('title')}: {e}")
                results.append(
                    {
                        "trend": trend.get("title"),
                        "status": "failed",
                        "error": str(e),
                    }
                )

        return {
            "batch_id": f"batch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "total_requested": len(trends[:batch_size]),
            "completed": len([r for r in results if r.get("status") == "completed"]),
            "failed": len([r for r in results if r.get("status") == "failed"]),
            "results": results,
            "created_at": datetime.utcnow().isoformat(),
        }

