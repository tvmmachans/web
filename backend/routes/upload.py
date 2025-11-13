from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from services.video_service import upload_video_service
from services.ai_service import generate_caption_service, generate_subtitles_service
from models.post import Post
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class UploadResponse(BaseModel):
    video_url: str
    thumbnail_url: str
    duration: float
    ai_caption: Optional[str] = None
    ai_subtitles: Optional[list] = None

@router.post("/video", response_model=UploadResponse)
async def upload_video(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload video, process it, generate AI caption and subtitles.
    """
    try:
        # Upload video to S3 and extract metadata
        upload_result = await upload_video_service(file)

        # Generate AI caption
        ai_caption = await generate_caption_service(file.filename, language="ml")

        # Generate subtitles
        ai_subtitles = await generate_subtitles_service(file.filename, language="ml")

        # Save to database
        new_post = Post(
            title=file.filename,
            video_url=upload_result["video_url"],
            thumbnail_url=upload_result["thumbnail_url"],
            duration=upload_result["duration"],
            ai_caption=ai_caption,
            ai_subtitles=ai_subtitles,
            platform="pending"  # Will be set when scheduled
        )
        db.add(new_post)
        await db.commit()
        await db.refresh(new_post)

        return UploadResponse(
            video_url=upload_result["video_url"],
            thumbnail_url=upload_result["thumbnail_url"],
            duration=upload_result["duration"],
            ai_caption=ai_caption,
            ai_subtitles=ai_subtitles
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
