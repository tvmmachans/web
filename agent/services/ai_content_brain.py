"""
AI Content Brain - Complete autonomous content discovery and planning system.
Handles trend detection, idea generation, script writing, and content calendar creation.
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

from agent.config.settings import OPENAI_MODEL, MALAYALAM_KEYWORDS, CONTENT_CATEGORIES

logger = logging.getLogger(__name__)


class TrendDetector:
    """Scans YouTube/Instagram/Twitter for trending Malayalam topics."""

    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.youtube_api_key = os.getenv("YOUTUBE_API_KEY")
        self.instagram_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
        self.twitter_bearer = os.getenv("TWITTER_BEARER_TOKEN")

    async def scan_trends(
        self, platforms: List[str] = ["youtube", "instagram"]
    ) -> List[Dict[str, Any]]:
        """Scan multiple platforms for trending topics."""
        all_trends = []

        for platform in platforms:
            try:
                if platform == "youtube":
                    trends = await self._scan_youtube_trends()
                elif platform == "instagram":
                    trends = await self._scan_instagram_trends()
                elif platform == "twitter":
                    trends = await self._scan_twitter_trends()
                else:
                    continue

                # Filter for Malayalam content
                malayalam_trends = [t for t in trends if self._is_malayalam_content(t)]
                all_trends.extend(malayalam_trends)

            except Exception as e:
                logger.error(f"Error scanning {platform} trends: {e}")

        # Rank by viral potential
        ranked_trends = self._rank_trends_by_viral_potential(all_trends)
        return ranked_trends[:20]  # Return top 20

    async def _scan_youtube_trends(self) -> List[Dict[str, Any]]:
        """Scan YouTube trending videos."""
        trends = []

        try:
            url = "https://www.googleapis.com/youtube/v3/videos"
            params = {
                "part": "snippet,statistics",
                "chart": "mostPopular",
                "regionCode": "IN",
                "maxResults": 50,
                "key": self.youtube_api_key,
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()

            for item in data.get("items", []):
                snippet = item.get("snippet", {})
                stats = item.get("statistics", {})

                trend = {
                    "platform": "youtube",
                    "title": snippet.get("title", ""),
                    "description": snippet.get("description", ""),
                    "url": f"https://www.youtube.com/watch?v={item['id']}",
                    "views": int(stats.get("viewCount", 0)),
                    "likes": int(stats.get("likeCount", 0)),
                    "comments": int(stats.get("commentCount", 0)),
                    "published_at": snippet.get("publishedAt"),
                    "tags": snippet.get("tags", []),
                    "category": self._categorize_content(snippet.get("title", "")),
                }
                trends.append(trend)

        except Exception as e:
            logger.error(f"YouTube trend scanning failed: {e}")

        return trends

    async def _scan_instagram_trends(self) -> List[Dict[str, Any]]:
        """Scan Instagram trending hashtags and reels."""
        trends = []

        try:
            # Instagram Graph API - get trending hashtags
            url = f"https://graph.instagram.com/v18.0/ig_hashtag_search"
            params = {
                "q": "malayalam",
                "access_token": self.instagram_token,
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    # Process hashtag data
                    for item in data.get("data", [])[:20]:
                        trend = {
                            "platform": "instagram",
                            "title": f"#{item.get('name', '')}",
                            "hashtag": item.get("name", ""),
                            "media_count": item.get("media_count", 0),
                            "category": "hashtag",
                        }
                        trends.append(trend)

        except Exception as e:
            logger.error(f"Instagram trend scanning failed: {e}")

        return trends

    async def _scan_twitter_trends(self) -> List[Dict[str, Any]]:
        """Scan Twitter trending topics."""
        trends = []

        try:
            # Twitter API v2 - get trending topics
            url = "https://api.twitter.com/2/trends/by/woeid/1"  # Worldwide trends
            headers = {"Authorization": f"Bearer {self.twitter_bearer}"}

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    for trend in data.get("trends", [])[:20]:
                        trend_data = {
                            "platform": "twitter",
                            "title": trend.get("name", ""),
                            "tweet_volume": trend.get("tweet_volume", 0),
                            "url": trend.get("url", ""),
                            "category": "trending",
                        }
                        trends.append(trend_data)

        except Exception as e:
            logger.error(f"Twitter trend scanning failed: {e}")

        return trends

    def _is_malayalam_content(self, trend: Dict[str, Any]) -> bool:
        """Check if content is Malayalam-related."""
        text = f"{trend.get('title', '')} {trend.get('description', '')}".lower()

        # Check for Malayalam keywords
        if any(keyword.lower() in text for keyword in MALAYALAM_KEYWORDS):
            return True

        # Check for Malayalam script characters
        malayalam_chars = "അആഇഈഉഊഋഌഎഏഐഒഓഔകഖഗഘങചഛജഝഞടഠഡഢണതഥദധനപഫബഭമയരറലളഴവശഷസഹ"
        if any(char in text for char in malayalam_chars):
            return True

        return False

    def _categorize_content(self, title: str) -> str:
        """Categorize content into predefined categories."""
        title_lower = title.lower()

        for category in CONTENT_CATEGORIES:
            if category.lower() in title_lower:
                return category

        return "general"

    def _rank_trends_by_viral_potential(
        self, trends: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Rank trends by viral potential score."""
        for trend in trends:
            score = 0.0

            # Engagement metrics
            views = trend.get("views", 0)
            likes = trend.get("likes", 0)
            comments = trend.get("comments", 0)

            if views > 0:
                engagement_rate = (likes + comments * 2) / views
                score += engagement_rate * 0.4

            # Recency (newer = better)
            if trend.get("published_at"):
                try:
                    pub_date = datetime.fromisoformat(
                        trend["published_at"].replace("Z", "+00:00")
                    )
                    hours_old = (
                        datetime.utcnow() - pub_date.replace(tzinfo=None)
                    ).total_seconds() / 3600
                    recency_score = max(0, 1 - (hours_old / 48))  # Decay over 48 hours
                    score += recency_score * 0.3
                except:
                    pass

            # Cross-platform presence
            if trend.get("platform"):
                score += 0.1

            # Category relevance
            category = trend.get("category", "general")
            if category in ["entertainment", "comedy", "music"]:
                score += 0.2

            trend["viral_score"] = min(score, 1.0)

        # Sort by viral score
        return sorted(trends, key=lambda x: x.get("viral_score", 0), reverse=True)


class IdeaGenerator:
    """Creates viral content concepts based on trends."""

    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def generate_content_ideas(
        self, trend: Dict[str, Any], count: int = 5
    ) -> List[Dict[str, Any]]:
        """Generate multiple content ideas from a trend."""
        try:
            prompt = f"""You are a viral Malayalam content creator. Given this trending topic, generate {count} unique, engaging content ideas for short-form videos (30-60 seconds).

Trend: {trend.get('title', '')}
Description: {trend.get('description', '')[:200]}
Platform: {trend.get('platform', 'youtube')}
Category: {trend.get('category', 'general')}

For each idea, provide:
1. A catchy title in Malayalam
2. A hook (first 3 seconds) that grabs attention
3. The main content angle
4. Target audience
5. Why it will go viral

Format as JSON array with keys: title, hook, angle, audience, viral_reason"""

            response = self.openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.8,
            )

            content = response.choices[0].message.content.strip()

            # Parse JSON response
            try:
                # Extract JSON from response
                json_match = re.search(r"\[.*\]", content, re.DOTALL)
                if json_match:
                    ideas = json.loads(json_match.group())
                else:
                    ideas = self._parse_ideas_fallback(content)
            except:
                ideas = self._parse_ideas_fallback(content)

            # Add metadata
            for idea in ideas:
                idea["trend_id"] = trend.get("id")
                idea["trend_title"] = trend.get("title")
                idea["platform"] = trend.get("platform")
                idea["generated_at"] = datetime.utcnow().isoformat()

            return ideas[:count]

        except Exception as e:
            logger.error(f"Content idea generation failed: {e}")
            return self._generate_fallback_ideas(trend, count)

    def _parse_ideas_fallback(self, content: str) -> List[Dict[str, Any]]:
        """Fallback parsing for non-JSON responses."""
        ideas = []
        lines = content.split("\n")

        current_idea = {}
        for line in lines:
            if "title" in line.lower() and ":" in line:
                current_idea["title"] = line.split(":", 1)[1].strip()
            elif "hook" in line.lower() and ":" in line:
                current_idea["hook"] = line.split(":", 1)[1].strip()
            elif "angle" in line.lower() and ":" in line:
                current_idea["angle"] = line.split(":", 1)[1].strip()
                ideas.append(current_idea)
                current_idea = {}

        return (
            ideas
            if ideas
            else [{"title": "ട്രെൻഡിങ്ങ് വിഷയം", "hook": "വിസ്മയം!", "angle": "പ്രചാരണം"}]
        )

    def _generate_fallback_ideas(
        self, trend: Dict[str, Any], count: int
    ) -> List[Dict[str, Any]]:
        """Generate fallback ideas when AI fails."""
        title = trend.get("title", "ട്രെൻഡിങ്ങ് വിഷയം")
        return [
            {
                "title": f"{title} - വിവരണം",
                "hook": "ഇത് നിങ്ങൾ കാണണം!",
                "angle": "പ്രചാരണം",
                "audience": "മലയാളി പ്രേക്ഷകർ",
                "viral_reason": "ട്രെൻഡിങ്ങ് വിഷയം",
            }
            for _ in range(count)
        ]


class ScriptWriter:
    """Writes complete video scripts with scenes and dialogue."""

    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def write_script(
        self, content_idea: Dict[str, Any], duration_seconds: int = 60
    ) -> Dict[str, Any]:
        """Write a complete video script with scenes."""
        try:
            prompt = f"""Write a complete {duration_seconds}-second Malayalam video script for this content idea.

Title: {content_idea.get('title', '')}
Hook: {content_idea.get('hook', '')}
Angle: {content_idea.get('angle', '')}

Create a script with:
1. Scene-by-scene breakdown (3-5 scenes)
2. Dialogue/narration in Malayalam
3. Visual cues [like this]
4. Caption suggestions
5. Timing for each scene

Format as JSON:
{{
  "scenes": [
    {{
      "scene_number": 1,
      "duration_seconds": 10,
      "dialogue": "Malayalam text",
      "visual_cue": "what to show",
      "caption": "caption text"
    }}
  ],
  "total_duration": {duration_seconds},
  "hook_line": "opening hook",
  "call_to_action": "ending CTA"
}}"""

            response = self.openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.7,
            )

            content = response.choices[0].message.content.strip()

            # Parse JSON
            try:
                json_match = re.search(r"\{.*\}", content, re.DOTALL)
                if json_match:
                    script = json.loads(json_match.group())
                else:
                    script = self._generate_fallback_script(
                        content_idea, duration_seconds
                    )
            except:
                script = self._generate_fallback_script(content_idea, duration_seconds)

            script["idea_id"] = content_idea.get("id")
            script["generated_at"] = datetime.utcnow().isoformat()

            return script

        except Exception as e:
            logger.error(f"Script writing failed: {e}")
            return self._generate_fallback_script(content_idea, duration_seconds)

    def _generate_fallback_script(
        self, content_idea: Dict[str, Any], duration_seconds: int
    ) -> Dict[str, Any]:
        """Generate fallback script."""
        scenes_per_second = duration_seconds / 3  # 3 scenes for 60s video

        return {
            "scenes": [
                {
                    "scene_number": 1,
                    "duration_seconds": duration_seconds / 3,
                    "dialogue": content_idea.get("hook", "വിസ്മയം!"),
                    "visual_cue": "ആകർഷകമായ ഇമേജ്",
                    "caption": content_idea.get("hook", ""),
                },
                {
                    "scene_number": 2,
                    "duration_seconds": duration_seconds / 3,
                    "dialogue": content_idea.get("angle", "പ്രചാരണം"),
                    "visual_cue": "വിവരണം",
                    "caption": content_idea.get("angle", ""),
                },
                {
                    "scene_number": 3,
                    "duration_seconds": duration_seconds / 3,
                    "dialogue": "നിങ്ങൾക്ക് ഇഷ്ടമാകും!",
                    "visual_cue": "ക്യാൾ ടു ആക്ഷൻ",
                    "caption": "ലൈക്ക് ചെയ്യുക!",
                },
            ],
            "total_duration": duration_seconds,
            "hook_line": content_idea.get("hook", "വിസ്മയം!"),
            "call_to_action": "ലൈക്ക് ചെയ്യുക, ഷെയർ ചെയ്യുക!",
        }


class ContentPlanner:
    """Creates 7-day content calendar automatically."""

    def __init__(self):
        self.idea_generator = IdeaGenerator()
        self.script_writer = ScriptWriter()

    async def create_content_calendar(
        self, trends: List[Dict[str, Any]], days: int = 7
    ) -> Dict[str, Any]:
        """Create a complete content calendar for the next N days."""
        calendar = {
            "start_date": datetime.utcnow().date().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=days)).date().isoformat(),
            "days": [],
        }

        # Generate content for each day
        for day_offset in range(days):
            day_date = datetime.utcnow() + timedelta(days=day_offset)
            day_plan = await self._plan_day(day_date, trends)
            calendar["days"].append(day_plan)

        return calendar

    async def _plan_day(
        self, date: datetime, trends: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Plan content for a single day."""
        # Select best trend for the day
        selected_trend = trends[date.weekday() % len(trends)] if trends else None

        if not selected_trend:
            return {
                "date": date.date().isoformat(),
                "day_of_week": date.strftime("%A"),
                "content": None,
                "status": "no_trends",
            }

        # Generate ideas
        ideas = await self.idea_generator.generate_content_ideas(
            selected_trend, count=3
        )
        best_idea = ideas[0] if ideas else None

        # Write script
        script = None
        if best_idea:
            script = await self.script_writer.write_script(
                best_idea, duration_seconds=60
            )

        return {
            "date": date.date().isoformat(),
            "day_of_week": date.strftime("%A"),
            "trend": {
                "title": selected_trend.get("title"),
                "platform": selected_trend.get("platform"),
                "viral_score": selected_trend.get("viral_score", 0),
            },
            "content_idea": best_idea,
            "script": script,
            "scheduled_time": self._calculate_optimal_time(date),
            "status": "planned",
        }

    def _calculate_optimal_time(self, date: datetime) -> str:
        """Calculate optimal posting time for the day."""
        # Best times: 9 AM, 12 PM, 6 PM, 8 PM
        optimal_hours = [9, 12, 18, 20]
        hour = optimal_hours[date.weekday() % len(optimal_hours)]

        return date.replace(hour=hour, minute=0, second=0).isoformat()


class AIContentBrain:
    """Main orchestrator for AI Content Brain module."""

    def __init__(self):
        self.trend_detector = TrendDetector()
        self.idea_generator = IdeaGenerator()
        self.script_writer = ScriptWriter()
        self.content_planner = ContentPlanner()

    async def discover_and_plan(self, days: int = 7) -> Dict[str, Any]:
        """Complete workflow: discover trends and create content calendar."""
        logger.info("Starting content discovery and planning...")

        # Step 1: Scan trends
        trends = await self.trend_detector.scan_trends()
        logger.info(f"Discovered {len(trends)} trending topics")

        # Step 2: Create content calendar
        calendar = await self.content_planner.create_content_calendar(trends, days=days)
        logger.info(f"Created {days}-day content calendar")

        return {
            "trends": trends,
            "calendar": calendar,
            "generated_at": datetime.utcnow().isoformat(),
        }

    async def generate_content_for_trend(self, trend: Dict[str, Any]) -> Dict[str, Any]:
        """Generate complete content package for a trend."""
        # Generate ideas
        ideas = await self.idea_generator.generate_content_ideas(trend, count=3)

        # Write script for best idea
        script = None
        if ideas:
            script = await self.script_writer.write_script(
                ideas[0], duration_seconds=60
            )

        return {
            "trend": trend,
            "ideas": ideas,
            "script": script,
            "generated_at": datetime.utcnow().isoformat(),
        }
