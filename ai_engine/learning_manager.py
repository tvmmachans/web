"""
AI Engine Learning Manager for continuous learning and adaptation.
Handles data collection, model training, and adaptive content generation.
Enhanced with advanced ML models and Malayalam-specific learning.
"""

import os
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import joblib
import numpy as np
import pandas as pd
try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification, AutoModelForCausalLM
except ImportError:
    pipeline = None
    AutoTokenizer = None
    AutoModelForSequenceClassification = None
    AutoModelForCausalLM = None
try:
    import xgboost as xgb
except ImportError:
    xgb = None
try:
    from prophet import Prophet
except ImportError:
    Prophet = None
try:
    import torch
except ImportError:
    torch = None
try:
    from sklearn.metrics import accuracy_score, precision_recall_fscore_support
except ImportError:
    accuracy_score = None
    precision_recall_fscore_support = None
try:
    import psutil
except ImportError:
    psutil = None
try:
    import gc
except ImportError:
    gc = None

try:
    from backend.database import async_session, Trends, LearningData, ModelMetrics, PostingOptimization
except ImportError:
    async_session = None
    Trends = None
    LearningData = None
    ModelMetrics = None
    PostingOptimization = None
try:
    from orchestrator.services.ml_prediction import MLPredictionService
except ImportError:
    MLPredictionService = None
except Exception as e:
    MLPredictionService = None
try:
    from backend.voice_engine.emotion_tts import EmotionAwareTTS
except ImportError:
    EmotionAwareTTS = None

logger = logging.getLogger(__name__)

class LearningManager:
    """
    Manages continuous learning for the Malayalam content strategist.
    """

    def __init__(self):
        self.ml_service = MLPredictionService() if MLPredictionService else None
        self.sentiment_analyzer = None
        self.caption_model = None
        self.prophet_model = None
        self.learning_active = False

        # Advanced models for enhanced learning
        self.transformer_sentiment_model = None
        self.malayalam_caption_generator = None
        self.voice_emotion_analyzer = None
        self.model_versions = {}
        self.performance_history = []

        # Initialize models
        self._initialize_models()
        self._initialize_advanced_models()

    def _initialize_models(self):
        """Initialize ML models and pipelines."""
        try:
            # Sentiment analysis for Malayalam content
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                tokenizer="cardiffnlp/twitter-roberta-base-sentiment-latest"
            )

            # Caption generation model (DistilBERT fine-tuned)
            self.caption_model = {
                'tokenizer': AutoTokenizer.from_pretrained('distilbert-base-multilingual-cased'),
                'model': AutoModelForSequenceClassification.from_pretrained('distilbert-base-multilingual-cased')
            }

            # Prophet for trend prediction
            self.prophet_model = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=True,
                daily_seasonality=True,
                changepoint_prior_scale=0.05
            )

            logger.info("Learning manager models initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize models: {e}")

    def _initialize_advanced_models(self):
        """Initialize advanced ML models for enhanced learning."""
        try:
            # Transformer-based sentiment analysis for Malayalam
            self.transformer_sentiment_model = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                tokenizer="cardiffnlp/twitter-roberta-base-sentiment-latest"
            )

            # Malayalam caption generator using GPT-2 fine-tuned
            self.malayalam_caption_generator = pipeline(
                "text-generation",
                model="gpt2",
                tokenizer="gpt2",
                max_length=100,
                num_return_sequences=1
            )

            # Voice emotion analyzer using pre-trained model
            self.voice_emotion_analyzer = pipeline(
                "audio-classification",
                model="ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition"
            )

            # Initialize model versions and performance tracking
            self.model_versions = {
                'sentiment': '1.0',
                'caption_generator': '1.0',
                'voice_emotion': '1.0'
            }

            self.performance_history = []

            logger.info("Advanced models initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize advanced models: {e}")
            # Continue without advanced models if initialization fails

    async def collect_learning_data(self, post_id: int, actual_performance: Dict[str, Any]):
        """
        Collect performance data for learning.
        """
        try:
            async with async_session() as session:
                # Get post features from database
                post_result = await session.execute(f"SELECT * FROM posts WHERE id = {post_id}")
                post = post_result.fetchone()

                if not post:
                    logger.warning(f"Post {post_id} not found for learning data collection")
                    return

                # Extract features
                features = self._extract_post_features(post)

                # Create learning data record
                learning_data = LearningData(
                    post_id=post_id,
                    features=json.dumps(features),
                    actual_performance=json.dumps(actual_performance),
                    predicted_performance=json.dumps(self.ml_service.predict_engagement(features)),
                    feedback_score=self._calculate_feedback_score(features, actual_performance),
                    learning_insights=json.dumps(self._generate_insights(features, actual_performance))
                )

                session.add(learning_data)
                await session.commit()

                logger.info(f"Collected learning data for post {post_id}")

        except Exception as e:
            logger.error(f"Failed to collect learning data: {e}")

    async def update_trends(self):
        """
        Update trend data from various sources.
        """
        try:
            # Collect trends from social media APIs
            malayalam_trends = await self._collect_malayalam_trends()
            platform_trends = await self._collect_platform_trends()

            async with async_session() as session:
                # Store trends in database
                for trend_data in malayalam_trends + platform_trends:
                    trend = Trends(
                        topic=trend_data['topic'],
                        platform=trend_data['platform'],
                        velocity=trend_data['velocity'],
                        trend_strength=trend_data['strength'],
                        cross_platform_count=trend_data['cross_platform'],
                        language=trend_data.get('language', 'ml'),
                        freshness=trend_data['freshness'],
                        predicted_peak=trend_data.get('predicted_peak')
                    )
                    session.add(trend)

                await session.commit()
                logger.info(f"Updated {len(malayalam_trends + platform_trends)} trends")

        except Exception as e:
            logger.error(f"Failed to update trends: {e}")

    async def retrain_models(self):
        """
        Retrain ML models with new data.
        """
        try:
            # Collect training data
            training_data = await self.ml_service.collect_training_data()

            if training_data.empty:
                logger.warning("No training data available")
                return

            # Train engagement prediction model
            engagement_metrics = self.ml_service.train_model(training_data)

            # Train trend prediction model
            trend_metrics = await self._train_trend_model()

            # Store model metrics
            await self._store_model_metrics(engagement_metrics, trend_metrics)

            logger.info("Model retraining completed")

        except Exception as e:
            logger.error(f"Model retraining failed: {e}")

    async def optimize_posting_schedule(self):
        """
        Optimize posting times based on learning data.
        """
        try:
            async with async_session() as session:
                # Analyze historical posting performance
                result = await session.execute("""
                    SELECT
                        EXTRACT(hour from posted_at) as hour,
                        EXTRACT(dow from posted_at) as day_of_week,
                        AVG(analytics.engagement_rate) as avg_engagement,
                        COUNT(*) as post_count
                    FROM posts p
                    JOIN analytics ON p.id = analytics.post_id
                    WHERE p.posted_at IS NOT NULL
                    GROUP BY hour, day_of_week
                    ORDER BY avg_engagement DESC
                """)

                optimizations = result.fetchall()

                # Update posting optimization table
                for opt in optimizations:
                    optimization = PostingOptimization(
                        platform="combined",  # Can be platform-specific later
                        optimal_hour=int(opt.hour),
                        optimal_day=int(opt.day_of_week),
                        engagement_score=float(opt.avg_engagement),
                        confidence=min(float(opt.post_count) / 10.0, 1.0),  # Confidence based on sample size
                        language="ml",
                        sample_size=int(opt.post_count)
                    )
                    session.add(optimization)

                await session.commit()
                logger.info("Posting schedule optimization completed")

        except Exception as e:
            logger.error(f"Failed to optimize posting schedule: {e}")

    async def generate_adaptive_caption(self, video_path: str, trend_context: Dict[str, Any]) -> str:
        """
        Generate caption with continuous learning adaptation.
        """
        try:
            # Lazy import to avoid circular dependency
            from backend.services.ai_service import generate_caption_service

            # Get base caption
            base_caption = await generate_caption_service(video_path, "ml")

            # Analyze sentiment and adapt
            sentiment = self.sentiment_analyzer(base_caption)[0]

            # Incorporate trend context
            trend_boost = self._calculate_trend_boost(trend_context)

            # Apply Malayalam-specific optimizations
            adapted_caption = await self._adapt_caption_for_malayalam(
                base_caption, sentiment, trend_boost, trend_context
            )

            return adapted_caption

        except Exception as e:
            logger.error(f"Failed to generate adaptive caption: {e}")
            # Lazy import for fallback
            from backend.services.ai_service import generate_caption_service
            return await generate_caption_service(video_path, "ml")

    def _extract_post_features(self, post) -> Dict[str, Any]:
        """Extract features from post data."""
        return {
            'title_length': len(post.title or ''),
            'has_caption': bool(post.ai_caption),
            'platform': post.platform,
            'duration': post.duration or 0,
            'has_subtitles': bool(post.ai_subtitles),
            'posted_hour': post.scheduled_at.hour if post.scheduled_at else 12,
            'posted_day': post.scheduled_at.weekday() if post.scheduled_at else 0,
            'title_has_emojis': any(ord(char) > 127 for char in (post.title or '')),
            'caption_has_emojis': any(ord(char) > 127 for char in (post.ai_caption or ''))
        }

    def _calculate_feedback_score(self, features: Dict[str, Any], actual: Dict[str, Any]) -> float:
        """Calculate how well predictions matched reality."""
        predicted = self.ml_service.predict_engagement(features)

        # Simple feedback score based on prediction accuracy
        views_accuracy = 1 - abs(predicted['predicted_views'] - actual.get('views', 0)) / max(actual.get('views', 1), 1)
        likes_accuracy = 1 - abs(predicted['predicted_likes'] - actual.get('likes', 0)) / max(actual.get('likes', 1), 1)

        return (views_accuracy + likes_accuracy) / 2

    def _generate_insights(self, features: Dict[str, Any], actual: Dict[str, Any]) -> Dict[str, Any]:
        """Generate learning insights from performance data."""
        insights = {}

        # Time-based insights
        if features.get('posted_hour', 12) in [18, 19, 20]:
            insights['time_performance'] = 'evening_posts_perform_better'
        elif features.get('posted_hour', 12) in [6, 7, 8]:
            insights['time_performance'] = 'morning_posts_underperform'

        # Content-based insights
        if features.get('has_emojis', False) and actual.get('likes', 0) > actual.get('views', 0) * 0.05:
            insights['emoji_impact'] = 'emojis_boost_engagement'

        if len(features.get('title', '')) > 50 and actual.get('views', 0) > 10000:
            insights['title_length'] = 'longer_titles_better'

        return insights

    async def _collect_malayalam_trends(self) -> List[Dict[str, Any]]:
        """Collect Malayalam-specific trends."""
        # This would integrate with Malayalam social media APIs
        # For now, return mock data
        return [
            {
                'topic': 'മലയാളം കോമഡി',
                'platform': 'youtube',
                'velocity': 0.8,
                'strength': 0.9,
                'cross_platform': 3,
                'language': 'ml',
                'freshness': 0.95,
                'predicted_peak': datetime.utcnow() + timedelta(hours=24)
            }
        ]

    async def _collect_platform_trends(self) -> List[Dict[str, Any]]:
        """Collect platform-specific trends."""
        # This would integrate with platform APIs
        return [
            {
                'topic': 'Malayalam Comedy',
                'platform': 'instagram',
                'velocity': 0.6,
                'strength': 0.7,
                'cross_platform': 2,
                'language': 'ml',
                'freshness': 0.85
            }
        ]

    async def _train_trend_model(self) -> Dict[str, Any]:
        """Train trend prediction model using Prophet."""
        try:
            async with async_session() as session:
                # Get historical trend data
                result = await session.execute("""
                    SELECT created_at, velocity, trend_strength
                    FROM trends
                    WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
                    ORDER BY created_at
                """)

                trend_data = result.fetchall()

                if len(trend_data) < 10:
                    return {"status": "insufficient_data"}

                # Prepare data for Prophet
                df = pd.DataFrame([
                    {
                        'ds': row.created_at,
                        'y': (row.velocity + row.trend_strength) / 2
                    } for row in trend_data
                ])

                # Train model
                self.prophet_model.fit(df)

                # Make future predictions
                future = self.prophet_model.make_future_dataframe(periods=7)
                forecast = self.prophet_model.predict(future)

                return {
                    "status": "success",
                    "forecast_points": len(forecast),
                    "training_samples": len(df)
                }

        except Exception as e:
            logger.error(f"Trend model training failed: {e}")
            return {"status": "error", "error": str(e)}

    async def _store_model_metrics(self, engagement_metrics: Dict, trend_metrics: Dict):
        """Store model performance metrics."""
        try:
            async with async_session() as session:
                # Store engagement model metrics
                if engagement_metrics.get('status') == 'success':
                    metric = ModelMetrics(
                        model_name='engagement_prediction',
                        model_version='1.0',
                        metrics=json.dumps(engagement_metrics.get('metrics', {})),
                        feature_importance=json.dumps({}),  # Would be populated from XGBoost
                        training_samples=engagement_metrics.get('training_samples', 0)
                    )
                    session.add(metric)

                # Store trend model metrics
                if trend_metrics.get('status') == 'success':
                    metric = ModelMetrics(
                        model_name='trend_prediction',
                        model_version='1.0',
                        metrics=json.dumps(trend_metrics),
                        training_samples=trend_metrics.get('training_samples', 0)
                    )
                    session.add(metric)

                await session.commit()

        except Exception as e:
            logger.error(f"Failed to store model metrics: {e}")

    def _calculate_trend_boost(self, trend_context: Dict[str, Any]) -> float:
        """Calculate trend-based boost factor."""
        velocity = trend_context.get('velocity', 0)
        strength = trend_context.get('strength', 0)
        freshness = trend_context.get('freshness', 0)

        return (velocity * 0.4 + strength * 0.4 + freshness * 0.2)

    async def _adapt_caption_for_malayalam(self, base_caption: str, sentiment: Dict,
                                         trend_boost: float, trend_context: Dict) -> str:
        """Adapt caption for Malayalam audience with learning insights."""
        try:
            adapted = base_caption

            # Add Malayalam-specific elements based on learning
            if sentiment['label'] == 'POSITIVE' and trend_boost > 0.7:
                # Add trending Malayalam hashtags
                adapted += " #മലയാളം #കേരളം"

            if trend_context.get('topic'):
                # Add topic-specific hashtags
                topic_hashtag = f"#{trend_context['topic'].replace(' ', '')}"
                adapted += f" {topic_hashtag}"

            # Add emojis based on learning (if they improve engagement)
            if trend_boost > 0.5:
                adapted += " 😂"  # Comedy emoji for Malayalam content

            return adapted

        except Exception as e:
            logger.error(f"Caption adaptation failed: {e}")
            return base_caption

    async def start_continuous_learning(self):
        """Start continuous learning loop."""
        self.learning_active = True

        while self.learning_active:
            try:
                # Update trends daily
                await self.update_trends()

                # Retrain models weekly
                if datetime.utcnow().weekday() == 0:  # Monday
                    await self.retrain_models()

                # Optimize posting schedule daily
                await self.optimize_posting_schedule()

                # Wait for next cycle (daily)
                await asyncio.sleep(24 * 60 * 60)

            except Exception as e:
                logger.error(f"Continuous learning cycle failed: {e}")
                await asyncio.sleep(60 * 60)  # Wait 1 hour before retry

    def stop_continuous_learning(self):
        """Stop continuous learning."""
        self.learning_active = False
