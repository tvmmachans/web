"""
Tests for AI Pipeline orchestrator.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from orchestrator.ai_pipeline import AIPipeline, PipelineState, PipelineContext
from orchestrator.event_bus import EventBus
from orchestrator.retry_manager import RetryManager
from orchestrator.cache_manager import CacheManager
from orchestrator.health_monitor import HealthMonitor


class TestAIPipeline:
    """Test cases for AI Pipeline."""

    @pytest.fixture
    def mock_components(self):
        """Create mock components for testing."""
        event_bus = MagicMock(spec=EventBus)
        retry_manager = MagicMock(spec=RetryManager)
        cache_manager = MagicMock(spec=CacheManager)
        health_monitor = MagicMock(spec=HealthMonitor)

        return event_bus, retry_manager, cache_manager, health_monitor

    @pytest.fixture
    def pipeline(self, mock_components):
        """Create pipeline instance with mocked components."""
        event_bus, retry_manager, cache_manager, health_monitor = mock_components
        return AIPipeline(event_bus, retry_manager, cache_manager, health_monitor)

    @pytest.fixture
    def sample_context(self):
        """Create sample pipeline context."""
        return PipelineContext(
            task_id="test_task_123",
            user_id="user_456",
            video_path="/path/to/video.mp4"
        )

    def test_pipeline_initialization(self, pipeline, mock_components):
        """Test pipeline initialization."""
        event_bus, retry_manager, cache_manager, health_monitor = mock_components

        assert pipeline.event_bus == event_bus
        assert pipeline.retry_manager == retry_manager
        assert pipeline.cache_manager == cache_manager
        assert pipeline.health_monitor == health_monitor
        assert len(pipeline.state_handlers) == 5  # All pipeline states
        assert len(pipeline.active_pipelines) == 0

    @pytest.mark.asyncio
    async def test_start_pipeline(self, pipeline, mock_components, sample_context):
        """Test starting a new pipeline."""
        event_bus, retry_manager, cache_manager, health_monitor = mock_components

        # Mock event publishing
        event_bus.publish = AsyncMock()

        # Mock pipeline execution
        with patch.object(pipeline, '_execute_pipeline', new_callable=AsyncMock) as mock_execute:
            task_id = await pipeline.start_pipeline(
                sample_context.task_id,
                sample_context.user_id,
                sample_context.video_path
            )

            assert task_id == sample_context.task_id
            assert task_id in pipeline.active_pipelines

            context = pipeline.active_pipelines[task_id]
            assert context.task_id == sample_context.task_id
            assert context.user_id == sample_context.user_id
            assert context.video_path == sample_context.video_path

            # Verify event was published
            event_bus.publish.assert_called_once()
            call_args = event_bus.publish.call_args
            assert call_args[0][0] == 'pipeline.started'
            assert call_args[0][1]['task_id'] == sample_context.task_id

            # Verify pipeline execution was started
            mock_execute.assert_called_once_with(context)

    @pytest.mark.asyncio
    async def test_pipeline_execution_success(self, pipeline, mock_components, sample_context):
        """Test successful pipeline execution."""
        event_bus, retry_manager, cache_manager, health_monitor = mock_components

        # Mock all state handlers to return next states
        pipeline._handle_upload = AsyncMock(return_value=PipelineState.CAPTION)
        pipeline._handle_caption = AsyncMock(return_value=PipelineState.SCHEDULE)
        pipeline._handle_schedule = AsyncMock(return_value=PipelineState.POST)
        pipeline._handle_post = AsyncMock(return_value=PipelineState.ANALYZE)
        pipeline._handle_analyze = AsyncMock(return_value=PipelineState.COMPLETED)

        # Mock event publishing and completion
        event_bus.publish = AsyncMock()
        pipeline._complete_pipeline = AsyncMock()

        # Execute pipeline
        await pipeline._execute_pipeline(sample_context)

        # Verify all handlers were called
        pipeline._handle_upload.assert_called_once_with(sample_context)
        pipeline._handle_caption.assert_called_once_with(sample_context)
        pipeline._handle_schedule.assert_called_once_with(sample_context)
        pipeline._handle_post.assert_called_once_with(sample_context)
        pipeline._handle_analyze.assert_called_once_with(sample_context)

        # Verify completion was called
        pipeline._complete_pipeline.assert_called_once_with(sample_context)

    @pytest.mark.asyncio
    async def test_pipeline_execution_failure(self, pipeline, mock_components, sample_context):
        """Test pipeline execution with failure."""
        event_bus, retry_manager, cache_manager, health_monitor = mock_components

        # Mock upload handler to fail
        pipeline._handle_upload = AsyncMock(return_value=PipelineState.FAILED)

        # Mock event publishing and failure handling
        event_bus.publish = AsyncMock()
        pipeline._fail_pipeline = AsyncMock()

        # Execute pipeline
        await pipeline._execute_pipeline(sample_context)

        # Verify failure was handled
        pipeline._fail_pipeline.assert_called_once()
        call_args = pipeline._fail_pipeline.call_args
        assert call_args[0][0] == sample_context
        assert "Pipeline execution failed" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_handle_upload_success(self, pipeline, mock_components, sample_context):
        """Test successful upload handling."""
        event_bus, retry_manager, cache_manager, health_monitor = mock_components

        # Mock dependencies
        pipeline._validate_video = AsyncMock(return_value=True)
        pipeline._extract_video_metadata = AsyncMock(return_value={'duration': 60})
        event_bus.publish = AsyncMock()
        cache_manager.set = AsyncMock()

        # Execute upload handler
        result = await pipeline._handle_upload(sample_context)

        assert result == PipelineState.CAPTION
        assert 'duration' in sample_context.metadata

        # Verify event was published
        event_bus.publish.assert_called_once()
        call_args = event_bus.publish.call_args
        assert call_args[0][0] == 'pipeline.upload_completed'

        # Verify cache was set
        cache_manager.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_upload_validation_failure(self, pipeline, mock_components, sample_context):
        """Test upload handling with validation failure."""
        event_bus, retry_manager, cache_manager, health_monitor = mock_components

        # Mock validation failure
        pipeline._validate_video = AsyncMock(return_value=False)

        # Execute upload handler
        result = await pipeline._handle_upload(sample_context)

        assert result == PipelineState.FAILED

    @pytest.mark.asyncio
    async def test_handle_caption_with_cache(self, pipeline, mock_components, sample_context):
        """Test caption handling with cached result."""
        event_bus, retry_manager, cache_manager, health_monitor = mock_components

        # Mock cache hit
        cached_result = {'caption': 'Cached caption', 'hashtags': ['#test']}
        cache_manager.get = AsyncMock(return_value=cached_result)
        cache_manager.set = AsyncMock()
        event_bus.publish = AsyncMock()

        # Execute caption handler
        result = await pipeline._handle_caption(sample_context)

        assert result == PipelineState.SCHEDULE
        assert sample_context.caption == cached_result['caption']
        assert sample_context.hashtags == cached_result['hashtags']

        # Verify cache was not set again
        cache_manager.set.assert_not_called()

        # Verify event was published
        event_bus.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_caption_without_cache(self, pipeline, mock_components, sample_context):
        """Test caption handling without cached result."""
        event_bus, retry_manager, cache_manager, health_monitor = mock_components

        # Mock cache miss and generation
        cache_manager.get = AsyncMock(return_value=None)
        pipeline._generate_caption = AsyncMock(return_value={
            'caption': 'Generated caption',
            'hashtags': ['#ai', '#generated']
        })
        cache_manager.set = AsyncMock()
        event_bus.publish = AsyncMock()

        # Execute caption handler
        result = await pipeline._handle_caption(sample_context)

        assert result == PipelineState.SCHEDULE
        assert sample_context.caption == 'Generated caption'
        assert sample_context.hashtags == ['#ai', '#generated']

        # Verify cache was set
        cache_manager.set.assert_called_once()

        # Verify event was published
        event_bus.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_pipeline_status_active(self, pipeline, sample_context):
        """Test getting status of active pipeline."""
        # Add context to active pipelines
        sample_context.metadata = {'current_state': 'upload'}
        sample_context.created_at = datetime.now(datetime.UTC)
        sample_context.updated_at = datetime.now(datetime.UTC)
        pipeline.active_pipelines[sample_context.task_id] = sample_context

        # Mock progress calculation
        pipeline._calculate_progress = MagicMock(return_value=20)

        status = await pipeline.get_pipeline_status(sample_context.task_id)

        assert status is not None
        assert status['task_id'] == sample_context.task_id
        assert status['state'] == 'upload'
        assert status['progress'] == 20

    @pytest.mark.asyncio
    async def test_get_pipeline_status_not_found(self, pipeline):
        """Test getting status of non-existent pipeline."""
        status = await pipeline.get_pipeline_status("non_existent_task")

        assert status is None

    def test_calculate_progress(self, pipeline, sample_context):
        """Test progress calculation."""
        # Test different states
        test_cases = [
            ('upload', 20),
            ('caption', 40),
            ('schedule', 60),
            ('post', 80),
            ('analyze', 100),
            ('unknown', 0)
        ]

        for state, expected_progress in test_cases:
            sample_context.metadata = {'current_state': state}
            progress = pipeline._calculate_progress(sample_context)
            assert progress == expected_progress

    @pytest.mark.asyncio
    async def test_get_metrics(self, pipeline):
        """Test getting pipeline metrics."""
        # Set up some metrics
        pipeline.pipeline_metrics = {
            'total_started': 10,
            'total_completed': 8,
            'total_failed': 2,
            'avg_completion_time': 120.5,
        }

        metrics = await pipeline.get_metrics()

        assert metrics['total_started'] == 10
        assert metrics['total_completed'] == 8
        assert metrics['total_failed'] == 2
        assert metrics['avg_completion_time'] == 120.5
