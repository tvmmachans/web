"""
Advanced database models for complete AI Social Media Manager.
"""

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    DateTime,
    JSON,
    Boolean,
    ForeignKey,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
from backend.database import Base
import enum


class ContentStatus(str, enum.Enum):
    DRAFT = "draft"
    GENERATING = "generating"
    READY = "ready"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    POSTED = "posted"
    FAILED = "failed"


class WorkflowStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class AIGeneratedContent(Base):
    """Model for AI-generated content from trends."""

    __tablename__ = "ai_generated_content"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(String(255), unique=True, index=True)
    trend_id = Column(Integer, ForeignKey("trends.id"), nullable=False)

    # Content elements
    title = Column(String(500), nullable=False)
    script = Column(Text)
    voiceover_text = Column(Text)
    voiceover_url = Column(String(1000))
    video_url = Column(String(1000))
    thumbnail_url = Column(String(1000))
    subtitles = Column(JSON)  # List of subtitle segments with timing

    # Generation metadata
    generation_method = Column(String(50))  # stable_video, dalle, etc.
    ai_model_used = Column(String(100))  # gpt-4, dall-e-3, etc.
    generation_params = Column(JSON)
    quality_score = Column(Float, default=0.0)

    # Status
    status = Column(SQLEnum(ContentStatus), default=ContentStatus.DRAFT)
    error_message = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    generated_at = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    trend = relationship("Trends", backref="ai_content")
    workflow_runs = relationship("AutomationWorkflow", back_populates="content")
    ab_tests = relationship("ABTestResult", back_populates="content")


class AutomationWorkflow(Base):
    """Model for tracking automation workflow runs."""

    __tablename__ = "automation_workflows"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(String(255), unique=True, index=True)
    workflow_type = Column(String(50))  # daily_pipeline, trend_to_post, batch_create

    # Workflow data
    input_data = Column(JSON)  # Input parameters
    steps = Column(JSON)  # List of workflow steps with status
    current_step = Column(Integer, default=0)

    # Content reference
    content_id = Column(Integer, ForeignKey("ai_generated_content.id"))

    # Status
    status = Column(SQLEnum(WorkflowStatus), default=WorkflowStatus.PENDING)
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)

    # Results
    output_data = Column(JSON)  # Final results
    performance_metrics = Column(JSON)  # Time taken, success rate, etc.

    # Timestamps
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    content = relationship("AIGeneratedContent", back_populates="workflow_runs")


class ContentCalendar(Base):
    """Model for AI-planned content calendar."""

    __tablename__ = "content_calendar"

    id = Column(Integer, primary_key=True, index=True)
    calendar_id = Column(String(255), unique=True, index=True)

    # Schedule
    scheduled_date = Column(DateTime, nullable=False, index=True)
    scheduled_time = Column(DateTime, nullable=False)
    platform = Column(String(50))  # youtube, instagram, both

    # Content reference
    content_id = Column(Integer, ForeignKey("ai_generated_content.id"))
    trend_id = Column(Integer, ForeignKey("trends.id"))

    # Planning metadata
    ai_reasoning = Column(Text)  # Why this time was chosen
    predicted_engagement = Column(Float)
    confidence_score = Column(Float)

    # Status
    status = Column(String(50), default="planned")  # planned, approved, posted, skipped
    posted_content_id = Column(Integer)  # Reference to posted content

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    content = relationship("AIGeneratedContent", backref="calendar_entries")
    trend = relationship("Trends", backref="calendar_entries")


class TrendPrediction(Base):
    """Model for viral topic predictions."""

    __tablename__ = "trend_predictions"

    id = Column(Integer, primary_key=True, index=True)
    prediction_id = Column(String(255), unique=True, index=True)

    # Prediction data
    topic = Column(String(500), nullable=False)
    category = Column(String(100))
    platform = Column(String(50))

    # Prediction metrics
    viral_score = Column(Float, nullable=False)
    predicted_peak_date = Column(DateTime)
    confidence = Column(Float, default=0.0)
    predicted_engagement = Column(Float)

    # ML model info
    model_version = Column(String(50))
    prediction_features = Column(JSON)

    # Validation
    actual_performance = Column(JSON)  # Actual metrics if trend materialized
    prediction_accuracy = Column(Float)  # How accurate was the prediction

    # Timestamps
    predicted_at = Column(DateTime, default=datetime.utcnow)
    validated_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class ABTestResult(Base):
    """Model for A/B testing results."""

    __tablename__ = "ab_test_results"

    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(String(255), unique=True, index=True)

    # Test configuration
    test_type = Column(String(50))  # thumbnail, title, caption, hashtags
    content_id = Column(Integer, ForeignKey("ai_generated_content.id"))

    # Variants
    variant_a = Column(JSON)  # Original/control
    variant_b = Column(JSON)  # Test variant
    variant_c = Column(JSON)  # Optional third variant

    # Performance data
    variant_a_metrics = Column(JSON)  # views, likes, engagement, etc.
    variant_b_metrics = Column(JSON)
    variant_c_metrics = Column(JSON)

    # Results
    winner = Column(String(10))  # A, B, C, or inconclusive
    improvement_percentage = Column(Float)
    statistical_significance = Column(Float)  # p-value

    # Status
    status = Column(String(50), default="running")  # running, completed, cancelled
    test_duration_days = Column(Integer, default=7)

    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    content = relationship("AIGeneratedContent", back_populates="ab_tests")


class CompetitorAnalysis(Base):
    """Model for competitor content analysis."""

    __tablename__ = "competitor_analysis"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(String(255), unique=True, index=True)

    # Competitor info
    competitor_name = Column(String(200))
    competitor_url = Column(String(1000))
    platform = Column(String(50))

    # Content analysis
    content_url = Column(String(1000))
    content_title = Column(String(500))
    content_category = Column(String(100))

    # Performance metrics
    views = Column(Integer)
    likes = Column(Integer)
    comments = Column(Integer)
    shares = Column(Integer)
    engagement_rate = Column(Float)

    # Analysis insights
    successful_elements = Column(JSON)  # What made it successful
    content_strategy = Column(JSON)  # Extracted strategy
    learnings = Column(Text)  # Key takeaways

    # AI analysis
    ai_insights = Column(JSON)  # AI-generated insights
    similarity_score = Column(Float)  # How similar to our content

    # Timestamps
    analyzed_at = Column(DateTime, default=datetime.utcnow)
    content_published_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class PerformanceMetrics(Base):
    """Enhanced performance metrics model."""

    __tablename__ = "performance_metrics"

    id = Column(Integer, primary_key=True, index=True)
    metric_id = Column(String(255), unique=True, index=True)

    # Content reference
    content_id = Column(Integer, ForeignKey("ai_generated_content.id"))
    post_id = Column(Integer, ForeignKey("posts.id"))

    # Platform
    platform = Column(String(50), nullable=False)

    # Engagement metrics
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    saves = Column(Integer, default=0)  # Instagram saves

    # Calculated metrics
    engagement_rate = Column(Float, default=0.0)
    click_through_rate = Column(Float, default=0.0)
    watch_time = Column(Float, default=0.0)  # For videos
    average_view_duration = Column(Float, default=0.0)

    # Audience metrics
    reach = Column(Integer, default=0)
    impressions = Column(Integer, default=0)
    unique_viewers = Column(Integer, default=0)

    # Revenue metrics (if applicable)
    revenue = Column(Float, default=0.0)
    ad_revenue = Column(Float, default=0.0)

    # Timestamps
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    content = relationship("AIGeneratedContent", backref="performance_metrics")
    post = relationship("Post", backref="performance_metrics")
