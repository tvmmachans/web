"""
Configuration settings for AI Social Manager Orchestrator.
"""

import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """Application settings."""

    # App settings
    APP_NAME: str = "AI Social Manager Orchestrator"
    VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    PORT: int = Field(default=8001, env="PORT")
    WEBSOCKET_PORT: int = Field(default=8003, env="WEBSOCKET_PORT")

    # Security
    JWT_SECRET_KEY: str = Field(default="your-secret-key-here", env="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")

    # CORS
    CORS_ORIGINS: List[str] = Field(default=["http://localhost:3000", "http://frontend:3000"], env="CORS_ORIGINS")

    # Database
    DATABASE_URL: str = Field(default="postgresql://user:password@localhost:5432/orchestrator", env="DATABASE_URL")

    # Redis/Celery
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/0", env="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/0", env="CELERY_RESULT_BACKEND")

    # External APIs
    YOUTUBE_API_KEY: str = Field(default="your-youtube-api-key", env="YOUTUBE_API_KEY")
    INSTAGRAM_ACCESS_TOKEN: str = Field(default="your-instagram-token", env="INSTAGRAM_ACCESS_TOKEN")
    TWITTER_BEARER_TOKEN: str = Field(default="your-twitter-token", env="TWITTER_BEARER_TOKEN")
    OPENAI_API_KEY: str = Field(default="your-openai-key", env="OPENAI_API_KEY")

    # Storage
    MINIO_ENDPOINT: str = Field(default="localhost:9000", env="MINIO_ENDPOINT")
    MINIO_ACCESS_KEY: str = Field(default="minioadmin", env="MINIO_ACCESS_KEY")
    MINIO_SECRET_KEY: str = Field(default="minioadmin", env="MINIO_SECRET_KEY")
    MINIO_BUCKET: str = Field(default="orchestrator-media", env="MINIO_BUCKET")

    # Service URLs
    BACKEND_BASE_URL: str = Field(default="http://backend:8000", env="BACKEND_BASE_URL")
    VOICE_ENGINE_URL: str = Field(default="http://voice-engine:8002", env="VOICE_ENGINE_URL")
    AGENT_BASE_URL: str = Field(default="http://agent:8001", env="AGENT_BASE_URL")

    # ML settings
    MODEL_PATH: str = Field(default="./models/engagement_predictor.pkl", env="MODEL_PATH")
    EMBEDDINGS_MODEL: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", env="EMBEDDINGS_MODEL")

    # Malayalam keywords for trend discovery
    MALAYALAM_KEYWORDS: List[str] = [
        "malayalam", "കേരളം", "കേരള", "മലയാളം", "ദക്ഷിണേന്ത്യൻ",
        "south indian", "kerala", "god's own country", "mallu"
    ]

    # Orchestration settings
    ENABLE_AUTO_POST: bool = Field(default=False, env="ENABLE_AUTO_POST")
    CONTENT_FILTER_ENABLED: bool = Field(default=True, env="CONTENT_FILTER_ENABLED")
    MAX_CONCURRENT_PIPELINES: int = Field(default=10, env="MAX_CONCURRENT_PIPELINES")
    PIPELINE_TIMEOUT_MINUTES: int = Field(default=30, env="PIPELINE_TIMEOUT_MINUTES")

    # Caching settings
    CACHE_DEFAULT_TTL: int = Field(default=3600, env="CACHE_DEFAULT_TTL")  # 1 hour
    CACHE_CAPTION_TTL: int = Field(default=1800, env="CACHE_CAPTION_TTL")  # 30 minutes
    CACHE_ANALYTICS_TTL: int = Field(default=7200, env="CACHE_ANALYTICS_TTL")  # 2 hours

    # Retry settings
    RETRY_MAX_ATTEMPTS: int = Field(default=3, env="RETRY_MAX_ATTEMPTS")
    RETRY_INITIAL_DELAY: float = Field(default=1.0, env="RETRY_INITIAL_DELAY")
    RETRY_MAX_DELAY: float = Field(default=300.0, env="RETRY_MAX_DELAY")
    RETRY_BACKOFF_MULTIPLIER: float = Field(default=2.0, env="RETRY_BACKOFF_MULTIPLIER")

    # Health monitoring
    HEALTH_CHECK_INTERVAL: int = Field(default=300, env="HEALTH_CHECK_INTERVAL")  # 5 minutes
    HEALTH_RESPONSE_TIMEOUT: float = Field(default=5.0, env="HEALTH_RESPONSE_TIMEOUT")
    HEALTH_MAX_CONSECUTIVE_FAILURES: int = Field(default=3, env="HEALTH_MAX_CONSECUTIVE_FAILURES")

    # Resource thresholds
    CPU_CRITICAL_THRESHOLD: float = Field(default=90.0, env="CPU_CRITICAL_THRESHOLD")
    CPU_DEGRADED_THRESHOLD: float = Field(default=70.0, env="CPU_DEGRADED_THRESHOLD")
    MEMORY_CRITICAL_THRESHOLD: float = Field(default=90.0, env="MEMORY_CRITICAL_THRESHOLD")
    MEMORY_DEGRADED_THRESHOLD: float = Field(default=80.0, env="MEMORY_DEGRADED_THRESHOLD")
    DISK_CRITICAL_THRESHOLD: float = Field(default=95.0, env="DISK_CRITICAL_THRESHOLD")
    DISK_DEGRADED_THRESHOLD: float = Field(default=85.0, env="DISK_DEGRADED_THRESHOLD")

    # Scheduling
    DISCOVERY_INTERVAL_MINUTES: int = Field(default=30, env="DISCOVERY_INTERVAL_MINUTES")
    RETRAIN_INTERVAL_HOURS: int = Field(default=24, env="RETRAIN_INTERVAL_HOURS")

    class Config:
        env_file = ".env"
        case_sensitive = True

# Global settings instance
settings = Settings()
