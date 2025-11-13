from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from services.ai_service import generate_caption_service, generate_subtitles_service
from pydantic import BaseModel
from typing import List, Dict, Optional

router = APIRouter()

class CaptionRequest(BaseModel):
    content: str
    language: Optional[str] = "ml"  # Default to Malayalam

class CaptionResponse(BaseModel):
    caption: str

class SubtitlesRequest(BaseModel):
    video_path: str
    language: Optional[str] = "ml"

class SubtitlesResponse(BaseModel):
    subtitles: List[Dict]

@router.post("/caption", response_model=CaptionResponse)
async def generate_caption(request: CaptionRequest):
    """
    Generate AI caption for given content.
    """
    try:
        caption = await generate_caption_service(request.content, request.language)
        return CaptionResponse(caption=caption)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/subtitles", response_model=SubtitlesResponse)
async def generate_subtitles(request: SubtitlesRequest):
    """
    Generate subtitles for video.
    """
    try:
        subtitles = await generate_subtitles_service(request.video_path, request.language)
        return SubtitlesResponse(subtitles=subtitles)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
