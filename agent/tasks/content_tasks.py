"""
Celery tasks for content repurposing.
"""

import logging
from agent.celery_app import celery_app
from agent.services.content_repurposer import ContentRepurposer

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="agent.tasks.content_tasks.repurpose_content")
def repurpose_content(self, post_data: dict, decision: dict):
    """
    Repurpose content for different platforms.
    """
    try:
        logger.info(f"Repurposing content for post {post_data.get('id')}")

        repurposer = ContentRepurposer()

        # Create mock post object
        class MockPost:
            def __init__(self, data):
                self.id = data.get("id")
                self.title = data.get("title", "")
                self.video_url = data.get("video_url")
                self.duration = data.get("duration")

        post = MockPost(post_data)

        import asyncio

        result = asyncio.run(repurposer.repurpose_content(post, decision))

        if result:
            logger.info(f"Content repurposed for post {post.id}")
            return {"status": "success", "repurposed": result}
        else:
            return {"status": "no_action", "message": "No repurposing needed"}

    except Exception as e:
        logger.error(f"Error repurposing content: {e}")
        self.retry(countdown=300, max_retries=3)
        return {"status": "error", "message": str(e)}


@celery_app.task(bind=True, name="agent.tasks.content_tasks.create_instagram_clip")
def create_instagram_clip(self, post_data: dict):
    """
    Create Instagram clip from YouTube video.
    """
    try:
        logger.info(f"Creating Instagram clip for post {post_data.get('id')}")

        repurposer = ContentRepurposer()

        class MockPost:
            def __init__(self, data):
                self.id = data.get("id")
                self.title = data.get("title", "")
                self.video_url = data.get("video_url")
                self.duration = data.get("duration")

        post = MockPost(post_data)

        import asyncio

        result = asyncio.run(repurposer._create_instagram_clip(post))

        if result:
            return {"status": "success", "clip": result}
        else:
            return {"status": "error", "message": "Failed to create clip"}

    except Exception as e:
        logger.error(f"Error creating Instagram clip: {e}")
        return {"status": "error", "message": str(e)}


@celery_app.task(bind=True, name="agent.tasks.content_tasks.optimize_for_platform")
def optimize_for_platform(self, post_data: dict, platform: str):
    """
    Optimize content for specific platform.
    """
    try:
        logger.info(f"Optimizing content for {platform}, post {post_data.get('id')}")

        repurposer = ContentRepurposer()

        class MockPost:
            def __init__(self, data):
                self.id = data.get("id")
                self.title = data.get("title", "")
                self.video_url = data.get("video_url")
                self.duration = data.get("duration")
                self.ai_caption = post_data.get("ai_caption")

        post = MockPost(post_data)

        import asyncio

        if platform == "instagram":
            result = asyncio.run(repurposer._create_instagram_clip(post))
        elif platform == "youtube":
            result = asyncio.run(repurposer._optimize_for_youtube(post))
        else:
            result = None

        if result:
            return {"status": "success", "optimized": result}
        else:
            return {"status": "error", "message": f"Failed to optimize for {platform}"}

    except Exception as e:
        logger.error(f"Error optimizing for {platform}: {e}")
        return {"status": "error", "message": str(e)}
