"""
Orchestrator Event Integration for Backend Service
Handles event publishing and subscription for orchestrator communication.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class OrchestratorEventIntegration:
    """Handles event integration between backend and orchestrator services."""

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_url = redis_url
        self.redis: Optional[redis.Redis] = None
        self.pubsub = None
        self.running = False

        # Event handlers for orchestrator events
        self.event_handlers = {
            "pipeline.started": self._handle_pipeline_started,
            "pipeline.state_changed": self._handle_pipeline_state_changed,
            "pipeline.completed": self._handle_pipeline_completed,
            "pipeline.failed": self._handle_pipeline_failed,
            "pipeline.upload_completed": self._handle_upload_completed,
            "pipeline.caption_generated": self._handle_caption_generated,
            "pipeline.scheduled": self._handle_scheduled,
            "pipeline.posted": self._handle_posted,
            "pipeline.analyzed": self._handle_analyzed,
        }

    async def start(self):
        """Start the event integration."""
        try:
            self.redis = redis.from_url(self.redis_url)
            self.pubsub = self.redis.pubsub()
            self.running = True

            # Subscribe to orchestrator events
            event_types = list(self.event_handlers.keys()) + ["events:all"]
            await self.pubsub.subscribe(*event_types)

            logger.info("Backend orchestrator event integration started")

            # Start event processing
            asyncio.create_task(self._process_events())

        except Exception as e:
            logger.error(f"Failed to start orchestrator event integration: {e}")
            raise

    async def stop(self):
        """Stop the event integration."""
        self.running = False
        if self.pubsub:
            await self.pubsub.unsubscribe()
        if self.redis:
            await self.redis.close()
        logger.info("Backend orchestrator event integration stopped")

    async def publish_event(
        self, event_type: str, data: Dict[str, Any], source: str = "backend"
    ):
        """Publish an event to the orchestrator."""
        if not self.redis:
            await self.start()

        event = {
            "event_type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
            "source": source,
            "event_id": f"{event_type}_{int(datetime.utcnow().timestamp() * 1000)}",
        }

        try:
            await self.redis.publish(event_type, json.dumps(event))
            await self.redis.publish("events:all", json.dumps(event))
            logger.debug(f"Published backend event: {event_type}")
        except Exception as e:
            logger.error(f"Failed to publish event {event_type}: {e}")

    async def _process_events(self):
        """Process incoming orchestrator events."""
        while self.running:
            try:
                message = await self.pubsub.get_message(
                    ignore_subscribe_messages=True, timeout=1.0
                )

                if message:
                    event_data = json.loads(message["data"])
                    event_type = message["channel"].decode("utf-8")

                    # Handle the event
                    if event_type in self.event_handlers:
                        await self.event_handlers[event_type](event_data)

            except Exception as e:
                logger.error(f"Error processing orchestrator event: {e}")
                await asyncio.sleep(1)

    # Event handlers for orchestrator events

    async def _handle_pipeline_started(self, event_data: Dict[str, Any]):
        """Handle pipeline started event."""
        logger.info(f"Pipeline started: {event_data.get('task_id')}")
        # Could trigger backend analytics initialization or monitoring

    async def _handle_pipeline_state_changed(self, event_data: Dict[str, Any]):
        """Handle pipeline state change event."""
        task_id = event_data.get("task_id")
        from_state = event_data.get("from_state")
        to_state = event_data.get("to_state")
        logger.info(f"Pipeline {task_id} state changed: {from_state} -> {to_state}")

    async def _handle_pipeline_completed(self, event_data: Dict[str, Any]):
        """Handle pipeline completed event."""
        task_id = event_data.get("task_id")
        completion_time = event_data.get("completion_time")
        logger.info(f"Pipeline {task_id} completed in {completion_time:.2f}s")

        # Publish backend analytics event
        await self.publish_event(
            "backend.pipeline_completed",
            {
                "task_id": task_id,
                "completion_time": completion_time,
                "analytics": event_data.get("analytics"),
            },
        )

    async def _handle_pipeline_failed(self, event_data: Dict[str, Any]):
        """Handle pipeline failed event."""
        task_id = event_data.get("task_id")
        error = event_data.get("error")
        logger.error(f"Pipeline {task_id} failed: {error}")

        # Publish backend error event
        await self.publish_event(
            "backend.pipeline_failed",
            {
                "task_id": task_id,
                "error": error,
                "last_state": event_data.get("last_state"),
            },
        )

    async def _handle_upload_completed(self, event_data: Dict[str, Any]):
        """Handle upload completed event."""
        task_id = event_data.get("task_id")
        video_path = event_data.get("video_path")
        logger.info(f"Upload completed for task {task_id}: {video_path}")

    async def _handle_caption_generated(self, event_data: Dict[str, Any]):
        """Handle caption generated event."""
        task_id = event_data.get("task_id")
        caption = event_data.get("caption")
        hashtags = event_data.get("hashtags")
        logger.info(f"Caption generated for task {task_id}")

        # Store caption data for analytics
        await self._store_caption_analytics(task_id, caption, hashtags)

    async def _handle_scheduled(self, event_data: Dict[str, Any]):
        """Handle scheduling completed event."""
        task_id = event_data.get("task_id")
        scheduled_time = event_data.get("scheduled_time")
        logger.info(f"Post scheduled for task {task_id} at {scheduled_time}")

    async def _handle_posted(self, event_data: Dict[str, Any]):
        """Handle posting completed event."""
        task_id = event_data.get("task_id")
        post_id = event_data.get("post_id")
        platforms = event_data.get("platforms")
        logger.info(f"Post published for task {task_id} on platforms: {platforms}")

        # Publish backend posting event for analytics
        await self.publish_event(
            "backend.post_published",
            {"task_id": task_id, "post_id": post_id, "platforms": platforms},
        )

    async def _handle_analyzed(self, event_data: Dict[str, Any]):
        """Handle analysis completed event."""
        task_id = event_data.get("task_id")
        analytics = event_data.get("analytics")
        logger.info(f"Analysis completed for task {task_id}")

        # Store analytics data
        await self._store_performance_analytics(task_id, analytics)

    # Helper methods

    async def _store_caption_analytics(
        self, task_id: str, caption: str, hashtags: list
    ):
        """Store caption analytics data."""
        # Implementation would store in database for learning
        logger.debug(f"Storing caption analytics for task {task_id}")

    async def _store_performance_analytics(
        self, task_id: str, analytics: Dict[str, Any]
    ):
        """Store performance analytics data."""
        # Implementation would store in database for learning
        logger.debug(f"Storing performance analytics for task {task_id}")

    async def health_check(self) -> Dict[str, Any]:
        """Health check for event integration."""
        return {
            "status": "healthy" if self.redis and self.running else "unhealthy",
            "redis_connected": self.redis is not None,
            "event_processing": self.running,
        }

    # Public methods for backend services to publish events

    async def publish_video_upload(
        self, video_id: str, user_id: str, metadata: Dict[str, Any]
    ):
        """Publish video upload event."""
        await self.publish_event(
            "backend.video_uploaded",
            {"video_id": video_id, "user_id": user_id, "metadata": metadata},
        )

    async def publish_caption_generated(
        self, video_id: str, caption: str, hashtags: list
    ):
        """Publish caption generation event."""
        await self.publish_event(
            "backend.caption_generated",
            {"video_id": video_id, "caption": caption, "hashtags": hashtags},
        )

    async def publish_post_scheduled(
        self, post_id: str, scheduled_time: str, platforms: list
    ):
        """Publish post scheduling event."""
        await self.publish_event(
            "backend.post_scheduled",
            {
                "post_id": post_id,
                "scheduled_time": scheduled_time,
                "platforms": platforms,
            },
        )

    async def publish_analytics_collected(
        self, post_id: str, analytics: Dict[str, Any]
    ):
        """Publish analytics collection event."""
        await self.publish_event(
            "backend.analytics_collected", {"post_id": post_id, "analytics": analytics}
        )
