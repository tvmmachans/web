"""
Scheduling routes for content posting.
"""

import logging
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
from datetime import datetime, timedelta

from orchestrator.config.settings import settings
from orchestrator.database.session import get_db
from orchestrator.database.models import ContentBlueprint

logger = logging.getLogger(__name__)

router = APIRouter()

class ScheduleRequest(BaseModel):
    blueprint_id: str
    scheduled_time: str  # ISO format datetime
    auto_post: bool = False

class ScheduleResponse(BaseModel):
    status: str
    post_id: str
    scheduled_time: str
    backend_response: Dict[str, Any]

@router.post("/schedule", response_model=ScheduleResponse)
async def schedule_blueprint(request: ScheduleRequest):
    """Schedule a blueprint for posting via backend scheduler."""
    try:
        # Get blueprint details
        async with get_db() as session:
            result = await session.execute("""
                SELECT
                    b.*, t.title as trend_title, t.source
                FROM content_blueprints b
                JOIN trends t ON b.trend_id = t.id
                WHERE b.blueprint_id = :blueprint_id
            """, {"blueprint_id": request.blueprint_id})

            blueprint_row = result.first()
            if not blueprint_row:
                raise HTTPException(status_code=404, detail="Blueprint not found")

            # Check if auto-post is enabled
            if request.auto_post and not settings.ENABLE_AUTO_POST:
                raise HTTPException(
                    status_code=403,
                    detail="Auto-posting is disabled. Enable in settings or use manual approval."
                )

            # Prepare post data for backend
            post_data = {
                "title": blueprint_row.title,
                "description": blueprint_row.script,
                "video_url": blueprint_row.video_url,
                "audio_url": blueprint_row.audio_url,
                "thumbnail_url": None,  # Would generate from prompt
                "hashtags": blueprint_row.hashtags,
                "scheduled_time": request.scheduled_time,
                "platform": "instagram",  # Default, could be parameterized
                "metadata": {
                    "blueprint_id": request.blueprint_id,
                    "trend_source": blueprint_row.source,
                    "predicted_views": blueprint_row.predicted_views,
                    "confidence_score": blueprint_row.confidence_score,
                    "auto_generated": True
                }
            }

            # Call backend schedule endpoint
            backend_response = await _call_backend_schedule(post_data)

            # Update blueprint status
            await session.execute("""
                UPDATE content_blueprints
                SET status = 'scheduled',
                    scheduled_at = :scheduled_at,
                    updated_at = :updated_at
                WHERE blueprint_id = :blueprint_id
            """, {
                "scheduled_at": datetime.fromisoformat(request.scheduled_time),
                "updated_at": datetime.utcnow(),
                "blueprint_id": request.blueprint_id
            })
            await session.commit()

            return ScheduleResponse(
                status="scheduled",
                post_id=backend_response.get("post_id", request.blueprint_id),
                scheduled_time=request.scheduled_time,
                backend_response=backend_response
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Scheduling failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/auto_schedule")
async def auto_schedule_top_blueprints(count: int = 5):
    """Automatically schedule top N blueprints for posting."""
    try:
        if not settings.ENABLE_AUTO_POST:
            raise HTTPException(
                status_code=403,
                detail="Auto-posting is disabled"
            )

        # Get top blueprints by ROI score
        async with get_db() as session:
            result = await session.execute("""
                SELECT blueprint_id, title, roi_score
                FROM content_blueprints
                WHERE status = 'draft'
                ORDER BY roi_score DESC
                LIMIT :count
            """, {"count": count})

            blueprints = result.fetchall()

            if not blueprints:
                return {"status": "no_blueprints", "message": "No draft blueprints available"}

            # Schedule each blueprint with optimal timing
            scheduled = []
            base_time = datetime.utcnow() + timedelta(hours=1)  # Start in 1 hour

            for i, blueprint in enumerate(blueprints):
                # Stagger posting times (every 2 hours)
                scheduled_time = base_time + timedelta(hours=i * 2)

                schedule_request = ScheduleRequest(
                    blueprint_id=blueprint.blueprint_id,
                    scheduled_time=scheduled_time.isoformat(),
                    auto_post=True
                )

                try:
                    response = await schedule_blueprint(schedule_request)
                    scheduled.append({
                        "blueprint_id": blueprint.blueprint_id,
                        "title": blueprint.title,
                        "roi_score": blueprint.roi_score,
                        "scheduled_time": response.scheduled_time,
                        "post_id": response.post_id
                    })
                except Exception as e:
                    logger.warning(f"Failed to auto-schedule {blueprint.blueprint_id}: {e}")

            return {
                "status": "success",
                "scheduled_count": len(scheduled),
                "blueprints": scheduled
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Auto-scheduling failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/scheduled")
async def get_scheduled_posts():
    """Get list of scheduled posts."""
    try:
        async with get_db() as session:
            result = await session.execute("""
                SELECT
                    b.blueprint_id, b.title, b.scheduled_at,
                    b.predicted_views, b.roi_score,
                    t.title as trend_title, t.source
                FROM content_blueprints b
                JOIN trends t ON b.trend_id = t.id
                WHERE b.status = 'scheduled' AND b.scheduled_at > NOW()
                ORDER BY b.scheduled_at ASC
            """)

            scheduled = result.fetchall()

            posts = []
            for post in scheduled:
                posts.append({
                    "blueprint_id": post.blueprint_id,
                    "title": post.title,
                    "scheduled_at": post.scheduled_at.isoformat(),
                    "predicted_views": post.predicted_views,
                    "roi_score": post.roi_score,
                    "trend_title": post.trend_title,
                    "source": post.source
                })

            return {"scheduled_posts": posts, "total": len(posts)}

    except Exception as e:
        logger.error(f"Failed to get scheduled posts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _call_backend_schedule(post_data: Dict[str, Any]) -> Dict[str, Any]:
    """Call backend /schedule/post endpoint."""
    try:
        url = f"{settings.BACKEND_BASE_URL}/schedule/post"

        # Would need auth token here in production
        headers = {
            "Content-Type": "application/json",
            # "Authorization": f"Bearer {token}"
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=post_data,
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Backend schedule call failed: {response.status_code} - {response.text}")
                # Return mock response for now
                return {
                    "post_id": f"post_{post_data['metadata']['blueprint_id']}",
                    "status": "scheduled",
                    "scheduled_time": post_data["scheduled_time"],
                    "platform": post_data.get("platform", "instagram")
                }

    except Exception as e:
        logger.error(f"Backend schedule call error: {e}")
        # Return fallback response
        return {
            "post_id": f"fallback_{post_data['metadata']['blueprint_id']}",
            "status": "scheduled_fallback",
            "error": str(e)
        }
