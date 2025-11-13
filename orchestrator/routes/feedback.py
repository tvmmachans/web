"""
Feedback and performance tracking routes.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime

from orchestrator.database.session import get_db
from orchestrator.database.models import PerformanceData, ContentBlueprint

logger = logging.getLogger(__name__)

router = APIRouter()

class PerformanceUpdate(BaseModel):
    blueprint_id: str
    actual_views: int
    actual_likes: int = 0
    actual_comments: int = 0
    actual_shares: int = 0
    watch_time: float = 0.0
    ctr: float = 0.0
    post_url: str
    platform: str = "instagram"

class FeedbackRequest(BaseModel):
    blueprint_id: str
    rating: int  # 1-5 scale
    feedback: str = ""
    approved: bool = True

@router.post("/performance")
async def update_performance(data: PerformanceUpdate):
    """Update actual performance metrics for a posted blueprint."""
    try:
        async with get_db() as session:
            # Get blueprint
            result = await session.execute("""
                SELECT id FROM content_blueprints WHERE blueprint_id = :blueprint_id
            """, {"blueprint_id": data.blueprint_id})

            blueprint = result.first()
            if not blueprint:
                raise HTTPException(status_code=404, detail="Blueprint not found")

            # Create performance record
            performance = PerformanceData(
                blueprint_id=blueprint.id,
                actual_views=data.actual_views,
                actual_likes=data.actual_likes,
                actual_comments=data.actual_comments,
                actual_shares=data.actual_shares,
                watch_time=data.watch_time,
                ctr=data.ctr,
                post_url=data.post_url,
                platform=data.platform,
                collected_at=datetime.utcnow()
            )

            # Calculate derived metrics
            performance.engagement_rate = (data.actual_likes + data.actual_comments + data.actual_shares) / max(data.actual_views, 1)
            performance.viral_coefficient = performance.engagement_rate * 1.5  # Simplified

            session.add(performance)

            # Update blueprint status
            await session.execute("""
                UPDATE content_blueprints
                SET status = 'posted', posted_at = :posted_at
                WHERE id = :blueprint_id
            """, {
                "posted_at": datetime.utcnow(),
                "blueprint_id": blueprint.id
            })

            await session.commit()

            return {
                "status": "updated",
                "engagement_rate": performance.engagement_rate,
                "viral_coefficient": performance.viral_coefficient
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Performance update failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/feedback")
async def submit_feedback(data: FeedbackRequest):
    """Submit human feedback on generated blueprint."""
    try:
        async with get_db() as session:
            # Update blueprint status based on feedback
            new_status = "approved" if data.approved else "rejected"

            await session.execute("""
                UPDATE content_blueprints
                SET status = :status, updated_at = :updated_at
                WHERE blueprint_id = :blueprint_id
            """, {
                "status": new_status,
                "updated_at": datetime.utcnow(),
                "blueprint_id": data.blueprint_id
            })

            await session.commit()

            return {
                "status": "feedback_recorded",
                "new_status": new_status,
                "rating": data.rating
            }

    except Exception as e:
        logger.error(f"Feedback submission failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics")
async def get_orchestrator_analytics(days: int = 7):
    """Get analytics on orchestrator performance."""
    try:
        async with get_db() as session:
            # Get performance metrics
            result = await session.execute("""
                SELECT
                    COUNT(*) as total_blueprints,
                    AVG(predicted_views) as avg_predicted_views,
                    AVG(actual_views) as avg_actual_views,
                    AVG(roi_score) as avg_roi_score,
                    COUNT(CASE WHEN status = 'approved' THEN 1 END) as approved_count,
                    COUNT(CASE WHEN status = 'posted' THEN 1 END) as posted_count
                FROM content_blueprints b
                LEFT JOIN performance_data p ON b.id = p.blueprint_id
                WHERE b.created_at > NOW() - INTERVAL ':days days'
            """, {"days": days})

            metrics = result.first()

            # Get trend discovery stats
            result = await session.execute("""
                SELECT
                    COUNT(*) as trends_discovered,
                    COUNT(DISTINCT source) as sources_used,
                    AVG(trend_strength) as avg_trend_strength
                FROM trends
                WHERE discovered_at > NOW() - INTERVAL ':days days'
            """, {"days": days})

            trend_stats = result.first()

            analytics = {
                "period_days": days,
                "blueprints": {
                    "total_generated": metrics.total_blueprints or 0,
                    "approved_rate": (metrics.approved_count or 0) / max(metrics.total_blueprints or 1, 1),
                    "posted_rate": (metrics.posted_count or 0) / max(metrics.total_blueprints or 1, 1),
                    "avg_predicted_views": metrics.avg_predicted_views or 0,
                    "avg_actual_views": metrics.avg_actual_views or 0,
                    "avg_roi_score": metrics.avg_roi_score or 0
                },
                "trends": {
                    "discovered": trend_stats.trends_discovered or 0,
                    "sources_used": trend_stats.sources_used or 0,
                    "avg_trend_strength": trend_stats.avg_trend_strength or 0
                },
                "performance": {
                    "prediction_accuracy": _calculate_prediction_accuracy(metrics),
                    "content_quality_score": _calculate_quality_score(metrics)
                }
            }

            return analytics

    except Exception as e:
        logger.error(f"Analytics retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def _calculate_prediction_accuracy(metrics) -> float:
    """Calculate prediction accuracy from metrics."""
    if not metrics.avg_actual_views or not metrics.avg_predicted_views:
        return 0.0

    # Simple accuracy metric (1 - MAPE)
    mape = abs(metrics.avg_actual_views - metrics.avg_predicted_views) / max(metrics.avg_actual_views, 1)
    return max(0, 1 - mape)

def _calculate_quality_score(metrics) -> float:
    """Calculate content quality score."""
    # Based on approval rate and engagement
    approval_score = (metrics.approved_count or 0) / max(metrics.total_blueprints or 1, 1)
    engagement_score = min(1.0, (metrics.avg_actual_views or 0) / 10000)  # Normalize to 10k views

    return (approval_score + engagement_score) / 2
