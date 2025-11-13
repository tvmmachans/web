"""
Event Bus - Task messaging system using Redis pub/sub.
Handles inter-service communication and event-driven architecture.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Callable, List, Optional
from dataclasses import dataclass
from datetime import datetime
import redis.asyncio as redis

logger = logging.getLogger(__name__)

@dataclass
class Event:
    """Event data structure."""
    event_type: str
    data: Dict[str, Any]
    timestamp: datetime
    source: str
    event_id: str

class EventBus:
    """Redis-based event bus for inter-service communication."""

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_url = redis_url
        self.redis: Optional[redis.Redis] = None
        self.subscribers: Dict[str, List[Callable]] = {}
        self._running = False
        self._pubsub = None

    async def connect(self):
        """Connect to Redis."""
        try:
            self.redis = redis.from_url(self.redis_url)
            self._pubsub = self.redis.pubsub()
            logger.info("EventBus connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def disconnect(self):
        """Disconnect from Redis."""
        if self._pubsub:
            await self._pubsub.close()
        if self.redis:
            await self.redis.close()
        logger.info("EventBus disconnected from Redis")

    async def publish(self, event_type: str, data: Dict[str, Any],
                     source: str = "orchestrator"):
        """Publish an event to the bus."""
        if not self.redis:
            await self.connect()

        event = Event(
            event_type=event_type,
            data=data,
            timestamp=datetime.utcnow(),
            source=source,
            event_id=f"{event_type}_{int(datetime.utcnow().timestamp() * 1000)}"
        )

        event_data = {
            'event_type': event.event_type,
            'data': event.data,
            'timestamp': event.timestamp.isoformat(),
            'source': event.source,
            'event_id': event.event_id
        }

        try:
            # Publish to Redis channel
            await self.redis.publish(event_type, json.dumps(event_data))

            # Also publish to wildcard channel for catch-all subscribers
            await self.redis.publish('events:all', json.dumps(event_data))

            logger.debug(f"Published event: {event_type}")

        except Exception as e:
            logger.error(f"Failed to publish event {event_type}: {e}")
            raise

    async def subscribe(self, event_type: str, callback: Callable):
        """Subscribe to an event type."""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []

        self.subscribers[event_type].append(callback)
        logger.info(f"Subscribed to event: {event_type}")

    async def unsubscribe(self, event_type: str, callback: Callable):
        """Unsubscribe from an event type."""
        if event_type in self.subscribers:
            try:
                self.subscribers[event_type].remove(callback)
                if not self.subscribers[event_type]:
                    del self.subscribers[event_type]
                logger.info(f"Unsubscribed from event: {event_type}")
            except ValueError:
                logger.warning(f"Callback not found for event: {event_type}")

    async def start_listening(self):
        """Start listening for events."""
        if not self.redis:
            await self.connect()

        self._running = True

        # Subscribe to all event types we have handlers for
        event_types = list(self.subscribers.keys()) + ['events:all']
        await self._pubsub.subscribe(*event_types)

        logger.info("EventBus started listening for events")

        # Start event processing loop
        asyncio.create_task(self._process_events())

    async def stop_listening(self):
        """Stop listening for events."""
        self._running = False
        if self._pubsub:
            await self._pubsub.unsubscribe()
        logger.info("EventBus stopped listening")

    async def _process_events(self):
        """Process incoming events."""
        while self._running:
            try:
                message = await self._pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)

                if message:
                    event_data = json.loads(message['data'])
                    event_type = message['channel'].decode('utf-8')

                    # Create Event object
                    event = Event(
                        event_type=event_data['event_type'],
                        data=event_data['data'],
                        timestamp=datetime.fromisoformat(event_data['timestamp']),
                        source=event_data['source'],
                        event_id=event_data['event_id']
                    )

                    # Notify subscribers
                    await self._notify_subscribers(event_type, event)

            except Exception as e:
                logger.error(f"Error processing event: {e}")
                await asyncio.sleep(1)

    async def _notify_subscribers(self, event_type: str, event: Event):
        """Notify all subscribers of an event."""
        # Notify specific event type subscribers
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                try:
                    await callback(event)
                except Exception as e:
                    logger.error(f"Error in event callback for {event_type}: {e}")

        # Notify catch-all subscribers
        if 'events:all' in self.subscribers and event_type != 'events:all':
            for callback in self.subscribers['events:all']:
                try:
                    await callback(event)
                except Exception as e:
                    logger.error(f"Error in catch-all event callback: {e}")

    # High-level event handlers for pipeline orchestration

    async def on_pipeline_started(self, callback: Callable):
        """Subscribe to pipeline started events."""
        await self.subscribe('pipeline.started', callback)

    async def on_pipeline_state_changed(self, callback: Callable):
        """Subscribe to pipeline state change events."""
        await self.subscribe('pipeline.state_changed', callback)

    async def on_pipeline_completed(self, callback: Callable):
        """Subscribe to pipeline completed events."""
        await self.subscribe('pipeline.completed', callback)

    async def on_pipeline_failed(self, callback: Callable):
        """Subscribe to pipeline failed events."""
        await self.subscribe('pipeline.failed', callback)

    # Service integration events

    async def on_video_uploaded(self, callback: Callable):
        """Subscribe to video upload events."""
        await self.subscribe('video.uploaded', callback)

    async def on_caption_generated(self, callback: Callable):
        """Subscribe to caption generation events."""
        await self.subscribe('caption.generated', callback)

    async def on_post_scheduled(self, callback: Callable):
        """Subscribe to post scheduling events."""
        await self.subscribe('post.scheduled', callback)

    async def on_post_published(self, callback: Callable):
        """Subscribe to post publishing events."""
        await self.subscribe('post.published', callback)

    async def on_analytics_collected(self, callback: Callable):
        """Subscribe to analytics collection events."""
        await self.subscribe('analytics.collected', callback)

    # System events

    async def on_health_check(self, callback: Callable):
        """Subscribe to health check events."""
        await self.subscribe('system.health_check', callback)

    async def on_service_down(self, callback: Callable):
        """Subscribe to service down events."""
        await self.subscribe('system.service_down', callback)

    async def on_service_recovered(self, callback: Callable):
        """Subscribe to service recovery events."""
        await self.subscribe('system.service_recovered', callback)

    # Utility methods

    async def publish_service_event(self, service_name: str, event_type: str, data: Dict[str, Any]):
        """Publish a service-specific event."""
        await self.publish(f"service.{service_name}.{event_type}", data, service_name)

    async def publish_system_event(self, event_type: str, data: Dict[str, Any]):
        """Publish a system event."""
        await self.publish(f"system.{event_type}", data, "system")

    async def get_event_history(self, event_type: str, limit: int = 100) -> List[Event]:
        """Get recent events of a specific type from Redis."""
        if not self.redis:
            return []

        try:
            # This would require storing events in Redis streams or lists
            # For now, return empty list as this is a simplified implementation
            return []
        except Exception as e:
            logger.error(f"Failed to get event history: {e}")
            return []

    async def clear_event_history(self, event_type: str):
        """Clear event history for a specific type."""
        # Implementation would clear Redis streams/lists
        pass
