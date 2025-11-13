"""
Celery tasks for monitoring service.
"""

import logging
from agent.celery_app import celery_app
from agent.core.monitoring import MonitoringService

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="agent.tasks.monitoring_tasks.check_pending_posts")
def check_pending_posts(self):
    """
    Check for pending posts and process them.
    """
    try:
        logger.info("Starting scheduled check for pending posts")

        monitoring_service = MonitoringService()

        # Run one monitoring cycle
        import asyncio
        asyncio.run(monitoring_service._check_pending_posts())

        logger.info("Completed scheduled check for pending posts")
        return {"status": "success", "message": "Monitoring check completed"}

    except Exception as e:
        logger.error(f"Error in scheduled monitoring check: {e}")
        self.retry(countdown=300, max_retries=3)  # Retry after 5 minutes
        return {"status": "error", "message": str(e)}

@celery_app.task(bind=True, name="agent.tasks.monitoring_tasks.process_single_post")
def process_single_post(self, post_id: int):
    """
    Process a single post through the agent pipeline.
    """
    try:
        logger.info(f"Processing single post {post_id}")

        monitoring_service = MonitoringService()

        # Get post and process it
        import asyncio
        async for session in monitoring_service._get_db_session():
            post = await session.get("Post", post_id)  # Adjust based on actual model
            if post:
                await monitoring_service._process_post(session, post)
                logger.info(f"Successfully processed post {post_id}")
                return {"status": "success", "post_id": post_id}
            else:
                return {"status": "error", "message": f"Post {post_id} not found"}

    except Exception as e:
        logger.error(f"Error processing post {post_id}: {e}")
        self.retry(countdown=60, max_retries=3)
        return {"status": "error", "message": str(e)}
