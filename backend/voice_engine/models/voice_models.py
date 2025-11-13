from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, JSON, ForeignKey
from datetime import datetime
from database import Base

class VoiceProfile(Base):
    __tablename__ = "voice_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    language = Column(String, default='ml')  # ml, en, hi
    voice_type = Column(String, default='neutral')  # male, female, comedy, serious
    model_path = Column(String)  # Path to trained model
    sample_audio_url = Column(String)  # URL to sample audio
    training_status = Column(String, default='pending')  # pending, training, completed, failed
    training_progress = Column(Float, default=0.0)
    quality_score = Column(Float, default=0.0)
    metadata = Column(JSON)  # Additional voice characteristics
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class TrainingJob(Base):
    __tablename__ = "training_jobs"

    id = Column(Integer, primary_key=True, index=True)
    voice_profile_id = Column(Integer, ForeignKey('voice_profiles.id'), index=True)
    status = Column(String, default='queued')  # queued, processing, completed, failed
    progress = Column(Float, default=0.0)
    error_message = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    training_config = Column(JSON)  # Training parameters
    metrics = Column(JSON)  # Training metrics
    created_at = Column(DateTime, default=datetime.utcnow)

class AudioSample(Base):
    __tablename__ = "audio_samples"

    id = Column(Integer, primary_key=True, index=True)
    voice_profile_id = Column(Integer, ForeignKey('voice_profiles.id'), index=True)
    audio_url = Column(String, nullable=False)
    duration = Column(Float)
    transcript = Column(Text)
    quality_score = Column(Float, default=0.0)
    metadata = Column(JSON)  # Audio analysis data
    created_at = Column(DateTime, default=datetime.utcnow)

class VoiceGeneration(Base):
    __tablename__ = "voice_generations"

    id = Column(Integer, primary_key=True, index=True)
    voice_profile_id = Column(Integer, ForeignKey('voice_profiles.id'), index=True)
    text = Column(Text, nullable=False)
    audio_url = Column(String)
    duration = Column(Float)
    settings = Column(JSON)  # emotion, speed, pitch settings
    quality_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

class VideoDub(Base):
    __tablename__ = "video_dubs"

    id = Column(Integer, primary_key=True, index=True)
    video_url = Column(String, nullable=False)
    dubbed_video_url = Column(String)
    voice_profile_id = Column(Integer, ForeignKey('voice_profiles.id'), index=True)
    language = Column(String, default='ml')
    status = Column(String, default='pending')  # pending, processing, completed, failed
    progress = Column(Float, default=0.0)
    duration = Column(Float)
    metadata = Column(JSON)  # Lip-sync data, timing info
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
