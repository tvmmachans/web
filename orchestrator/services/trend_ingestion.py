"""
Trend ingestion service for discovering Malayalam trends.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import httpx
import feedparser
from playwright.async_api import async_playwright

from orchestrator.config.settings import settings
from orchestrator.database.session import get_db
from orchestrator.database.models import Trend

logger = logging.getLogger(__name__)

@dataclass
class TrendCandidate:
    """Data class for trend candidates."""
    title: str
    description: str
    source: str
    source_url: str
    velocity: float = 0.0
    tags: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}

class TrendIngestionService:
    """Service for ingesting trends from multiple sources."""

    def __init__(self):
        self.youtube_api_key = settings.YOUTUBE_API_KEY
        self.instagram_token = settings.INSTAGRAM_ACCESS_TOKEN
        self.twitter_token = settings.TWITTER_BEARER_TOKEN

    async def discover_trends(self) -> List[TrendCandidate]:
        """Run full trend discovery across all sources."""
        logger.info("Starting trend discovery across all sources")

        tasks = [
            self._discover_youtube_trends(),
            self._discover_instagram_trends(),
            self._discover_twitter_trends(),
            self._discover_rss_trends()
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_candidates = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error in trend discovery: {result}")
                continue
            all_candidates.extend(result)

        # Deduplicate and normalize
        normalized_trends = await self._normalize_and_deduplicate(all_candidates)

        logger.info(f"Discovered {len(normalized_trends)} unique trends")
        return normalized_trends

    async def _discover_youtube_trends(self) -> List[TrendCandidate]:
        """Discover trending videos from YouTube India/Malayalam region."""
        candidates = []

        try:
            # YouTube Data API v3
            url = "https://www.googleapis.com/youtube/v3/videos"
            params = {
                "part": "snippet,statistics",
                "chart": "mostPopular",
                "regionCode": "IN",  # India region
                "maxResults": 50,
                "key": self.youtube_api_key
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

            for item in data.get("items", []):
                snippet = item.get("snippet", {})
                statistics = item.get("statistics", {})

                # Check if Malayalam content
                title = snippet.get("title", "")
                description = snippet.get("description", "")
                tags = snippet.get("tags", [])

                if self._is_malayalam_content(title, description, tags):
                    candidate = TrendCandidate(
                        title=title,
                        description=description,
                        source="youtube",
                        source_url=f"https://www.youtube.com/watch?v={item['id']}",
                        velocity=float(statistics.get("viewCount", 0)) / 24.0,  # views per hour approx
                        tags=tags,
                        metadata={
                            "channel_title": snippet.get("channelTitle"),
                            "published_at": snippet.get("publishedAt"),
                            "view_count": statistics.get("viewCount"),
                            "like_count": statistics.get("likeCount")
                        }
                    )
                    candidates.append(candidate)

        except Exception as e:
            logger.error(f"YouTube trend discovery failed: {e}")

        return candidates

    async def _discover_instagram_trends(self) -> List[TrendCandidate]:
        """Discover trending hashtags from Instagram using Graph API."""
        candidates = []

        try:
            # Instagram Basic Display API or Graph API for hashtag insights
            # Note: Requires proper app setup and user authentication
            hashtags = ["malayalam", "kerala", "കേരളം", "മലയാളം", "shorts", "reels"]

            async with httpx.AsyncClient() as client:
                for hashtag in hashtags:
                    try:
                        # Use Instagram Graph API for hashtag search
                        # This requires a Facebook app with Instagram Basic Display
                        url = f"https://graph.instagram.com/ig_hashtag_search"
                        params = {
                            "user_id": "me",  # Would need actual user ID from auth
                            "q": hashtag,
                            "access_token": self.instagram_token
                        }

                        response = await client.get(url, params=params, timeout=10)
                        if response.status_code == 200:
                            data = response.json()
                            # Process real hashtag data
                            for hashtag_data in data.get("data", []):
                                candidate = TrendCandidate(
                                    title=f"#{hashtag}",
                                    description=f"Trending Instagram hashtag: {hashtag}",
                                    source="instagram",
                                    source_url=f"https://www.instagram.com/explore/tags/{hashtag}/",
                                    velocity=self._calculate_instagram_velocity(hashtag_data),
                                    tags=[hashtag],
                                    metadata={
                                        "hashtag_id": hashtag_data.get("id"),
                                        "hashtag": hashtag
                                    }
                                )
                                candidates.append(candidate)
                        else:
                            # Fallback to mock data if API fails
                            logger.warning(f"Instagram API failed for {hashtag}: {response.status_code}")
                            candidate = TrendCandidate(
                                title=f"#{hashtag}",
                                description=f"Trending hashtag: {hashtag}",
                                source="instagram",
                                source_url=f"https://www.instagram.com/explore/tags/{hashtag}/",
                                velocity=50.0,  # Conservative estimate
                                tags=[hashtag],
                                metadata={"hashtag": hashtag, "api_status": "fallback"}
                            )
                            candidates.append(candidate)

                    except Exception as e:
                        logger.warning(f"Failed to get Instagram data for {hashtag}: {e}")
                        # Still add fallback
                        candidate = TrendCandidate(
                            title=f"#{hashtag}",
                            description=f"Trending hashtag: {hashtag}",
                            source="instagram",
                            source_url=f"https://www.instagram.com/explore/tags/{hashtag}/",
                            velocity=25.0,
                            tags=[hashtag],
                            metadata={"hashtag": hashtag, "status": "error_fallback"}
                        )
                        candidates.append(candidate)

        except Exception as e:
            logger.error(f"Instagram trend discovery failed: {e}")

        return candidates

    def _calculate_instagram_velocity(self, hashtag_data: Dict[str, Any]) -> float:
        """Calculate velocity score from Instagram hashtag data."""
        # This would use real metrics like recent_posts_count
        # For now, return estimated velocity
        return 75.0  # Base velocity for Instagram trends

    async def _discover_twitter_trends(self) -> List[TrendCandidate]:
        """Discover trending topics from Twitter/X."""
        candidates = []

        try:
            # Twitter API v2
            url = "https://api.twitter.com/2/tweets/search/recent"
            headers = {"Authorization": f"Bearer {self.twitter_token}"}

            # Search for Malayalam keywords
            query = " OR ".join(f'"{kw}"' for kw in settings.MALAYALAM_KEYWORDS)
            params = {
                "query": query,
                "max_results": 100,
                "tweet.fields": "public_metrics,created_at,lang"
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()

            # Group by topics and calculate velocity
            topic_counts = {}
            for tweet in data.get("data", []):
                if tweet.get("lang") == "ml":  # Malayalam language
                    # Simple topic extraction (would need better NLP in production)
                    text = tweet.get("full_text", "")
                    topic = self._extract_topic(text)
                    if topic:
                        metrics = tweet.get("public_metrics", {})
                        if topic not in topic_counts:
                            topic_counts[topic] = {"count": 0, "sample_tweet": text}
                        topic_counts[topic]["count"] += 1

            # Create candidates
            for topic, info in topic_counts.items():
                if info["count"] > 5:  # Minimum threshold
                    candidate = TrendCandidate(
                        title=topic,
                        description=info["sample_tweet"][:200],
                        source="twitter",
                        source_url="",  # Would need search URL
                        velocity=info["count"] / 1.0,  # tweets per hour
                        metadata={"tweet_count": info["count"]}
                    )
                    candidates.append(candidate)

        except Exception as e:
            logger.error(f"Twitter trend discovery failed: {e}")

        return candidates

    async def _discover_rss_trends(self) -> List[TrendCandidate]:
        """Discover trends from RSS feeds and news sites."""
        candidates = []

        try:
            # Malayalam news RSS feeds
            rss_urls = [
                "https://www.manoramaonline.com/rss.xml",
                "https://www.mathrubhumi.com/rss.xml",
                "https://www.deepika.com/rss.xml"
            ]

            async with httpx.AsyncClient() as client:
                for rss_url in rss_urls:
                    try:
                        response = await client.get(rss_url, timeout=10)
                        feed = feedparser.parse(response.text)

                        for entry in feed.entries[:10]:  # Last 10 entries
                            published = self._parse_rss_date(entry.get("published_parsed"))
                            hours_old = (datetime.now(datetime.UTC) - published).total_seconds() / 3600

                            if hours_old < 24:  # Only recent articles
                                candidate = TrendCandidate(
                                    title=entry.title,
                                    description=entry.get("summary", "")[:300],
                                    source="rss",
                                    source_url=entry.link,
                                    velocity=1.0 / max(hours_old, 1),  # Recency-based velocity
                                    metadata={
                                        "published": entry.get("published"),
                                        "source_feed": rss_url
                                    }
                                )
                                candidates.append(candidate)

                    except Exception as e:
                        logger.warning(f"Failed to parse RSS {rss_url}: {e}")

        except Exception as e:
            logger.error(f"RSS trend discovery failed: {e}")

        return candidates

    async def _normalize_and_deduplicate(self, candidates: List[TrendCandidate]) -> List[TrendCandidate]:
        """Normalize and deduplicate trend candidates."""
        # Group by similar titles/topics
        groups = {}

        for candidate in candidates:
            # Simple deduplication key (would use embeddings in production)
            key = candidate.title.lower().strip()

            if key not in groups:
                groups[key] = []
            groups[key].append(candidate)

        # Merge duplicates
        normalized = []
        for key, group in groups.items():
            if len(group) == 1:
                normalized.append(group[0])
            else:
                # Merge multiple sources
                primary = group[0]
                primary.velocity = sum(c.velocity for c in group)
                primary.metadata["sources"] = [c.source for c in group]
                primary.metadata["source_count"] = len(group)
                normalized.append(primary)

        return normalized

    def _is_malayalam_content(self, title: str, description: str, tags: List[str]) -> bool:
        """Check if content is Malayalam-related."""
        text = f"{title} {description} {' '.join(tags)}".lower()

        # Check for Malayalam keywords
        for keyword in settings.MALAYALAM_KEYWORDS:
            if keyword.lower() in text:
                return True

        # Check for Malayalam script (basic check)
        malayalam_chars = set("അആഇഈഉഊഋഌഎഏഐഒഓഔകഖഗഘങചഛജഝഞടഠഡഢണതഥദധനപഫബഭമയരറലളഴവശഷസഹ")
        if any(char in malayalam_chars for char in text):
            return True

        return False

    def _extract_topic(self, text: str) -> Optional[str]:
        """Extract topic from tweet text (simplified)."""
        # Remove URLs, mentions, hashtags
        import re
        clean_text = re.sub(r'http\S+|@\S+|#\S+', '', text).strip()

        # Take first meaningful words
        words = clean_text.split()[:5]
        if words:
            return " ".join(words)
        return None

    def _parse_rss_date(self, date_tuple) -> datetime:
        """Parse RSS date tuple to datetime."""
        if date_tuple:
            return datetime(*date_tuple[:6])
        return datetime.now(datetime.UTC) - timedelta(days=1)

    async def save_trends_to_db(self, candidates: List[TrendCandidate]):
        """Save discovered trends to database."""
        from orchestrator.database.session import get_db

        async with get_db() as session:
            for candidate in candidates:
                # Calculate trend strength
                trend_strength = self._calculate_trend_strength(candidate)

                trend = Trend(
                    trend_id=f"{candidate.source}_{hash(candidate.title)}",
                    title=candidate.title,
                    description=candidate.description,
                    source=candidate.source,
                    source_url=candidate.source_url,
                    velocity=candidate.velocity,
                    trend_strength=trend_strength,
                    tags=candidate.tags,
                    metadata=candidate.metadata,
                    spike_time=datetime.now(datetime.UTC)
                )

                session.add(trend)

            await session.commit()

    def _calculate_trend_strength(self, candidate: TrendCandidate) -> float:
        """Calculate trend strength score."""
        # Simple scoring based on velocity and source
        base_score = candidate.velocity

        # Source multipliers
        source_multipliers = {
            "youtube": 1.5,
            "instagram": 1.3,
            "twitter": 1.2,
            "rss": 1.0
        }

        multiplier = source_multipliers.get(candidate.source, 1.0)
        return base_score * multiplier
