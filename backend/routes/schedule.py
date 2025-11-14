from datetime import datetime
from typing import Optional

import scheduler
from database import Post, get_db
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


class ScheduleRequest(BaseModel):
    post_id: int
    platform: str  # "youtube" or "instagram"
    scheduled_at: datetime
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[list] = None


class ScheduleResponse(BaseModel):
    message: str
    job_id: str


@router.post("/post", response_model=ScheduleResponse)
async def schedule_post(request: ScheduleRequest, db: AsyncSession = Depends(get_db)):
    """
    Schedule a post for upload to YouTube or Instagram.
    """
    try:
        # Get post from database
        post = await db.get(Post, request.post_id)
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        # Update post details
        post.platform = request.platform
        post.scheduled_at = request.scheduled_at
        post.status = "scheduled"
        if request.title:
            post.title = request.title
        if request.description:
            post.description = request.description

        await db.commit()

        # Schedule the job
        job_id = scheduler.schedule_upload(
            post_id=request.post_id,
            platform=request.platform,
            scheduled_time=request.scheduled_at,
            title=request.title or post.title,
            description=request.description or post.ai_caption,
            tags=request.tags,
        )

        return ScheduleResponse(
            message=f"Post scheduled for {request.platform} at {request.scheduled_at}",
            job_id=job_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs")
async def get_scheduled_jobs():
    """
    Get list of scheduled jobs.
    """
    try:
        jobs = scheduler.get_scheduled_jobs()
        return {"jobs": jobs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/job/{job_id}")
async def cancel_scheduled_job(job_id: str):
    """
    Cancel a scheduled job.
    """
    try:
        success = scheduler.cancel_job(job_id)
        if success:
            return {"message": "Job cancelled successfully"}
        else:
            raise HTTPException(status_code=404, detail="Job not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
