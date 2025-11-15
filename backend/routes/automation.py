"""
Automation API Routes - Expose automation orchestrator functionality.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any

# Import automation orchestrator
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "agent"))

from agent.services.automation_orchestrator import AutomationOrchestrator

logger = logging.getLogger(__name__)
router = APIRouter()

# Global orchestrator instance
orchestrator = AutomationOrchestrator()


class StartAutomationRequest(BaseModel):
    days: int = 7


class AutomationStatusResponse(BaseModel):
    running: bool
    current_cycle: Optional[str]
    status: str
    timestamp: str


@router.post("/start")
async def start_automation(request: StartAutomationRequest):
    """Start the automation system."""
    try:
        result = await orchestrator.start_automation(days=request.days)
        return result
    except Exception as e:
        logger.error(f"Failed to start automation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def stop_automation():
    """Stop the automation system."""
    try:
        result = await orchestrator.stop_automation()
        return result
    except Exception as e:
        logger.error(f"Failed to stop automation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_automation_status():
    """Get current automation status."""
    try:
        status = await orchestrator.get_status()
        return status
    except Exception as e:
        logger.error(f"Failed to get automation status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/single-video")
async def execute_single_video_workflow(trend: Dict[str, Any]):
    """Execute workflow for a single video from a trend."""
    try:
        result = await orchestrator.execute_single_video_workflow(trend)
        return result
    except Exception as e:
        logger.error(f"Single video workflow failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

