"""
Discovery routes for trend ingestion.
"""

import logging
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from orchestrator.services.trend_ingestion import TrendIngestionService
from orchestrator.database.session import get_db
from orchestrator.database.models import Trend, DiscoveryRun

logger = logging.getLogger(__name__)

router = APIRouter()
trend_service = TrendIngestionService()

class DiscoveryResponse(BaseModel):
    status: str
    trends_found: int
    run_id: str
    duration_seconds: float

class TrendsList(BaseModel):
    trends: List[Dict[str, Any]]
    total: int

@router.post("/run_once", response_model=DiscoveryResponse)
async def run_discovery_once(background_tasks: BackgroundTasks):
    """Run one complete discovery cycle."""
    import time
    import uuid
    from datetime import datetime

    run_id = str(uuid.uuid4())
    start_time = time.time()

    try:
        logger.info(f"Starting discovery run {run_id}")

        # Create discovery run record
        async with get_db() as session:
            run_record = DiscoveryRun(
                run_id=run_id,
                status="running",
                started_at=datetime.utcnow()
            )
            session.add(run_record)
            await session.commit()

        # Run discovery in background
        background_tasks.add_task(_run_discovery_background, run_id)

        return DiscoveryResponse(
            status="started",
            trends_found=0,  # Will be updated when complete
            run_id=run_id,
            duration_seconds=0.0
        )

    except Exception as e:
        logger.error(f"Discovery run failed to start: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_discovery_status():
    """Get current discovery status and last run stats."""
    try:
        async with get_db() as session:
            # Get latest run
            result = await session.execute("""
                SELECT * FROM discovery_runs
                ORDER BY started_at DESC
                LIMIT 1
            """)
            last_run = result.first()

            # Get trend counts by source
            result = await session.execute("""
                SELECT source, COUNT(*) as count
                FROM trends
                WHERE discovered_at > NOW() - INTERVAL '24 hours'
                GROUP BY source
            """)
            recent_trends = result.fetchall()

            status = {
                "last_run": {
                    "run_id": last_run.run_id if last_run else None,
                    "status": last_run.status if last_run else "never",
                    "started_at": last_run.started_at.isoformat() if last_run else None,
                    "completed_at": last_run.completed_at.isoformat() if last_run and last_run.completed_at else None,
                    "trends_discovered": last_run.trends_discovered if last_run else 0,
                    "duration_seconds": last_run.duration_seconds if last_run else 0
                },
                "recent_trends": {row.source: row.count for row in recent_trends},
                "next_scheduled": "30 minutes"  # Would be dynamic
            }

            return status

    except Exception as e:
        logger.error(f"Failed to get discovery status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trends", response_model=TrendsList)
async def get_current_trends(limit: int = 50, min_score: float = 0.0):
    """Get list of current discovered trends."""
    try:
        async with get_db() as session:
            result = await session.execute("""
                SELECT
                    id, trend_id, title, description, source, source_url,
                    velocity, trend_strength, tags, discovered_at,
                    cross_platform_count
                FROM trends
                WHERE trend_strength >= :min_score
                ORDER BY trend_strength DESC, discovered_at DESC
                LIMIT :limit
            """, {"min_score": min_score, "limit": limit})

            trends = result.fetchall()

            trend_list = []
            for trend in trends:
                trend_dict = {
                    "id": trend.id,
                    "trend_id": trend.trend_id,
                    "title": trend.title,
                    "description": trend.description,
                    "source": trend.source,
                    "source_url": trend.source_url,
                    "velocity": trend.velocity,
                    "trend_strength": trend.trend_strength,
                    "tags": trend.tags or [],
                    "discovered_at": trend.discovered_at.isoformat(),
                    "cross_platform_count": trend.cross_platform_count
                }
                trend_list.append(trend_dict)

            return TrendsList(trends=trend_list, total=len(trend_list))

    except Exception as e:
        logger.error(f"Failed to get trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _run_discovery_background(run_id: str):
    """Background task to run discovery."""
    import time
    from datetime import datetime

    start_time = time.time()

    try:
        logger.info(f"Running discovery in background for {run_id}")

        # Run discovery
        candidates = await trend_service.discover_trends()

        # Save to database
        await trend_service.save_trends_to_db(candidates)

        duration = time.time() - start_time

        # Update run record
        async with get_db() as session:
            await session.execute("""
                UPDATE discovery_runs
                SET status = 'completed',
                    completed_at = :completed_at,
                    trends_discovered = :count,
                    duration_seconds = :duration
                WHERE run_id = :run_id
            """, {
                "completed_at": datetime.utcnow(),
                "count": len(candidates),
                "duration": duration,
                "run_id": run_id
            })
            await session.commit()

        logger.info(f"Discovery completed for {run_id}: {len(candidates)} trends found in {duration:.2f}s")

    except Exception as e:
        logger.error(f"Discovery background task failed for {run_id}: {e}")

        # Update run record with error
        async with get_db() as session:
            await session.execute("""
                UPDATE discovery_runs
                SET status = 'failed',
                    completed_at = :completed_at,
                    error_message = :error
                WHERE run_id = :run_id
            """, {
                "completed_at": datetime.utcnow(),
                "error": str(e),
                "run_id": run_id
            })
            await session.commit()
