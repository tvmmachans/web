import os
from typing import List

# Agent Configuration
AGENT_NAME = "AI Social Media Manager Agent"
AGENT_VERSION = "1.0.0"

# Monitoring Settings
MONITORING_INTERVAL_HOURS = int(os.getenv("MONITORING_INTERVAL_HOURS", "2"))
MAX_POSTS_PER_CHECK = int(os.getenv("MAX_POSTS_PER_CHECK", "10"))

# AI Decision Engine Settings
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")
MAX_TOKENS_DECISION = int(os.getenv("MAX_TOKENS_DECISION", "500"))
TEMPERATURE_DECISION = float(os.getenv("TEMPERATURE_DECISION", "0.7"))

# Content Repurposing Settings
CLIP_DURATION_SECONDS = int(os.getenv("CLIP_DURATION_SECONDS", "60"))
CLIP_START_OFFSET_SECONDS = int(os.getenv("CLIP_START_OFFSET_SECONDS", "30"))

# Comment Automation Settings
COMMENT_CHECK_INTERVAL_MINUTES = int(os.getenv("COMMENT_CHECK_INTERVAL_MINUTES", "30"))
MAX_COMMENTS_PER_POST = int(os.getenv("MAX_COMMENTS_PER_POST", "5"))
MALAYALAM_LANGUAGE_CODE = "ml"

# Report Generation Settings
REPORT_GENERATION_DAY = os.getenv("REPORT_GENERATION_DAY", "monday")  # monday, tuesday, etc.
REPORT_GENERATION_HOUR = int(os.getenv("REPORT_GENERATION_HOUR", "9"))  # 9 AM

# Notification Settings
EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "false").lower() == "true"
WHATSAPP_ENABLED = os.getenv("WHATSAPP_ENABLED", "false").lower() == "true"
EMAIL_RECIPIENT = os.getenv("EMAIL_RECIPIENT")
WHATSAPP_NUMBER = os.getenv("WHATSAPP_NUMBER")

# Database Settings (reuse from backend)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost/social_media_manager")

# Backend API Settings (for agent-backend communication)
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")
BACKEND_API_KEY = os.getenv("BACKEND_API_KEY", "")

# Celery Settings
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
CELERY_TIMEZONE = os.getenv("CELERY_TIMEZONE", "UTC")

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "agent.log")

# Platform Settings
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
INSTAGRAM_ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID")

# Performance Settings
MAX_CONCURRENT_TASKS = int(os.getenv("MAX_CONCURRENT_TASKS", "3"))
TIMEOUT_SECONDS = int(os.getenv("TIMEOUT_SECONDS", "300"))

# Analytics Settings
MIN_ENGAGEMENT_RATE_THRESHOLD = float(os.getenv("MIN_ENGAGEMENT_RATE_THRESHOLD", "0.02"))
ANALYTICS_RETENTION_DAYS = int(os.getenv("ANALYTICS_RETENTION_DAYS", "90"))

# Best posting times (can be learned from analytics)
DEFAULT_BEST_POSTING_HOURS = [9, 12, 18, 20]  # 9 AM, 12 PM, 6 PM, 8 PM

# Content categories for AI decisions
CONTENT_CATEGORIES = [
    "educational", "entertainment", "lifestyle", "technology",
    "food", "travel", "comedy", "music", "sports", "news"
]

# Malayalam content keywords for better categorization
MALAYALAM_KEYWORDS = [
    "മലയാളം", "കേരളം", "കോഴിക്കോട്", "തിരുവനന്തപുരം", "എറണാകുളം",
    "കോമഡി", "സിനിമ", "ഗാനം", "നൃത്തം", "സംഗീതം"
]
