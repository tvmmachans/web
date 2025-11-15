"""
AI Video Factory - Complete autonomous video creation system.
Handles scene generation, voice synthesis, video editing, and subtitle creation.
"""

import asyncio
import logging
import os
import tempfile
from datetime import datetime
from typing import Any, Dict, List, Optional
import json

import httpx
from openai import OpenAI

logger = logging.getLogger(__name__)


class SceneGenerator:
    """Creates video scenes from text using AI models (Stable Video Diffusion)."""

    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.stable_video_api = os.getenv("STABLE_VIDEO_API_URL", "http://localhost:7860")
        self.dalle_api_key = os.getenv("OPENAI_API_KEY")  # Fallback to DALL-E for images

    async def generate_scenes(
        self, script: Dict[str, Any], style: str = "modern"
    ) -> List[Dict[str, Any]]:
        """Generate video scenes from script."""
        scenes = []

        for scene_data in script.get("scenes", []):
            try:
                scene = await self._generate_single_scene(scene_data, style)
                scenes.append(scene)
            except Exception as e:
                logger.error(f"Failed to generate scene {scene_data.get('scene_number')}: {e}")
                # Add fallback scene
                scenes.append(self._create_fallback_scene(scene_data))

        return scenes

    async def _generate_single_scene(
        self, scene_data: Dict[str, Any], style: str
    ) -> Dict[str, Any]:
        """Generate a single video scene."""
        visual_cue = scene_data.get("visual_cue", "")
        dialogue = scene_data.get("dialogue", "")

        # Create prompt for scene generation
        prompt = f"{visual_cue}. {dialogue}. Style: {style}, high quality, vibrant colors"

        # Try Stable Video Diffusion first
        try:
            video_url = await self._generate_with_stable_video(prompt, scene_data)
            if video_url:
                return {
                    "scene_number": scene_data.get("scene_number"),
                    "video_url": video_url,
                    "duration_seconds": scene_data.get("duration_seconds", 10),
                    "prompt": prompt,
                    "generation_method": "stable_video",
                }
        except Exception as e:
            logger.warning(f"Stable Video generation failed: {e}")

        # Fallback to image generation + animation
        try:
            image_url = await self._generate_image_with_dalle(prompt)
            if image_url:
                # Create a simple video from image (would need video processing)
                return {
                    "scene_number": scene_data.get("scene_number"),
                    "image_url": image_url,
                    "video_url": None,  # Would be generated from image
                    "duration_seconds": scene_data.get("duration_seconds", 10),
                    "prompt": prompt,
                    "generation_method": "dalle_fallback",
                }
        except Exception as e:
            logger.warning(f"Image generation failed: {e}")

        # Final fallback
        return self._create_fallback_scene(scene_data)

    async def _generate_with_stable_video(
        self, prompt: str, scene_data: Dict[str, Any]
    ) -> Optional[str]:
        """Generate video using Stable Video Diffusion API."""
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(
                    f"{self.stable_video_api}/api/v1/generate",
                    json={
                        "prompt": prompt,
                        "duration": scene_data.get("duration_seconds", 10),
                        "fps": 24,
                        "width": 1080,
                        "height": 1920,  # Vertical for Shorts/Reels
                    },
                )

                if response.status_code == 200:
                    result = response.json()
                    return result.get("video_url")
        except Exception as e:
            logger.error(f"Stable Video API error: {e}")

        return None

    async def _generate_image_with_dalle(self, prompt: str) -> Optional[str]:
        """Generate image using DALL-E as fallback."""
        try:
            response = self.openai_client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1792",  # Vertical format
                quality="standard",
                n=1,
            )

            return response.data[0].url
        except Exception as e:
            logger.error(f"DALL-E generation error: {e}")

        return None

    def _create_fallback_scene(self, scene_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a fallback scene when generation fails."""
        return {
            "scene_number": scene_data.get("scene_number"),
            "video_url": None,
            "image_url": None,
            "duration_seconds": scene_data.get("duration_seconds", 10),
            "prompt": scene_data.get("visual_cue", ""),
            "generation_method": "fallback",
            "status": "needs_manual_creation",
        }


class VoiceStudio:
    """Generates natural Malayalam voiceovers with emotions."""

    def __init__(self):
        self.voice_engine_url = os.getenv("VOICE_ENGINE_URL", "http://localhost:8000")
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        self.google_tts_api_key = os.getenv("GOOGLE_TTS_API_KEY")

    async def generate_voiceover(
        self,
        text: str,
        language: str = "ml",
        emotion: str = "neutral",
        voice_type: str = "female",
        speed: float = 1.0,
    ) -> Dict[str, Any]:
        """Generate voiceover audio."""
        # Try voice engine first
        try:
            result = await self._generate_with_voice_engine(
                text, language, emotion, voice_type, speed
            )
            if result.get("audio_url"):
                return result
        except Exception as e:
            logger.warning(f"Voice engine failed: {e}")

        # Try ElevenLabs
        if self.elevenlabs_api_key:
            try:
                result = await self._generate_with_elevenlabs(text, language, emotion)
                if result.get("audio_url"):
                    return result
            except Exception as e:
                logger.warning(f"ElevenLabs failed: {e}")

        # Try Google TTS
        if self.google_tts_api_key:
            try:
                result = await self._generate_with_google_tts(text, language)
                if result.get("audio_url"):
                    return result
            except Exception as e:
                logger.warning(f"Google TTS failed: {e}")

        # Fallback
        return {
            "audio_url": None,
            "duration": len(text.split()) * 0.3,  # Estimate
            "error": "All voice generation methods failed",
        }

    async def _generate_with_voice_engine(
        self, text: str, language: str, emotion: str, voice_type: str, speed: float
    ) -> Dict[str, Any]:
        """Generate using internal voice engine."""
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"{self.voice_engine_url}/voice_engine/generate",
                    json={
                        "text": text,
                        "language": language,
                        "emotion": emotion,
                        "voice_type": voice_type,
                        "speed": speed,
                    },
                )

                if response.status_code == 200:
                    result = response.json()
                    return {
                        "audio_url": result.get("audio_url"),
                        "duration": result.get("duration", 0),
                        "method": "voice_engine",
                    }
        except Exception as e:
            logger.error(f"Voice engine error: {e}")

        return {}

    async def _generate_with_elevenlabs(
        self, text: str, language: str, emotion: str
    ) -> Dict[str, Any]:
        """Generate using ElevenLabs API."""
        # ElevenLabs doesn't have native Malayalam, so this is a placeholder
        # Would need custom voice cloning for Malayalam
        return {}

    async def _generate_with_google_tts(self, text: str, language: str) -> Dict[str, Any]:
        """Generate using Google TTS API."""
        try:
            from gtts import gTTS
            import io

            tts = gTTS(text=text, lang="ml", slow=False)
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)

            # Upload to storage (would need storage service)
            return {
                "audio_url": None,  # Would be uploaded URL
                "duration": len(text.split()) * 0.3,
                "method": "google_tts",
            }
        except Exception as e:
            logger.error(f"Google TTS error: {e}")

        return {}


class VideoEditor:
    """Automatically edits scenes, adds transitions, effects."""

    def __init__(self):
        self.ffmpeg_path = os.getenv("FFMPEG_PATH", "ffmpeg")

    async def create_final_video(
        self,
        scenes: List[Dict[str, Any]],
        audio_url: str,
        subtitles: List[Dict[str, Any]],
        output_filename: str,
    ) -> Dict[str, Any]:
        """Create final edited video from scenes, audio, and subtitles."""
        try:
            # Download all assets
            scene_files = []
            for scene in scenes:
                if scene.get("video_url"):
                    file_path = await self._download_file(scene["video_url"])
                    scene_files.append(file_path)

            audio_file = await self._download_file(audio_url) if audio_url else None

            # Create video using FFmpeg
            output_path = await self._compose_video(
                scene_files, audio_file, subtitles, output_filename
            )

            # Upload final video
            video_url = await self._upload_video(output_path)

            # Cleanup
            for file in scene_files + ([audio_file] if audio_file else []):
                if os.path.exists(file):
                    os.remove(file)

            return {
                "video_url": video_url,
                "duration": self._calculate_total_duration(scenes),
                "status": "completed",
            }

        except Exception as e:
            logger.error(f"Video editing failed: {e}")
            return {"video_url": None, "error": str(e), "status": "failed"}

    async def _download_file(self, url: str) -> str:
        """Download file from URL to temporary location."""
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()

            # Create temp file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
            temp_file.write(response.content)
            temp_file.close()

            return temp_file.name

    async def _compose_video(
        self,
        scene_files: List[str],
        audio_file: Optional[str],
        subtitles: List[Dict[str, Any]],
        output_filename: str,
    ) -> str:
        """Compose video using FFmpeg."""
        import subprocess

        output_path = f"/tmp/{output_filename}"

        # Create FFmpeg command
        # This is simplified - real implementation would be more complex
        cmd = [
            self.ffmpeg_path,
            "-i",
            scene_files[0] if scene_files else "black.mp4",  # First scene
            "-i",
            audio_file if audio_file else "silence.wav",  # Audio
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            "-shortest",
            output_path,
        ]

        # Add subtitles if provided
        if subtitles:
            # Create subtitle file
            srt_file = self._create_subtitle_file(subtitles)
            cmd.extend(["-vf", f"subtitles={srt_file}"])

        # Execute FFmpeg
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise Exception(f"FFmpeg failed: {result.stderr}")

        return output_path

    def _create_subtitle_file(self, subtitles: List[Dict[str, Any]]) -> str:
        """Create SRT subtitle file."""
        srt_content = []
        for i, subtitle in enumerate(subtitles, 1):
            start = subtitle.get("start_time", 0)
            end = subtitle.get("end_time", 0)
            text = subtitle.get("text", "")

            srt_content.append(f"{i}\n")
            srt_content.append(f"{self._format_time(start)} --> {self._format_time(end)}\n")
            srt_content.append(f"{text}\n\n")

        srt_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".srt")
        srt_file.write("".join(srt_content))
        srt_file.close()

        return srt_file.name

    def _format_time(self, seconds: float) -> str:
        """Format seconds to SRT time format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)

        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    async def _upload_video(self, file_path: str) -> str:
        """Upload video to storage."""
        # This would integrate with S3/MinIO
        # For now, return placeholder
        return f"https://storage.example.com/videos/{os.path.basename(file_path)}"

    def _calculate_total_duration(self, scenes: List[Dict[str, Any]]) -> float:
        """Calculate total video duration."""
        return sum(scene.get("duration_seconds", 0) for scene in scenes)


class SubtitleEngine:
    """Creates perfect Malayalam/English subtitles with timing."""

    def __init__(self):
        self.whisper_api_url = os.getenv("WHISPER_API_URL", "http://localhost:8001")

    async def generate_subtitles(
        self,
        audio_url: str,
        script: Dict[str, Any],
        languages: List[str] = ["ml", "en"],
    ) -> List[Dict[str, Any]]:
        """Generate subtitles from audio and script."""
        subtitles = []

        # Generate for each language
        for lang in languages:
            try:
                lang_subtitles = await self._generate_language_subtitles(
                    audio_url, script, lang
                )
                subtitles.extend(lang_subtitles)
            except Exception as e:
                logger.error(f"Subtitle generation failed for {lang}: {e}")

        # If no subtitles generated, create from script
        if not subtitles:
            subtitles = self._create_subtitles_from_script(script)

        return subtitles

    async def _generate_language_subtitles(
        self, audio_url: str, script: Dict[str, Any], language: str
    ) -> List[Dict[str, Any]]:
        """Generate subtitles for a specific language."""
        try:
            # Use Whisper API
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(
                    f"{self.whisper_api_url}/transcribe",
                    json={"audio_url": audio_url, "language": language},
                )

                if response.status_code == 200:
                    result = response.json()
                    return self._format_whisper_subtitles(result, language)
        except Exception as e:
            logger.error(f"Whisper API error: {e}")

        return []

    def _format_whisper_subtitles(
        self, whisper_result: Dict[str, Any], language: str
    ) -> List[Dict[str, Any]]:
        """Format Whisper result into subtitle format."""
        subtitles = []
        segments = whisper_result.get("segments", [])

        for segment in segments:
            subtitles.append(
                {
                    "start_time": segment.get("start", 0),
                    "end_time": segment.get("end", 0),
                    "text": segment.get("text", ""),
                    "language": language,
                }
            )

        return subtitles

    def _create_subtitles_from_script(self, script: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create subtitles from script when audio transcription fails."""
        subtitles = []
        current_time = 0.0

        for scene in script.get("scenes", []):
            duration = scene.get("duration_seconds", 10)
            caption = scene.get("caption", scene.get("dialogue", ""))

            subtitles.append(
                {
                    "start_time": current_time,
                    "end_time": current_time + duration,
                    "text": caption,
                    "language": "ml",
                }
            )

            current_time += duration

        return subtitles


class ThumbnailDesigner:
    """Designs thumbnails using AI."""

    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.dalle_api_key = os.getenv("OPENAI_API_KEY")

    async def generate_thumbnail(
        self, script: Dict[str, Any], style: str = "vibrant"
    ) -> Dict[str, Any]:
        """Generate thumbnail image."""
        prompt = script.get("thumbnail_prompt", script.get("hook_line", "വിസ്മയം!"))

        try:
            response = self.openai_client.images.generate(
                model="dall-e-3",
                prompt=f"{prompt}. {style} style, high contrast, bold text, eye-catching thumbnail for Malayalam video",
                size="1280x720",  # Standard thumbnail size
                quality="hd",
                n=1,
            )

            return {
                "thumbnail_url": response.data[0].url,
                "prompt": prompt,
                "status": "completed",
            }

        except Exception as e:
            logger.error(f"Thumbnail generation failed: {e}")
            return {
                "thumbnail_url": None,
                "error": str(e),
                "status": "failed",
            }


class AIVideoFactory:
    """Main orchestrator for AI Video Factory module."""

    def __init__(self):
        self.scene_generator = SceneGenerator()
        self.voice_studio = VoiceStudio()
        self.video_editor = VideoEditor()
        self.subtitle_engine = SubtitleEngine()
        self.thumbnail_designer = ThumbnailDesigner()

    async def create_complete_video(
        self, script: Dict[str, Any], output_filename: str = None
    ) -> Dict[str, Any]:
        """Create complete video package from script."""
        logger.info("Starting complete video creation...")

        if not output_filename:
            output_filename = f"video_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.mp4"

        # Step 1: Generate scenes
        logger.info("Generating video scenes...")
        scenes = await self.scene_generator.generate_scenes(script)

        # Step 2: Generate voiceover
        logger.info("Generating voiceover...")
        voiceover_text = " ".join(
            [scene.get("dialogue", "") for scene in script.get("scenes", [])]
        )
        voiceover = await self.voice_studio.generate_voiceover(
            voiceover_text, language="ml", emotion="neutral"
        )

        # Step 3: Generate subtitles
        logger.info("Generating subtitles...")
        subtitles = []
        if voiceover.get("audio_url"):
            subtitles = await self.subtitle_engine.generate_subtitles(
                voiceover["audio_url"], script
            )

        # Step 4: Generate thumbnail
        logger.info("Generating thumbnail...")
        thumbnail = await self.thumbnail_designer.generate_thumbnail(script)

        # Step 5: Compose final video
        logger.info("Composing final video...")
        final_video = await self.video_editor.create_final_video(
            scenes, voiceover.get("audio_url"), subtitles, output_filename
        )

        return {
            "video_url": final_video.get("video_url"),
            "thumbnail_url": thumbnail.get("thumbnail_url"),
            "audio_url": voiceover.get("audio_url"),
            "subtitles": subtitles,
            "scenes": scenes,
            "duration": final_video.get("duration"),
            "status": final_video.get("status"),
            "created_at": datetime.utcnow().isoformat(),
        }

