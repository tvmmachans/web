"""
Smart Publisher - Complete autonomous publishing system.
Handles platform management, scheduling, caption generation, and hashtag optimization.
"""

import asyncio
import logging
import os
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import json

from openai import OpenAI
import httpx

from agent.config.settings import OPENAI_MODEL

logger = logging.getLogger(__name__)


class PlatformManager:
    """Handles YouTube & Instagram APIs for publishing."""

    def __init__(self):
        self.youtube_api_key = os.getenv("YOUTUBE_API_KEY")
        self.youtube_oauth_token = os.getenv("YOUTUBE_OAUTH_TOKEN")
        self.instagram_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
        self.instagram_account_id = os.getenv("INSTAGRAM_ACCOUNT_ID")

    async def publish_to_youtube(
        self,
        video_url: str,
        title: str,
        description: str,
        thumbnail_url: str,
        tags: List[str],
        scheduled_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Publish video to YouTube."""
        try:
            # YouTube Data API v3 - Upload video
            # Note: This is simplified - real implementation needs OAuth flow
            async with httpx.AsyncClient(timeout=300) as client:
                # First, upload video file
                upload_response = await self._upload_video_file(
                    video_url, title, description
                )

                if upload_response.get("video_id"):
                    # Set thumbnail
                    if thumbnail_url:
                        await self._set_thumbnail(
                            upload_response["video_id"], thumbnail_url
                        )

                    # Schedule if needed
                    if scheduled_time:
                        await self._schedule_video(
                            upload_response["video_id"], scheduled_time
                        )

                    return {
                        "platform": "youtube",
                        "video_id": upload_response["video_id"],
                        "url": f"https://www.youtube.com/watch?v={upload_response['video_id']}",
                        "status": "published" if not scheduled_time else "scheduled",
                        "scheduled_time": (
                            scheduled_time.isoformat() if scheduled_time else None
                        ),
                    }

        except Exception as e:
            logger.error(f"YouTube publishing failed: {e}")
            return {"platform": "youtube", "status": "failed", "error": str(e)}

    async def publish_to_instagram(
        self,
        video_url: str,
        caption: str,
        thumbnail_url: str,
        scheduled_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Publish video/reel to Instagram."""
        try:
            # Instagram Graph API - Upload Reel
            async with httpx.AsyncClient(timeout=300) as client:
                # Step 1: Create container
                container_response = await client.post(
                    f"https://graph.instagram.com/v18.0/{self.instagram_account_id}/media",
                    params={
                        "media_type": "REELS",
                        "video_url": video_url,
                        "caption": caption,
                        "access_token": self.instagram_token,
                    },
                )

                if container_response.status_code == 200:
                    container_id = container_response.json().get("id")

                    # Step 2: Publish container
                    publish_response = await client.post(
                        f"https://graph.instagram.com/v18.0/{self.instagram_account_id}/media_publish",
                        params={
                            "creation_id": container_id,
                            "access_token": self.instagram_token,
                        },
                    )

                    if publish_response.status_code == 200:
                        media_id = publish_response.json().get("id")

                        return {
                            "platform": "instagram",
                            "media_id": media_id,
                            "url": f"https://www.instagram.com/reel/{media_id}",
                            "status": "published",
                        }

        except Exception as e:
            logger.error(f"Instagram publishing failed: {e}")
            return {"platform": "instagram", "status": "failed", "error": str(e)}

    async def _upload_video_file(
        self, video_url: str, title: str, description: str
    ) -> Dict[str, Any]:
        """Upload video file to YouTube."""
        # This is a placeholder - real implementation needs OAuth and resumable upload
        # Would need to download video, then upload using YouTube API
        return {"video_id": "placeholder_video_id"}

    async def _set_thumbnail(self, video_id: str, thumbnail_url: str) -> bool:
        """Set video thumbnail."""
        # Placeholder - would use YouTube API
        return True

    async def _schedule_video(self, video_id: str, scheduled_time: datetime) -> bool:
        """Schedule video for later publishing."""
        # Placeholder - would use YouTube API scheduling
        return True


class SchedulingEngine:
    """Finds perfect posting times for maximum views."""

    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def find_optimal_time(
        self,
        platform: str,
        content_category: str,
        analytics_data: Optional[Dict[str, Any]] = None,
    ) -> datetime:
        """Find optimal posting time based on analytics and AI."""
        try:
            # Get historical analytics
            if not analytics_data:
                analytics_data = await self._get_historical_analytics(platform)

            # Use AI to determine best time
            prompt = f"""Based on this analytics data, determine the optimal posting time for a {content_category} video on {platform}.

Analytics:
{json.dumps(analytics_data, indent=2)}

Consider:
- Peak engagement hours
- Audience timezone (IST for Malayalam content)
- Day of week patterns
- Content category performance

Respond with just the hour (0-23) and day offset (0-6) in JSON format:
{{"hour": 18, "day_offset": 0}}"""

            response = self.openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=0.3,
            )

            result_text = response.choices[0].message.content.strip()
            result = json.loads(result_text)

            # Calculate datetime
            now = datetime.utcnow()
            target_date = now + timedelta(days=result.get("day_offset", 0))
            target_time = target_date.replace(
                hour=result.get("hour", 18), minute=0, second=0, microsecond=0
            )

            # If time has passed today, schedule for tomorrow
            if target_time <= now:
                target_time += timedelta(days=1)

            return target_time

        except Exception as e:
            logger.error(f"Optimal time calculation failed: {e}")
            # Fallback to default best times
            return self._get_default_optimal_time()

    async def _get_historical_analytics(self, platform: str) -> Dict[str, Any]:
        """Get historical analytics data."""
        # This would query the database for past performance
        return {
            "peak_hours": [9, 12, 18, 20],
            "best_days": ["Monday", "Wednesday", "Friday"],
            "avg_engagement": 0.05,
        }

    def _get_default_optimal_time(self) -> datetime:
        """Get default optimal posting time."""
        now = datetime.utcnow()
        # Default: 6 PM IST (12:30 PM UTC)
        target = now.replace(hour=12, minute=30, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
        return target


class CaptionGenerator:
    """Writes engaging captions in Malayalam + English."""

    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def generate_caption(
        self,
        script: Dict[str, Any],
        platform: str,
        include_hashtags: bool = True,
        languages: List[str] = ["ml", "en"],
    ) -> Dict[str, Any]:
        """Generate engaging caption for platform."""
        try:
            hook = script.get("hook_line", "")
            title = script.get("title", "")

            prompt = f"""Write an engaging social media caption for {platform} in both Malayalam and English.

Title: {title}
Hook: {hook}
Platform: {platform}

Requirements:
- Start with an attention-grabbing hook
- Include key points from the content
- Add relevant emojis
- Include call-to-action
- {"Include hashtags" if include_hashtags else "No hashtags"}
- Keep it platform-appropriate length ({'short' if platform == 'instagram' else 'medium'})

Format as JSON:
{{
  "malayalam": "Malayalam caption text",
  "english": "English caption text",
  "combined": "Bilingual caption",
  "hashtags": ["hashtag1", "hashtag2"]
}}"""

            response = self.openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.7,
            )

            content = response.choices[0].message.content.strip()

            # Parse JSON
            try:
                json_match = re.search(r"\{.*\}", content, re.DOTALL)
                if json_match:
                    caption = json.loads(json_match.group())
                else:
                    caption = self._generate_fallback_caption(script, platform)
            except:
                caption = self._generate_fallback_caption(script, platform)

            return caption

        except Exception as e:
            logger.error(f"Caption generation failed: {e}")
            return self._generate_fallback_caption(script, platform)

    def _generate_fallback_caption(
        self, script: Dict[str, Any], platform: str
    ) -> Dict[str, Any]:
        """Generate fallback caption."""
        hook = script.get("hook_line", "വിസ്മയം!")
        return {
            "malayalam": f"{hook} നിങ്ങൾക്ക് ഇഷ്ടമാകും!",
            "english": f"{hook} You'll love this!",
            "combined": f"{hook} നിങ്ങൾക്ക് ഇഷ്ടമാകും! You'll love this!",
            "hashtags": ["malayalam", "trending", "shorts"],
        }


class HashtagOptimizer:
    """Creates trending hashtag combinations."""

    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def generate_hashtags(
        self,
        content: Dict[str, Any],
        platform: str,
        count: int = 10,
    ) -> List[str]:
        """Generate optimized hashtags."""
        try:
            title = content.get("title", "")
            category = content.get("category", "general")
            script = content.get("script", {})

            prompt = f"""Generate {count} trending hashtags for this Malayalam content on {platform}.

Title: {title}
Category: {category}
Content: {script.get('hook_line', '')}

Requirements:
- Mix of Malayalam and English hashtags
- Include trending tags
- Platform-specific ({platform})
- Mix of broad and niche tags
- Include location tags (Kerala, Malayalam)

Return as JSON array: ["hashtag1", "hashtag2", ...]"""

            response = self.openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.8,
            )

            content_text = response.choices[0].message.content.strip()

            # Parse JSON
            try:
                json_match = re.search(r"\[.*\]", content_text, re.DOTALL)
                if json_match:
                    hashtags = json.loads(json_match.group())
                else:
                    hashtags = self._generate_fallback_hashtags(category, platform)
            except:
                hashtags = self._generate_fallback_hashtags(category, platform)

            return hashtags[:count]

        except Exception as e:
            logger.error(f"Hashtag generation failed: {e}")
            return self._generate_fallback_hashtags(
                content.get("category", "general"), platform
            )

    def _generate_fallback_hashtags(self, category: str, platform: str) -> List[str]:
        """Generate fallback hashtags."""
        base_tags = ["malayalam", "kerala", "trending", "shorts", "reels"]
        category_tags = {
            "entertainment": ["entertainment", "comedy", "funny"],
            "sports": ["sports", "cricket", "football"],
            "lifestyle": ["lifestyle", "food", "travel"],
        }

        tags = base_tags + category_tags.get(category, [])
        return tags[:10]


class SmartPublisher:
    """Main orchestrator for Smart Publisher module."""

    def __init__(self):
        self.platform_manager = PlatformManager()
        self.scheduling_engine = SchedulingEngine()
        self.caption_generator = CaptionGenerator()
        self.hashtag_optimizer = HashtagOptimizer()

    async def publish_content(
        self,
        video_data: Dict[str, Any],
        platforms: List[str] = ["youtube", "instagram"],
        auto_schedule: bool = True,
    ) -> Dict[str, Any]:
        """Publish content to multiple platforms."""
        results = {}

        for platform in platforms:
            try:
                # Generate caption
                caption = await self.caption_generator.generate_caption(
                    video_data.get("script", {}), platform
                )

                # Generate hashtags
                hashtags = await self.hashtag_optimizer.generate_hashtags(
                    video_data, platform
                )

                # Find optimal time
                scheduled_time = None
                if auto_schedule:
                    scheduled_time = await self.scheduling_engine.find_optimal_time(
                        platform, video_data.get("category", "general")
                    )

                # Publish
                if platform == "youtube":
                    result = await self.platform_manager.publish_to_youtube(
                        video_data.get("video_url"),
                        video_data.get("title", ""),
                        caption.get("combined", ""),
                        video_data.get("thumbnail_url"),
                        hashtags,
                        scheduled_time,
                    )
                elif platform == "instagram":
                    instagram_caption = f"{caption.get('combined', '')} {' '.join(['#' + h for h in hashtags])}"
                    result = await self.platform_manager.publish_to_instagram(
                        video_data.get("video_url"),
                        instagram_caption,
                        video_data.get("thumbnail_url"),
                        scheduled_time,
                    )
                else:
                    result = {"platform": platform, "status": "unsupported"}

                results[platform] = result

            except Exception as e:
                logger.error(f"Publishing to {platform} failed: {e}")
                results[platform] = {
                    "platform": platform,
                    "status": "failed",
                    "error": str(e),
                }

        return {
            "publish_results": results,
            "published_at": datetime.utcnow().isoformat(),
        }
