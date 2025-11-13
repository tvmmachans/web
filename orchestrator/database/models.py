"""
Database models for AI Trend Orchestrator.
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, JSON, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Trend(Base):
    """Model for discovered trends."""
    __tablename__ = "trends"

    id = Column(Integer, primary_key=True, index=True)
    trend_id = Column(String(255), unique=True, index=True)  # Unique identifier
    title = Column(String(500), nullable=False)
    description = Column(Text)
    source = Column(String(50), nullable=False)  # youtube, instagram, twitter, rss
    source_url = Column(String(1000))
    language = Column(String(10), default="ml")  # ISO language code
    category = Column(String(100))

    # Trend metrics
    velocity = Column(Float, default=0.0)  # mentions/hour
    freshness_score = Column(Float, default=0.0)  # time-based decay
    cross_platform_count = Column(Integer, default=1)
    trend_strength = Column(Float, default=0.0)  # computed score

    # Metadata
    tags = Column(JSON)  # List of hashtags/tags
    trend_metadata = Column(JSON)  # Additional source-specific data

    # Timestamps
    discovered_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    spike_time = Column(DateTime)  # When trend spiked

    # Relationships
    blueprints = relationship("ContentBlueprint", back_populates="trend")

class ContentBlueprint(Base):
    """Model for generated content blueprints."""
    __tablename__ = "content_blueprints"

    id = Column(Integer, primary_key=True, index=True)
    blueprint_id = Column(String(255), unique=True, index=True)
    trend_id = Column(Integer, ForeignKey("trends.id"), nullable=False)

    # Content elements
    title = Column(String(200))
    hook = Column(String(300))
    script = Column(Text)
    voiceover_text = Column(Text)
    captions = Column(JSON)  # List of caption segments
    hashtags = Column(JSON)  # List of hashtags

    # Media assets
    video_url = Column(String(1000))  # Source video URL
    clip_timestamps = Column(JSON)  # Start/end times for clips
    audio_url = Column(String(1000))  # Generated voiceover URL
    thumbnail_prompt = Column(String(500))

    # ML predictions
    predicted_views = Column(Float)
    predicted_likes = Column(Float)
    predicted_ctr = Column(Float)
    confidence_score = Column(Float)
    roi_score = Column(Float)  # Overall ranking score

    # Status
    status = Column(String(50), default="draft")  # draft, approved, rejected, scheduled, posted
    scheduled_at = Column(DateTime)
    posted_at = Column(DateTime)

    # Metadata
    generation_params = Column(JSON)  # Parameters used for generation
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    trend = relationship("Trend", back_populates="blueprints")
    performances = relationship("PerformanceData", back_populates="blueprint")

class PerformanceData(Base):
    """Model for tracking actual performance of posted content."""
    __tablename__ = "performance_data"

    id = Column(Integer, primary_key=True, index=True)
    blueprint_id = Column(Integer, ForeignKey("content_blueprints.id"), nullable=False)

    # Actual metrics
    actual_views = Column(Integer, default=0)
    actual_likes = Column(Integer, default=0)
    actual_comments = Column(Integer, default=0)
    actual_shares = Column(Integer, default=0)
    watch_time = Column(Float, default=0.0)  # Average watch time
    ctr = Column(Float, default=0.0)

    # Time horizons
    measured_at_1h = Column(DateTime)
    measured_at_24h = Column(DateTime)
    measured_at_7d = Column(DateTime)

    # Computed metrics
    engagement_rate = Column(Float, default=0.0)
    viral_coefficient = Column(Float, default=0.0)

    # Metadata
    platform = Column(String(50))
    post_url = Column(String(1000))
    collected_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    blueprint = relationship("ContentBlueprint", back_populates="performances")

class MLModel(Base):
    """Model for tracking ML model versions and metrics."""
    __tablename__ = "ml_models"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(100), nullable=False)
    version = Column(String(50), nullable=False)
    model_type = Column(String(50), default="xgboost")  # xgboost, sklearn, etc.

    # Model artifacts
    model_path = Column(String(500))
    feature_names = Column(JSON)  # List of features used
    hyperparameters = Column(JSON)

    # Performance metrics
    train_mape = Column(Float)  # Mean Absolute Percentage Error
    val_mape = Column(Float)
    train_auc = Column(Float)
    val_auc = Column(Float)
    feature_importance = Column(JSON)

    # Metadata
    trained_on = Column(DateTime, default=datetime.utcnow)
    training_data_size = Column(Integer)
    is_active = Column(Boolean, default=False)

class DiscoveryRun(Base):
    """Model for tracking discovery runs."""
    __tablename__ = "discovery_runs"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String(255), unique=True, index=True)
    status = Column(String(50), default="running")  # running, completed, failed

    # Run stats
    trends_discovered = Column(Integer, default=0)
    blueprints_generated = Column(Integer, default=0)
    duration_seconds = Column(Float)

    # Source breakdown
    youtube_trends = Column(Integer, default=0)
    instagram_trends = Column(Integer, default=0)
    twitter_trends = Column(Integer, default=0)
    rss_trends = Column(Integer, default=0)

    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

    # Error info
    error_message = Column(Text)
