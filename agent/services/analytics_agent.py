import os
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
import statistics
import sys

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from agent.config.settings import MIN_ENGAGEMENT_RATE_THRESHOLD, ANALYTICS_RETENTION_DAYS
from agent.utils.database import get_recent_analytics, create_analytics_record
from openai import OpenAI

logger = logging.getLogger(__name__)

class AnalyticsAgent:
    """
    AI-powered analytics agent that analyzes performance and provides insights.
    Learns from data to improve future decisions.
    """

    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def analyze_performance(self, post_id: int = None, platform: str = None, days: int = 30) -> Dict[str, Any]:
        """
        Analyze performance of posts and provide insights.
        """
        try:
            async for session in get_recent_analytics():
                analytics = await get_recent_analytics(session, days)
                break

            if not analytics:
                return {"error": "No analytics data available"}

            # Filter by post_id or platform if specified
            if post_id:
                analytics = [a for a in analytics if a.post_id == post_id]
            if platform:
                analytics = [a for a in analytics if a.platform == platform]

            # Calculate metrics
            total_posts = len(analytics)
            total_views = sum(a.views for a in analytics)
            total_likes = sum(a.likes for a in analytics)
            total_comments = sum(a.comments for a in analytics)
            total_shares = sum(a.shares for a in analytics)

            engagement_rates = [a.engagement_rate for a in analytics if a.engagement_rate > 0]
            avg_engagement = statistics.mean(engagement_rates) if engagement_rates else 0

            # Platform breakdown
            platform_stats = {}
            for analytic in analytics:
                if analytic.platform not in platform_stats:
                    platform_stats[analytic.platform] = {
                        "posts": 0, "views": 0, "likes": 0, "comments": 0, "engagement": []
                    }
                platform_stats[analytic.platform]["posts"] += 1
                platform_stats[analytic.platform]["views"] += analytic.views
                platform_stats[analytic.platform]["likes"] += analytic.likes
                platform_stats[analytic.platform]["comments"] += analytic.comments
                if analytic.engagement_rate > 0:
                    platform_stats[analytic.platform]["engagement"].append(analytic.engagement_rate)

            # Calculate averages for platforms
            for platform_data in platform_stats.values():
                engagement_list = platform_data["engagement"]
                platform_data["avg_engagement"] = statistics.mean(engagement_list) if engagement_list else 0
                del platform_data["engagement"]

            # Generate AI insights
            insights = await self._generate_insights(analytics, platform_stats)

            analysis = {
                "total_posts": total_posts,
                "total_views": total_views,
                "total_likes": total_likes,
                "total_comments": total_comments,
                "total_shares": total_shares,
                "average_engagement_rate": avg_engagement,
                "platform_breakdown": platform_stats,
                "insights": insights,
                "analyzed_at": datetime.utcnow().isoformat()
            }

            logger.info(f"Performance analysis completed for {total_posts} posts")
            return analysis

        except Exception as e:
            logger.error(f"Error analyzing performance: {e}")
            return {"error": str(e)}

    async def predict_success(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict the success potential of a post based on historical data.
        """
        try:
            # Get historical data for training
            async for session in get_recent_analytics():
                analytics = await get_recent_analytics(session, 90)  # 90 days for training
                break

            if not analytics:
                return {"prediction": 0.5, "confidence": 0.1, "reasoning": "No historical data"}

            # Simple prediction based on content features
            # In a real implementation, this would use ML models
            prediction_data = {
                "title_length": len(post_data.get("title", "")),
                "has_caption": bool(post_data.get("ai_caption")),
                "platform": post_data.get("platform", "youtube"),
                "duration": post_data.get("duration", 0)
            }

            # Calculate success score based on historical patterns
            success_score = await self._calculate_success_score(prediction_data, analytics)

            return {
                "prediction": success_score,
                "confidence": 0.7,  # Placeholder
                "reasoning": f"Based on {len(analytics)} historical posts",
                "recommendations": await self._generate_recommendations(success_score, post_data)
            }

        except Exception as e:
            logger.error(f"Error predicting success: {e}")
            return {"prediction": 0.5, "confidence": 0.1, "reasoning": "Error in prediction"}

    async def learn_from_performance(self) -> Dict[str, Any]:
        """
        Learn from recent performance data to improve future decisions.
        """
        try:
            analysis = await self.analyze_performance(days=30)

            # Extract learning points
            learning = {
                "best_platform": self._find_best_platform(analysis),
                "optimal_posting_times": await self._find_optimal_times(analysis),
                "content_insights": await self._extract_content_insights(analysis),
                "engagement_drivers": await self._identify_engagement_drivers(analysis),
                "learned_at": datetime.utcnow().isoformat()
            }

            logger.info("Learning completed from performance data")
            return learning

        except Exception as e:
            logger.error(f"Error learning from performance: {e}")
            return {"error": str(e)}

    async def _generate_insights(self, analytics: List, platform_stats: Dict) -> List[str]:
        """
        Generate AI-powered insights from analytics data.
        """
        try:
            if not analytics:
                return ["No data available for insights"]

            # Prepare data summary for AI
            data_summary = f"""
            Analytics Summary:
            - Total posts: {len(analytics)}
            - Platforms: {list(platform_stats.keys())}
            - Average engagement: {statistics.mean([a.engagement_rate for a in analytics if a.engagement_rate > 0]) if analytics else 0:.3f}

            Platform breakdown: {platform_stats}
            """

            prompt = f"""
            Analyze this social media analytics data and provide 3-5 key insights for improving future performance.
            Focus on platform performance, engagement patterns, and actionable recommendations.

            {data_summary}

            Provide insights as a numbered list.
            """

            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.7
            )

            insights_text = response.choices[0].message.content.strip()
            insights = [line.strip() for line in insights_text.split('\n') if line.strip() and not line.startswith('#')]

            return insights[:5]  # Limit to 5 insights

        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return ["Unable to generate insights due to error"]

    async def _calculate_success_score(self, prediction_data: Dict, historical_data: List) -> float:
        """
        Calculate success prediction score based on historical data.
        """
        try:
            # Simple scoring based on historical patterns
            score = 0.5  # Base score

            # Platform performance
            platform = prediction_data.get("platform", "youtube")
            platform_posts = [a for a in historical_data if a.platform == platform]
            if platform_posts:
                platform_engagement = statistics.mean([a.engagement_rate for a in platform_posts if a.engagement_rate > 0])
                if platform_engagement > MIN_ENGAGEMENT_RATE_THRESHOLD:
                    score += 0.2

            # Content features
            if prediction_data.get("has_caption"):
                score += 0.1

            title_length = prediction_data.get("title_length", 0)
            if 30 <= title_length <= 60:
                score += 0.1

            duration = prediction_data.get("duration", 0)
            if platform == "instagram" and duration <= 90:
                score += 0.1
            elif platform == "youtube" and duration >= 300:  # 5+ minutes
                score += 0.1

            return min(max(score, 0.0), 1.0)  # Clamp between 0 and 1

        except Exception as e:
            logger.error(f"Error calculating success score: {e}")
            return 0.5

    async def _generate_recommendations(self, success_score: float, post_data: Dict) -> List[str]:
        """
        Generate recommendations based on prediction score.
        """
        try:
            recommendations = []

            if success_score < 0.4:
                recommendations.extend([
                    "Consider improving the title to be more engaging",
                    "Add a compelling caption with relevant hashtags",
                    "Review content quality and engagement potential"
                ])
            elif success_score < 0.7:
                recommendations.extend([
                    "Title and content look good",
                    "Consider optimal posting time for better reach",
                    "Monitor initial engagement and adjust strategy if needed"
                ])
            else:
                recommendations.extend([
                    "High potential content - great job!",
                    "Ensure optimal posting time for maximum reach",
                    "Consider cross-promotion on other platforms"
                ])

            return recommendations

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return ["Review content and posting strategy"]

    def _find_best_platform(self, analysis: Dict) -> str:
        """
        Find the best performing platform from analysis.
        """
        try:
            platform_stats = analysis.get("platform_breakdown", {})
            if not platform_stats:
                return "youtube"

            best_platform = max(platform_stats.items(),
                              key=lambda x: x[1].get("avg_engagement", 0))
            return best_platform[0]

        except Exception as e:
            logger.error(f"Error finding best platform: {e}")
            return "youtube"

    async def _find_optimal_times(self, analysis: Dict) -> List[str]:
        """
        Find optimal posting times (placeholder - would need time-based analytics).
        """
        # This would analyze posting times vs engagement
        # For now, return general recommendations
        return ["18:00-20:00", "12:00-14:00", "09:00-11:00"]

    async def _extract_content_insights(self, analysis: Dict) -> List[str]:
        """
        Extract insights about content performance.
        """
        try:
            insights = []
            avg_engagement = analysis.get("average_engagement_rate", 0)

            if avg_engagement > MIN_ENGAGEMENT_RATE_THRESHOLD:
                insights.append("Content is performing above average")
            else:
                insights.append("Content engagement could be improved")

            platform_breakdown = analysis.get("platform_breakdown", {})
            if len(platform_breakdown) > 1:
                insights.append("Multi-platform strategy is effective")

            return insights

        except Exception as e:
            logger.error(f"Error extracting content insights: {e}")
            return ["Content analysis inconclusive"]

    async def _identify_engagement_drivers(self, analysis: Dict) -> List[str]:
        """
        Identify what drives engagement.
        """
        try:
            drivers = []
            total_likes = analysis.get("total_likes", 0)
            total_comments = analysis.get("total_comments", 0)
            total_shares = analysis.get("total_shares", 0)

            if total_likes > total_comments:
                drivers.append("Likes are the primary engagement metric")
            if total_comments > total_shares:
                drivers.append("Comments indicate strong audience interaction")
            if total_shares > 0:
                drivers.append("Shares show content virality potential")

            return drivers or ["Engagement patterns still being analyzed"]

        except Exception as e:
            logger.error(f"Error identifying engagement drivers: {e}")
            return ["Engagement analysis inconclusive"]
