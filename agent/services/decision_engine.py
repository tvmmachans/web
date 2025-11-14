import logging
import os
import random
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

from openai import OpenAI

from agent.config.settings import (
    CONTENT_CATEGORIES,
    DEFAULT_BEST_POSTING_HOURS,
    MALAYALAM_KEYWORDS,
    MAX_TOKENS_DECISION,
    OPENAI_MODEL,
    TEMPERATURE_DECISION,
)
from agent.utils.database import get_recent_analytics

logger = logging.getLogger(__name__)


class DecisionEngine:
    """
    AI-powered decision engine for social media optimization.
    Makes intelligent decisions about platform selection, timing, and content optimization.
    """

    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.content_categories = CONTENT_CATEGORIES
        self.malayalam_keywords = MALAYALAM_KEYWORDS

    async def make_decision(self, post) -> Dict[str, Any]:
        """
        Make comprehensive decision for a post including platform, timing, and optimizations.
        """
        try:
            # Analyze content to determine category and language
            content_analysis = await self._analyze_content(post)

            # Get analytics data for decision making
            analytics_data = await self._get_analytics_context()

            # Use AI to make platform decision
            platform_decision = await self._decide_platform(
                post, content_analysis, analytics_data
            )

            # Determine if repurposing is needed
            needs_repurposing = self._check_repurposing_need(post, platform_decision)

            # Generate tags and hashtags
            tags = await self._generate_tags(post, content_analysis)

            decision = {
                "platform": platform_decision["platform"],
                "confidence": platform_decision["confidence"],
                "reasoning": platform_decision["reasoning"],
                "needs_repurposing": needs_repurposing,
                "content_category": content_analysis["category"],
                "is_malayalam": content_analysis["is_malayalam"],
                "tags": tags,
                "suggested_improvements": platform_decision.get("improvements", []),
            }

            logger.info(f"Decision made for post {post.id}: {decision}")
            return decision

        except Exception as e:
            logger.error(f"Error making decision for post {post.id}: {e}")
            # Fallback decision
            return {
                "platform": "youtube",
                "confidence": 0.5,
                "reasoning": "Fallback decision due to error",
                "needs_repurposing": False,
                "content_category": "general",
                "is_malayalam": False,
                "tags": [],
                "suggested_improvements": [],
            }

    async def suggest_timing(self, post, decision: Dict[str, Any]) -> datetime:
        """
        Suggest optimal posting time based on analytics and content type.
        """
        try:
            # Get analytics data
            analytics_data = await self._get_analytics_context()

            # Use AI to suggest best time
            prompt = f"""
            Based on the following analytics data, suggest the optimal posting time for a {decision.get('content_category', 'general')} video.
            Consider engagement patterns and platform best practices.

            Analytics Summary:
            {analytics_data}

            Content: {post.title} - {post.description or post.ai_caption}

            Respond with just the hour (0-23) that would be best for posting.
            """

            response = self.openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=TEMPERATURE_DECISION,
            )

            suggested_hour = int(response.choices[0].message.content.strip())

            # Create datetime for next occurrence of that hour
            now = datetime.utcnow()
            suggested_time = now.replace(
                hour=suggested_hour, minute=0, second=0, microsecond=0
            )

            # If the time has passed today, schedule for tomorrow
            if suggested_time <= now:
                suggested_time += timedelta(days=1)

            logger.info(f"Suggested timing for post {post.id}: {suggested_time}")
            return suggested_time

        except Exception as e:
            logger.error(f"Error suggesting timing for post {post.id}: {e}")
            # Fallback to random best hour
            fallback_hour = random.choice(DEFAULT_BEST_POSTING_HOURS)
            now = datetime.utcnow()
            fallback_time = now.replace(
                hour=fallback_hour, minute=0, second=0, microsecond=0
            )
            if fallback_time <= now:
                fallback_time += timedelta(days=1)
            return fallback_time

    async def optimize_caption(self, caption: str, decision: Dict[str, Any]) -> str:
        """
        Optimize caption for better engagement using AI.
        """
        if not caption:
            return "Check out this amazing video! #Content"

        try:
            platform = decision.get("platform", "youtube")
            category = decision.get("content_category", "general")
            is_malayalam = decision.get("is_malayalam", False)

            prompt = f"""
            Optimize this social media caption for {platform} to maximize engagement.
            Content category: {category}
            Language: {'Malayalam' if is_malayalam else 'English'}
            Include relevant hashtags and emojis.

            Original caption: {caption}

            Provide an optimized version that's engaging and platform-appropriate.
            """

            response = self.openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=MAX_TOKENS_DECISION,
                temperature=TEMPERATURE_DECISION,
            )

            optimized_caption = response.choices[0].message.content.strip()
            logger.info(f"Caption optimized for post: {optimized_caption[:50]}...")
            return optimized_caption

        except Exception as e:
            logger.error(f"Error optimizing caption: {e}")
            return caption

    async def _analyze_content(self, post) -> Dict[str, Any]:
        """
        Analyze post content to determine category and language.
        """
        text_content = f"{post.title} {post.description or ''} {post.ai_caption or ''}"

        # Check for Malayalam keywords
        is_malayalam = any(
            keyword in text_content.lower() for keyword in self.malayalam_keywords
        )

        # Determine category using AI
        try:
            prompt = f"""
            Analyze this content and determine the most appropriate category from: {', '.join(self.content_categories)}

            Content: {text_content}

            Respond with just the category name.
            """

            response = self.openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=20,
                temperature=0.3,
            )

            category = response.choices[0].message.content.strip().lower()

            # Ensure it's a valid category
            if category not in self.content_categories:
                category = "entertainment"

        except Exception as e:
            logger.error(f"Error analyzing content: {e}")
            category = "entertainment"

        return {
            "category": category,
            "is_malayalam": is_malayalam,
            "text_content": text_content,
        }

    async def _decide_platform(
        self, post, content_analysis: Dict, analytics_data: str
    ) -> Dict[str, Any]:
        """
        Use AI to decide between YouTube and Instagram based on content and analytics.
        """
        try:
            prompt = f"""
            Decide whether this content is better suited for YouTube or Instagram based on:
            1. Content type: {content_analysis['category']}
            2. Language: {'Malayalam' if content_analysis['is_malayalam'] else 'English'}
            3. Historical analytics: {analytics_data}
            4. Platform strengths (YouTube: long-form, educational; Instagram: short-form, visual)

            Content: {content_analysis['text_content']}

            Respond in JSON format:
            {{
                "platform": "youtube" or "instagram",
                "confidence": 0.0-1.0,
                "reasoning": "brief explanation",
                "improvements": ["suggestion1", "suggestion2"]
            }}
            """

            response = self.openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=MAX_TOKENS_DECISION,
                temperature=TEMPERATURE_DECISION,
            )

            # Parse JSON response
            import json

            decision_text = response.choices[0].message.content.strip()
            decision = json.loads(decision_text)

            return decision

        except Exception as e:
            logger.error(f"Error deciding platform: {e}")
            return {
                "platform": "youtube",
                "confidence": 0.6,
                "reasoning": "Default decision due to error",
                "improvements": [],
            }

    async def _generate_tags(self, post, content_analysis: Dict) -> List[str]:
        """
        Generate relevant tags and hashtags for the post.
        """
        try:
            prompt = f"""
            Generate 5-8 relevant hashtags and tags for this content.
            Category: {content_analysis['category']}
            Language: {'Malayalam' if content_analysis['is_malayalam'] else 'English'}

            Content: {content_analysis['text_content']}

            Provide comma-separated hashtags (without # symbol).
            """

            response = self.openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=TEMPERATURE_DECISION,
            )

            tags_text = response.choices[0].message.content.strip()
            tags = [tag.strip() for tag in tags_text.split(",") if tag.strip()]

            return tags[:8]  # Limit to 8 tags

        except Exception as e:
            logger.error(f"Error generating tags: {e}")
            return ["content", "video", "socialmedia"]

    def _check_repurposing_need(self, post, platform_decision: Dict) -> bool:
        """
        Determine if content needs repurposing for the chosen platform.
        """
        platform = platform_decision.get("platform", "youtube")

        # Instagram typically needs shorter content
        if (
            platform == "instagram" and post.duration and post.duration > 90
        ):  # Longer than 90 seconds
            return True

        return False

    async def _get_analytics_context(self) -> str:
        """
        Get recent analytics data as context for decision making.
        """
        try:
            async for session in get_recent_analytics():
                analytics = await get_recent_analytics(session, days=30)
                break

            if not analytics:
                return "No recent analytics data available"

            # Summarize analytics
            total_posts = len(analytics)
            avg_engagement = (
                sum(a.engagement_rate for a in analytics) / total_posts
                if total_posts > 0
                else 0
            )

            platform_summary = {}
            for a in analytics:
                if a.platform not in platform_summary:
                    platform_summary[a.platform] = {"count": 0, "avg_engagement": 0}
                platform_summary[a.platform]["count"] += 1
                platform_summary[a.platform]["avg_engagement"] += a.engagement_rate

            for platform in platform_summary:
                count = platform_summary[platform]["count"]
                platform_summary[platform]["avg_engagement"] /= count

            summary = f"""
            Total posts analyzed: {total_posts}
            Average engagement rate: {avg_engagement:.3f}
            Platform performance: {platform_summary}
            """

            return summary.strip()

        except Exception as e:
            logger.error(f"Error getting analytics context: {e}")
            return "Analytics data unavailable"
