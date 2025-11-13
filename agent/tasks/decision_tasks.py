"""
Celery tasks for decision engine.
"""

import logging
from agent.celery_app import celery_app
from agent.services.decision_engine import DecisionEngine

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="agent.tasks.decision_tasks.make_decision")
def make_decision(self, post_data: dict):
    """
    Make AI-powered decision for a post.
    """
    try:
        logger.info(f"Making decision for post {post_data.get('id')}")

        decision_engine = DecisionEngine()

        # Create a mock post object from data
        class MockPost:
            def __init__(self, data):
                self.id = data.get('id')
                self.title = data.get('title', '')
                self.description = data.get('description', '')
                self.ai_caption = data.get('ai_caption')
                self.duration = data.get('duration')
                self.video_url = data.get('video_url')

        post = MockPost(post_data)

        import asyncio
        decision = asyncio.run(decision_engine.make_decision(post))

        logger.info(f"Decision made for post {post.id}")
        return {"status": "success", "decision": decision}

    except Exception as e:
        logger.error(f"Error making decision: {e}")
        self.retry(countdown=60, max_retries=3)
        return {"status": "error", "message": str(e)}

@celery_app.task(bind=True, name="agent.tasks.decision_tasks.optimize_caption")
def optimize_caption(self, caption: str, decision: dict):
    """
    Optimize caption using AI.
    """
    try:
        logger.info("Optimizing caption")

        decision_engine = DecisionEngine()

        import asyncio
        optimized = asyncio.run(decision_engine.optimize_caption(caption, decision))

        return {"status": "success", "caption": optimized}

    except Exception as e:
        logger.error(f"Error optimizing caption: {e}")
        return {"status": "error", "message": str(e)}

@celery_app.task(bind=True, name="agent.tasks.decision_tasks.suggest_timing")
def suggest_timing(self, post_data: dict, decision: dict):
    """
    Suggest optimal posting time.
    """
    try:
        logger.info(f"Suggesting timing for post {post_data.get('id')}")

        decision_engine = DecisionEngine()

        class MockPost:
            def __init__(self, data):
                self.id = data.get('id')
                self.title = data.get('title', '')

        post = MockPost(post_data)

        import asyncio
        timing = asyncio.run(decision_engine.suggest_timing(post, decision))

        return {"status": "success", "timing": timing.isoformat()}

    except Exception as e:
        logger.error(f"Error suggesting timing: {e}")
        return {"status": "error", "message": str(e)}
