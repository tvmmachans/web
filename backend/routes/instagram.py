from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from services.instagram_service import upload_to_instagram, get_instagram_analytics
from database import Post, Analytics
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter()

class InstagramUploadRequest(BaseModel):
    post_id: int
    caption: str

class InstagramUploadResponse(BaseModel):
    post_id: str
    media_url: str

@router.post("/upload", response_model=InstagramUploadResponse)
async def upload_reel_to_instagram(
    request: InstagramUploadRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Upload video as Reel to Instagram.
    """
    try:
        # Get post from database
        post = await db.get(Post, request.post_id)
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        # Upload to Instagram
        result = await upload_to_instagram(
            video_path=post.video_url,
            caption=request.caption
        )

        # Update post status
        post.status = "posted"
        post.posted_at = datetime.utcnow()

        # Create analytics entry
        analytics = Analytics(
            post_id=post.id,
            platform="instagram",
            views=0,
            likes=0,
            comments=0
        )
        db.add(analytics)
        await db.commit()

        return InstagramUploadResponse(
            post_id=result.get("id"),
            media_url=f"https://www.instagram.com/p/{result.get('id')}/"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/{post_id}")
async def get_instagram_post_analytics(post_id: str):
    """
    Get analytics for an Instagram post.
    """
    try:
        analytics = await get_instagram_analytics(post_id)
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
