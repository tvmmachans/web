"""
Automation Orchestrator - Complete end-to-end automation workflow manager.
Coordinates all modules seamlessly for zero-touch content creation and publishing.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import json

from agent.services.ai_content_brain import AIContentBrain
from agent.services.ai_video_factory import AIVideoFactory
from agent.services.smart_publisher import SmartPublisher
from agent.services.performance_optimizer import PerformanceOptimizer

logger = logging.getLogger(__name__)


class WorkflowManager:
    """Manages complete automation workflows."""

    def __init__(self):
        self.content_brain = AIContentBrain()
        self.video_factory = AIVideoFactory()
        self.publisher = SmartPublisher()
        self.optimizer = PerformanceOptimizer()

    async def execute_full_automation_cycle(self, days: int = 7) -> Dict[str, Any]:
        """Execute complete automation cycle: Discovery → Creation → Publishing → Optimization."""
        logger.info("🚀 Starting full automation cycle...")

        results = {
            "cycle_id": f"cycle_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "started_at": datetime.utcnow().isoformat(),
            "phases": {},
        }

        try:
            # Phase 1: Content Discovery & Planning
            logger.info("📊 Phase 1: Content Discovery & Planning...")
            discovery_result = await self.content_brain.discover_and_plan(days=days)
            results["phases"]["discovery"] = {
                "status": "completed",
                "trends_found": len(discovery_result.get("trends", [])),
                "calendar_days": len(
                    discovery_result.get("calendar", {}).get("days", [])
                ),
            }

            # Phase 2: Video Creation
            logger.info("🎬 Phase 2: Video Creation...")
            creation_results = []
            calendar = discovery_result.get("calendar", {})

            for day_plan in calendar.get("days", [])[:days]:  # Limit to requested days
                if day_plan.get("status") == "planned" and day_plan.get("script"):
                    try:
                        video_result = await self.video_factory.create_complete_video(
                            day_plan.get("script")
                        )
                        creation_results.append(
                            {
                                "date": day_plan.get("date"),
                                "video": video_result,
                                "status": video_result.get("status"),
                            }
                        )
                    except Exception as e:
                        logger.error(
                            f"Video creation failed for {day_plan.get('date')}: {e}"
                        )
                        creation_results.append(
                            {
                                "date": day_plan.get("date"),
                                "status": "failed",
                                "error": str(e),
                            }
                        )

            results["phases"]["creation"] = {
                "status": "completed",
                "videos_created": len(
                    [r for r in creation_results if r.get("status") == "completed"]
                ),
                "videos_failed": len(
                    [r for r in creation_results if r.get("status") == "failed"]
                ),
                "results": creation_results,
            }

            # Phase 3: Publishing
            logger.info("📡 Phase 3: Publishing...")
            publishing_results = []

            for creation_result in creation_results:
                if creation_result.get("status") == "completed":
                    video_data = creation_result.get("video", {})
                    try:
                        publish_result = await self.publisher.publish_content(
                            {
                                "video_url": video_data.get("video_url"),
                                "thumbnail_url": video_data.get("thumbnail_url"),
                                "script": creation_result.get("script"),
                                "title": video_data.get("title", "Auto-generated"),
                                "category": "general",
                            },
                            platforms=["youtube", "instagram"],
                            auto_schedule=True,
                        )
                        publishing_results.append(
                            {
                                "date": creation_result.get("date"),
                                "publish_result": publish_result,
                                "status": "published",
                            }
                        )
                    except Exception as e:
                        logger.error(f"Publishing failed: {e}")
                        publishing_results.append(
                            {
                                "date": creation_result.get("date"),
                                "status": "failed",
                                "error": str(e),
                            }
                        )

            results["phases"]["publishing"] = {
                "status": "completed",
                "published": len(
                    [r for r in publishing_results if r.get("status") == "published"]
                ),
                "failed": len(
                    [r for r in publishing_results if r.get("status") == "failed"]
                ),
                "results": publishing_results,
            }

            # Phase 4: Performance Tracking (async, runs in background)
            logger.info("📊 Phase 4: Performance Tracking (background)...")
            asyncio.create_task(self._track_performance_background(publishing_results))

            results["phases"]["tracking"] = {
                "status": "started",
                "note": "Running in background",
            }

            results["completed_at"] = datetime.utcnow().isoformat()
            results["status"] = "completed"

            logger.info("✅ Full automation cycle completed!")

        except Exception as e:
            logger.error(f"Automation cycle failed: {e}")
            results["status"] = "failed"
            results["error"] = str(e)
            results["completed_at"] = datetime.utcnow().isoformat()

        return results

    async def _track_performance_background(
        self, publishing_results: List[Dict[str, Any]]
    ):
        """Track performance in background."""
        await asyncio.sleep(3600)  # Wait 1 hour after publishing

        for result in publishing_results:
            if result.get("status") == "published":
                publish_result = result.get("publish_result", {})
                for platform, platform_result in publish_result.get(
                    "publish_results", {}
                ).items():
                    if platform_result.get("status") == "published":
                        video_id = platform_result.get(
                            "video_id"
                        ) or platform_result.get("media_id")
                        if video_id:
                            try:
                                await self.optimizer.analytics_tracker.track_performance(
                                    video_id, platform
                                )
                            except Exception as e:
                                logger.error(f"Performance tracking failed: {e}")


class ErrorHandler:
    """Automatically retries failed operations."""

    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries

    async def retry_operation(self, operation, *args, **kwargs) -> Dict[str, Any]:
        """Retry an operation with exponential backoff."""
        for attempt in range(self.max_retries):
            try:
                result = await operation(*args, **kwargs)
                if result and not result.get("error"):
                    return {"success": True, "result": result, "attempts": attempt + 1}
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    wait_time = 2**attempt  # Exponential backoff
                    await asyncio.sleep(wait_time)

        return {
            "success": False,
            "error": "Max retries exceeded",
            "attempts": self.max_retries,
        }


class QualityChecker:
    """Ensures all content meets quality standards."""

    def __init__(self):
        self.min_quality_score = 0.7

    async def check_content_quality(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Check if content meets quality standards."""
        issues = []
        score = 1.0

        # Check video
        if not content.get("video_url"):
            issues.append("Missing video URL")
            score -= 0.3

        # Check thumbnail
        if not content.get("thumbnail_url"):
            issues.append("Missing thumbnail")
            score -= 0.2

        # Check script
        script = content.get("script", {})
        if not script.get("scenes"):
            issues.append("Missing script scenes")
            score -= 0.2

        # Check voiceover
        if not content.get("audio_url"):
            issues.append("Missing voiceover")
            score -= 0.2

        # Check subtitles
        if not content.get("subtitles"):
            issues.append("Missing subtitles")
            score -= 0.1

        passed = score >= self.min_quality_score

        return {
            "passed": passed,
            "score": score,
            "issues": issues,
            "checked_at": datetime.utcnow().isoformat(),
        }


class BackupSystems:
    """Prevents single points of failure."""

    def __init__(self):
        self.backup_storage = []  # Would be actual backup storage

    async def create_backup(self, data: Dict[str, Any]) -> bool:
        """Create backup of important data."""
        try:
            backup_entry = {
                "data": data,
                "backed_up_at": datetime.utcnow().isoformat(),
            }
            self.backup_storage.append(backup_entry)
            return True
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return False

    async def restore_from_backup(self, backup_id: str) -> Optional[Dict[str, Any]]:
        """Restore data from backup."""
        # Simplified - would restore from actual backup storage
        return None


class AutomationOrchestrator:
    """Main orchestrator that coordinates all automation modules."""

    def __init__(self):
        self.workflow_manager = WorkflowManager()
        self.error_handler = ErrorHandler()
        self.quality_checker = QualityChecker()
        self.backup_systems = BackupSystems()
        self.running = False
        self.current_cycle = None

    async def start_automation(self, days: int = 7) -> Dict[str, Any]:
        """Start the automation system."""
        if self.running:
            return {"status": "already_running", "current_cycle": self.current_cycle}

        self.running = True
        logger.info("🤖 Starting automation orchestrator...")

        try:
            # Execute full cycle
            cycle_result = await self.workflow_manager.execute_full_automation_cycle(
                days
            )

            # Create backup
            await self.backup_systems.create_backup(cycle_result)

            self.current_cycle = cycle_result.get("cycle_id")

            return {
                "status": "started",
                "cycle_id": self.current_cycle,
                "result": cycle_result,
            }

        except Exception as e:
            logger.error(f"Automation start failed: {e}")
            return {"status": "failed", "error": str(e)}
        finally:
            self.running = False

    async def stop_automation(self) -> Dict[str, Any]:
        """Stop the automation system."""
        self.running = False
        logger.info("🛑 Stopping automation orchestrator...")
        return {"status": "stopped", "stopped_at": datetime.utcnow().isoformat()}

    async def get_status(self) -> Dict[str, Any]:
        """Get current automation status."""
        return {
            "running": self.running,
            "current_cycle": self.current_cycle,
            "status": "active" if self.running else "idle",
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def execute_single_video_workflow(
        self, trend: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute workflow for a single video from a trend."""
        logger.info(
            f"🎯 Executing single video workflow for trend: {trend.get('title')}"
        )

        try:
            # Step 1: Generate content
            content_result = (
                await self.workflow_manager.content_brain.generate_content_for_trend(
                    trend
                )
            )

            if not content_result.get("script"):
                return {"status": "failed", "error": "Script generation failed"}

            # Step 2: Create video
            video_result = (
                await self.workflow_manager.video_factory.create_complete_video(
                    content_result.get("script")
                )
            )

            # Step 3: Quality check
            quality_check = await self.quality_checker.check_content_quality(
                video_result
            )

            if not quality_check.get("passed"):
                return {
                    "status": "failed",
                    "error": "Quality check failed",
                    "issues": quality_check.get("issues"),
                }

            # Step 4: Publish
            publish_result = await self.workflow_manager.publisher.publish_content(
                {
                    "video_url": video_result.get("video_url"),
                    "thumbnail_url": video_result.get("thumbnail_url"),
                    "script": content_result.get("script"),
                    "title": content_result.get("ideas", [{}])[0].get(
                        "title", "Auto-generated"
                    ),
                    "category": trend.get("category", "general"),
                },
                platforms=["youtube", "instagram"],
                auto_schedule=True,
            )

            return {
                "status": "completed",
                "content": content_result,
                "video": video_result,
                "publish": publish_result,
                "quality_score": quality_check.get("score"),
            }

        except Exception as e:
            logger.error(f"Single video workflow failed: {e}")
            return {"status": "failed", "error": str(e)}
