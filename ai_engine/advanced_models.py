import os
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import json
import pickle
from pathlib import Path

import xgboost as xgb
from prophet import Prophet
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

from backend.database import async_session, LearningData, ModelMetrics, Trends
from ai_engine.learning_manager import LearningManager

logger = logging.getLogger(__name__)

class AdvancedMLModels:
    """
    Advanced ML models for engagement prediction and trend forecasting.
    """

    def __init__(self):
        self.models_dir = Path("models")
        self.models_dir.mkdir(exist_ok=True)

        # Initialize models
        self.xgb_model = None
        self.prophet_model = None
        self.distilbert_model = None
        self.distilbert_tokenizer = None

        # Model versions for A/B testing
        self.model_versions = {}

        self._load_models()

    def _load_models(self):
        """Load or initialize ML models."""
        try:
            # Load XGBoost model
            xgb_path = self.models_dir / "engagement_predictor.json"
            if xgb_path.exists():
                self.xgb_model = xgb.Booster()
                self.xgb_model.load_model(str(xgb_path))
            else:
                self.xgb_model = None

            # Load DistilBERT for Malayalam caption optimization
            model_name = "distilbert-base-multilingual-cased"
            try:
                self.distilbert_tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.distilbert_model = AutoModelForSequenceClassification.from_pretrained(
                    model_name, num_labels=3  # positive, neutral, negative
                )
                # Load fine-tuned weights if available
                model_path = self.models_dir / "distilbert_malayalam_caption"
                if model_path.exists():
                    self.distilbert_model.load_state_dict(torch.load(model_path / "pytorch_model.bin"))
            except Exception as e:
                logger.warning(f"Could not load DistilBERT model: {e}")

        except Exception as e:
            logger.error(f"Error loading models: {e}")

    async def predict_engagement(self, features: Dict[str, Any]) -> Dict[str, float]:
        """
        Predict engagement using XGBoost model.
        """
        try:
            if not self.xgb_model:
                # Fallback to simple prediction
                return self._simple_engagement_prediction(features)

            # Prepare features for XGBoost
            feature_vector = self._prepare_features(features)
            dmatrix = xgb.DMatrix([feature_vector])

            # Get prediction
            prediction = self.xgb_model.predict(dmatrix)[0]

            # Convert to engagement metrics
            return {
                "predicted_views": max(0, prediction * 1000),
                "predicted_likes": max(0, prediction * 50),
                "predicted_comments": max(0, prediction * 10),
                "engagement_rate": min(1.0, max(0, prediction)),
                "confidence": 0.8  # Model confidence score
            }

        except Exception as e:
            logger.error(f"XGBoost prediction failed: {e}")
            return self._simple_engagement_prediction(features)

    def _prepare_features(self, features: Dict[str, Any]) -> List[float]:
        """
        Prepare features for ML model input.
        """
        # Extract and normalize features
        hour = features.get('hour', 12) / 24.0
        day_of_week = features.get('day_of_week', 0) / 6.0
        platform_youtube = 1 if features.get('platform') == 'youtube' else 0
        platform_instagram = 1 if features.get('platform') == 'instagram' else 0
        caption_length = min(len(features.get('caption', '')), 500) / 500.0
        has_hashtags = 1 if '#' in features.get('caption', '') else 0
        has_emojis = 1 if any(ord(char) > 127 for char in features.get('caption', '')) else 0

        # Historical performance features
        avg_engagement = features.get('avg_engagement', 0.02)
        trend_score = features.get('trend_score', 0.5)

        return [
            hour, day_of_week, platform_youtube, platform_instagram,
            caption_length, has_hashtags, has_emojis, avg_engagement, trend_score
        ]

    def _simple_engagement_prediction(self, features: Dict[str, Any]) -> Dict[str, float]:
        """
        Simple rule-based engagement prediction as fallback.
        """
        base_engagement = 0.02  # 2% base engagement

        # Time-based multipliers
        hour = features.get('hour', 12)
        if 18 <= hour <= 21:  # Prime time
            base_engagement *= 1.5
        elif 6 <= hour <= 9:  # Morning
            base_engagement *= 1.2

        # Platform multipliers
        platform = features.get('platform', 'youtube')
        if platform == 'instagram':
            base_engagement *= 1.3  # Instagram typically has higher engagement

        # Content quality multipliers
        caption = features.get('caption', '')
        if len(caption) > 50:
            base_engagement *= 1.2
        if '#' in caption:
            base_engagement *= 1.1

        return {
            "predicted_views": base_engagement * 1000,
            "predicted_likes": base_engagement * 500,
            "predicted_comments": base_engagement * 50,
            "engagement_rate": base_engagement,
            "confidence": 0.5
        }

    async def forecast_trends(self, platform: str = "youtube", days: int = 7) -> List[Dict[str, Any]]:
        """
        Forecast trends using Prophet model.
        """
        try:
            async with async_session() as session:
                # Get historical trend data
                result = await session.execute("""
                    SELECT created_at, trend_strength, velocity
                    FROM trends
                    WHERE platform = $1 AND created_at >= $2
                    ORDER BY created_at
                """, (platform, datetime.utcnow() - timedelta(days=30)))

                trend_data = result.fetchall()

                if len(trend_data) < 7:
                    return self._simple_trend_forecast(platform, days)

                # Prepare data for Prophet
                df = pd.DataFrame(trend_data, columns=['ds', 'y', 'velocity'])
                df['ds'] = pd.to_datetime(df['ds'])
                df['y'] = df['y'].astype(float)

                # Fit Prophet model
                model = Prophet(
                    daily_seasonality=True,
                    weekly_seasonality=True,
                    yearly_seasonality=False
                )
                model.fit(df[['ds', 'y']])

                # Make future predictions
                future = model.make_future_dataframe(periods=days)
                forecast = model.predict(future)

                # Convert to response format
                predictions = []
                for _, row in forecast.tail(days).iterrows():
                    predictions.append({
                        "date": row['ds'].strftime('%Y-%m-%d'),
                        "predicted_trend_strength": float(row['yhat']),
                        "trend_lower": float(row['yhat_lower']),
                        "trend_upper": float(row['yhat_upper']),
                        "platform": platform
                    })

                return predictions

        except Exception as e:
            logger.error(f"Trend forecasting failed: {e}")
            return self._simple_trend_forecast(platform, days)

    def _simple_trend_forecast(self, platform: str, days: int) -> List[Dict[str, Any]]:
        """
        Simple trend forecast as fallback.
        """
        predictions = []
        base_trend = 0.5

        for i in range(days):
            date = datetime.utcnow() + timedelta(days=i+1)
            # Add some weekly seasonality
            day_multiplier = 1 + 0.2 * np.sin(2 * np.pi * date.weekday() / 7)

            predictions.append({
                "date": date.strftime('%Y-%m-%d'),
                "predicted_trend_strength": base_trend * day_multiplier,
                "trend_lower": base_trend * day_multiplier * 0.8,
                "trend_upper": base_trend * day_multiplier * 1.2,
                "platform": platform
            })

        return predictions

    async def optimize_caption(self, base_caption: str, target_engagement: float = 0.05) -> Dict[str, Any]:
        """
        Optimize caption using DistilBERT for Malayalam content.
        """
        try:
            if not self.distilbert_model or not self.distilbert_tokenizer:
                return self._simple_caption_optimization(base_caption, target_engagement)

            # Analyze current caption
            inputs = self.distilbert_tokenizer(
                base_caption,
                return_tensors="pt",
                truncation=True,
                max_length=512
            )

            with torch.no_grad():
                outputs = self.distilbert_model(**inputs)
                sentiment_scores = torch.softmax(outputs.logits, dim=1)

            # Get sentiment (0: negative, 1: neutral, 2: positive)
            sentiment = torch.argmax(sentiment_scores, dim=1).item()

            # Generate optimized caption suggestions
            suggestions = await self._generate_caption_variations(base_caption, sentiment, target_engagement)

            return {
                "original_caption": base_caption,
                "sentiment_score": sentiment,
                "optimized_captions": suggestions,
                "recommended_caption": suggestions[0] if suggestions else base_caption
            }

        except Exception as e:
            logger.error(f"Caption optimization failed: {e}")
            return self._simple_caption_optimization(base_caption, target_engagement)

    async def _generate_caption_variations(self, base_caption: str, sentiment: int,
                                         target_engagement: float) -> List[str]:
        """
        Generate caption variations using learning data.
        """
        try:
            async with async_session() as session:
                # Get successful captions from learning data
                result = await session.execute("""
                    SELECT ai_caption, actual_performance
                    FROM learning_data
                    WHERE ai_caption IS NOT NULL
                    AND json_extract(actual_performance, '$.engagement_rate') > 0.03
                    ORDER BY json_extract(actual_performance, '$.engagement_rate') DESC
                    LIMIT 5
                """)

                successful_captions = result.fetchall()

                variations = []
                for row in successful_captions:
                    if row.ai_caption and len(row.ai_caption) > 10:
                        # Adapt successful patterns to current content
                        variation = self._adapt_caption_pattern(base_caption, row.ai_caption)
                        if variation and variation not in variations:
                            variations.append(variation)

                # Add Malayalam-specific optimizations
                malayalam_variations = self._add_malayalam_optimizations(base_caption, sentiment)
                variations.extend(malayalam_variations)

                return variations[:3]  # Return top 3 variations

        except Exception as e:
            logger.error(f"Failed to generate caption variations: {e}")
            return [base_caption]

    def _adapt_caption_pattern(self, base_caption: str, successful_caption: str) -> str:
        """
        Adapt patterns from successful captions.
        """
        # Extract hashtags from successful caption
        import re
        hashtags = re.findall(r'#\w+', successful_caption)

        # Add successful hashtags to base caption
        if hashtags and len(base_caption) < 200:
            adapted = base_caption.rstrip()
            if not adapted.endswith(('!', '.', '?')):
                adapted += '!'
            adapted += ' ' + ' '.join(hashtags[:3])  # Add up to 3 hashtags
            return adapted

        return base_caption

    def _add_malayalam_optimizations(self, caption: str, sentiment: int) -> List[str]:
        """
        Add Malayalam-specific optimizations based on sentiment.
        """
        variations = []

        # Sentiment-based Malayalam phrases
        sentiment_phrases = {
            0: ["ദുഖകരമായ", "സങ്കടകരമായ", "കരുണാജനകമായ"],  # Negative
            1: ["സാധാരണ", "ശാന്തമായ", "സമാധാനപരമായ"],  # Neutral
            2: ["സന്തോഷകരമായ", "ആനന്ദകരമായ", "ഉത്സാഹജനകമായ"]  # Positive
        }

        phrases = sentiment_phrases.get(sentiment, ["അടിസ്ഥാന"])
        emojis = ["📱", "🎥", "❤️", "🔥", "😊"]

        for phrase in phrases[:2]:  # Use 2 phrases
            for emoji in emojis[:2]:  # Use 2 emojis
                variation = f"{caption} {phrase} {emoji}"
                if len(variation) <= 2200:  # Instagram caption limit
                    variations.append(variation)

        return variations

    def _simple_caption_optimization(self, caption: str, target_engagement: float) -> Dict[str, Any]:
        """
        Simple caption optimization as fallback.
        """
        # Add basic Malayalam hashtags and emojis
        optimized = caption
        if not caption.endswith('!'):
            optimized += '!'

        # Add popular Malayalam hashtags
        hashtags = ["#Malayalam", "#Kerala", "#സിനിമ", "#മലയാളം"]
        optimized += ' ' + ' '.join(hashtags)

        return {
            "original_caption": caption,
            "sentiment_score": 1,  # Neutral
            "optimized_captions": [optimized],
            "recommended_caption": optimized
        }

    async def train_models(self, force_retrain: bool = False):
        """
        Train and update ML models with new data.
        """
        try:
            logger.info("Starting model training...")

            # Train XGBoost engagement predictor
            await self._train_xgboost_model()

            # Fine-tune DistilBERT for Malayalam
            await self._fine_tune_distilbert()

            # Update model versions
            self._update_model_versions()

            logger.info("Model training completed")

        except Exception as e:
            logger.error(f"Model training failed: {e}")

    async def _train_xgboost_model(self):
        """
        Train XGBoost model for engagement prediction.
        """
        try:
            async with async_session() as session:
                # Get training data from learning_data table
                result = await session.execute("""
                    SELECT features, actual_performance
                    FROM learning_data
                    WHERE features IS NOT NULL AND actual_performance IS NOT NULL
                    ORDER BY created_at DESC
                    LIMIT 1000
                """)

                training_data = result.fetchall()

                if len(training_data) < 50:
                    logger.warning("Insufficient training data for XGBoost")
                    return

                # Prepare training data
                X = []
                y = []

                for row in training_data:
                    try:
                        features = json.loads(row.features)
                        performance = json.loads(row.actual_performance)

                        feature_vector = self._prepare_features(features)
                        engagement_rate = performance.get('engagement_rate', 0.02)

                        X.append(feature_vector)
                        y.append(engagement_rate)
                    except:
                        continue

                if len(X) < 20:
                    return

                # Train XGBoost model
                dtrain = xgb.DMatrix(X, label=y)
                params = {
                    'objective': 'reg:squarederror',
                    'max_depth': 6,
                    'eta': 0.1,
                    'subsample': 0.8,
                    'colsample_bytree': 0.8
                }

                self.xgb_model = xgb.train(params, dtrain, num_boost_round=100)

                # Save model
                model_path = self.models_dir / "engagement_predictor.json"
                self.xgb_model.save_model(str(model_path))

                logger.info(f"XGBoost model trained with {len(X)} samples")

        except Exception as e:
            logger.error(f"XGBoost training failed: {e}")

    async def _fine_tune_distilbert(self):
        """
        Fine-tune DistilBERT for Malayalam caption optimization.
        """
        # This would require significant computational resources
        # For now, we'll use the pre-trained model
        logger.info("DistilBERT fine-tuning skipped (requires GPU resources)")

    def _update_model_versions(self):
        """
        Update model version tracking for A/B testing.
        """
        version = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        self.model_versions['xgboost'] = version
        self.model_versions['distilbert'] = version

        # Save version info
        version_path = self.models_dir / "model_versions.json"
        with open(version_path, 'w') as f:
            json.dump(self.model_versions, f)

    async def get_model_metrics(self) -> Dict[str, Any]:
        """
        Get current model performance metrics.
        """
        try:
            async with async_session() as session:
                # Get latest metrics from database
                result = await session.execute("""
                    SELECT model_name, metrics, training_date
                    FROM model_metrics
                    WHERE is_active = 1
                    ORDER BY training_date DESC
                    LIMIT 5
                """)

                metrics_data = result.fetchall()

                metrics = {}
                for row in metrics_data:
                    try:
                        model_metrics = json.loads(row.metrics)
                        metrics[row.model_name] = {
                            "metrics": model_metrics,
                            "last_trained": row.training_date.isoformat()
                        }
                    except:
                        continue

                return metrics

        except Exception as e:
            logger.error(f"Failed to get model metrics: {e}")
            return {}
