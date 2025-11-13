# API Examples

## 1. Upload Video

```bash
curl -X POST "http://localhost:8000/upload/video" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/your/video.mp4"
```

Response:
```json
{
  "video_url": "https://social-media-videos.s3.amazonaws.com/videos/video.mp4",
  "thumbnail_url": "https://social-media-videos.s3.amazonaws.com/thumbnails/video_thumb.jpg",
  "duration": 45.67,
  "ai_caption": "നല്ലൊരു മലയാളം കോമഡി വീഡിയോ! 😂 #MalayalamComedy",
  "ai_subtitles": [
    {"start": 0.0, "end": 5.0, "text": "ഹലോ എല്ലാവർക്കും"},
    {"start": 5.0, "end": 10.0, "text": "ഇന്ന് ഒരു കോമഡി സ്റ്റോറി പറയാം"}
  ]
}
```

## 2. Generate Caption

```bash
curl -X POST "http://localhost:8000/generate/caption" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "College life comedy video",
    "language": "ml"
  }'
```

Response:
```json
{
  "caption": "കോളേജ് ജീവിതം മനസ്സിലാക്കാൻ നല്ലൊരു കോമഡി വീഡിയോ! 📚😂 #CollegeLife #MalayalamComedy"
}
```

## 3. Schedule Post

```bash
curl -X POST "http://localhost:8000/schedule/post" \
  -H "Content-Type: application/json" \
  -d '{
    "post_id": 1,
    "platform": "youtube",
    "scheduled_at": "2024-01-15T18:00:00Z",
    "title": "Malayalam Comedy - College Life",
    "description": "AI generated caption...",
    "tags": ["Malayalam", "Comedy", "College"]
  }'
```

Response:
```json
{
  "message": "Post scheduled for youtube at 2024-01-15T18:00:00Z",
  "job_id": "youtube_1_1705341600.0"
}
```

## 4. Get Analytics

```bash
curl -X GET "http://localhost:8000/analytics/?platform=youtube&days=30"
```

Response:
```json
[
  {
    "platform": "youtube",
    "total_posts": 5,
    "total_views": 12500,
    "total_likes": 890,
    "total_comments": 230,
    "engagement_rate": 0.15,
    "top_hashtags": ["#MalayalamComedy", "#CollegeLife"]
  }
]
```

## 5. Get Insights

```bash
curl -X GET "http://localhost:8000/analytics/insights"
```

Response:
```json
{
  "best_posting_times": ["18:00-20:00", "12:00-14:00"],
  "top_topics": ["Malayalam Comedy", "College Life", "Travel"],
  "caption_suggestions": [
    "നല്ലൊരു കോമഡി വീഡിയോ! 😂 #MalayalamComedy",
    "കോളേജ് ജീവിതം മനസ്സിലാക്കാൻ... 📚 #CollegeLife"
  ]
}
```

## 6. Upload to YouTube

```bash
curl -X POST "http://localhost:8000/youtube/upload" \
  -H "Content-Type: application/json" \
  -d '{
    "post_id": 1,
    "title": "Malayalam Comedy Video",
    "description": "AI generated description...",
    "tags": ["Malayalam", "Comedy"],
    "privacy_status": "private"
  }'
```

Response:
```json
{
  "video_id": "abc123def456",
  "video_url": "https://www.youtube.com/watch?v=abc123def456"
}
```

## 7. Upload to Instagram

```bash
curl -X POST "http://localhost:8000/instagram/upload" \
  -H "Content-Type: application/json" \
  -d '{
    "post_id": 1,
    "caption": "നല്ലൊരു മലയാളം റീൽ! #Malayalam #Comedy"
  }'
```

Response:
```json
{
  "post_id": "1789569566...",
  "media_url": "https://www.instagram.com/p/ABC123/"
}
```

## 8. Get Scheduled Jobs

```bash
curl -X GET "http://localhost:8000/schedule/jobs"
```

Response:
```json
{
  "jobs": [
    {
      "id": "youtube_1_1705341600.0",
      "next_run_time": "2024-01-15T18:00:00",
      "args": [1, "youtube", "Malayalam Comedy - College Life", "...", ["Malayalam", "Comedy"]]
    }
  ]
}
```

## 9. Cancel Scheduled Job

```bash
curl -X DELETE "http://localhost:8000/schedule/job/youtube_1_1705341600.0"
```

Response:
```json
{
  "message": "Job cancelled successfully"
}
