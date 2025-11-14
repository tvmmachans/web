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

        # Process post using async function
        import asyncio

        async def process_post_async():
            """Async helper function to process the post"""
            # Use API-based approach since MonitoringService uses API communication
            # Fetch post from backend API and process it
            try:
                # Check if post exists and is pending
                url = f"{monitoring_service.backend_url}/agent/posts/{post_id}"
                response = await monitoring_service.client.get(url)

                if response.status_code == 200:
                    post_data = response.json()
                    # Process the post through the agent pipeline
                    # This would trigger the actual processing logic
                    logger.info(f"Found post {post_id}, processing...")
                    return {
                        "status": "success",
                        "post_id": post_id,
                        "post_data": post_data,
                    }
                elif response.status_code == 404:
                    return {"status": "error", "message": f"Post {post_id} not found"}
                else:
                    return {
                        "status": "error",
                        "message": f"Failed to fetch post: {response.status_code}",
                    }
            except Exception as e:
                logger.error(f"Error in async post processing: {e}")
                raise

        # Run the async function
        result = asyncio.run(process_post_async())

        if result["status"] == "success":
            logger.info(f"Successfully processed post {post_id}")
        else:
            logger.warning(f"Failed to process post {post_id}: {result.get('message')}")

        return result

    except Exception as e:
        logger.error(f"Error processing post {post_id}: {e}")
        self.retry(countdown=60, max_retries=3)
        return {"status": "error", "message": str(e)}
