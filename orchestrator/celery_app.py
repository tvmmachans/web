"""
Celery configuration for AI Trend Orchestrator.
"""

import os
from celery import Celery
from orchestrator.config.settings import settings

# Create Celery app
celery_app = Celery(
    "orchestrator",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["orchestrator.tasks"]
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Worker settings
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=50,

    # Beat settings (scheduler)
    beat_schedule={
        "discover-trends": {
            "task": "orchestrator.tasks.discovery.discover_trends_task",
            "schedule": settings.DISCOVERY_INTERVAL_MINUTES * 60,  # Convert to seconds
        },
        "retrain-model": {
            "task": "orchestrator.tasks.models.retrain_model_task",
            "schedule": settings.RETRAIN_INTERVAL_HOURS * 3600,  # Convert to seconds
        },
        "generate-blueprints": {
            "task": "orchestrator.tasks.generation.generate_blueprints_task",
            "schedule": 1800,  # Every 30 minutes
        },
        "auto-schedule": {
            "task": "orchestrator.tasks.scheduling.auto_schedule_task",
            "schedule": 3600,  # Every hour
        },
    },
)

# Import tasks to register them
try:
    from orchestrator.tasks import discovery, generation, models, scheduling
except ImportError:
    # Tasks will be imported when available
    pass
