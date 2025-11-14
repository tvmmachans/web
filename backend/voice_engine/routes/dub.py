import logging
import uuid
from datetime import datetime
from typing import Optional

from database import get_db
from fastapi import (APIRouter, BackgroundTasks, Depends, File, HTTPException,
                     UploadFile)
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from voice_engine.models.voice_models import VideoDub, VoiceProfile
from voice_engine.services.storage_service import storage_service

logger = logging.getLogger(__name__)
router = APIRouter()


class DubVideoRequest(BaseModel):
    video_url: str
    voice_profile_id: Optional[int] = None
    language: str = "ml"
    voice_type: str = "female"


class DubVideoResponse(BaseModel):
    dub_id: int
    status: str
    progress: float
    estimated_time: int  # minutes


@router.post("/", response_model=DubVideoResponse)
async def dub_video(
    request: DubVideoRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Dub video with voice"""
    try:
        # Verify voice profile if specified
        voice_profile = None
        if request.voice_profile_id:
            voice_profile = await db.get(VoiceProfile, request.voice_profile_id)
            if not voice_profile:
                raise HTTPException(status_code=404, detail="Voice profile not found")

        # Download video to check if it exists
        try:
            video_data = await storage_service.download_file(request.video_url)
        except Exception:
            raise HTTPException(status_code=400, detail="Video URL is not accessible")

        # Create dubbing job
        dub_job = VideoDub(
            video_url=request.video_url,
            voice_profile_id=request.voice_profile_id,
            language=request.language,
            status="queued",
            progress=0.0,
        )
        db.add(dub_job)
        await db.commit()
        await db.refresh(dub_job)

        # Start dubbing in background
        background_tasks.add_task(
            process_video_dubbing,
            dub_job.id,
            request.video_url,
            voice_profile,
            request.language,
            db,
        )

        return DubVideoResponse(
            dub_id=dub_job.id,
            status="queued",
            progress=0.0,
            estimated_time=10,  # 10 minutes estimate
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start video dubbing: {e}")
        raise HTTPException(status_code=500, detail="Failed to start video dubbing")


async def process_video_dubbing(
    dub_id: int,
    video_url: str,
    voice_profile: Optional[VoiceProfile],
    language: str,
    db: AsyncSession,
):
    """Background task to process video dubbing"""
    try:
        # Update status to processing
        dub = await db.get(VideoDub, dub_id)
        dub.status = "processing"
        await db.commit()

        # Download video
        video_data = await storage_service.download_file(video_url)

        # Save video temporarily
        import os
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_video:
            temp_video.write(video_data)
            temp_video_path = temp_video.name

        dubbed_video_path = None

        try:
            # Extract audio from video
            from moviepy.editor import VideoFileClip

            video_clip = VideoFileClip(temp_video_path)
            audio_path = temp_video_path.replace(".mp4", "_audio.wav")
            video_clip.audio.write_audiofile(audio_path, verbose=False, logger=None)

            # Transcribe audio (placeholder - would use Whisper or similar)
            transcript = extract_transcript_from_audio(audio_path)

            # Generate voice for transcript
            from voice_engine.services.tts_service import tts_service

            voice_audio_data = await tts_service.generate_speech(
                text=transcript,
                voice_profile=voice_profile,
                settings={"language": language},
            )

            # Save generated voice
            voice_audio_path = temp_video_path.replace(".mp4", "_voice.wav")
            with open(voice_audio_path, "wb") as f:
                f.write(voice_audio_data)

            # Combine video with new audio
            from moviepy.editor import AudioFileClip

            voice_audio_clip = AudioFileClip(voice_audio_path)
            dubbed_video_clip = video_clip.set_audio(voice_audio_clip)

            dubbed_video_path = temp_video_path.replace(".mp4", "_dubbed.mp4")
            dubbed_video_clip.write_videofile(
                dubbed_video_path, audio_codec="aac", verbose=False, logger=None
            )

            # Upload dubbed video
            with open(dubbed_video_path, "rb") as f:
                dubbed_data = f.read()

            filename = f"dubbed_{uuid.uuid4()}.mp4"
            dubbed_url = await storage_service.upload_video(
                dubbed_data, filename, content_type="video/mp4"
            )

            # Update database
            dub.dubbed_video_url = dubbed_url
            dub.status = "completed"
            dub.progress = 1.0
            dub.completed_at = datetime.utcnow()
            dub.duration = video_clip.duration
            dub.metadata = {
                "original_duration": video_clip.duration,
                "transcript": transcript,
                "language": language,
            }
            await db.commit()

            logger.info(f"Video dubbing completed for dub_id {dub_id}")

        finally:
            # Cleanup temp files
            for path in [
                temp_video_path,
                audio_path,
                voice_audio_path,
                dubbed_video_path,
            ]:
                if path and os.path.exists(path):
                    os.unlink(path)

    except Exception as e:
        logger.error(f"Video dubbing failed: {e}")

        # Update status to failed
        dub = await db.get(VideoDub, dub_id)
        dub.status = "failed"
        dub.metadata = {"error": str(e)}
        await db.commit()


def extract_transcript_from_audio(audio_path: str) -> str:
    """Extract transcript from audio (placeholder implementation)"""
    # This would use Whisper or similar service
    # For now, return a placeholder transcript
    return "ഇത് ഒരു സാമ്പിൾ ട്രാൻസ്ക്രിപ്റ്റ് ആണ്. ഇത് മലയാളം ഭാഷയിൽ ആണ്."


@router.get("/{dub_id}/status")
async def get_dubbing_status(dub_id: int, db: AsyncSession = Depends(get_db)):
    """Get dubbing status"""
    try:
        dub = await db.get(VideoDub, dub_id)
        if not dub:
            raise HTTPException(status_code=404, detail="Dubbing job not found")

        return {
            "dub_id": dub.id,
            "status": dub.status,
            "progress": dub.progress,
            "video_url": dub.video_url,
            "dubbed_video_url": dub.dubbed_video_url,
            "duration": dub.duration,
            "created_at": dub.created_at.isoformat(),
            "completed_at": dub.completed_at.isoformat() if dub.completed_at else None,
            "metadata": dub.metadata,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get dubbing status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dubbing status")


@router.get("/history")
async def get_dubbing_history(
    skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db)
):
    """Get dubbing history"""
    try:
        result = await db.execute(
            text(
                "SELECT id, video_url, dubbed_video_url, status, progress, duration, created_at, completed_at FROM video_dubs ORDER BY created_at DESC LIMIT :limit OFFSET :skip"
            ),
            {"limit": limit, "skip": skip},
        )
        dubs = result.fetchall()

        return [
            {
                "id": d.id,
                "video_url": d.video_url,
                "dubbed_video_url": d.dubbed_video_url,
                "status": d.status,
                "progress": d.progress,
                "duration": d.duration,
                "created_at": d.created_at.isoformat(),
                "completed_at": d.completed_at.isoformat() if d.completed_at else None,
            }
            for d in dubs
        ]

    except Exception as e:
        logger.error(f"Failed to get dubbing history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dubbing history")
