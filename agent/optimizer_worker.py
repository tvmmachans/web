"""
Agent Optimizer Worker for continuous optimization and learning.
Handles daily cron jobs, trend updates, and adaptive scheduling.
"""

import os
import logging
import asyncio
import sys
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from ai_engine.learning_manager import LearningManager
from agent.utils.database import get_recent_analytics
from database import async_session, PostingOptimization, Trends
from scheduler import schedule_upload

logger = logging.getLogger(__name__)

class OptimizerWorker:
    """
    Worker that performs daily optimization tasks for the content strategist.
    """

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.learning_manager = LearningManager()
        self.is_running = False

    async def start(self):
        """Start the optimizer worker."""
        if self.is_running:
            return

        self.is_running = True

        # Schedule daily tasks
        self.scheduler.add_job(
            self.daily_trend_update,
            trigger=CronTrigger(hour=6),  # 6 AM daily
            id='daily_trend_update',
            replace_existing=True
        )

        self.scheduler.add_job(
            self.weekly_model_retraining,
            trigger=CronTrigger(day_of_week=0, hour=2),  # Monday 2 AM
            id='weekly_model_retraining',
            replace_existing=True
        )

        self.scheduler.add_job(
            self.hourly_schedule_optimization,
            trigger=CronTrigger(minute=0),  # Every hour
            id='hourly_schedule_optimization',
            replace_existing=True
        )

        self.scheduler.add_job(
            self.daily_performance_analysis,
            trigger=CronTrigger(hour=8),  # 8 AM daily
            id='daily_performance_analysis',
            replace_existing=True
        )

        self.scheduler.start()
        logger.info("Optimizer worker started")

        # Start continuous learning in background
        asyncio.create_task(self.learning_manager.start_continuous_learning())

    async def stop(self):
        """Stop the optimizer worker."""
        if not self.is_running:
            return

        self.is_running = False
        self.scheduler.shutdown()
        self.learning_manager.stop_continuous_learning()
        logger.info("Optimizer worker stopped")

    async def daily_trend_update(self):
        """Update trends and optimize content strategy."""
        try:
            logger.info("Starting daily trend update")

            # Update trends from learning manager
            await self.learning_manager.update_trends()

            # Analyze current trends
            trend_insights = await self._analyze_current_trends()

            # Generate content suggestions based on trends
            content_suggestions = await self._generate_content_suggestions(trend_insights)

            # Update posting optimization
            await self.learning_manager.optimize_posting_schedule()

            # Log optimization results
            logger.info(f"Daily trend update completed. Generated {len(content_suggestions)} content suggestions")

        except Exception as e:
            logger.error(f"Daily trend update failed: {e}")

    async def weekly_model_retraining(self):
        """Retrain ML models with new data."""
        try:
            logger.info("Starting weekly model retraining")

            # Retrain models
            await self.learning_manager.retrain_models()

            # Validate model performance
            validation_results = await self._validate_model_performance()

            # Update model configurations if needed
            await self._update_model_configurations(validation_results)

            logger.info("Weekly model retraining completed")

        except Exception as e:
            logger.error(f"Weekly model retraining failed: {e}")

    async def hourly_schedule_optimization(self):
        """Optimize posting schedule based on current performance."""
        try:
            # Get current optimal times
            optimal_times = await self._get_current_optimal_times()

            # Adjust existing scheduled posts if needed
            await self._adjust_scheduled_posts(optimal_times)

            # Update optimization recommendations
            await self._update_optimization_recommendations(optimal_times)

        except Exception as e:
            logger.error(f"Hourly schedule optimization failed: {e}")

    async def daily_performance_analysis(self):
        """Analyze daily performance and generate insights."""
        try:
            logger.info("Starting daily performance analysis")

            # Analyze yesterday's performance
            yesterday = datetime.utcnow() - timedelta(days=1)
            performance_data = await self._collect_performance_data(yesterday)

            # Generate performance insights
            insights = await self._generate_performance_insights(performance_data)

            # Update learning data
            await self._update_learning_from_performance(performance_data, insights)

            # Generate optimization recommendations
            recommendations = await self._generate_optimization_recommendations(insights)

            logger.info(f"Daily performance analysis completed. Generated {len(insights)} insights")

        except Exception as e:
            logger.error(f"Daily performance analysis failed: {e}")

    async def optimize_specific_post(self, post_id: int, platform: str) -> Dict[str, Any]:
        """Optimize a specific post based on learning data."""
        try:
            # Get post data
            post_data = await self._get_post_data(post_id)

            # Get current trends
            trends = await self._get_relevant_trends(platform)

            # Generate optimization suggestions
            suggestions = await self._generate_post_optimizations(post_data, trends)

            # Apply optimizations if automatic mode is enabled
            if os.getenv("AUTO_OPTIMIZE", "false").lower() == "true":
                await self._apply_post_optimizations(post_id, suggestions)

            return {
                "post_id": post_id,
                "optimizations": suggestions,
                "applied": os.getenv("AUTO_OPTIMIZE", "false").lower() == "true"
            }

        except Exception as e:
            logger.error(f"Post optimization failed for {post_id}: {e}")
            return {"error": str(e)}

    async def _analyze_current_trends(self) -> Dict[str, Any]:
        """Analyze current trends for content strategy."""
        try:
            async with async_session() as session:
                # Get recent trends
                result = await session.execute("""
                    SELECT topic, platform, velocity, trend_strength, language,
                           freshness, cross_platform_count
                    FROM trends
                    WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
                    ORDER BY trend_strength DESC
                    LIMIT 20
                """)

                trends = result.fetchall()

                # Analyze by language and platform
                malayalam_trends = [t for t in trends if t.language == 'ml']
                platform_trends = {}
                for trend in trends:
                    if trend.platform not in platform_trends:
                        platform_trends[trend.platform] = []
                    platform_trends[trend.platform].append(trend)

                return {
                    "malayalam_trends": malayalam_trends,
                    "platform_trends": platform_trends,
                    "top_trends": trends[:5],
                    "trend_velocity_avg": sum(t.velocity for t in trends) / len(trends) if trends else 0
                }

        except Exception as e:
            logger.error(f"Trend analysis failed: {e}")
            return {}

    async def _generate_content_suggestions(self, trend_insights: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate content suggestions based on trend analysis."""
        suggestions = []

        try:
            malayalam_trends = trend_insights.get("malayalam_trends", [])
            platform_trends = trend_insights.get("platform_trends", {})

            # Generate Malayalam-specific suggestions
            for trend in malayalam_trends[:3]:  # Top 3 trends
                suggestion = {
                    "type": "malayalam_trend",
                    "topic": trend.topic,
                    "platform": trend.platform,
                    "suggested_title": f"{trend.topic} - മലയാളം കോമഡി",
                    "trend_strength": trend.trend_strength,
                    "optimal_posting_time": await self._get_optimal_time_for_platform(trend.platform),
                    "hashtags": self._generate_malayalam_hashtags(trend.topic)
                }
                suggestions.append(suggestion)

            # Generate cross-platform suggestions
            for platform, trends in platform_trends.items():
                if len(trends) > 1:
                    suggestion = {
                        "type": "cross_platform",
                        "platform": platform,
                        "topics": [t.topic for t in trends[:2]],
                        "suggested_title": f"Cross-platform content: {trends[0].topic}",
                        "engagement_potential": sum(t.trend_strength for t in trends[:2]) / 2
                    }
                    suggestions.append(suggestion)

            return suggestions

        except Exception as e:
            logger.error(f"Content suggestion generation failed: {e}")
            return []

    async def _validate_model_performance(self) -> Dict[str, Any]:
        """Validate current model performance."""
        try:
            # Test engagement prediction accuracy
            test_data = await self.learning_manager.ml_service.collect_training_data(limit=100)

            if test_data.empty:
                return {"status": "no_test_data"}

            # Get predictions
            predictions = []
            for _, row in test_data.iterrows():
                pred = self.learning_manager.ml_service.predict_engagement(dict(row))
                predictions.append(pred)

            # Calculate metrics
            actual_views = test_data['views'].values
            predicted_views = [p['predicted_views'] for p in predictions]

            mae = sum(abs(a - p) for a, p in zip(actual_views, predicted_views)) / len(actual_views)
            accuracy = 1 - (mae / sum(actual_views) * len(actual_views))

            return {
                "status": "success",
                "mae": mae,
                "accuracy": accuracy,
                "test_samples": len(test_data)
            }

        except Exception as e:
            logger.error(f"Model validation failed: {e}")
            return {"status": "error", "error": str(e)}

    async def _update_model_configurations(self, validation_results: Dict[str, Any]):
        """Update model configurations based on validation."""
        try:
            if validation_results.get("status") == "success":
                accuracy = validation_results.get("accuracy", 0)

                # If accuracy is below threshold, trigger model retraining
                if accuracy < 0.7:  # 70% threshold
                    logger.warning(f"Model accuracy {accuracy:.2f} below threshold, retraining...")
                    await self.learning_manager.retrain_models()

        except Exception as e:
            logger.error(f"Model configuration update failed: {e}")

    async def _get_current_optimal_times(self) -> Dict[str, Any]:
        """Get current optimal posting times."""
        try:
            async with async_session() as session:
                result = await session.execute("""
                    SELECT platform, optimal_hour, optimal_day, engagement_score, confidence
                    FROM posting_optimization
                    WHERE last_updated >= CURRENT_DATE - INTERVAL '1 day'
                    ORDER BY engagement_score DESC
                """)

                optimizations = result.fetchall()

                optimal_times = {}
                for opt in optimizations:
                    if opt.platform not in optimal_times:
                        optimal_times[opt.platform] = {
                            "hour": opt.optimal_hour,
                            "day": opt.optimal_day,
                            "score": opt.engagement_score,
                            "confidence": opt.confidence
                        }

                return optimal_times

        except Exception as e:
            logger.error(f"Failed to get optimal times: {e}")
            return {}

    async def _adjust_scheduled_posts(self, optimal_times: Dict[str, Any]):
        """Adjust scheduled posts to optimal times."""
        try:
            # This would integrate with the scheduler to reschedule posts
            # For now, just log the optimal times
            logger.info(f"Optimal posting times: {optimal_times}")

        except Exception as e:
            logger.error(f"Failed to adjust scheduled posts: {e}")

    async def _update_optimization_recommendations(self, optimal_times: Dict[str, Any]):
        """Update optimization recommendations."""
        try:
            # Store recommendations for dashboard
            recommendations = []

            for platform, times in optimal_times.items():
                rec = {
                    "platform": platform,
                    "optimal_hour": times["hour"],
                    "optimal_day": times["day"],
                    "expected_engagement": times["score"],
                    "confidence": times["confidence"],
                    "recommendation": f"Post on {platform} at {times['hour']}:00 on {self._day_name(times['day'])}"
                }
                recommendations.append(rec)

            # Cache recommendations (would be stored in Redis/database)
            self.current_recommendations = recommendations

        except Exception as e:
            logger.error(f"Failed to update optimization recommendations: {e}")

    async def _collect_performance_data(self, date: datetime) -> Dict[str, Any]:
        """Collect performance data for a specific date."""
        try:
            async for session in get_recent_analytics():
                analytics = await get_recent_analytics(session, days=1, start_date=date)
                break

            if not analytics:
                return {}

            # Aggregate performance metrics
            total_views = sum(a.views for a in analytics)
            total_likes = sum(a.likes for a in analytics)
            total_comments = sum(a.comments for a in analytics)
            total_shares = sum(a.shares for a in analytics)

            engagement_rates = [a.engagement_rate for a in analytics if a.engagement_rate > 0]
            avg_engagement = sum(engagement_rates) / len(engagement_rates) if engagement_rates else 0

            # Platform breakdown
            platform_performance = {}
            for analytic in analytics:
                if analytic.platform not in platform_performance:
                    platform_performance[analytic.platform] = {
                        "posts": 0, "views": 0, "likes": 0, "comments": 0, "shares": 0
                    }
                platform_performance[analytic.platform]["posts"] += 1
                platform_performance[analytic.platform]["views"] += analytic.views
                platform_performance[analytic.platform]["likes"] += analytic.likes
                platform_performance[analytic.platform]["comments"] += analytic.comments
                platform_performance[analytic.platform]["shares"] += analytic.shares

            return {
                "date": date.isoformat(),
                "total_posts": len(analytics),
                "total_views": total_views,
                "total_likes": total_likes,
                "total_comments": total_comments,
                "total_shares": total_shares,
                "avg_engagement": avg_engagement,
                "platform_performance": platform_performance
            }

        except Exception as e:
            logger.error(f"Performance data collection failed: {e}")
            return {}

    async def _generate_performance_insights(self, performance_data: Dict[str, Any]) -> List[str]:
        """Generate insights from performance data."""
        insights = []

        try:
            if not performance_data:
                return ["No performance data available"]

            avg_engagement = performance_data.get("avg_engagement", 0)
            platform_performance = performance_data.get("platform_performance", {})

            # Engagement insights
            if avg_engagement > 0.05:
                insights.append("Excellent engagement performance above 5%")
            elif avg_engagement > 0.02:
                insights.append("Good engagement performance above 2%")
            else:
                insights.append("Engagement performance needs improvement")

            # Platform insights
            best_platform = max(platform_performance.items(),
                              key=lambda x: x[1]["views"]) if platform_performance else None
            if best_platform:
                insights.append(f"{best_platform[0]} is the top performing platform")

            # Content insights
            total_posts = performance_data.get("total_posts", 0)
            if total_posts > 10:
                insights.append("High posting frequency - consider quality over quantity")

            return insights

        except Exception as e:
            logger.error(f"Performance insights generation failed: {e}")
            return ["Unable to generate insights"]

    async def _update_learning_from_performance(self, performance_data: Dict[str, Any], insights: List[str]):
        """Update learning models from performance data."""
        try:
            # This would feed performance data back into learning models
            # For now, just log the insights
            logger.info(f"Performance insights: {insights}")

        except Exception as e:
            logger.error(f"Learning update from performance failed: {e}")

    async def _generate_optimization_recommendations(self, insights: List[str]) -> List[str]:
        """Generate optimization recommendations from insights."""
        recommendations = []

        try:
            for insight in insights:
                if "needs improvement" in insight:
                    recommendations.extend([
                        "Experiment with different posting times",
                        "Try new content formats",
                        "Increase audience interaction"
                    ])
                elif "excellent" in insight.lower():
                    recommendations.extend([
                        "Continue current successful strategy",
                        "Scale up posting frequency",
                        "Experiment with similar content types"
                    ])

            return recommendations[:5]  # Limit to 5 recommendations

        except Exception as e:
            logger.error(f"Optimization recommendations generation failed: {e}")
            return []

    async def _get_post_data(self, post_id: int) -> Dict[str, Any]:
        """Get data for a specific post."""
        try:
            async with async_session() as session:
                result = await session.execute(f"SELECT * FROM posts WHERE id = {post_id}")
                post = result.fetchone()
                return dict(post) if post else {}

        except Exception as e:
            logger.error(f"Failed to get post data for {post_id}: {e}")
            return {}

    async def _get_relevant_trends(self, platform: str) -> List[Dict[str, Any]]:
        """Get relevant trends for a platform."""
        try:
            async with async_session() as session:
                result = await session.execute(f"""
                    SELECT * FROM trends
                    WHERE platform = '{platform}' AND language = 'ml'
                    ORDER BY trend_strength DESC
                    LIMIT 5
                """)
                trends = result.fetchall()
                return [dict(trend) for trend in trends]

        except Exception as e:
            logger.error(f"Failed to get trends for {platform}: {e}")
            return []

    async def _generate_post_optimizations(self, post_data: Dict[str, Any], trends: List[Dict[str, Any]]) -> List[str]:
        """Generate optimization suggestions for a post."""
        optimizations = []

        try:
            # Title optimization
            title = post_data.get("title", "")
            if len(title) < 30:
                optimizations.append("Title is too short - consider making it more descriptive")

            # Hashtag optimization
            caption = post_data.get("ai_caption", "")
            hashtag_count = caption.count("#")
            if hashtag_count < 3:
                optimizations.append("Add more relevant hashtags for better reach")

            # Trend alignment
            if trends:
                top_trend = trends[0]["topic"]
                if top_trend.lower() not in caption.lower():
                    optimizations.append(f"Consider incorporating trending topic: {top_trend}")

            # Timing optimization
            scheduled_time = post_data.get("scheduled_at")
            if scheduled_time:
                hour = scheduled_time.hour
                if not (18 <= hour <= 21):  # Peak Malayalam viewing hours
                    optimizations.append("Consider posting during peak Malayalam viewing hours (6-9 PM)")

            return optimizations

        except Exception as e:
            logger.error(f"Post optimization generation failed: {e}")
            return []

    async def _apply_post_optimizations(self, post_id: int, optimizations: List[str]):
        """Apply optimizations to a post."""
        try:
            # This would update the post in database with optimizations
            logger.info(f"Applying optimizations to post {post_id}: {optimizations}")

        except Exception as e:
            logger.error(f"Failed to apply optimizations to post {post_id}: {e}")

    async def _get_optimal_time_for_platform(self, platform: str) -> str:
        """Get optimal posting time for a platform."""
        try:
            optimal_times = await self._get_current_optimal_times()
            platform_time = optimal_times.get(platform, {})

            if platform_time:
                hour = platform_time["hour"]
                day = self._day_name(platform_time["day"])
                return f"{day} at {hour}:00"
            else:
                # Default times for Malayalam content
                return "Tuesday at 19:00" if platform == "youtube" else "Friday at 18:00"

        except Exception as e:
            logger.error(f"Failed to get optimal time for {platform}: {e}")
            return "18:00"

    def _generate_malayalam_hashtags(self, topic: str) -> List[str]:
        """Generate Malayalam hashtags for a topic."""
        base_hashtags = ["#മലയാളം", "#കേരളം", "#കോമഡി"]

        # Add topic-specific hashtags
        if "കോമഡി" in topic:
            base_hashtags.extend(["#ഫണ്", "#ലോല"])
        elif "സോങ്" in topic:
            base_hashtags.extend(["#സംഗീതം", "#ഗാനം"])

        return base_hashtags

    def _day_name(self, day_num: int) -> str:
        """Convert day number to name."""
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        return days[day_num] if 0 <= day_num < 7 else "Monday"

    async def get_current_recommendations(self) -> List[Dict[str, Any]]:
        """Get current optimization recommendations."""
        return getattr(self, 'current_recommendations', [])
