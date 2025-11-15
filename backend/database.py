import os
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Float, Integer, String, Text, ForeignKey
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, relationship

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://user:password@localhost/social_media_manager"
)

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    video_url = Column(String)
    thumbnail_url = Column(String)
    duration = Column(Float)
    platform = Column(String)  # youtube, instagram
    scheduled_at = Column(DateTime)
    posted_at = Column(DateTime)
    status = Column(String, default="draft")  # draft, scheduled, posted
    ai_caption = Column(Text)
    ai_subtitles = Column(JSON)  # Store subtitles as JSON
    analytics = Column(JSON)  # Store analytics data
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Analytics(Base):
    __tablename__ = "analytics"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, index=True)
    platform = Column(String)
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    engagement_rate = Column(Float, default=0.0)
    recorded_at = Column(DateTime, default=datetime.utcnow)


class Trends(Base):
    __tablename__ = "trends"

    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String, nullable=False)
    platform = Column(String)
    velocity = Column(Float, default=0.0)  # Rate of growth
    trend_strength = Column(Float, default=0.0)  # Overall strength
    cross_platform_count = Column(Integer, default=0)
    language = Column(String, default="ml")  # Malayalam focus
    freshness = Column(Float, default=0.0)  # How recent the trend is
    predicted_peak = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LearningData(Base):
    __tablename__ = "learning_data"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, index=True)
    features = Column(JSON)  # ML features used for prediction
    actual_performance = Column(JSON)  # Actual engagement metrics
    predicted_performance = Column(JSON)  # ML predictions
    feedback_score = Column(Float, default=0.0)  # How well predictions matched reality
    learning_insights = Column(JSON)  # Insights extracted for future learning
    created_at = Column(DateTime, default=datetime.utcnow)


class ModelMetrics(Base):
    __tablename__ = "model_metrics"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String, nullable=False)
    model_version = Column(String)
    training_date = Column(DateTime, default=datetime.utcnow)
    metrics = Column(JSON)  # MAE, R2, accuracy scores
    feature_importance = Column(JSON)  # Which features mattered most
    training_samples = Column(Integer, default=0)
    is_active = Column(Integer, default=1)


class PostingOptimization(Base):
    __tablename__ = "posting_optimization"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String, nullable=False)
    optimal_hour = Column(Integer)  # 0-23
    optimal_day = Column(Integer)  # 0-6 (Monday-Sunday)
    engagement_score = Column(Float, default=0.0)
    confidence = Column(Float, default=0.0)
    language = Column(String, default="ml")
    last_updated = Column(DateTime, default=datetime.utcnow)
    sample_size = Column(Integer, default=0)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session


# Import advanced models to register them
from backend.models.advanced_models import (
    AIGeneratedContent,
    AutomationWorkflow,
    ContentCalendar,
    TrendPrediction,
    ABTestResult,
    CompetitorAnalysis,
    PerformanceMetrics,
)
