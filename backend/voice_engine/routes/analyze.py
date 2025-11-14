from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging
from database import get_db
from voice_engine.services.tts_service import tts_service
from voice_engine.services.storage_service import storage_service
from voice_engine.models.voice_models import VoiceProfile, AudioSample

logger = logging.getLogger(__name__)
router = APIRouter()

class AnalyzeAudioRequest(BaseModel):
    audio_url: str
    language: str = "ml"

class AnalyzeAudioResponse(BaseModel):
    quality_score: float
    metrics: Dict[str, float]
    suggestions: List[str]

@router.post("/audio", response_model=AnalyzeAudioResponse)
async def analyze_audio_quality(
    request: AnalyzeAudioRequest,
    db: AsyncSession = Depends(get_db)
):
    """Analyze audio quality and provide feedback"""
    try:
        # Download audio for analysis
        audio_data = await storage_service.download_file(request.audio_url)

        # Save temporarily for analysis
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_file.write(audio_data)
            temp_path = temp_file.name

        try:
            # Analyze quality
            quality_metrics = await tts_service.analyze_voice_quality(temp_path)

            # Generate suggestions based on metrics
            suggestions = generate_improvement_suggestions(quality_metrics)

            return AnalyzeAudioResponse(
                quality_score=quality_metrics.get('overall_quality', 0.5),
                metrics=quality_metrics,
                suggestions=suggestions
            )

        finally:
            # Clean up temp file
            os.unlink(temp_path)

    except Exception as e:
        logger.error(f"Audio analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Audio analysis failed: {str(e)}")

def generate_improvement_suggestions(metrics: Dict[str, float]) -> List[str]:
    """Generate improvement suggestions based on quality metrics"""
    suggestions = []

    volume = metrics.get('volume', 0.5)
    stability = metrics.get('stability', 0.5)
    brightness = metrics.get('brightness', 0.5)
    snr = metrics.get('snr', 30)

    if volume < 0.3:
        suggestions.append("സംസാരം കൂടുതൽ ഉച്ചത്തിൽ ആയിരിക്കണം")
    elif volume > 0.8:
        suggestions.append("സംസാരം കുറച്ച് ഉച്ചത്തിൽ ആയിരിക്കണം")

    if stability < 0.4:
        suggestions.append("സ്ഥിരമായ ശബ്ദം നിലനിർത്തുക")
        suggestions.append("മൈക്രോഫോൺ സ്ഥിരമായി പിടിക്കുക")

    if brightness < 0.5:
        suggestions.append("കൂടുതൽ സ്പഷ്ടമായ സംസാര രീതി")
    elif brightness > 3.0:
        suggestions.append("സംസാരം കുറച്ച് മൃദുവായി ആയിരിക്കണം")

    if snr < 20:
        suggestions.append("ശബ്ദമില്ലാത്ത സ്ഥലത്ത് റെക്കോർഡ് ചെയ്യുക")
        suggestions.append("മൈക്രോഫോൺ നിലവാരം മെച്ചപ്പെടുത്തുക")

    if not suggestions:
        suggestions.append("ഓഡിയോ നിലവാരം മികച്ചതാണ്!")

    return suggestions

@router.get("/profile/{profile_id}/samples")
async def get_profile_samples(profile_id: int, db: AsyncSession = Depends(get_db)):
    """Get audio samples for a voice profile"""
    try:
        result = await db.execute(
            text("SELECT id, audio_url, transcript, duration, quality_score, created_at FROM audio_samples WHERE voice_profile_id = :profile_id ORDER BY created_at DESC"),
            {"profile_id": profile_id}
        )
        samples = result.fetchall()

        return [
            {
                "id": s.id,
                "audio_url": s.audio_url,
                "transcript": s.transcript,
                "duration": s.duration,
                "quality_score": s.quality_score,
                "created_at": s.created_at.isoformat()
            }
            for s in samples
        ]

    except Exception as e:
        logger.error(f"Failed to get profile samples: {e}")
        raise HTTPException(status_code=500, detail="Failed to get profile samples")

@router.post("/profile/{profile_id}/sample/{sample_id}/analyze")
async def analyze_sample_quality(
    profile_id: int,
    sample_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Analyze quality of a specific audio sample"""
    try:
        sample = await db.get(AudioSample, sample_id)
        if not sample or sample.voice_profile_id != profile_id:
            raise HTTPException(status_code=404, detail="Audio sample not found")

        # Analyze the sample
        analysis_request = AnalyzeAudioRequest(audio_url=sample.audio_url)
        analysis_result = await analyze_audio_quality(analysis_request, db)

        # Update sample quality score
        sample.quality_score = analysis_result.quality_score
        await db.commit()

        return {
            "sample_id": sample_id,
            "analysis": analysis_result.dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Sample analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Sample analysis failed")

@router.get("/profile/{profile_id}/stats")
async def get_profile_stats(profile_id: int, db: AsyncSession = Depends(get_db)):
    """Get statistics for a voice profile"""
    try:
        # Get sample count and average quality
        result = await db.execute(
            text("SELECT COUNT(*) as sample_count, AVG(quality_score) as avg_quality, AVG(duration) as avg_duration FROM audio_samples WHERE voice_profile_id = :profile_id"),
            {"profile_id": profile_id}
        )
        stats = result.first()

        # Get training jobs count
        result = await db.execute(
            text("SELECT COUNT(*) as training_jobs FROM training_jobs WHERE voice_profile_id = :profile_id"),
            {"profile_id": profile_id}
        )
        training_count = result.scalar()

        return {
            "profile_id": profile_id,
            "sample_count": stats.sample_count or 0,
            "average_quality": float(stats.avg_quality or 0),
            "average_duration": float(stats.avg_duration or 0),
            "training_jobs_count": training_count or 0
        }

    except Exception as e:
        logger.error(f"Failed to get profile stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get profile stats")

@router.get("/languages")
async def get_supported_languages():
    """Get list of supported languages for voice analysis"""
    return {
        "languages": [
            {"code": "ml", "name": "മലയാളം", "native_name": "Malayalam"},
            {"code": "en", "name": "English", "native_name": "English"},
            {"code": "hi", "name": "हिंदी", "native_name": "Hindi"}
        ]
    }
