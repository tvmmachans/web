from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
from database import get_db
from voice_engine.services.tts_service import tts_service
from voice_engine.services.storage_service import storage_service
from voice_engine.models.voice_models import VoiceProfile, VoiceGeneration
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()


class GenerateVoiceRequest(BaseModel):
    text: str
    voice_profile_id: Optional[int] = None
    voice_type: str = "female"
    language: str = "ml"
    emotion: str = "neutral"
    speed: float = 1.0
    pitch: float = 1.0


class GenerateVoiceResponse(BaseModel):
    audio_url: str
    duration: float
    quality_score: float
    generation_id: int


@router.post("/", response_model=GenerateVoiceResponse)
async def generate_voice(
    request: GenerateVoiceRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Generate voice from text"""
    try:
        # Get voice profile if specified
        voice_profile = None
        if request.voice_profile_id:
            voice_profile = await db.get(VoiceProfile, request.voice_profile_id)
            if not voice_profile:
                raise HTTPException(status_code=404, detail="Voice profile not found")

        # Prepare settings
        settings = {
            "emotion": request.emotion,
            "speed": request.speed,
            "pitch": request.pitch,
        }

        # Generate speech
        audio_data = await tts_service.generate_speech(
            text=request.text, voice_profile=voice_profile, settings=settings
        )

        # Upload to storage
        filename = f"voice_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.wav"
        audio_url = await storage_service.upload_audio(
            audio_data, filename, content_type="audio/wav"
        )

        # Calculate duration (rough estimate)
        duration = len(request.text.split()) * 0.3  # ~0.3 seconds per word

        # Create database record
        voice_gen = VoiceGeneration(
            voice_profile_id=request.voice_profile_id,
            text=request.text,
            audio_url=audio_url,
            duration=duration,
            settings=settings,
            quality_score=0.8,  # Placeholder quality score
        )
        db.add(voice_gen)
        await db.commit()
        await db.refresh(voice_gen)

        # Analyze quality in background
        background_tasks.add_task(
            analyze_and_update_quality, voice_gen.id, audio_url, db
        )

        return GenerateVoiceResponse(
            audio_url=audio_url,
            duration=duration,
            quality_score=voice_gen.quality_score,
            generation_id=voice_gen.id,
        )

    except Exception as e:
        logger.error(f"Voice generation failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Voice generation failed: {str(e)}"
        )


async def analyze_and_update_quality(
    generation_id: int, audio_url: str, db: AsyncSession
):
    """Analyze audio quality and update database"""
    try:
        # Download audio for analysis
        audio_data = await storage_service.download_file(audio_url)

        # Save temporarily for analysis
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_file.write(audio_data)
            temp_path = temp_file.name

        try:
            # Analyze quality
            quality_metrics = await tts_service.analyze_voice_quality(temp_path)

            # Update database
            voice_gen = await db.get(VoiceGeneration, generation_id)
            if voice_gen:
                voice_gen.quality_score = quality_metrics.get("overall_quality", 0.5)
                await db.commit()

        finally:
            # Clean up temp file
            os.unlink(temp_path)

    except Exception as e:
        logger.error(f"Quality analysis failed: {e}")


@router.get("/profiles")
async def get_voice_profiles(db: AsyncSession = Depends(get_db)):
    """Get available voice profiles"""
    try:
        result = await db.execute(
            text(
                "SELECT id, name, language, voice_type, quality_score FROM voice_profiles WHERE training_status = 'completed'"
            )
        )
        profiles = result.fetchall()

        return [
            {
                "id": p.id,
                "name": p.name,
                "language": p.language,
                "voice_type": p.voice_type,
                "quality_score": p.quality_score,
            }
            for p in profiles
        ]

    except Exception as e:
        logger.error(f"Failed to get voice profiles: {e}")
        raise HTTPException(status_code=500, detail="Failed to get voice profiles")


@router.get("/history")
async def get_generation_history(
    skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db)
):
    """Get voice generation history"""
    try:
        result = await db.execute(
            text(
                "SELECT id, text, audio_url, duration, quality_score, created_at FROM voice_generations ORDER BY created_at DESC LIMIT :limit OFFSET :skip"
            ),
            {"limit": limit, "skip": skip},
        )
        generations = result.fetchall()

        return [
            {
                "id": g.id,
                "text": g.text[:100] + "..." if len(g.text) > 100 else g.text,
                "audio_url": g.audio_url,
                "duration": g.duration,
                "quality_score": g.quality_score,
                "created_at": g.created_at.isoformat(),
            }
            for g in generations
        ]

    except Exception as e:
        logger.error(f"Failed to get generation history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get generation history")
