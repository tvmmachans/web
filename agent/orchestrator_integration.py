"""
Orchestrator Event Integration for Agent Service
Handles event publishing and subscription for orchestrator communication.
"""

import asyncio
import logging
import redis.asyncio as redis
from typing import Dict, Any, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class OrchestratorEventIntegration:
    """Handles event integration between agent and orchestrator services."""

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_url = redis_url
        self.redis: Optional[redis.Redis] = None
        self.pubsub = None
        self.running = False

        # Event handlers for orchestrator events
        self.event_handlers = {
            "pipeline.started": self._handle_pipeline_started,
            "pipeline.completed": self._handle_pipeline_completed,
            "pipeline.failed": self._handle_pipeline_failed,
            "pipeline.analyzed": self._handle_analytics_available,
            "backend.post_published": self._handle_post_published,
            "backend.analytics_collected": self._handle_analytics_collected,
        }

    async def start(self):
        """Start the event integration."""
        try:
            self.redis = redis.from_url(self.redis_url)
            self.pubsub = self.redis.pubsub()
            self.running = True

            # Subscribe to orchestrator and backend events
            event_types = list(self.event_handlers.keys()) + ["events:all"]
            await self.pubsub.subscribe(*event_types)

            logger.info("Agent orchestrator event integration started")

            # Start event processing
            asyncio.create_task(self._process_events())

        except Exception as e:
            logger.error(f"Failed to start agent orchestrator event integration: {e}")
            raise

    async def stop(self):
        """Stop the event integration."""
        self.running = False
        if self.pubsub:
            await self.pubsub.unsubscribe()
        if self.redis:
            await self.redis.close()
        logger.info("Agent orchestrator event integration stopped")

    async def publish_event(
        self, event_type: str, data: Dict[str, Any], source: str = "agent"
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
            logger.debug(f"Published agent event: {event_type}")
        except Exception as e:
            logger.error(f"Failed to publish agent event {event_type}: {e}")

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
                logger.error(f"Error processing orchestrator event in agent: {e}")
                await asyncio.sleep(1)

    # Event handlers for orchestrator events

    async def _handle_pipeline_started(self, event_data: Dict[str, Any]):
        """Handle pipeline started event."""
        task_id = event_data.get("task_id")
        user_id = event_data.get("user_id")
        logger.info(
            f"Agent notified: Pipeline started for task {task_id}, user {user_id}"
        )

        # Agent could prepare monitoring for this pipeline
        await self._prepare_pipeline_monitoring(task_id, user_id)

    async def _handle_pipeline_completed(self, event_data: Dict[str, Any]):
        """Handle pipeline completed event."""
        task_id = event_data.get("task_id")
        completion_time = event_data.get("completion_time")
        analytics = event_data.get("analytics")

        logger.info(
            f"Agent notified: Pipeline {task_id} completed in {completion_time:.2f}s"
        )

        # Store analytics for agent learning
        if analytics:
            await self._store_pipeline_analytics(task_id, analytics)

        # Publish agent completion event
        await self.publish_event(
            "agent.pipeline_completed",
            {
                "task_id": task_id,
                "completion_time": completion_time,
                "analytics_processed": bool(analytics),
            },
        )

    async def _handle_pipeline_failed(self, event_data: Dict[str, Any]):
        """Handle pipeline failed event."""
        task_id = event_data.get("task_id")
        error = event_data.get("error")
        logger.error(f"Agent notified: Pipeline {task_id} failed: {error}")

        # Agent could trigger error analysis or recovery
        await self._handle_pipeline_error(task_id, error)

    async def _handle_analytics_available(self, event_data: Dict[str, Any]):
        """Handle analytics available event."""
        task_id = event_data.get("task_id")
        analytics = event_data.get("analytics")
        logger.info(f"Agent notified: Analytics available for task {task_id}")

        # Process analytics for agent learning
        await self._process_analytics_for_learning(task_id, analytics)

    async def _handle_post_published(self, event_data: Dict[str, Any]):
        """Handle post published event from backend."""
        task_id = event_data.get("task_id")
        post_id = event_data.get("post_id")
        platforms = event_data.get("platforms")
        logger.info(f"Agent notified: Post published for task {task_id} on {platforms}")

        # Agent starts monitoring this post
        await self._start_post_monitoring(post_id, platforms)

    async def _handle_analytics_collected(self, event_data: Dict[str, Any]):
        """Handle analytics collected event from backend."""
        post_id = event_data.get("post_id")
        analytics = event_data.get("analytics")
        logger.info(f"Agent notified: Analytics collected for post {post_id}")

        # Agent processes analytics for optimization
        await self._process_performance_analytics(post_id, analytics)

    # Helper methods

    async def _prepare_pipeline_monitoring(self, task_id: str, user_id: str):
        """Prepare monitoring for a new pipeline."""
        # Implementation would set up monitoring hooks
        logger.debug(f"Preparing monitoring for pipeline {task_id}")

    async def _store_pipeline_analytics(self, task_id: str, analytics: Dict[str, Any]):
        """Store pipeline analytics for agent learning."""
        # Implementation would store in agent's learning database
        logger.debug(f"Storing pipeline analytics for task {task_id}")

    async def _handle_pipeline_error(self, task_id: str, error: str):
        """Handle pipeline error for agent analysis."""
        # Implementation would analyze error and potentially trigger recovery
        logger.debug(f"Handling pipeline error for task {task_id}: {error}")

    async def _process_analytics_for_learning(
        self, task_id: str, analytics: Dict[str, Any]
    ):
        """Process analytics data for machine learning."""
        # Implementation would update agent's ML models
        logger.debug(f"Processing analytics for learning: task {task_id}")

    async def _start_post_monitoring(self, post_id: str, platforms: list):
        """Start monitoring a published post."""
        # Implementation would set up monitoring tasks
        logger.debug(f"Starting monitoring for post {post_id} on {platforms}")

    async def _process_performance_analytics(
        self, post_id: str, analytics: Dict[str, Any]
    ):
        """Process performance analytics for optimization."""
        # Implementation would analyze performance and update strategies
        logger.debug(f"Processing performance analytics for post {post_id}")

    async def health_check(self) -> Dict[str, Any]:
        """Health check for event integration."""
        return {
            "status": "healthy" if self.redis and self.running else "unhealthy",
            "redis_connected": self.redis is not None,
            "event_processing": self.running,
        }

    # Public methods for agent services to publish events

    async def publish_monitoring_alert(self, alert_type: str, data: Dict[str, Any]):
        """Publish monitoring alert event."""
        await self.publish_event(
            "agent.monitoring_alert", {"alert_type": alert_type, "data": data}
        )

    async def publish_comment_automation(
        self, post_id: str, comment_data: Dict[str, Any]
    ):
        """Publish comment automation event."""
        await self.publish_event(
            "agent.comment_automated",
            {"post_id": post_id, "comment_data": comment_data},
        )

    async def publish_report_generated(
        self, report_type: str, report_data: Dict[str, Any]
    ):
        """Publish report generation event."""
        await self.publish_event(
            "agent.report_generated",
            {"report_type": report_type, "report_data": report_data},
        )

    async def publish_learning_update(
        self, model_type: str, update_data: Dict[str, Any]
    ):
        """Publish learning model update event."""
        await self.publish_event(
            "agent.learning_update",
            {"model_type": model_type, "update_data": update_data},
        )
