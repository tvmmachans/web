import asyncio
import logging
import signal
import sys
from typing import Dict, Any
from datetime import datetime

from agent.core.monitoring import MonitoringService
from agent.services.comment_automation import CommentAutomation
from agent.services.report_generator import ReportGenerator
from agent.config.settings import AGENT_NAME, AGENT_VERSION
from agent.orchestrator_integration import OrchestratorEventIntegration

logger = logging.getLogger(__name__)

class AgentOrchestrator:
    """
    Main orchestrator that coordinates all agent services.
    Manages the lifecycle of background services and handles graceful shutdown.
    """

    def __init__(self):
        self.monitoring_service = MonitoringService()
        self.comment_automation = CommentAutomation()
        self.report_generator = ReportGenerator()

        # Add orchestrator event integration
        self.orchestrator_integration = OrchestratorEventIntegration()

        self.services = [
            self.monitoring_service,
            self.comment_automation,
            self.report_generator,
            self.orchestrator_integration
        ]

        self.running = False
        self.start_time = None

    async def start_agent(self):
        """
        Start the autonomous agent with all services.
        """
        try:
            self.running = True
            self.start_time = datetime.utcnow()

            logger.info(f"🚀 Starting {AGENT_NAME} v{AGENT_VERSION}")

            # Setup signal handlers for graceful shutdown
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)

            # Start all services concurrently
            tasks = []

            # Start monitoring service
            tasks.append(asyncio.create_task(self._run_monitoring()))

            # Start comment automation
            tasks.append(asyncio.create_task(self._run_comment_automation()))

            # Schedule weekly reports
            tasks.append(asyncio.create_task(self._schedule_reports()))

            # Wait for all tasks
            await asyncio.gather(*tasks, return_exceptions=True)

        except Exception as e:
            logger.error(f"Error starting agent: {e}")
            await self.stop_agent()

    async def stop_agent(self):
        """
        Stop all agent services gracefully.
        """
        try:
            logger.info("🛑 Stopping autonomous agent...")

            self.running = False

            # Stop monitoring service
            await self.monitoring_service.stop_monitoring()

            # Log final status
            uptime = datetime.utcnow() - self.start_time if self.start_time else None
            logger.info(f"Agent stopped. Uptime: {uptime}")

        except Exception as e:
            logger.error(f"Error stopping agent: {e}")

    def _signal_handler(self, signum, frame):
        """
        Handle shutdown signals.
        """
        logger.info(f"Received signal {signum}, initiating shutdown...")
        asyncio.create_task(self.stop_agent())

    async def _run_monitoring(self):
        """
        Run the monitoring service.
        """
        try:
            logger.info("Starting monitoring service...")
            await self.monitoring_service.start_monitoring()
        except Exception as e:
            logger.error(f"Monitoring service error: {e}")

    async def _run_comment_automation(self):
        """
        Run comment automation service.
        """
        try:
            logger.info("Starting comment automation service...")
            await self.comment_automation.start_comment_monitoring()
        except Exception as e:
            logger.error(f"Comment automation error: {e}")

    async def _schedule_reports(self):
        """
        Handle report scheduling.
        """
        try:
            # Schedule initial report generation
            await self.report_generator.schedule_weekly_reports()

            # In production, this would run a loop to check for report times
            # For now, just keep the service alive
            while self.running:
                await asyncio.sleep(3600)  # Check every hour

        except Exception as e:
            logger.error(f"Report scheduling error: {e}")

    async def get_agent_status(self) -> Dict[str, Any]:
        """
        Get comprehensive agent status.
        """
        try:
            services_status = {}

            # Get status from each service
            services_status["monitoring"] = await self.monitoring_service.get_monitoring_status()
            services_status["comment_automation"] = await self.comment_automation.get_comment_stats()
            services_status["report_generator"] = await self.report_generator.get_report_status()

            status = {
                "agent_name": AGENT_NAME,
                "version": AGENT_VERSION,
                "running": self.running,
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds() if self.start_time else 0,
                "services": services_status
            }

            return status

        except Exception as e:
            logger.error(f"Error getting agent status: {e}")
            return {"error": str(e)}

    async def trigger_manual_report(self) -> Dict[str, Any]:
        """
        Manually trigger a report generation.
        """
        try:
            logger.info("Manually triggering report generation...")
            report = await self.report_generator.generate_weekly_report()
            return {"status": "success", "report": report}
        except Exception as e:
            logger.error(f"Error generating manual report: {e}")
            return {"status": "error", "message": str(e)}

    async def trigger_manual_check(self) -> Dict[str, Any]:
        """
        Manually trigger a monitoring check.
        """
        try:
            logger.info("Manually triggering monitoring check...")

            # Force a monitoring check
            async for session in self.monitoring_service._check_pending_posts():
                pass

            return {"status": "success", "message": "Manual check completed"}
        except Exception as e:
            logger.error(f"Error in manual check: {e}")
            return {"status": "error", "message": str(e)}
