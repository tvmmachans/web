"""
AI Generation API Routes - Video creation, content generation
"""

import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "agent"))

from agent.services.ai_content_brain import AIContentBrain
from agent.services.ai_video_factory import AIVideoFactory
from agent.services.enhanced_video_factory import (
    MultiFormatCreator,
    BatchContentCreator,
)

logger = logging.getLogger(__name__)
router = APIRouter()

content_brain = AIContentBrain()
video_factory = AIVideoFactory()
multi_format = MultiFormatCreator()
batch_creator = BatchContentCreator()


class GenerateVideoRequest(BaseModel):
    trend_id: Optional[int] = None
    trend_data: Optional[Dict[str, Any]] = None
    script: Optional[Dict[str, Any]] = None


class GenerateMultiFormatRequest(BaseModel):
    script: Dict[str, Any]
    formats: List[str] = ["short", "reel"]


class BatchCreateRequest(BaseModel):
    trend_ids: List[int]
    batch_size: int = 5


@router.post("/generate-video")
async def generate_video(
    request: GenerateVideoRequest, background_tasks: BackgroundTasks
):
    """Generate complete video from trend or script."""
    try:
        if request.script:
            # Generate from script
            result = await video_factory.create_complete_video(request.script)
        elif request.trend_data:
            # Generate from trend
            content_result = await content_brain.generate_content_for_trend(
                request.trend_data
            )
            if content_result.get("script"):
                result = await video_factory.create_complete_video(
                    content_result.get("script")
                )
            else:
                raise HTTPException(
                    status_code=400, detail="Failed to generate script from trend"
                )
        else:
            raise HTTPException(
                status_code=400, detail="Either script or trend_data required"
            )

        return {
            "status": "success",
            "video": result,
            "generated_at": result.get("created_at"),
        }
    except Exception as e:
        logger.error(f"Video generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-multi-format")
async def generate_multi_format(request: GenerateMultiFormatRequest):
    """Generate content in multiple formats."""
    try:
        result = await multi_format.create_multi_format(request.script, request.formats)
        return {
            "status": "success",
            "formats": result,
        }
    except Exception as e:
        logger.error(f"Multi-format generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-create")
async def batch_create(request: BatchCreateRequest, background_tasks: BackgroundTasks):
    """Create multiple videos in batch."""
    try:
        # Fetch trends (would query database)
        trends = []  # Placeholder - would fetch from DB

        result = await batch_creator.create_batch(trends, request.batch_size)

        return {
            "status": "success",
            "batch": result,
        }
    except Exception as e:
        logger.error(f"Batch creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/content/{content_id}")
async def get_generated_content(content_id: str):
    """Get AI-generated content details."""
    # Would query database
    return {
        "content_id": content_id,
        "status": "generated",
        "message": "Content retrieval not yet implemented",
    }
