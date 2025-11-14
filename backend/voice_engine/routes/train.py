from fastapi import (
    APIRouter,
    HTTPException,
    Depends,
    UploadFile,
    File,
    Form,
    BackgroundTasks,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
from typing import List, Optional
import logging
import uuid
from database import get_db
from voice_engine.services.storage_service import storage_service
from voice_engine.models.voice_models import VoiceProfile, TrainingJob, AudioSample
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()


class CreateVoiceProfileRequest(BaseModel):
    name: str
    description: Optional[str] = None
    language: str = "ml"
    voice_type: str = "neutral"


class TrainingJobResponse(BaseModel):
    job_id: int
    status: str
    progress: float
    estimated_time: int  # minutes


@router.post("/profile", response_model=dict)
async def create_voice_profile(
    request: CreateVoiceProfileRequest, db: AsyncSession = Depends(get_db)
):
    """Create a new voice profile"""
    try:
        profile = VoiceProfile(
            name=request.name,
            description=request.description,
            language=request.language,
            voice_type=request.voice_type,
            training_status="pending",
        )
        db.add(profile)
        await db.commit()
        await db.refresh(profile)

        return {
            "profile_id": profile.id,
            "message": "Voice profile created successfully",
            "next_step": "Upload audio samples for training",
        }

    except Exception as e:
        logger.error(f"Failed to create voice profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to create voice profile")


@router.post("/profile/{profile_id}/samples")
async def upload_audio_samples(
    profile_id: int,
    files: List[UploadFile] = File(...),
    transcripts: List[str] = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload audio samples for voice training"""
    try:
        # Verify profile exists
        profile = await db.get(VoiceProfile, profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Voice profile not found")

        if len(files) != len(transcripts):
            raise HTTPException(
                status_code=400,
                detail="Number of files must match number of transcripts",
            )

        uploaded_samples = []

        for file, transcript in zip(files, transcripts):
            # Validate file type
            if not file.filename.lower().endswith((".wav", ".mp3", ".flac")):
                continue

            # Read file content
            content = await file.read()

            # Upload to storage
            filename = f"sample_{uuid.uuid4()}_{file.filename}"
            audio_url = await storage_service.upload_audio(
                content, filename, content_type=file.content_type or "audio/wav"
            )

            # Calculate duration (rough estimate)
            duration = len(content) / (44100 * 2)  # Rough calculation for WAV

            # Create database record
            sample = AudioSample(
                voice_profile_id=profile_id,
                audio_url=audio_url,
                transcript=transcript,
                duration=duration,
            )
            db.add(sample)
            uploaded_samples.append(
                {
                    "sample_id": sample.id,
                    "filename": filename,
                    "transcript": transcript,
                    "duration": duration,
                }
            )

        await db.commit()

        return {
            "message": f"Uploaded {len(uploaded_samples)} audio samples",
            "samples": uploaded_samples,
            "next_step": "Start training with these samples",
        }

    except Exception as e:
        logger.error(f"Failed to upload audio samples: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload audio samples")


@router.post("/profile/{profile_id}/start", response_model=TrainingJobResponse)
async def start_voice_training(
    profile_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Start voice training for a profile"""
    try:
        # Verify profile exists and has samples
        profile = await db.get(VoiceProfile, profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Voice profile not found")

        # Check if profile has enough samples
        result = await db.execute(
            text(
                "SELECT COUNT(*) FROM audio_samples WHERE voice_profile_id = :profile_id"
            ),
            {"profile_id": profile_id},
        )
        sample_count = result.scalar()
        if sample_count < 10:
            raise HTTPException(
                status_code=400,
                detail="At least 10 audio samples required for training",
            )

        # Create training job
        training_job = TrainingJob(
            voice_profile_id=profile_id,
            status="queued",
            training_config={"epochs": 100, "batch_size": 16, "learning_rate": 0.001},
        )
        db.add(training_job)

        # Update profile status
        profile.training_status = "training"
        profile.training_progress = 0.0

        await db.commit()
        await db.refresh(training_job)

        # Start training in background
        background_tasks.add_task(train_voice_model, training_job.id, profile_id, db)

        return TrainingJobResponse(
            job_id=training_job.id,
            status="queued",
            progress=0.0,
            estimated_time=30,  # 30 minutes estimate
        )

    except Exception as e:
        logger.error(f"Failed to start voice training: {e}")
        raise HTTPException(status_code=500, detail="Failed to start voice training")


async def train_voice_model(job_id: int, profile_id: int, db: AsyncSession):
    """Background task to train voice model"""
    try:
        # Update job status
        job = await db.get(TrainingJob, job_id)
        job.status = "processing"
        job.started_at = datetime.utcnow()
        await db.commit()

        # Simulate training progress (replace with actual training logic)
        import asyncio

        total_steps = 100

        for step in range(total_steps):
            await asyncio.sleep(1)  # Simulate training time

            # Update progress
            progress = (step + 1) / total_steps
            job.progress = progress
            await db.commit()

            # Update profile progress
            profile = await db.get(VoiceProfile, profile_id)
            profile.training_progress = progress
            await db.commit()

        # Training completed
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        job.metrics = {"loss": 0.05, "accuracy": 0.95, "epochs_completed": 100}
        await db.commit()

        # Update profile
        profile.training_status = "completed"
        profile.quality_score = 0.9
        profile.model_path = f"/models/voice_{profile_id}"
        await db.commit()

        logger.info(f"Voice training completed for profile {profile_id}")

    except Exception as e:
        logger.error(f"Voice training failed: {e}")

        # Update job status to failed
        job = await db.get(TrainingJob, job_id)
        job.status = "failed"
        job.error_message = str(e)
        await db.commit()

        # Update profile status
        profile = await db.get(VoiceProfile, profile_id)
        profile.training_status = "failed"
        await db.commit()


@router.get("/profile/{profile_id}/status")
async def get_training_status(profile_id: int, db: AsyncSession = Depends(get_db)):
    """Get training status for a voice profile"""
    try:
        profile = await db.get(VoiceProfile, profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Voice profile not found")

        # Get latest training job
        result = await db.execute(
            text(
                "SELECT id, status, progress, error_message, started_at, completed_at FROM training_jobs WHERE voice_profile_id = :profile_id ORDER BY created_at DESC LIMIT 1"
            ),
            {"profile_id": profile_id},
        )
        job = result.first()

        return {
            "profile_id": profile_id,
            "training_status": profile.training_status,
            "progress": profile.training_progress,
            "quality_score": profile.quality_score,
            "current_job": (
                {
                    "job_id": job.id if job else None,
                    "status": job.status if job else None,
                    "progress": job.progress if job else None,
                    "error_message": job.error_message if job else None,
                    "started_at": (
                        job.started_at.isoformat() if job and job.started_at else None
                    ),
                    "completed_at": (
                        job.completed_at.isoformat()
                        if job and job.completed_at
                        else None
                    ),
                }
                if job
                else None
            ),
        }

    except Exception as e:
        logger.error(f"Failed to get training status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get training status")


@router.get("/profiles")
async def list_voice_profiles(db: AsyncSession = Depends(get_db)):
    """List all voice profiles"""
    try:
        result = await db.execute(
            text(
                "SELECT id, name, description, language, voice_type, training_status, training_progress, quality_score, created_at FROM voice_profiles ORDER BY created_at DESC"
            )
        )
        profiles = result.fetchall()

        return [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "language": p.language,
                "voice_type": p.voice_type,
                "training_status": p.training_status,
                "training_progress": p.training_progress,
                "quality_score": p.quality_score,
                "created_at": p.created_at.isoformat(),
            }
            for p in profiles
        ]

    except Exception as e:
        logger.error(f"Failed to list voice profiles: {e}")
        raise HTTPException(status_code=500, detail="Failed to list voice profiles")
