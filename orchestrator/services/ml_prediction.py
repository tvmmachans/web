"""
ML prediction service for content performance.
"""

import logging
import os
import joblib
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, r2_score
import xgboost as xgb

from orchestrator.config.settings import settings
from orchestrator.database.session import get_db

logger = logging.getLogger(__name__)

class MLPredictionService:
    """Service for ML-based content performance prediction."""

    def __init__(self):
        self.model = None
        self.scaler = None
        self.model_path = "orchestrator/models/content_prediction.pkl"
        self.scaler_path = "orchestrator/models/scaler.pkl"
        self.is_trained = False

        self.feature_columns = [
            'trend_velocity', 'trend_freshness', 'cross_platform_count',
            'creator_followers', 'past_avg_views', 'posting_hour',
            'day_of_week', 'video_category_score', 'has_faces',
            'language_match', 'title_length', 'has_emojis'
        ]

        # Load existing model if available
        self._load_model()

    def predict_engagement(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Predict engagement metrics for content."""
        if not self.is_trained:
            logger.warning("Model not trained, using heuristic predictions")
            return self._heuristic_predictions(features)

        try:
            # Prepare features
            feature_vector = self._prepare_features(features)
            scaled_features = self.scaler.transform([feature_vector])

            # Make prediction
            prediction = self.model.predict(scaled_features)[0]

            # Extract individual predictions
            predicted_views = max(int(prediction[0]), 1000)
            predicted_likes = max(int(prediction[1]), 50)
            predicted_ctr = min(max(prediction[2], 0.01), 0.20)  # Clamp between 1% and 20%

            # Calculate confidence based on prediction variance
            confidence_score = self._calculate_confidence(features)

            return {
                "predicted_views": predicted_views,
                "predicted_likes": predicted_likes,
                "predicted_ctr": predicted_ctr,
                "confidence_score": confidence_score,
            }

        except Exception as e:
            logger.error(f"ML prediction failed: {e}")
            return self._heuristic_predictions(features)

    def calculate_roi_score(self, predictions: Dict[str, Any], trend_strength: float) -> float:
        """Calculate ROI score for content."""
        views = predictions.get("predicted_views", 0)
        ctr = predictions.get("predicted_ctr", 0)
        confidence = predictions.get("confidence_score", 0.5)

        # Engagement score based on views and CTR
        engagement_score = views * ctr * 0.1

        # Trend strength multiplier (normalized)
        trend_multiplier = min(trend_strength / 50.0, 2.0)

        # Confidence multiplier
        confidence_multiplier = 0.5 + (confidence * 0.5)

        roi = engagement_score * trend_multiplier * confidence_multiplier
        return min(roi, 10.0)  # Cap at 10

    async def collect_training_data(self) -> pd.DataFrame:
        """Collect training data from database."""
        try:
            async with get_db() as session:
                # Query for content performance data
                result = await session.execute("""
                    SELECT
                        cb.predicted_views,
                        cb.predicted_likes,
                        cb.predicted_ctr,
                        cb.generation_params,
                        cb.created_at,
                        t.velocity as trend_velocity,
                        t.trend_strength,
                        t.cross_platform_count,
                        cb.roi_score
                    FROM content_blueprints cb
                    JOIN trends t ON cb.trend_id = t.id
                    WHERE cb.status IN ('posted', 'completed')
                    AND cb.predicted_views > 0
                    ORDER BY cb.created_at DESC
                    LIMIT 1000
                """)

                rows = result.fetchall()

                if len(rows) < 50:
                    logger.warning(f"Insufficient training data: {len(rows)} samples")
                    return pd.DataFrame()

                # Convert to DataFrame
                data = []
                for row in rows:
                    features = row.generation_params or {}
                    features.update({
                        'actual_views': row.predicted_views,  # Using predicted as proxy for actual
                        'actual_likes': row.predicted_likes,
                        'actual_ctr': row.predicted_ctr,
                        'trend_velocity': row.trend_velocity,
                        'trend_strength': row.trend_strength,
                        'cross_platform_count': row.cross_platform_count,
                        'roi_score': row.roi_score
                    })
                    data.append(features)

                df = pd.DataFrame(data)
                logger.info(f"Collected {len(df)} training samples")
                return df

        except Exception as e:
            logger.error(f"Failed to collect training data: {e}")
            return pd.DataFrame()

    def train_model(self, training_data: pd.DataFrame) -> Dict[str, Any]:
        """Train XGBoost model on collected data."""
        try:
            if training_data.empty or len(training_data) < 50:
                logger.warning("Insufficient training data")
                return {"status": "insufficient_data"}

            # Prepare features and targets
            X = training_data[self.feature_columns]
            y_views = training_data['actual_views']
            y_likes = training_data['actual_likes']
            y_ctr = training_data['actual_ctr']

            # Handle missing values
            X = X.fillna(X.mean())

            # Split data
            X_train, X_test, y_train_views, y_test_views = train_test_split(
                X, y_views, test_size=0.2, random_state=42
            )
            _, _, y_train_likes, y_test_likes = train_test_split(
                X, y_likes, test_size=0.2, random_state=42
            )
            _, _, y_train_ctr, y_test_ctr = train_test_split(
                X, y_ctr, test_size=0.2, random_state=42
            )

            # Scale features
            self.scaler = StandardScaler()
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)

            # Train models for each target
            models = {}
            metrics = {}

            for target_name, y_train, y_test in [
                ('views', y_train_views, y_test_views),
                ('likes', y_train_likes, y_test_likes),
                ('ctr', y_train_ctr, y_test_ctr)
            ]:
                model = xgb.XGBRegressor(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    random_state=42
                )

                model.fit(X_train_scaled, y_train)
                models[target_name] = model

                # Evaluate
                y_pred = model.predict(X_test_scaled)
                mae = mean_absolute_error(y_test, y_pred)
                r2 = r2_score(y_test, y_pred)

                metrics[target_name] = {
                    'mae': mae,
                    'r2': r2,
                    'mean_actual': y_test.mean(),
                    'mean_predicted': y_pred.mean()
                }

            # Create ensemble model that predicts all targets
            self.model = MultiOutputXGBModel(models)
            self.is_trained = True

            # Save model
            self._save_model()

            logger.info(f"Model trained successfully. Metrics: {metrics}")
            return {
                "status": "success",
                "metrics": metrics,
                "training_samples": len(training_data)
            }

        except Exception as e:
            logger.error(f"Model training failed: {e}")
            return {"status": "error", "error": str(e)}

    def _prepare_features(self, features: Dict[str, Any]) -> List[float]:
        """Prepare feature vector for prediction."""
        feature_vector = []
        for col in self.feature_columns:
            value = features.get(col, 0)
            if isinstance(value, bool):
                value = 1.0 if value else 0.0
            feature_vector.append(float(value))

        return feature_vector

    def _calculate_confidence(self, features: Dict[str, Any]) -> float:
        """Calculate prediction confidence score."""
        # Simple confidence based on feature completeness and trend strength
        completeness = sum(1 for col in self.feature_columns if features.get(col) is not None) / len(self.feature_columns)
        trend_strength = min(features.get('trend_velocity', 0) / 100.0, 1.0)

        confidence = (completeness * 0.6) + (trend_strength * 0.4)
        return min(confidence, 1.0)

    def _heuristic_predictions(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback heuristic predictions when model unavailable."""
        base_views = self._calculate_base_views(features)
        base_likes = base_views * 0.05
        base_ctr = self._calculate_ctr(features)

        # Add some randomness
        views = int(base_views * (0.8 + np.random.random() * 0.4))
        likes = int(base_likes * (0.8 + np.random.random() * 0.4))
        ctr = base_ctr * (0.9 + np.random.random() * 0.2)

        return {
            "predicted_views": views,
            "predicted_likes": likes,
            "predicted_ctr": ctr,
            "confidence_score": 0.5,
        }

    def _calculate_base_views(self, features: Dict[str, Any]) -> float:
        """Calculate base view prediction."""
        trend_velocity = features.get('trend_velocity', 0)
        creator_followers = features.get('creator_followers', 10000)
        posting_hour = features.get('posting_hour', 14)
        day_of_week = features.get('day_of_week', 0)

        base = trend_velocity * 10
        base += creator_followers * 0.001

        if 18 <= posting_hour <= 22:
            base *= 1.3
        elif 6 <= posting_hour <= 10:
            base *= 0.8

        if day_of_week in [5, 6]:
            base *= 1.2

        return max(base, 1000)

    def _calculate_ctr(self, features: Dict[str, Any]) -> float:
        """Calculate click-through rate."""
        base_ctr = 0.03

        if features.get('has_emojis', False):
            base_ctr *= 1.2
        if features.get('language_match', 1.0) > 0.8:
            base_ctr *= 1.1
        if features.get('has_faces', 1.0) > 0:
            base_ctr *= 1.15

        title_length = features.get('title_length', 50)
        if 30 <= title_length <= 70:
            base_ctr *= 1.1

        return min(base_ctr, 0.15)

    def _load_model(self):
        """Load trained model from disk."""
        try:
            if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
                self.model = joblib.load(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
                self.is_trained = True
                logger.info("Loaded trained model from disk")
            else:
                logger.info("No trained model found, will use heuristics")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")

    def _save_model(self):
        """Save trained model to disk."""
        try:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.scaler, self.scaler_path)
            logger.info("Model saved to disk")
        except Exception as e:
            logger.error(f"Failed to save model: {e}")


class MultiOutputXGBModel:
    """Wrapper for multiple XGBoost models predicting different targets."""

    def __init__(self, models: Dict[str, xgb.XGBRegressor]):
        self.models = models

    def predict(self, X):
        """Predict all targets."""
        predictions = []
        for model in self.models.values():
            pred = model.predict(X)
            predictions.append(pred[0] if len(pred) == 1 else pred)

        return np.array(predictions).T
