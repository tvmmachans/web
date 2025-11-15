"""
Performance Optimizer - Complete analytics and learning system.
Handles analytics tracking, ML learning, A/B testing, and improvement suggestions.
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import json

from openai import OpenAI
import httpx
import numpy as np

logger = logging.getLogger(__name__)


class AnalyticsTracker:
    """Monitors views, likes, comments, engagement."""

    def __init__(self):
        self.youtube_api_key = os.getenv("YOUTUBE_API_KEY")
        self.instagram_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")

    async def track_performance(self, video_id: str, platform: str) -> Dict[str, Any]:
        """Track performance metrics for a video."""
        try:
            if platform == "youtube":
                return await self._track_youtube(video_id)
            elif platform == "instagram":
                return await self._track_instagram(video_id)
            else:
                return {"error": "Unsupported platform"}

        except Exception as e:
            logger.error(f"Analytics tracking failed: {e}")
            return {"error": str(e)}

    async def _track_youtube(self, video_id: str) -> Dict[str, Any]:
        """Track YouTube analytics."""
        try:
            url = "https://www.googleapis.com/youtube/v3/videos"
            params = {
                "part": "statistics,snippet",
                "id": video_id,
                "key": self.youtube_api_key,
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()

            if data.get("items"):
                item = data["items"][0]
                stats = item.get("statistics", {})

                views = int(stats.get("viewCount", 0))
                likes = int(stats.get("likeCount", 0))
                comments = int(stats.get("commentCount", 0))

                # Calculate engagement rate
                engagement_rate = (likes + comments * 2) / views if views > 0 else 0

                return {
                    "platform": "youtube",
                    "video_id": video_id,
                    "views": views,
                    "likes": likes,
                    "comments": comments,
                    "engagement_rate": engagement_rate,
                    "tracked_at": datetime.utcnow().isoformat(),
                }

        except Exception as e:
            logger.error(f"YouTube tracking failed: {e}")
            return {"error": str(e)}

    async def _track_instagram(self, media_id: str) -> Dict[str, Any]:
        """Track Instagram analytics."""
        try:
            url = f"https://graph.instagram.com/v18.0/{media_id}"
            params = {
                "fields": "like_count,comments_count,play_count,reach,impressions",
                "access_token": self.instagram_token,
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()

            views = data.get("play_count", 0) or data.get("reach", 0)
            likes = data.get("like_count", 0)
            comments = data.get("comments_count", 0)

            engagement_rate = (likes + comments * 2) / views if views > 0 else 0

            return {
                "platform": "instagram",
                "media_id": media_id,
                "views": views,
                "likes": likes,
                "comments": comments,
                "engagement_rate": engagement_rate,
                "tracked_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Instagram tracking failed: {e}")
            return {"error": str(e)}

    async def get_historical_analytics(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get historical analytics data."""
        # This would query the database
        # For now, return placeholder
        return []


class MLLearningEngine:
    """Learns what content performs best and improves predictions."""

    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model_weights = {}  # Would be loaded from trained model

    async def learn_from_performance(
        self, content_data: Dict[str, Any], performance: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Learn from content performance and update model."""
        try:
            # Extract features
            features = self._extract_features(content_data, performance)

            # Update model weights (simplified - would use actual ML training)
            self._update_weights(features, performance)

            # Generate insights
            insights = await self._generate_insights(features, performance)

            return {
                "learned": True,
                "insights": insights,
                "updated_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Learning failed: {e}")
            return {"learned": False, "error": str(e)}

    def _extract_features(
        self, content_data: Dict[str, Any], performance: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract features for learning."""
        return {
            "title_length": len(content_data.get("title", "")),
            "has_emoji": "🤩" in content_data.get("title", ""),
            "category": content_data.get("category", "general"),
            "posting_hour": performance.get("posted_at", {}).get("hour", 12),
            "day_of_week": performance.get("posted_at", {}).get("weekday", 0),
            "engagement_rate": performance.get("engagement_rate", 0),
        }

    def _update_weights(self, features: Dict[str, Any], performance: Dict[str, Any]):
        """Update model weights based on performance."""
        # Simplified - real implementation would use gradient descent
        engagement = performance.get("engagement_rate", 0)

        # Update weights for positive features
        for key, value in features.items():
            if key not in self.model_weights:
                self.model_weights[key] = 0.0

            # Simple update rule
            if engagement > 0.05:  # Good engagement
                self.model_weights[key] += 0.01 * value
            else:  # Poor engagement
                self.model_weights[key] -= 0.01 * value

    async def _generate_insights(
        self, features: Dict[str, Any], performance: Dict[str, Any]
    ) -> List[str]:
        """Generate insights from performance data."""
        insights = []

        engagement = performance.get("engagement_rate", 0)

        if engagement > 0.05:
            insights.append("Content performed well - replicate successful elements")
        else:
            insights.append("Content underperformed - review and adjust strategy")

        # Category insights
        category = features.get("category", "general")
        if engagement > 0.05:
            insights.append(f"{category} content is resonating with audience")

        # Timing insights
        hour = features.get("posting_hour", 12)
        if engagement > 0.05:
            insights.append(f"Posting at {hour}:00 is effective")

        return insights

    async def predict_performance(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Predict content performance using learned model."""
        try:
            # Extract features
            features = {
                "title_length": len(content_data.get("title", "")),
                "has_emoji": "🤩" in content_data.get("title", ""),
                "category": content_data.get("category", "general"),
            }

            # Simple prediction based on weights
            predicted_engagement = 0.03  # Base

            for key, value in features.items():
                weight = self.model_weights.get(key, 0.0)
                predicted_engagement += weight * (
                    value if isinstance(value, (int, float)) else 1.0
                )

            predicted_engagement = max(0, min(1, predicted_engagement))

            return {
                "predicted_engagement": predicted_engagement,
                "predicted_views": int(predicted_engagement * 10000),  # Estimate
                "confidence": 0.7,
            }

        except Exception as e:
            logger.error(f"Performance prediction failed: {e}")
            return {
                "predicted_engagement": 0.03,
                "predicted_views": 300,
                "confidence": 0.3,
            }


class ABTesting:
    """Tests different thumbnails, titles, captions automatically."""

    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def create_variants(
        self, content: Dict[str, Any], variant_type: str = "thumbnail"
    ) -> List[Dict[str, Any]]:
        """Create A/B test variants."""
        try:
            if variant_type == "thumbnail":
                return await self._create_thumbnail_variants(content)
            elif variant_type == "title":
                return await self._create_title_variants(content)
            elif variant_type == "caption":
                return await self._create_caption_variants(content)
            else:
                return []

        except Exception as e:
            logger.error(f"Variant creation failed: {e}")
            return []

    async def _create_thumbnail_variants(
        self, content: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Create thumbnail variants."""
        variants = []

        styles = ["vibrant", "minimal", "text_heavy", "emotion_focused"]

        for style in styles:
            try:
                prompt = f"{content.get('title', '')}. {style} style thumbnail"
                # Would generate thumbnail using DALL-E
                variants.append(
                    {
                        "variant_id": f"thumb_{style}",
                        "style": style,
                        "prompt": prompt,
                        "status": "generated",
                    }
                )
            except Exception as e:
                logger.error(f"Thumbnail variant {style} failed: {e}")

        return variants

    async def _create_title_variants(
        self, content: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Create title variants."""
        base_title = content.get("title", "")

        prompt = f"""Generate 3 alternative titles for this content:

Original: {base_title}

Create variants that:
1. Are more clickbait-y
2. Are more descriptive
3. Include emojis

Return as JSON array: ["title1", "title2", "title3"]"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.8,
            )

            content_text = response.choices[0].message.content.strip()
            import re

            json_match = re.search(r"\[.*\]", content_text, re.DOTALL)
            if json_match:
                titles = json.loads(json_match.group())
            else:
                titles = [base_title + " - Variant 1", base_title + " - Variant 2"]

            variants = []
            for i, title in enumerate(titles[:3], 1):
                variants.append(
                    {
                        "variant_id": f"title_{i}",
                        "title": title,
                        "status": "generated",
                    }
                )

            return variants

        except Exception as e:
            logger.error(f"Title variant creation failed: {e}")
            return [
                {"variant_id": "title_1", "title": base_title, "status": "fallback"}
            ]

    async def _create_caption_variants(
        self, content: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Create caption variants."""
        base_caption = content.get("caption", "")

        variants = [
            {
                "variant_id": "caption_short",
                "caption": base_caption[:100] + "...",
                "style": "short",
            },
            {
                "variant_id": "caption_long",
                "caption": base_caption + " More details...",
                "style": "long",
            },
            {
                "variant_id": "caption_emoji",
                "caption": base_caption + " 🤩🔥",
                "style": "emoji_heavy",
            },
        ]

        return variants

    async def evaluate_variants(
        self, variants: List[Dict[str, Any]], performance_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Evaluate which variant performed best."""
        best_variant = None
        best_performance = 0

        for variant in variants:
            variant_id = variant.get("variant_id")
            # Find performance for this variant
            variant_perf = next(
                (p for p in performance_data if p.get("variant_id") == variant_id),
                None,
            )

            if variant_perf:
                engagement = variant_perf.get("engagement_rate", 0)
                if engagement > best_performance:
                    best_performance = engagement
                    best_variant = variant

        return {
            "best_variant": best_variant,
            "best_performance": best_performance,
            "evaluated_at": datetime.utcnow().isoformat(),
        }


class ImprovementSuggester:
    """Recommends content strategy changes based on data."""

    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def suggest_improvements(
        self, analytics_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate improvement suggestions based on analytics."""
        try:
            # Analyze performance patterns
            patterns = self._analyze_patterns(analytics_data)

            # Generate suggestions using AI
            prompt = f"""Based on this analytics data, provide strategic recommendations for improving content performance.

Analytics Summary:
{json.dumps(patterns, indent=2)}

Provide recommendations for:
1. Content strategy
2. Posting schedule
3. Content format
4. Engagement tactics

Format as JSON:
{{
  "content_strategy": ["suggestion1", "suggestion2"],
  "posting_schedule": ["suggestion1"],
  "content_format": ["suggestion1"],
  "engagement_tactics": ["suggestion1"]
}}"""

            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.7,
            )

            content = response.choices[0].message.content.strip()

            # Parse JSON
            try:
                import re

                json_match = re.search(r"\{.*\}", content, re.DOTALL)
                if json_match:
                    suggestions = json.loads(json_match.group())
                else:
                    suggestions = self._generate_fallback_suggestions(patterns)
            except:
                suggestions = self._generate_fallback_suggestions(patterns)

            return {
                "suggestions": suggestions,
                "based_on_data_points": len(analytics_data),
                "generated_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Improvement suggestion failed: {e}")
            return self._generate_fallback_suggestions({})

    def _analyze_patterns(self, analytics_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns in analytics data."""
        if not analytics_data:
            return {}

        # Calculate averages
        avg_engagement = np.mean([a.get("engagement_rate", 0) for a in analytics_data])
        avg_views = np.mean([a.get("views", 0) for a in analytics_data])

        # Best performing content
        best_content = max(analytics_data, key=lambda x: x.get("engagement_rate", 0))

        # Worst performing content
        worst_content = min(analytics_data, key=lambda x: x.get("engagement_rate", 0))

        return {
            "avg_engagement": float(avg_engagement),
            "avg_views": float(avg_views),
            "best_category": best_content.get("category", "unknown"),
            "worst_category": worst_content.get("category", "unknown"),
            "total_posts": len(analytics_data),
        }

    def _generate_fallback_suggestions(
        self, patterns: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate fallback suggestions."""
        return {
            "content_strategy": [
                "Focus on trending topics",
                "Increase posting frequency",
            ],
            "posting_schedule": ["Post during peak hours (6 PM - 8 PM)"],
            "content_format": ["Use more engaging thumbnails"],
            "engagement_tactics": ["Ask questions in captions"],
        }


class PerformanceOptimizer:
    """Main orchestrator for Performance Optimizer module."""

    def __init__(self):
        self.analytics_tracker = AnalyticsTracker()
        self.ml_learning = MLLearningEngine()
        self.ab_testing = ABTesting()
        self.improvement_suggester = ImprovementSuggester()

    async def optimize_content_strategy(
        self, content_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Complete optimization workflow."""
        logger.info("Starting content strategy optimization...")

        # Track performance for all content
        performance_data = []
        for content in content_history:
            perf = await self.analytics_tracker.track_performance(
                content.get("video_id"), content.get("platform")
            )
            if perf and not perf.get("error"):
                performance_data.append(perf)

                # Learn from performance
                await self.ml_learning.learn_from_performance(content, perf)

        # Generate improvement suggestions
        suggestions = await self.improvement_suggester.suggest_improvements(
            performance_data
        )

        return {
            "performance_data": performance_data,
            "suggestions": suggestions,
            "optimized_at": datetime.utcnow().isoformat(),
        }
