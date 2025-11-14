from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, desc, and_, or_, select, text
from sqlalchemy.orm import selectinload
from database import get_db, Trends, LearningData, Analytics, Post
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json

router = APIRouter()

class TrendPredictionResponse(BaseModel):
    topic: str
    platform: str
    predicted_velocity: float
    predicted_peak_date: Optional[datetime]
    confidence_score: float
    trend_strength: float
    language: str
    cross_platform_count: int

class WeeklyTrendForecastResponse(BaseModel):
    week_start: datetime
    week_end: datetime
    top_trends: List[TrendPredictionResponse]
    total_predicted_trends: int
    language_focus: str

class TrendAnalysisResponse(BaseModel):
    current_trends: List[Dict]
    emerging_trends: List[Dict]
    declining_trends: List[Dict]
    cross_platform_insights: List[Dict]
    language_specific_insights: Dict[str, List[Dict]]

@router.get("/weekly-forecast", response_model=WeeklyTrendForecastResponse)
async def get_weekly_trend_forecast(
    language: str = "ml",
    db: AsyncSession = Depends(get_db)
):
    """
    Get weekly trend forecast for Malayalam content.
    """
    try:
        # Calculate week boundaries
        today = datetime.utcnow()
        week_start = today - timedelta(days=today.weekday())  # Monday
        week_end = week_start + timedelta(days=6)  # Sunday

        # Get current trends with predictions
        trends_query = select(Trends).where(
            Trends.language == language,
            Trends.created_at >= week_start - timedelta(days=7)
        ).order_by(desc(Trends.velocity)).limit(20)
        trends_result = await db.execute(trends_query)
        trends = trends_result.scalars().all()

        # Generate predictions for top trends
        top_trends = []
        for trend in trends[:10]:  # Top 10 trends
            # Simple prediction logic (in production, use ML models)
            predicted_velocity = trend.velocity * (1 + trend.trend_strength / 100)
            predicted_peak = week_start + timedelta(days=3)  # Mid-week peak

            confidence_score = min(trend.trend_strength / 10, 0.95)  # Confidence based on strength

            top_trends.append(TrendPredictionResponse(
                topic=trend.topic,
                platform=trend.platform,
                predicted_velocity=predicted_velocity,
                predicted_peak_date=predicted_peak,
                confidence_score=confidence_score,
                trend_strength=trend.trend_strength,
                language=trend.language,
                cross_platform_count=trend.cross_platform_count
            ))

        return WeeklyTrendForecastResponse(
            week_start=week_start,
            week_end=week_end,
            top_trends=top_trends,
            total_predicted_trends=len(top_trends),
            language_focus=language
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis", response_model=TrendAnalysisResponse)
async def get_trend_analysis(
    language: str = "ml",
    days: int = 7,
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive trend analysis with insights.
    """
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Get current trends
        current_trends_query = select(Trends).where(
            Trends.language == language,
            Trends.created_at >= start_date
        ).order_by(desc(Trends.velocity)).limit(10)
        current_trends_result = await db.execute(current_trends_query)

        current_trends = []
        for trend in current_trends_result.scalars().all():
            current_trends.append({
                "topic": trend.topic,
                "platform": trend.platform,
                "velocity": trend.velocity,
                "trend_strength": trend.trend_strength,
                "freshness": trend.freshness,
                "cross_platform_count": trend.cross_platform_count
            })

        # Emerging trends (high velocity, recent)
        emerging_trends_query = select(Trends).where(
            Trends.language == language,
            Trends.created_at >= start_date,
            Trends.velocity > 50,
            Trends.freshness > 0.7
        ).order_by(desc(Trends.velocity)).limit(5)
        emerging_trends_result = await db.execute(emerging_trends_query)

        emerging_trends = []
        for trend in emerging_trends_result.scalars().all():
            emerging_trends.append({
                "topic": trend.topic,
                "platform": trend.platform,
                "velocity": trend.velocity,
                "growth_rate": trend.trend_strength,
                "emergence_date": trend.created_at
            })

        # Declining trends (low velocity, older)
        declining_trends_query = select(Trends).where(
            Trends.language == language,
            Trends.created_at >= start_date - timedelta(days=14),
            Trends.velocity < 20
        ).order_by(Trends.velocity).limit(5)
        declining_trends_result = await db.execute(declining_trends_query)

        declining_trends = []
        for trend in declining_trends_result.scalars().all():
            declining_trends.append({
                "topic": trend.topic,
                "platform": trend.platform,
                "current_velocity": trend.velocity,
                "trend_strength": trend.trend_strength,
                "last_updated": trend.created_at
            })

        # Cross-platform insights
        cross_platform_result = await db.execute(
            text("""
                SELECT platform, COUNT(*) as trend_count,
                       AVG(velocity) as avg_velocity,
                       AVG(trend_strength) as avg_strength
                FROM trends
                WHERE language = :language AND created_at >= :start_date
                GROUP BY platform
                ORDER BY trend_count DESC
            """),
            {"language": language, "start_date": start_date}
        )

        cross_platform_insights = []
        for row in cross_platform_result.fetchall():
            cross_platform_insights.append({
                "platform": row.platform,
                "trend_count": row.trend_count,
                "avg_velocity": row.avg_velocity,
                "avg_strength": row.avg_strength
            })

        # Language-specific insights
        language_insights = {
            "ml": [],  # Malayalam insights
            "en": []   # English insights for comparison
        }

        # Malayalam-specific insights
        ml_insights_result = await db.execute(
            text("""
                SELECT topic, platform, velocity, trend_strength,
                       cross_platform_count, freshness
                FROM trends
                WHERE language = 'ml' AND created_at >= :start_date
                ORDER BY velocity DESC
                LIMIT 5
            """),
            {"start_date": start_date}
        )

        for row in ml_insights_result.fetchall():
            language_insights["ml"].append({
                "topic": row.topic,
                "platform": row.platform,
                "velocity": row.velocity,
                "trend_strength": row.trend_strength,
                "cross_platform_count": row.cross_platform_count,
                "freshness": row.freshness
            })

        return TrendAnalysisResponse(
            current_trends=current_trends,
            emerging_trends=emerging_trends,
            declining_trends=declining_trends,
            cross_platform_insights=cross_platform_insights,
            language_specific_insights=language_insights
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/predictions/{topic}")
async def get_topic_prediction(
    topic: str,
    language: str = "ml",
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed prediction for a specific topic.
    """
    try:
        # Get trend data for the topic
        trend_query = select(Trends).where(
            Trends.topic.ilike(f"%{topic}%"),
            Trends.language == language
        ).order_by(desc(Trends.created_at)).limit(1)
        trend_result = await db.execute(trend_query)
        trend = trend_result.scalar_one_or_none()

        if not trend:
            raise HTTPException(status_code=404, detail="Topic not found")

        # Get historical data for prediction
        historical_query = select(Trends).where(
            Trends.topic.ilike(f"%{topic}%"),
            Trends.language == language
        ).order_by(Trends.created_at).limit(10)
        historical_result = await db.execute(historical_query)
        historical_data = historical_result.scalars().all()

        # Simple prediction algorithm (in production, use ML models)
        velocities = [t.velocity for t in historical_data]
        avg_velocity = sum(velocities) / len(velocities) if velocities else 0

        # Predict next 7 days
        predictions = []
        for i in range(7):
            predicted_date = datetime.utcnow() + timedelta(days=i)
            predicted_velocity = avg_velocity * (1 + (trend.trend_strength / 100) * (i / 7))

            predictions.append({
                "date": predicted_date,
                "predicted_velocity": predicted_velocity,
                "confidence": max(0.5, 1 - (i * 0.1))  # Confidence decreases over time
            })

        return {
            "topic": trend.topic,
            "current_velocity": trend.velocity,
            "trend_strength": trend.trend_strength,
            "platform": trend.platform,
            "language": trend.language,
            "predictions": predictions,
            "historical_data": [
                {
                    "date": t.created_at,
                    "velocity": t.velocity,
                    "trend_strength": t.trend_strength
                } for t in historical_data
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
