"""
Celery configuration for the AI Social Media Agent.
Provides background task scheduling and execution.
"""

from celery import Celery
from agent.config.settings import (
    CELERY_BROKER_URL,
    CELERY_RESULT_BACKEND,
    CELERY_TIMEZONE,
)

# Create Celery app
celery_app = Celery(
    "ai_social_media_agent",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    timezone=CELERY_TIMEZONE,
    include=[
        "agent.tasks.monitoring_tasks",
        "agent.tasks.decision_tasks",
        "agent.tasks.content_tasks",
        "agent.tasks.comment_tasks",
        "agent.tasks.report_tasks",
    ],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone=CELERY_TIMEZONE,
    enable_utc=True,
    task_routes={
        "agent.tasks.monitoring_tasks.*": {"queue": "monitoring"},
        "agent.tasks.decision_tasks.*": {"queue": "decision"},
        "agent.tasks.content_tasks.*": {"queue": "content"},
        "agent.tasks.comment_tasks.*": {"queue": "comment"},
        "agent.tasks.report_tasks.*": {"queue": "report"},
    },
    task_default_queue="default",
    task_default_exchange="default",
    task_default_routing_key="default",
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_disable_rate_limits=False,
    beat_schedule={
        "check-pending-posts": {
            "task": "agent.tasks.monitoring_tasks.check_pending_posts",
            "schedule": 7200.0,  # Every 2 hours
        },
        "process-comments": {
            "task": "agent.tasks.comment_tasks.process_comments",
            "schedule": 1800.0,  # Every 30 minutes
        },
        "generate-weekly-report": {
            "task": "agent.tasks.report_tasks.generate_weekly_report",
            "schedule": 604800.0,  # Every 7 days (weekly)
        },
    },
)

if __name__ == "__main__":
    celery_app.start()
