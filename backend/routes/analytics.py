from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, desc, select, text
from sqlalchemy.orm import selectinload
from database import (
    get_db,
    Trends,
    LearningData,
    ModelMetrics,
    PostingOptimization,
    Post,
    Analytics,
)
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json

router = APIRouter()


class AnalyticsResponse(BaseModel):
    platform: str
    total_posts: int
    total_views: int
    total_likes: int
    total_comments: int
    engagement_rate: float
    top_hashtags: List[str]


class InsightsResponse(BaseModel):
    best_posting_times: List[str]
    top_topics: List[str]
    caption_suggestions: List[str]


class TrendsResponse(BaseModel):
    topic: str
    platform: str
    velocity: float
    trend_strength: float
    cross_platform_count: int
    language: str
    freshness: float
    predicted_peak: Optional[datetime]
    created_at: datetime


class OptimizationSuggestionsResponse(BaseModel):
    platform: str
    optimal_hour: int
    optimal_day: int
    engagement_score: float
    confidence: float
    language: str
    recommendation: str


class LearningInsightsResponse(BaseModel):
    total_learning_samples: int
    model_accuracy: Optional[float]
    top_insights: List[str]
    learning_progress: Dict[str, float]
    recent_trends: List[str]


@router.get("/", response_model=List[AnalyticsResponse])
async def get_analytics(
    platform: str = None, days: int = 30, db: AsyncSession = Depends(get_db)
):
    """
    Get analytics data for posts.
    """
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Build query using SQLAlchemy 2.x async syntax
        query = select(
            Post.platform,
            func.count(Post.id).label("total_posts"),
            func.sum(Analytics.views).label("total_views"),
            func.sum(Analytics.likes).label("total_likes"),
            func.sum(Analytics.comments).label("total_comments"),
            func.avg(Analytics.engagement_rate).label("avg_engagement"),
        ).join(Analytics, Post.id == Analytics.post_id)

        if platform:
            query = query.where(Post.platform == platform)

        query = query.where(Post.posted_at >= start_date).group_by(Post.platform)

        results = await db.execute(query)
        analytics_data = results.fetchall()

        response = []
        for row in analytics_data:
            response.append(
                AnalyticsResponse(
                    platform=row.platform,
                    total_posts=row.total_posts,
                    total_views=row.total_views or 0,
                    total_likes=row.total_likes or 0,
                    total_comments=row.total_comments or 0,
                    engagement_rate=row.avg_engagement or 0.0,
                    top_hashtags=[],  # TODO: Implement hashtag extraction
                )
            )

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/insights", response_model=InsightsResponse)
async def get_insights(db: AsyncSession = Depends(get_db)):
    """
    Get AI-generated insights for better posting.
    """
    try:
        # This would integrate with AI service for insights
        # For now, return mock data
        return InsightsResponse(
            best_posting_times=["18:00-20:00", "12:00-14:00"],
            top_topics=["Malayalam Comedy", "College Life", "Travel"],
            caption_suggestions=[
                "നല്ലൊരു കോമഡി വീഡിയോ! 😂 #MalayalamComedy",
                "കോളേജ് ജീവിതം മനസ്സിലാക്കാൻ... 📚 #CollegeLife",
            ],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trends", response_model=List[TrendsResponse])
async def get_trends(
    platform: str = None,
    language: str = "ml",
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """
    Get current trends data for content strategy.
    """
    try:
        query = select(Trends).order_by(desc(Trends.trend_strength))

        if platform:
            query = query.where(Trends.platform == platform)

        if language:
            query = query.where(Trends.language == language)

        query = query.limit(limit)

        results = await db.execute(query)
        trends = results.scalars().all()

        return [
            TrendsResponse(
                topic=trend.topic,
                platform=trend.platform,
                velocity=trend.velocity,
                trend_strength=trend.trend_strength,
                cross_platform_count=trend.cross_platform_count,
                language=trend.language,
                freshness=trend.freshness,
                predicted_peak=trend.predicted_peak,
                created_at=trend.created_at,
            )
            for trend in trends
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/optimization-suggestions", response_model=List[OptimizationSuggestionsResponse]
)
async def get_optimization_suggestions(
    platform: str = None, language: str = "ml", db: AsyncSession = Depends(get_db)
):
    """
    Get posting optimization suggestions based on learning data.
    """
    try:
        query = select(PostingOptimization).order_by(
            desc(PostingOptimization.engagement_score)
        )

        if platform:
            query = query.where(PostingOptimization.platform == platform)

        if language:
            query = query.where(PostingOptimization.language == language)

        results = await db.execute(query)
        optimizations = results.scalars().all()

        response = []
        for opt in optimizations:
            day_names = [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            ]
            day_name = (
                day_names[opt.optimal_day] if 0 <= opt.optimal_day < 7 else "Monday"
            )

            recommendation = f"Post on {opt.platform} at {opt.optimal_hour}:00 on {day_name} (Expected engagement: {opt.engagement_score:.3f})"

            response.append(
                OptimizationSuggestionsResponse(
                    platform=opt.platform,
                    optimal_hour=opt.optimal_hour,
                    optimal_day=opt.optimal_day,
                    engagement_score=opt.engagement_score,
                    confidence=opt.confidence,
                    language=opt.language,
                    recommendation=recommendation,
                )
            )

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/learning-insights", response_model=LearningInsightsResponse)
async def get_learning_insights(db: AsyncSession = Depends(get_db)):
    """
    Get insights from the learning system and model performance.
    """
    try:
        # Get learning data count
        learning_count_result = await db.execute(
            text("SELECT COUNT(*) as count FROM learning_data")
        )
        learning_count = learning_count_result.scalar() or 0

        # Get latest model metrics
        model_metrics_query = (
            select(ModelMetrics)
            .where(ModelMetrics.model_name == "engagement_prediction")
            .order_by(desc(ModelMetrics.training_date))
            .limit(1)
        )
        model_metrics_result = await db.execute(model_metrics_query)
        latest_metrics = model_metrics_result.scalar_one_or_none()

        model_accuracy = None
        if latest_metrics and latest_metrics.metrics:
            if isinstance(latest_metrics.metrics, str):
                metrics_data = json.loads(latest_metrics.metrics)
            else:
                metrics_data = latest_metrics.metrics
            model_accuracy = metrics_data.get("accuracy")

        # Get top insights from learning data
        insights_result = await db.execute(
            text(
                """
                SELECT learning_insights
                FROM learning_data
                WHERE learning_insights IS NOT NULL
                ORDER BY created_at DESC
                LIMIT 10
            """
            )
        )

        insights_rows = insights_result.fetchall()
        top_insights = []
        for row in insights_rows:
            if row.learning_insights:
                if isinstance(row.learning_insights, str):
                    insights_list = json.loads(row.learning_insights)
                else:
                    insights_list = row.learning_insights
                if isinstance(insights_list, list):
                    top_insights.extend(insights_list)

        # Remove duplicates and limit
        top_insights = list(set(top_insights))[:5]

        # Get recent trends
        trends_query = (
            select(Trends.topic)
            .where(Trends.language == "ml")
            .order_by(desc(Trends.created_at))
            .limit(5)
        )
        trends_result = await db.execute(trends_query)
        recent_trends = [row.topic for row in trends_result.fetchall()]

        # Calculate learning progress (mock for now)
        learning_progress = {
            "data_collection": min(
                learning_count / 1000, 1.0
            ),  # Progress towards 1000 samples
            "model_accuracy": model_accuracy or 0.0,
            "trend_coverage": min(
                len(recent_trends) / 10, 1.0
            ),  # Progress towards 10 trends
        }

        return LearningInsightsResponse(
            total_learning_samples=learning_count,
            model_accuracy=model_accuracy,
            top_insights=top_insights,
            learning_progress=learning_progress,
            recent_trends=recent_trends,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
