"""
Content generation routes.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from orchestrator.services.content_generation import ContentGenerationService
from orchestrator.database.session import get_db
from orchestrator.database.models import Trend, ContentBlueprint

logger = logging.getLogger(__name__)

router = APIRouter()
generation_service = ContentGenerationService()

class GenerateRequest(BaseModel):
    trend_id: int
    source_video_url: Optional[str] = None

class BlueprintResponse(BaseModel):
    blueprint: Dict[str, Any]
    validation: Dict[str, Any]

@router.post("/generate", response_model=BlueprintResponse)
async def generate_blueprint(request: GenerateRequest, background_tasks: BackgroundTasks):
    """Generate content blueprint for a trend."""
    try:
        # Get trend data
        async with get_db() as session:
            result = await session.execute("""
                SELECT id, trend_id, title, description, source, source_url,
                       velocity, trend_strength, tags, metadata
                FROM trends WHERE id = :trend_id
            """, {"trend_id": request.trend_id})

            trend_row = result.first()
            if not trend_row:
                raise HTTPException(status_code=404, detail="Trend not found")

            trend_data = {
                "id": trend_row.id,
                "trend_id": trend_row.trend_id,
                "title": trend_row.title,
                "description": trend_row.description,
                "source": trend_row.source,
                "source_url": trend_row.source_url,
                "velocity": trend_row.velocity,
                "trend_strength": trend_row.trend_strength,
                "tags": trend_row.tags,
                "metadata": trend_row.metadata
            }

        # Generate blueprint
        blueprint = await generation_service.generate_blueprint(
            trend_data, request.source_video_url
        )

        # Validate content
        validation = await generation_service.validate_content(blueprint)

        # Save blueprint to database in background
        background_tasks.add_task(_save_blueprint_background, blueprint)

        return BlueprintResponse(
            blueprint=blueprint,
            validation=validation
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Blueprint generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/blueprints")
async def get_blueprints(limit: int = 20, status: Optional[str] = None):
    """Get list of generated blueprints."""
    try:
        async with get_db() as session:
            query = """
                SELECT
                    b.id, b.blueprint_id, b.title, b.status, b.roi_score,
                    b.predicted_views, b.confidence_score, b.created_at,
                    t.title as trend_title, t.source
                FROM content_blueprints b
                JOIN trends t ON b.trend_id = t.id
            """

            params = {}
            if status:
                query += " WHERE b.status = :status"
                params["status"] = status

            query += " ORDER BY b.roi_score DESC, b.created_at DESC LIMIT :limit"
            params["limit"] = limit

            result = await session.execute(query, params)
            rows = result.fetchall()

            blueprints = []
            for row in rows:
                blueprint = {
                    "id": row.id,
                    "blueprint_id": row.blueprint_id,
                    "title": row.title,
                    "status": row.status,
                    "roi_score": row.roi_score,
                    "predicted_views": row.predicted_views,
                    "confidence_score": row.confidence_score,
                    "created_at": row.created_at.isoformat(),
                    "trend_title": row.trend_title,
                    "source": row.source
                }
                blueprints.append(blueprint)

            return {"blueprints": blueprints, "total": len(blueprints)}

    except Exception as e:
        logger.error(f"Failed to get blueprints: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/blueprint/{blueprint_id}")
async def get_blueprint_details(blueprint_id: str):
    """Get detailed blueprint information."""
    try:
        async with get_db() as session:
            result = await session.execute("""
                SELECT
                    b.*, t.title as trend_title, t.description as trend_description
                FROM content_blueprints b
                JOIN trends t ON b.trend_id = t.id
                WHERE b.blueprint_id = :blueprint_id
            """, {"blueprint_id": blueprint_id})

            row = result.first()
            if not row:
                raise HTTPException(status_code=404, detail="Blueprint not found")

            blueprint = {
                "id": row.id,
                "blueprint_id": row.blueprint_id,
                "trend_id": row.trend_id,
                "title": row.title,
                "hook": row.hook,
                "script": row.script,
                "voiceover_text": row.voiceover_text,
                "captions": row.captions,
                "hashtags": row.hashtags,
                "video_url": row.video_url,
                "clip_timestamps": row.clip_timestamps,
                "audio_url": row.audio_url,
                "thumbnail_prompt": row.thumbnail_prompt,
                "predicted_views": row.predicted_views,
                "predicted_likes": row.predicted_likes,
                "predicted_ctr": row.predicted_ctr,
                "confidence_score": row.confidence_score,
                "roi_score": row.roi_score,
                "status": row.status,
                "created_at": row.created_at.isoformat(),
                "trend_title": row.trend_title,
                "trend_description": row.trend_description
            }

            return blueprint

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get blueprint details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _save_blueprint_background(blueprint: Dict[str, Any]):
    """Background task to save blueprint to database."""
    try:
        async with get_db() as session:
            # Create blueprint record
            db_blueprint = ContentBlueprint(
                blueprint_id=blueprint["blueprint_id"],
                trend_id=blueprint["trend_id"],
                title=blueprint["title"],
                hook=blueprint.get("hook"),
                script=blueprint.get("script"),
                voiceover_text=blueprint.get("voiceover_text"),
                captions=blueprint.get("captions", []),
                hashtags=blueprint.get("hashtags", []),
                video_url=blueprint.get("video_url"),
                clip_timestamps=blueprint.get("clip_timestamps", []),
                audio_url=blueprint.get("audio_url"),
                thumbnail_prompt=blueprint.get("thumbnail_prompt"),
                predicted_views=blueprint.get("predicted_views"),
                predicted_likes=blueprint.get("predicted_likes"),
                predicted_ctr=blueprint.get("predicted_ctr"),
                confidence_score=blueprint.get("confidence_score"),
                roi_score=blueprint.get("roi_score"),
                generation_params=blueprint.get("generation_params", {}),
                status="draft"
            )

            session.add(db_blueprint)
            await session.commit()

            logger.info(f"Saved blueprint {blueprint['blueprint_id']} to database")

    except Exception as e:
        logger.error(f"Failed to save blueprint to database: {e}")
