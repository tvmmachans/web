#!/usr/bin/env python3
"""
Autonomous AI Social Media Agent
Main entry point for running the agent service.
"""

import asyncio
import logging
import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from agent.config.settings import LOG_FILE, LOG_LEVEL
from agent.core.orchestrator import AgentOrchestrator


def setup_logging():
    """
    Setup logging configuration.
    """
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler(sys.stdout)],
    )


async def main():
    """
    Main entry point for the agent.
    """
    try:
        # Setup logging
        setup_logging()

        logger = logging.getLogger(__name__)
        logger.info("🤖 Starting Autonomous AI Social Media Agent")

        # Create and start orchestrator
        orchestrator = AgentOrchestrator()

        # Handle command line arguments
        if len(sys.argv) > 1:
            command = sys.argv[1]

            if command == "status":
                status = await orchestrator.get_agent_status()
                print("Agent Status:")
                print(f"Running: {status['running']}")
                print(f"Uptime: {status.get('uptime_seconds', 0):.0f} seconds")
                for service_name, service_status in status.get("services", {}).items():
                    print(f"{service_name}: {service_status}")

            elif command == "report":
                result = await orchestrator.trigger_manual_report()
                if result["status"] == "success":
                    print("✅ Manual report generated successfully")
                else:
                    print(f"❌ Report generation failed: {result['message']}")

            elif command == "check":
                result = await orchestrator.trigger_manual_check()
                if result["status"] == "success":
                    print("✅ Manual monitoring check completed")
                else:
                    print(f"❌ Manual check failed: {result['message']}")

            else:
                print("Usage: python -m agent [status|report|check]")
                print("  status: Show agent status")
                print("  report: Generate manual report")
                print("  check:  Run manual monitoring check")
                print("  (no args): Start agent service")

        else:
            # Start the agent service
            await orchestrator.start_agent()

    except KeyboardInterrupt:
        logger.info("Agent interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
