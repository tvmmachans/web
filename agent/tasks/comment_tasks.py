"""
Celery tasks for comment automation.
"""

import logging
from agent.celery_app import celery_app
from agent.services.comment_automation import CommentAutomation

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="agent.tasks.comment_tasks.process_comments")
def process_comments(self):
    """
    Process comments for all active posts.
    """
    try:
        logger.info("Starting scheduled comment processing")

        comment_automation = CommentAutomation()

        import asyncio

        asyncio.run(comment_automation._check_and_respond_to_comments())

        logger.info("Completed scheduled comment processing")
        return {"status": "success", "message": "Comment processing completed"}

    except Exception as e:
        logger.error(f"Error in scheduled comment processing: {e}")
        self.retry(countdown=300, max_retries=3)
        return {"status": "error", "message": str(e)}


@celery_app.task(bind=True, name="agent.tasks.comment_tasks.respond_to_post_comments")
def respond_to_post_comments(self, post_id: int):
    """
    Process comments for a specific post.
    """
    try:
        logger.info(f"Processing comments for post {post_id}")

        comment_automation = CommentAutomation()

        # Get post and process comments
        import asyncio

        async for session in comment_automation._get_db_session():
            # This would need to be implemented based on actual database structure
            # For now, just log
            logger.info(f"Would process comments for post {post_id}")
            return {"status": "success", "post_id": post_id}

    except Exception as e:
        logger.error(f"Error processing comments for post {post_id}: {e}")
        return {"status": "error", "message": str(e)}


@celery_app.task(bind=True, name="agent.tasks.comment_tasks.generate_reply")
def generate_reply(self, comment_data: dict, post_data: dict):
    """
    Generate AI reply for a specific comment.
    """
    try:
        logger.info(f"Generating reply for comment {comment_data.get('id')}")

        comment_automation = CommentAutomation()

        # Create mock objects
        class MockPost:
            def __init__(self, data):
                self.id = data.get("id")
                self.title = data.get("title", "")
                self.description = data.get("description", "")
                self.ai_caption = data.get("ai_caption")

        class MockComment:
            def __init__(self, data):
                self.id = data.get("id")
                self.text = data.get("text", "")
                self.author = data.get("author", "")
                self.language = data.get("language", "english")

        post = MockPost(post_data)
        comment = MockComment(comment_data)

        import asyncio

        reply = asyncio.run(
            comment_automation._generate_comment_response(post, comment)
        )

        if reply:
            return {"status": "success", "reply": reply}
        else:
            return {"status": "no_reply", "message": "No reply needed"}

    except Exception as e:
        logger.error(f"Error generating reply: {e}")
        return {"status": "error", "message": str(e)}
