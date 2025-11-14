import os
import tempfile
from datetime import datetime, timedelta
from typing import Tuple

import boto3
from fastapi import HTTPException, UploadFile
from moviepy.editor import VideoFileClip

S3_BUCKET = os.getenv("AWS_S3_BUCKET_NAME", "social-media-videos")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION,
)


async def upload_video_service(file: UploadFile) -> dict:
    """
    Upload video to S3, extract metadata, generate thumbnail.
    Returns dict with video_url, thumbnail_url, duration.
    """
    if not file.filename.lower().endswith((".mp4", ".avi", ".mov", ".mkv")):
        raise HTTPException(status_code=400, detail="Unsupported file format")

    # Save file temporarily
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=os.path.splitext(file.filename)[1]
    ) as temp_file:
        temp_file.write(await file.read())
        temp_path = temp_file.name

    try:
        # Extract metadata
        duration, thumbnail_path = extract_video_metadata(temp_path)

        # Upload video to S3 with signed URL
        video_key = f"videos/{file.filename}"
        s3_client.upload_file(temp_path, S3_BUCKET, video_key)
        video_url = generate_signed_url(S3_BUCKET, video_key)

        # Upload thumbnail to S3 with signed URL
        thumbnail_key = f"thumbnails/{os.path.splitext(file.filename)[0]}.jpg"
        s3_client.upload_file(thumbnail_path, S3_BUCKET, thumbnail_key)
        thumbnail_url = generate_signed_url(S3_BUCKET, thumbnail_key)

        return {
            "video_url": video_url,
            "thumbnail_url": thumbnail_url,
            "duration": duration,
        }
    finally:
        # Clean up temp files
        os.unlink(temp_path)
        if "thumbnail_path" in locals():
            os.unlink(thumbnail_path)


def extract_video_metadata(video_path: str) -> Tuple[float, str]:
    """
    Extract duration and generate thumbnail from video.
    Returns (duration, thumbnail_path).
    """
    clip = VideoFileClip(video_path)
    duration = clip.duration

    # Generate thumbnail at 1 second
    thumbnail_time = min(1, duration / 2)
    thumbnail_path = video_path.replace(os.path.splitext(video_path)[1], "_thumb.jpg")
    clip.save_frame(thumbnail_path, t=thumbnail_time)

    clip.close()
    return duration, thumbnail_path


def generate_signed_url(bucket: str, key: str, expiration: int = 3600) -> str:
    """
    Generate a signed URL for S3 object access.
    Expiration is in seconds (default 1 hour).
    """
    try:
        url = s3_client.generate_presigned_url(
            "get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=expiration
        )
        return url
    except Exception as e:
        # Fallback to public URL if signing fails
        return f"https://{bucket}.s3.{AWS_REGION}.amazonaws.com/{key}"
