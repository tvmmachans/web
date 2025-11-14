import os
import tempfile
from datetime import datetime
from typing import List, Optional

from database import Analytics, Post, get_db
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from services.youtube_service import upload_to_youtube
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


class YouTubeUploadRequest(BaseModel):
    post_id: int
    title: str
    description: str
    tags: Optional[List[str]] = None
    privacy_status: Optional[str] = "private"


class YouTubeUploadResponse(BaseModel):
    video_id: str
    video_url: str


@router.post("/upload", response_model=YouTubeUploadResponse)
async def upload_video_to_youtube(
    request: YouTubeUploadRequest, db: AsyncSession = Depends(get_db)
):
    """
    Upload video directly to YouTube.
    """
    try:
        # Get post from database
        post = await db.get(Post, request.post_id)
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        # Download video from S3 temporarily
        import requests

        response = requests.get(post.video_url)
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to download video")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
            temp_file.write(response.content)
            temp_path = temp_file.name

        try:
            # Upload to YouTube
            video_id = await upload_to_youtube(
                video_path=temp_path,
                title=request.title,
                description=request.description,
                tags=request.tags,
            )

            # Update post status
            post.status = "posted"
            post.posted_at = datetime.utcnow()

            # Create analytics entry
            analytics = Analytics(
                post_id=post.id, platform="youtube", views=0, likes=0, comments=0
            )
            db.add(analytics)
            await db.commit()

            video_url = f"https://www.youtube.com/watch?v={video_id}"

            return YouTubeUploadResponse(video_id=video_id, video_url=video_url)
        finally:
            os.unlink(temp_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/{video_id}")
async def get_youtube_analytics(video_id: str):
    """
    Get analytics for a YouTube video.
    """
    try:
        # This would integrate with YouTube Analytics API
        # For now, return mock data
        return {
            "video_id": video_id,
            "views": 12500,
            "likes": 890,
            "comments": 230,
            "subscribers_gained": 45,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
