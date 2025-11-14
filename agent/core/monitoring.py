"""
Monitoring service for checking pending posts and triggering agent processing.
Now uses API-based communication with the backend instead of direct DB access.
"""

import asyncio
import logging
import httpx
from typing import List, Dict, Any
from datetime import datetime, timedelta
import sys
import os
import psutil
import time

# Add backend to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

from agent.config.settings import (
    MONITORING_INTERVAL_HOURS,
    MAX_POSTS_PER_CHECK,
    BACKEND_API_URL,
    BACKEND_API_KEY,
)

logger = logging.getLogger(__name__)


class MonitoringService:
    """
    Monitors for pending posts and processes them through the agent pipeline.
    """

    def __init__(self):
        self.backend_url = BACKEND_API_URL.rstrip("/")
        self.api_key = BACKEND_API_KEY
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {},
        )

    async def start_monitoring_loop(self):
        """
        Start the continuous monitoring loop.
        """
        logger.info(
            f"Starting monitoring loop - checking every {MONITORING_INTERVAL_HOURS} hours"
        )

        while True:
            try:
                await self._check_pending_posts()
                await asyncio.sleep(MONITORING_INTERVAL_HOURS * 3600)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error

    async def _check_pending_posts(self):
        """
        Check for pending posts and process them.
        """
        try:
            # Get pending posts from backend API
            pending_posts = await self._get_pending_posts()

            if not pending_posts:
                logger.info("No pending posts found")
                return

            logger.info(f"Found {len(pending_posts)} pending posts")

            # Process posts up to the limit
            processed_count = 0
            for post_data in pending_posts[:MAX_POSTS_PER_CHECK]:
                try:
                    await self._process_post(post_data)
                    processed_count += 1
                except Exception as e:
                    logger.error(f"Error processing post {post_data.get('id')}: {e}")

            logger.info(f"Processed {processed_count} posts in this cycle")

        except Exception as e:
            logger.error(f"Error checking pending posts: {e}")

    async def _get_pending_posts(self) -> List[Dict[str, Any]]:
        """
        Get pending posts from backend API.
        """
        try:
            url = f"{self.backend_url}/agent/pending-posts"
            response = await self.client.get(url)

            if response.status_code == 200:
                data = response.json()
                return data.get("posts", [])
            else:
                logger.error(
                    f"Failed to get pending posts: {response.status_code} - {response.text}"
                )
                return []

        except Exception as e:
            logger.error(f"Error fetching pending posts: {e}")
            return []

    async def _process_post(self, post_data: Dict[str, Any]):
        """
        Process a single post through the agent pipeline.
        """
        try:
            post_id = post_data["id"]
            logger.info(f"Processing post {post_id}")

            # Import orchestrator here to avoid circular imports
            from agent.core.orchestrator import Orchestrator

            orchestrator = Orchestrator()
            await orchestrator.process_post(post_data)

            # Mark post as processed in backend
            await self._mark_post_processed(post_id)

            logger.info(f"Successfully processed post {post_id}")

        except Exception as e:
            logger.error(f"Error processing post {post_id}: {e}")
            # Mark post as failed
            await self._mark_post_failed(post_data["id"], str(e))

    async def _mark_post_processed(self, post_id: int):
        """
        Mark post as processed in backend.
        """
        try:
            url = f"{self.backend_url}/agent/posts/{post_id}/status"
            data = {
                "status": "processed",
                "processed_at": datetime.utcnow().isoformat(),
            }
            response = await self.client.put(url, json=data)

            if response.status_code != 200:
                logger.error(
                    f"Failed to mark post {post_id} as processed: {response.status_code}"
                )

        except Exception as e:
            logger.error(f"Error marking post {post_id} as processed: {e}")

    async def _mark_post_failed(self, post_id: int, error_message: str):
        """
        Mark post as failed in backend.
        """
        try:
            url = f"{self.backend_url}/agent/posts/{post_id}/status"
            data = {"status": "failed", "error_message": error_message}
            response = await self.client.put(url, json=data)

            if response.status_code != 200:
                logger.error(
                    f"Failed to mark post {post_id} as failed: {response.status_code}"
                )

        except Exception as e:
            logger.error(f"Error marking post {post_id} as failed: {e}")

    async def get_monitoring_status(self) -> Dict[str, Any]:
        """
        Get monitoring service status and metrics.
        """
        return {
            "service": "monitoring",
            "interval_hours": MONITORING_INTERVAL_HOURS,
            "max_posts_per_check": MAX_POSTS_PER_CHECK,
            "backend_url": self.backend_url,
            "api_connected": await self._test_api_connection(),
            "system_metrics": self._get_system_metrics(),
        }

    def _get_system_metrics(self) -> Dict[str, Any]:
        """
        Get basic system metrics.
        """
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage("/").percent,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def _test_api_connection(self) -> bool:
        """
        Test connection to backend API.
        """
        try:
            url = f"{self.backend_url}/health/live"
            response = await self.client.get(url)
            return response.status_code == 200
        except Exception:
            return False

    async def close(self):
        """
        Close the HTTP client.
        """
        await self.client.aclose()
