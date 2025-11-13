"""
AI Pipeline Orchestrator - Main AI flow controller with workflow states.
Manages the complete AI pipeline: UPLOAD → CAPTION → SCHEDULE → POST → ANALYZE
"""

import asyncio
import logging
from enum import Enum
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

from orchestrator.event_bus import EventBus
from orchestrator.retry_manager import RetryManager
from orchestrator.cache_manager import CacheManager
from orchestrator.health_monitor import HealthMonitor

logger = logging.getLogger(__name__)

class PipelineState(Enum):
    """Pipeline workflow states."""
    UPLOAD = "upload"
    CAPTION = "caption"
    SCHEDULE = "schedule"
    POST = "post"
    ANALYZE = "analyze"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class PipelineContext:
    """Context data for pipeline execution."""
    task_id: str
    user_id: str
    video_path: Optional[str] = None
    caption: Optional[str] = None
    hashtags: Optional[list] = None
    scheduled_time: Optional[datetime] = None
    post_id: Optional[str] = None
    analytics: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = None
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(datetime.UTC)
        if self.updated_at is None:
            self.updated_at = datetime.now(datetime.UTC)
        if self.metadata is None:
            self.metadata = {}

class AIPipeline:
    """Main AI pipeline orchestrator."""

    def __init__(self, event_bus: EventBus, retry_manager: RetryManager,
                 cache_manager: CacheManager, health_monitor: HealthMonitor):
        self.event_bus = event_bus
        self.retry_manager = retry_manager
        self.cache_manager = cache_manager
        self.health_monitor = health_monitor

        # Pipeline state machine
        self.state_handlers: Dict[PipelineState, Callable] = {
            PipelineState.UPLOAD: self._handle_upload,
            PipelineState.CAPTION: self._handle_caption,
            PipelineState.SCHEDULE: self._handle_schedule,
            PipelineState.POST: self._handle_post,
            PipelineState.ANALYZE: self._handle_analyze,
        }

        # Active pipelines
        self.active_pipelines: Dict[str, PipelineContext] = {}

        # Performance metrics
        self.pipeline_metrics = {
            'total_started': 0,
            'total_completed': 0,
            'total_failed': 0,
            'avg_completion_time': 0.0,
        }

    async def start_pipeline(self, task_id: str, user_id: str,
                           video_path: str) -> str:
        """Start a new AI pipeline execution."""
        logger.info(f"Starting pipeline for task {task_id}")

        context = PipelineContext(
            task_id=task_id,
            user_id=user_id,
            video_path=video_path,
            metadata={'start_time': datetime.now(datetime.UTC)}
        )

        self.active_pipelines[task_id] = context
        self.pipeline_metrics['total_started'] += 1

        # Publish pipeline started event
        await self.event_bus.publish('pipeline.started', {
            'task_id': task_id,
            'user_id': user_id,
            'state': PipelineState.UPLOAD.value
        })

        # Start pipeline execution
        asyncio.create_task(self._execute_pipeline(context))

        return task_id

    async def _execute_pipeline(self, context: PipelineContext):
        """Execute the complete pipeline workflow."""
        current_state = PipelineState.UPLOAD

        try:
            while current_state != PipelineState.COMPLETED:
                logger.info(f"Executing state {current_state.value} for task {context.task_id}")

                # Execute current state handler
                next_state = await self.state_handlers[current_state](context)

                # Update context
                context.updated_at = datetime.now(datetime.UTC)
                context.metadata['current_state'] = current_state.value

                # Publish state change event
                await self.event_bus.publish('pipeline.state_changed', {
                    'task_id': context.task_id,
                    'from_state': current_state.value,
                    'to_state': next_state.value if next_state else None,
                    'timestamp': context.updated_at.isoformat()
                })

                # Move to next state
                current_state = next_state

                if current_state == PipelineState.FAILED:
                    break

            # Pipeline completed successfully
            if current_state == PipelineState.COMPLETED:
                await self._complete_pipeline(context)
            else:
                await self._fail_pipeline(context, "Pipeline execution failed")

        except Exception as e:
            logger.error(f"Pipeline execution failed for task {context.task_id}: {e}")
            await self._fail_pipeline(context, str(e))

    async def _handle_upload(self, context: PipelineContext) -> PipelineState:
        """Handle video upload processing."""
        try:
            # Validate video file
            if not await self._validate_video(context.video_path):
                raise ValueError("Invalid video file")

            # Extract video metadata
            metadata = await self._extract_video_metadata(context.video_path)
            context.metadata.update(metadata)

            # Cache video processing results
            await self.cache_manager.set(
                f"video:{context.task_id}",
                {'path': context.video_path, 'metadata': metadata},
                ttl=3600  # 1 hour
            )

            # Publish upload completed event
            await self.event_bus.publish('pipeline.upload_completed', {
                'task_id': context.task_id,
                'video_path': context.video_path,
                'metadata': metadata
            })

            return PipelineState.CAPTION

        except Exception as e:
            logger.error(f"Upload handling failed: {e}")
            return PipelineState.FAILED

    async def _handle_caption(self, context: PipelineContext) -> PipelineState:
        """Handle AI caption generation."""
        try:
            # Check cache first
            cache_key = f"caption:{context.task_id}"
            cached_result = await self.cache_manager.get(cache_key)

            if cached_result:
                context.caption = cached_result['caption']
                context.hashtags = cached_result['hashtags']
            else:
                # Generate caption using AI service
                caption_result = await self._generate_caption(context)

                context.caption = caption_result['caption']
                context.hashtags = caption_result['hashtags']

                # Cache the result
                await self.cache_manager.set(cache_key, caption_result, ttl=1800)  # 30 min

            # Publish caption generated event
            await self.event_bus.publish('pipeline.caption_generated', {
                'task_id': context.task_id,
                'caption': context.caption,
                'hashtags': context.hashtags
            })

            return PipelineState.SCHEDULE

        except Exception as e:
            logger.error(f"Caption generation failed: {e}")
            return PipelineState.FAILED

    async def _handle_schedule(self, context: PipelineContext) -> PipelineState:
        """Handle post scheduling."""
        try:
            # Determine optimal posting time
            optimal_time = await self._calculate_optimal_post_time(context)

            context.scheduled_time = optimal_time

            # Schedule the post
            await self._schedule_post(context)

            # Publish scheduling completed event
            await self.event_bus.publish('pipeline.scheduled', {
                'task_id': context.task_id,
                'scheduled_time': optimal_time.isoformat(),
                'caption': context.caption,
                'hashtags': context.hashtags
            })

            return PipelineState.POST

        except Exception as e:
            logger.error(f"Scheduling failed: {e}")
            return PipelineState.FAILED

    async def _handle_post(self, context: PipelineContext) -> PipelineState:
        """Handle social media posting."""
        try:
            # Wait for scheduled time if not yet reached
            if context.scheduled_time and datetime.now(datetime.UTC) < context.scheduled_time:
                wait_seconds = (context.scheduled_time - datetime.now(datetime.UTC)).total_seconds()
                await asyncio.sleep(min(wait_seconds, 300))  # Max wait 5 minutes for demo

            # Post to social media platforms
            post_result = await self._post_to_platforms(context)
            context.post_id = post_result['post_id']

            # Publish posting completed event
            await self.event_bus.publish('pipeline.posted', {
                'task_id': context.task_id,
                'post_id': context.post_id,
                'platforms': post_result['platforms']
            })

            return PipelineState.ANALYZE

        except Exception as e:
            logger.error(f"Posting failed: {e}")
            return PipelineState.FAILED

    async def _handle_analyze(self, context: PipelineContext) -> PipelineState:
        """Handle post performance analysis."""
        try:
            # Collect analytics data
            analytics = await self._collect_analytics(context.post_id)
            context.analytics = analytics

            # Store analytics for learning
            await self._store_analytics_for_learning(context)

            # Publish analysis completed event
            await self.event_bus.publish('pipeline.analyzed', {
                'task_id': context.task_id,
                'analytics': analytics
            })

            return PipelineState.COMPLETED

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return PipelineState.FAILED

    async def _complete_pipeline(self, context: PipelineContext):
        """Mark pipeline as completed."""
        self.pipeline_metrics['total_completed'] += 1

        # Calculate completion time
        completion_time = (context.updated_at - context.created_at).total_seconds()
        self.pipeline_metrics['avg_completion_time'] = (
            (self.pipeline_metrics['avg_completion_time'] *
             (self.pipeline_metrics['total_completed'] - 1) + completion_time) /
            self.pipeline_metrics['total_completed']
        )

        # Publish completion event
        await self.event_bus.publish('pipeline.completed', {
            'task_id': context.task_id,
            'completion_time': completion_time,
            'analytics': context.analytics
        })

        # Clean up
        del self.active_pipelines[context.task_id]

    async def _fail_pipeline(self, context: PipelineContext, error: str):
        """Mark pipeline as failed."""
        self.pipeline_metrics['total_failed'] += 1

        # Publish failure event
        await self.event_bus.publish('pipeline.failed', {
            'task_id': context.task_id,
            'error': error,
            'last_state': context.metadata.get('current_state')
        })

        # Clean up
        del self.active_pipelines[context.task_id]

    # Helper methods (implementations would integrate with actual services)

    async def _validate_video(self, video_path: str) -> bool:
        """Validate video file."""
        # Implementation would check file size, format, duration, etc.
        return True

    async def _extract_video_metadata(self, video_path: str) -> Dict[str, Any]:
        """Extract video metadata."""
        # Implementation would use ffmpeg or similar
        return {'duration': 60, 'format': 'mp4', 'size': 1024000}

    async def _generate_caption(self, context: PipelineContext) -> Dict[str, Any]:
        """Generate AI caption and hashtags."""
        # Implementation would call AI service
        return {
            'caption': 'Amazing content! #trending',
            'hashtags': ['#viral', '#content', '#ai']
        }

    async def _calculate_optimal_post_time(self, context: PipelineContext) -> datetime:
        """Calculate optimal posting time."""
        # Implementation would use analytics data
        return datetime.now(datetime.UTC) + timedelta(minutes=5)

    async def _schedule_post(self, context: PipelineContext):
        """Schedule the post."""
        # Implementation would use scheduling service
        pass

    async def _post_to_platforms(self, context: PipelineContext) -> Dict[str, Any]:
        """Post to social media platforms."""
        # Implementation would integrate with platform APIs
        return {'post_id': '12345', 'platforms': ['instagram', 'youtube']}

    async def _collect_analytics(self, post_id: str) -> Dict[str, Any]:
        """Collect post analytics."""
        # Implementation would fetch from platform APIs
        return {'views': 1000, 'likes': 50, 'comments': 10}

    async def _store_analytics_for_learning(self, context: PipelineContext):
        """Store analytics data for machine learning."""
        # Implementation would store in database for learning
        pass

    async def get_pipeline_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get current pipeline status."""
        context = self.active_pipelines.get(task_id)
        if not context:
            return None

        return {
            'task_id': context.task_id,
            'state': context.metadata.get('current_state'),
            'progress': self._calculate_progress(context),
            'created_at': context.created_at.isoformat(),
            'updated_at': context.updated_at.isoformat()
        }

    def _calculate_progress(self, context: PipelineContext) -> float:
        """Calculate pipeline progress percentage."""
        state_progress = {
            PipelineState.UPLOAD.value: 20,
            PipelineState.CAPTION.value: 40,
            PipelineState.SCHEDULE.value: 60,
            PipelineState.POST.value: 80,
            PipelineState.ANALYZE.value: 100,
        }
        current_state = context.metadata.get('current_state')
        return state_progress.get(current_state, 0)

    async def get_metrics(self) -> Dict[str, Any]:
        """Get pipeline metrics."""
        return dict(self.pipeline_metrics)
