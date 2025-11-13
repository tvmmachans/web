"""
Retry Manager - Auto-retry & recovery with exponential backoff.
Handles failed operations with intelligent retry strategies and self-healing.
"""

import asyncio
import logging
import random
from typing import Dict, Any, Callable, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)

class RetryStrategy(Enum):
    """Retry strategy types."""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_DELAY = "fixed_delay"
    IMMEDIATE = "immediate"

@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_attempts: int = 3
    initial_delay: float = 1.0  # seconds
    max_delay: float = 300.0  # 5 minutes
    backoff_multiplier: float = 2.0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    jitter: bool = True  # Add random jitter to prevent thundering herd

@dataclass
class RetryTask:
    """Represents a task that can be retried."""
    task_id: str
    operation: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    config: RetryConfig = field(default_factory=RetryConfig)
    created_at: datetime = field(default_factory=lambda: datetime.now(datetime.UTC))
    attempts: int = 0
    last_attempt: Optional[datetime] = None
    last_error: Optional[str] = None
    completed: bool = False
    result: Any = None

class RetryManager:
    """Manages retry logic with various strategies and self-healing."""

    def __init__(self):
        self.active_tasks: Dict[str, RetryTask] = {}
        self.completed_tasks: List[RetryTask] = []
        self._running = False

        # Metrics
        self.metrics = {
            'total_tasks': 0,
            'successful_tasks': 0,
            'failed_tasks': 0,
            'retry_attempts': 0,
            'avg_attempts_per_task': 0.0
        }

    async def start(self):
        """Start the retry manager."""
        self._running = True
        asyncio.create_task(self._process_retry_queue())
        logger.info("RetryManager started")

    async def stop(self):
        """Stop the retry manager."""
        self._running = False
        logger.info("RetryManager stopped")

    async def submit_task(self, task_id: str, operation: Callable,
                         config: RetryConfig = None, *args, **kwargs) -> str:
        """Submit a task for retry management."""
        if config is None:
            config = RetryConfig()

        task = RetryTask(
            task_id=task_id,
            operation=operation,
            args=args,
            kwargs=kwargs,
            config=config
        )

        self.active_tasks[task_id] = task
        self.metrics['total_tasks'] += 1

        logger.info(f"Submitted retry task: {task_id}")
        return task_id

    async def _process_retry_queue(self):
        """Process tasks in the retry queue."""
        while self._running:
            try:
                current_time = datetime.now(datetime.UTC)
                tasks_to_retry = []

                # Find tasks ready for retry
                for task_id, task in self.active_tasks.items():
                    if self._should_retry(task, current_time):
                        tasks_to_retry.append(task)

                # Execute retry tasks
                for task in tasks_to_retry:
                    asyncio.create_task(self._execute_task(task))

                await asyncio.sleep(1)  # Check every second

            except Exception as e:
                logger.error(f"Error in retry queue processing: {e}")
                await asyncio.sleep(5)

    def _should_retry(self, task: RetryTask, current_time: datetime) -> bool:
        """Check if a task should be retried."""
        if task.completed:
            return False

        if task.attempts >= task.config.max_attempts:
            return False

        if task.last_attempt is None:
            return True  # First attempt

        # Check if enough time has passed since last attempt
        delay = self._calculate_delay(task)
        next_attempt_time = task.last_attempt + timedelta(seconds=delay)

        return current_time >= next_attempt_time

    def _calculate_delay(self, task: RetryTask) -> float:
        """Calculate delay before next retry attempt."""
        config = task.config

        if config.strategy == RetryStrategy.IMMEDIATE:
            return 0.0

        elif config.strategy == RetryStrategy.FIXED_DELAY:
            delay = config.initial_delay

        elif config.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = config.initial_delay * (task.attempts + 1)

        elif config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = config.initial_delay * (config.backoff_multiplier ** task.attempts)

        else:
            delay = config.initial_delay

        # Apply maximum delay limit
        delay = min(delay, config.max_delay)

        # Add jitter if enabled
        if config.jitter:
            jitter_factor = random.uniform(0.5, 1.5)
            delay *= jitter_factor

        return delay

    async def _execute_task(self, task: RetryTask):
        """Execute a retry task."""
        task.attempts += 1
        task.last_attempt = datetime.now(datetime.UTC)
        self.metrics['retry_attempts'] += 1

        logger.info(f"Executing retry task {task.task_id} (attempt {task.attempts}/{task.config.max_attempts})")

        try:
            # Execute the operation
            if asyncio.iscoroutinefunction(task.operation):
                result = await task.operation(*task.args, **task.kwargs)
            else:
                result = await asyncio.get_event_loop().run_in_executor(
                    None, task.operation, *task.args, **task.kwargs
                )

            # Success
            task.completed = True
            task.result = result

            self.metrics['successful_tasks'] += 1
            self._update_avg_attempts()

            logger.info(f"Retry task {task.task_id} completed successfully")

            # Move to completed tasks
            self.completed_tasks.append(task)
            del self.active_tasks[task.task_id]

            # Publish success event
            await self._publish_task_event(task, 'completed', result=result)

        except Exception as e:
            error_msg = str(e)
            task.last_error = error_msg

            logger.warning(f"Retry task {task.task_id} failed (attempt {task.attempts}): {error_msg}")

            if task.attempts >= task.config.max_attempts:
                # Max attempts reached, mark as failed
                task.completed = True
                self.metrics['failed_tasks'] += 1
                self._update_avg_attempts()

                logger.error(f"Retry task {task.task_id} failed permanently after {task.attempts} attempts")

                # Move to completed tasks
                self.completed_tasks.append(task)
                del self.active_tasks[task.task_id]

                # Publish failure event
                await self._publish_task_event(task, 'failed', error=error_msg)
            else:
                # Will retry later
                await self._publish_task_event(task, 'retry_scheduled',
                                             next_attempt=self._calculate_delay(task))

    def _update_avg_attempts(self):
        """Update average attempts per task metric."""
        total_completed = self.metrics['successful_tasks'] + self.metrics['failed_tasks']
        if total_completed > 0:
            total_attempts = sum(task.attempts for task in self.completed_tasks)
            self.metrics['avg_attempts_per_task'] = total_attempts / total_completed

    async def _publish_task_event(self, task: RetryTask, event_type: str, **kwargs):
        """Publish a task event (would integrate with event bus)."""
        # This would publish to event bus in real implementation
        event_data = {
            'task_id': task.task_id,
            'attempts': task.attempts,
            'max_attempts': task.config.max_attempts,
            'last_error': task.last_error,
            **kwargs
        }

        logger.debug(f"Task event: {event_type} for {task.task_id}: {event_data}")

    # High-level retry methods for common operations

    async def retry_pipeline_step(self, task_id: str, step_name: str,
                                operation: Callable, *args, **kwargs) -> Any:
        """Retry a pipeline step with default config."""
        config = RetryConfig(
            max_attempts=5,
            initial_delay=2.0,
            max_delay=120.0,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF
        )

        retry_task_id = f"{task_id}_{step_name}"
        await self.submit_task(retry_task_id, operation, config, *args, **kwargs)

        # Wait for completion
        return await self.wait_for_task(retry_task_id)

    async def retry_api_call(self, task_id: str, operation: Callable, *args, **kwargs) -> Any:
        """Retry an API call with aggressive retry config."""
        config = RetryConfig(
            max_attempts=3,
            initial_delay=0.5,
            max_delay=30.0,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF
        )

        retry_task_id = f"{task_id}_api_call"
        await self.submit_task(retry_task_id, operation, config, *args, **kwargs)

        return await self.wait_for_task(retry_task_id)

    async def retry_with_custom_config(self, task_id: str, config: RetryConfig,
                                     operation: Callable, *args, **kwargs) -> Any:
        """Retry with custom configuration."""
        await self.submit_task(task_id, operation, config, *args, **kwargs)
        return await self.wait_for_task(task_id)

    async def wait_for_task(self, task_id: str, timeout: float = 300.0) -> Any:
        """Wait for a task to complete."""
        start_time = asyncio.get_event_loop().time()

        while asyncio.get_event_loop().time() - start_time < timeout:
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                if task.completed:
                    if task.result is not None:
                        return task.result
                    else:
                        raise Exception(f"Task {task_id} failed: {task.last_error}")
            elif task_id in [t.task_id for t in self.completed_tasks]:
                # Check completed tasks
                for task in self.completed_tasks:
                    if task.task_id == task_id:
                        if task.result is not None:
                            return task.result
                        else:
                            raise Exception(f"Task {task_id} failed: {task.last_error}")

            await asyncio.sleep(0.1)

        raise TimeoutError(f"Task {task_id} did not complete within {timeout} seconds")

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a retry task."""
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            return {
                'task_id': task.task_id,
                'attempts': task.attempts,
                'max_attempts': task.config.max_attempts,
                'last_attempt': task.last_attempt.isoformat() if task.last_attempt else None,
                'last_error': task.last_error,
                'completed': task.completed,
                'next_retry_in': self._calculate_delay(task) if not task.completed else 0
            }

        # Check completed tasks
        for task in self.completed_tasks[-100:]:  # Last 100 completed tasks
            if task.task_id == task_id:
                return {
                    'task_id': task.task_id,
                    'attempts': task.attempts,
                    'max_attempts': task.config.max_attempts,
                    'last_attempt': task.last_attempt.isoformat() if task.last_attempt else None,
                    'last_error': task.last_error,
                    'completed': task.completed,
                    'result': 'success' if task.result is not None else 'failed'
                }

        return None

    def get_metrics(self) -> Dict[str, Any]:
        """Get retry manager metrics."""
        return dict(self.metrics)

    async def cancel_task(self, task_id: str):
        """Cancel a retry task."""
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            task.completed = True
            task.last_error = "Task cancelled"

            self.completed_tasks.append(task)
            del self.active_tasks[task_id]

            logger.info(f"Cancelled retry task: {task_id}")

    async def force_retry(self, task_id: str):
        """Force immediate retry of a task."""
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            task.last_attempt = datetime.now(datetime.UTC) - timedelta(seconds=3600)  # Set to past
            logger.info(f"Forced retry for task: {task_id}")
