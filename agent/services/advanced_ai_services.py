"""
Advanced AI Services - Competitor Analysis, Viral Predictor, Content Repurposing
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import json

from openai import OpenAI
import httpx

logger = logging.getLogger(__name__)


class CompetitorAnalyzer:
    """Analyzes competitor content to learn from their success."""

    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.youtube_api_key = os.getenv("YOUTUBE_API_KEY")
        self.instagram_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")

    async def analyze_competitor_content(
        self, competitor_url: str, platform: str
    ) -> Dict[str, Any]:
        """Analyze a specific competitor's content."""
        try:
            # Fetch competitor content
            content_data = await self._fetch_competitor_content(competitor_url, platform)

            # Analyze performance
            performance_analysis = await self._analyze_performance(content_data)

            # Extract successful elements
            successful_elements = await self._extract_successful_elements(
                content_data, performance_analysis
            )

            # Generate insights
            insights = await self._generate_insights(
                content_data, performance_analysis, successful_elements
            )

            return {
                "competitor_url": competitor_url,
                "platform": platform,
                "content_data": content_data,
                "performance": performance_analysis,
                "successful_elements": successful_elements,
                "insights": insights,
                "learnings": self._extract_learnings(insights),
                "analyzed_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Competitor analysis failed: {e}")
            return {"error": str(e)}

    async def _fetch_competitor_content(
        self, url: str, platform: str
    ) -> Dict[str, Any]:
        """Fetch competitor content data."""
        if platform == "youtube":
            return await self._fetch_youtube_content(url)
        elif platform == "instagram":
            return await self._fetch_instagram_content(url)
        else:
            return {}

    async def _fetch_youtube_content(self, url: str) -> Dict[str, Any]:
        """Fetch YouTube video data."""
        try:
            # Extract video ID from URL
            video_id = url.split("v=")[-1].split("&")[0]

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://www.googleapis.com/youtube/v3/videos",
                    params={
                        "part": "snippet,statistics,contentDetails",
                        "id": video_id,
                        "key": self.youtube_api_key,
                    },
                    timeout=10,
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("items"):
                        item = data["items"][0]
                        return {
                            "title": item["snippet"]["title"],
                            "description": item["snippet"]["description"],
                            "tags": item["snippet"].get("tags", []),
                            "category": item["snippet"]["categoryId"],
                            "views": int(item["statistics"].get("viewCount", 0)),
                            "likes": int(item["statistics"].get("likeCount", 0)),
                            "comments": int(item["statistics"].get("commentCount", 0)),
                            "duration": item["contentDetails"]["duration"],
                            "published_at": item["snippet"]["publishedAt"],
                        }
        except Exception as e:
            logger.error(f"YouTube content fetch failed: {e}")

        return {}

    async def _fetch_instagram_content(self, url: str) -> Dict[str, Any]:
        """Fetch Instagram content data."""
        # Placeholder - would use Instagram Graph API
        return {}

    async def _analyze_performance(
        self, content_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze content performance metrics."""
        views = content_data.get("views", 0)
        likes = content_data.get("likes", 0)
        comments = content_data.get("comments", 0)

        engagement_rate = (likes + comments * 2) / views if views > 0 else 0

        return {
            "views": views,
            "likes": likes,
            "comments": comments,
            "engagement_rate": engagement_rate,
            "performance_tier": self._classify_performance(engagement_rate),
        }

    def _classify_performance(self, engagement_rate: float) -> str:
        """Classify performance tier."""
        if engagement_rate > 0.1:
            return "excellent"
        elif engagement_rate > 0.05:
            return "good"
        elif engagement_rate > 0.02:
            return "average"
        else:
            return "poor"

    async def _extract_successful_elements(
        self, content_data: Dict[str, Any], performance: Dict[str, Any]
    ) -> List[str]:
        """Extract what made the content successful."""
        elements = []

        # Analyze title
        title = content_data.get("title", "")
        if len(title) > 0:
            if any(word in title.lower() for word in ["top", "best", "amazing"]):
                elements.append("Power words in title")
            if "?" in title:
                elements.append("Question format")
            if len(title) < 60:
                elements.append("Concise title")

        # Analyze engagement
        if performance.get("engagement_rate", 0) > 0.05:
            elements.append("High engagement rate")
            if content_data.get("comments", 0) > 100:
                elements.append("Strong community engagement")

        # Analyze tags
        tags = content_data.get("tags", [])
        if len(tags) > 5:
            elements.append("Good hashtag strategy")

        return elements

    async def _generate_insights(
        self,
        content_data: Dict[str, Any],
        performance: Dict[str, Any],
        elements: List[str],
    ) -> Dict[str, Any]:
        """Generate AI insights from competitor analysis."""
        try:
            prompt = f"""Analyze this successful competitor content and provide strategic insights:

Title: {content_data.get('title', '')}
Performance: {performance}
Successful Elements: {', '.join(elements)}

Provide insights on:
1. Content strategy that worked
2. What we can learn and adapt
3. Key differentiators
4. Recommendations for our content

Format as JSON with keys: strategy, learnings, differentiators, recommendations"""

            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.7,
            )

            content = response.choices[0].message.content.strip()
            import re

            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            logger.error(f"Insight generation failed: {e}")

        return {
            "strategy": "Analyze successful patterns",
            "learnings": elements,
            "differentiators": [],
            "recommendations": ["Study competitor content", "Adapt successful elements"],
        }

    def _extract_learnings(self, insights: Dict[str, Any]) -> str:
        """Extract key learnings as text."""
        learnings = insights.get("learnings", [])
        recommendations = insights.get("recommendations", [])

        return f"Key learnings: {', '.join(learnings[:3])}. Recommendations: {', '.join(recommendations[:2])}"


class ViralTopicPredictor:
    """Predicts next viral topics using ML and trend analysis."""

    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def predict_viral_topics(
        self, days_ahead: int = 7, category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Predict topics that will go viral."""
        try:
            # Get current trends
            current_trends = await self._get_current_trends()

            # Analyze patterns
            patterns = await self._analyze_viral_patterns(current_trends)

            # Generate predictions
            predictions = await self._generate_predictions(
                patterns, days_ahead, category
            )

            # Rank by viral potential
            ranked = self._rank_by_viral_potential(predictions)

            return ranked[:20]  # Top 20 predictions

        except Exception as e:
            logger.error(f"Viral prediction failed: {e}")
            return []

    async def _get_current_trends(self) -> List[Dict[str, Any]]:
        """Get current trending topics."""
        # This would integrate with trend detection
        return []

    async def _analyze_viral_patterns(
        self, trends: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze patterns in viral content."""
        return {
            "common_themes": [],
            "timing_patterns": {},
            "content_types": [],
            "engagement_patterns": {},
        }

    async def _generate_predictions(
        self, patterns: Dict[str, Any], days: int, category: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Generate viral topic predictions."""
        try:
            prompt = f"""Predict viral topics for the next {days} days in Malayalam social media.

Category focus: {category or 'all categories'}
Current patterns: {json.dumps(patterns, indent=2)}

Generate 10 topic predictions with:
- Topic title
- Why it will go viral
- Predicted peak date
- Confidence score (0-1)
- Target audience

Format as JSON array."""

            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.8,
            )

            content = response.choices[0].message.content.strip()
            import re

            json_match = re.search(r"\[.*\]", content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            logger.error(f"Prediction generation failed: {e}")

        return []

    def _rank_by_viral_potential(
        self, predictions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Rank predictions by viral potential."""
        for pred in predictions:
            score = pred.get("confidence", 0.5)
            # Add additional scoring factors
            if pred.get("urgency"):
                score += 0.1
            if pred.get("novelty"):
                score += 0.1

            pred["viral_score"] = min(score, 1.0)

        return sorted(predictions, key=lambda x: x.get("viral_score", 0), reverse=True)


class ContentRepurposingEngine:
    """Repurposes content for different platforms and formats."""

    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def repurpose_content(
        self,
        source_content: Dict[str, Any],
        target_platform: str,
        target_format: str = "short",
    ) -> Dict[str, Any]:
        """Repurpose content for different platform/format."""
        try:
            # Analyze source content
            source_analysis = self._analyze_source_content(source_content)

            # Generate repurposed version
            repurposed = await self._generate_repurposed_content(
                source_analysis, target_platform, target_format
            )

            # Optimize for target platform
            optimized = await self._optimize_for_platform(
                repurposed, target_platform
            )

            return {
                "source_content_id": source_content.get("id"),
                "target_platform": target_platform,
                "target_format": target_format,
                "repurposed_content": optimized,
                "changes_made": self._identify_changes(source_analysis, optimized),
                "created_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Content repurposing failed: {e}")
            return {"error": str(e)}

    def _analyze_source_content(
        self, content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze source content structure."""
        return {
            "duration": content.get("duration", 0),
            "title": content.get("title", ""),
            "script": content.get("script", ""),
            "key_points": self._extract_key_points(content.get("script", "")),
            "format": content.get("format", "long"),
        }

    def _extract_key_points(self, script: str) -> List[str]:
        """Extract key points from script."""
        # Simple extraction - would use NLP in production
        sentences = script.split(".")
        return [s.strip() for s in sentences[:5] if len(s.strip()) > 20]

    async def _generate_repurposed_content(
        self,
        source_analysis: Dict[str, Any],
        platform: str,
        format_type: str,
    ) -> Dict[str, Any]:
        """Generate repurposed content."""
        try:
            prompt = f"""Repurpose this content for {platform} in {format_type} format:

Original Title: {source_analysis.get('title', '')}
Key Points: {', '.join(source_analysis.get('key_points', []))}

Create:
1. New title optimized for {platform}
2. Condensed script ({format_type} format)
3. Hook for first 3 seconds
4. Call-to-action
5. Platform-specific hashtags

Format as JSON."""

            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.7,
            )

            content = response.choices[0].message.content.strip()
            import re

            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            logger.error(f"Repurposing generation failed: {e}")

        return {
            "title": source_analysis.get("title", ""),
            "script": source_analysis.get("script", "")[:200],
            "hook": "Check this out!",
            "hashtags": [],
        }

    async def _optimize_for_platform(
        self, content: Dict[str, Any], platform: str
    ) -> Dict[str, Any]:
        """Optimize content for specific platform."""
        optimizations = {
            "youtube": {
                "title_length": 60,
                "description_length": 5000,
                "tags_count": 10,
            },
            "instagram": {
                "title_length": 30,
                "caption_length": 2200,
                "hashtags_count": 30,
            },
        }

        platform_specs = optimizations.get(platform, {})
        content["platform_optimized"] = True
        content["optimization_specs"] = platform_specs

        return content

    def _identify_changes(
        self, source: Dict[str, Any], repurposed: Dict[str, Any]
    ) -> List[str]:
        """Identify what changed in repurposing."""
        changes = []

        if source.get("title") != repurposed.get("title"):
            changes.append("Title adapted for platform")
        if len(source.get("script", "")) > len(repurposed.get("script", "")):
            changes.append("Script condensed")
        if repurposed.get("hashtags"):
            changes.append("Hashtags added/updated")

        return changes


class AudienceBehaviorAnalyzer:
    """Analyzes audience behavior patterns."""

    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def analyze_audience_behavior(
        self, analytics_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze audience behavior from analytics."""
        try:
            # Extract patterns
            patterns = self._extract_patterns(analytics_data)

            # Analyze engagement patterns
            engagement_analysis = self._analyze_engagement_patterns(analytics_data)

            # Generate insights
            insights = await self._generate_behavior_insights(
                patterns, engagement_analysis
            )

            return {
                "patterns": patterns,
                "engagement_analysis": engagement_analysis,
                "insights": insights,
                "recommendations": self._generate_recommendations(insights),
                "analyzed_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Audience behavior analysis failed: {e}")
            return {"error": str(e)}

    def _extract_patterns(
        self, analytics_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Extract behavior patterns."""
        if not analytics_data:
            return {}

        # Calculate averages
        avg_engagement = sum(
            a.get("engagement_rate", 0) for a in analytics_data
        ) / len(analytics_data)

        # Best performing times
        best_times = {}
        for data in analytics_data:
            hour = data.get("posted_hour", 12)
            if hour not in best_times:
                best_times[hour] = []
            best_times[hour].append(data.get("engagement_rate", 0))

        best_hour = max(
            best_times.items(), key=lambda x: sum(x[1]) / len(x[1])
        )[0] if best_times else 12

        return {
            "avg_engagement": avg_engagement,
            "best_posting_hour": best_hour,
            "total_content_analyzed": len(analytics_data),
        }

    def _analyze_engagement_patterns(
        self, analytics_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze engagement patterns."""
        return {
            "peak_engagement_times": [],
            "content_type_preferences": {},
            "audience_growth_trend": "stable",
        }

    async def _generate_behavior_insights(
        self, patterns: Dict[str, Any], engagement: Dict[str, Any]
    ) -> List[str]:
        """Generate insights about audience behavior."""
        insights = []

        if patterns.get("best_posting_hour"):
            insights.append(
                f"Audience most active at {patterns['best_posting_hour']}:00"
            )

        if patterns.get("avg_engagement", 0) > 0.05:
            insights.append("High overall engagement - content resonates well")

        return insights

    def _generate_recommendations(self, insights: List[str]) -> List[str]:
        """Generate recommendations based on insights."""
        recommendations = []

        for insight in insights:
            if "most active" in insight.lower():
                recommendations.append("Schedule content during peak hours")
            if "high engagement" in insight.lower():
                recommendations.append("Continue current content strategy")

        return recommendations

