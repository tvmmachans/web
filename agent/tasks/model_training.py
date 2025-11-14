import asyncio
import logging
import os
from datetime import datetime, timedelta

import joblib
from celery import Celery
from database import Analytics, LearningData, ModelMetrics, Post, async_session
from sklearn.metrics import mean_absolute_error, r2_score

from ai_engine.advanced_models import AdvancedMLModels
from ai_engine.learning_manager import LearningManager

logger = logging.getLogger(__name__)

celery_app = Celery("model_training")
celery_app.config_from_object("agent.config.settings")


class ModelTrainer:
    def __init__(self):
        self.advanced_models = AdvancedMLModels()
        self.learning_manager = LearningManager()
        self.model_dir = "models"
        os.makedirs(self.model_dir, exist_ok=True)

    async def collect_training_data(self, days_back: int = 30):
        """
        Collect training data from recent posts and analytics.
        """
        async with async_session() as session:
            # Get posts with analytics from the last N days
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)

            result = await session.execute(
                """
                SELECT
                    p.id, p.title, p.description, p.platform, p.created_at,
                    a.views, a.likes, a.comments, a.shares, a.engagement_rate,
                    ld.features, ld.actual_performance
                FROM posts p
                LEFT JOIN analytics a ON p.id = a.post_id
                LEFT JOIN learning_data ld ON p.id = ld.post_id
                WHERE p.created_at >= ?
                AND a.views IS NOT NULL
                ORDER BY p.created_at DESC
            """,
                (cutoff_date,),
            )

            training_data = []
            for row in result.fetchall():
                features = row.features if row.features else self.extract_features(row)
                actual_performance = (
                    row.actual_performance
                    if row.actual_performance
                    else {
                        "views": row.views or 0,
                        "likes": row.likes or 0,
                        "comments": row.comments or 0,
                        "engagement_rate": row.engagement_rate or 0,
                    }
                )

                training_data.append(
                    {
                        "features": features,
                        "actual_performance": actual_performance,
                        "post_id": row.id,
                        "platform": row.platform,
                    }
                )

            return training_data

    def extract_features(self, post_data):
        """
        Extract features from post data for ML training.
        """
        title = post_data.title or ""
        description = post_data.description or ""

        return {
            "title_length": len(title),
            "description_length": len(description),
            "has_hashtags": "#" in title + description,
            "has_emojis": any(ord(char) > 127 for char in title + description),
            "platform": post_data.platform,
            "hour_posted": post_data.created_at.hour,
            "day_of_week": post_data.created_at.weekday(),
            "is_weekend": post_data.created_at.weekday() >= 5,
            "word_count": len((title + description).split()),
            "avg_word_length": sum(len(word) for word in (title + description).split())
            / max(1, len((title + description).split())),
        }

    async def train_engagement_model(self):
        """
        Train the engagement prediction model.
        """
        try:
            logger.info("Starting engagement model training...")

            # Collect training data
            training_data = await self.collect_training_data(days_back=60)

            if len(training_data) < 10:
                logger.warning("Insufficient training data for engagement model")
                return False

            # Prepare features and targets
            X = []
            y_views = []
            y_engagement = []

            for data in training_data:
                X.append(list(data["features"].values()))
                y_views.append(data["actual_performance"]["views"])
                y_engagement.append(data["actual_performance"]["engagement_rate"])

            # Train models
            self.advanced_models.train_engagement_predictor(X, y_engagement)
            self.advanced_models.train_view_predictor(X, y_views)

            # Evaluate models
            predictions_engagement = self.advanced_models.predict_engagement(
                X[:10]
            )  # Test on subset
            predictions_views = self.advanced_models.predict_views(X[:10])

            mae_engagement = mean_absolute_error(
                y_engagement[:10], predictions_engagement
            )
            r2_engagement = r2_score(y_engagement[:10], predictions_engagement)

            mae_views = mean_absolute_error(y_views[:10], predictions_views)
            r2_views = r2_score(y_views[:10], predictions_views)

            # Save model metrics
            await self.save_model_metrics(
                "engagement_predictor",
                "xgboost",
                {"mae": mae_engagement, "r2": r2_engagement},
                len(training_data),
                (
                    self.advanced_models.engagement_model.feature_importances_.tolist()
                    if hasattr(
                        self.advanced_models.engagement_model, "feature_importances_"
                    )
                    else []
                ),
            )

            await self.save_model_metrics(
                "view_predictor",
                "xgboost",
                {"mae": mae_views, "r2": r2_views},
                len(training_data),
                (
                    self.advanced_models.view_model.feature_importances_.tolist()
                    if hasattr(self.advanced_models.view_model, "feature_importances_")
                    else []
                ),
            )

            # Save models
            self.save_models()

            logger.info(
                f"Engagement model training completed. MAE: {mae_engagement:.4f}, R2: {r2_engagement:.4f}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to train engagement model: {e}")
            return False

    async def train_caption_optimizer(self):
        """
        Train the caption optimization model.
        """
        try:
            logger.info("Starting caption optimizer training...")

            # Collect caption performance data
            training_data = await self.collect_caption_training_data()

            if len(training_data) < 5:
                logger.warning("Insufficient training data for caption optimizer")
                return False

            # Prepare data for DistilBERT fine-tuning
            texts = [data["caption"] for data in training_data]
            scores = [data["performance_score"] for data in training_data]

            # Fine-tune the model
            self.advanced_models.train_caption_optimizer(texts, scores)

            # Save model
            self.save_caption_model()

            # Save metrics
            await self.save_model_metrics(
                "caption_optimizer",
                "distilbert",
                {"training_samples": len(training_data)},
                len(training_data),
                [],
            )

            logger.info(
                f"Caption optimizer training completed with {len(training_data)} samples"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to train caption optimizer: {e}")
            return False

    async def collect_caption_training_data(self):
        """
        Collect caption performance data for training.
        """
        async with async_session() as session:
            result = await session.execute(
                """
                SELECT
                    p.ai_caption,
                    a.views, a.likes, a.comments, a.engagement_rate,
                    ld.actual_performance
                FROM posts p
                LEFT JOIN analytics a ON p.id = a.post_id
                LEFT JOIN learning_data ld ON p.id = ld.post_id
                WHERE p.ai_caption IS NOT NULL
                AND a.views IS NOT NULL
                AND p.created_at >= ?
                ORDER BY p.created_at DESC
            """,
                (datetime.utcnow() - timedelta(days=90),),
            )

            training_data = []
            for row in result.fetchall():
                if row.ai_caption and len(row.ai_caption.strip()) > 10:
                    # Calculate performance score based on engagement
                    performance_score = (
                        (row.views or 0) * 0.3
                        + (row.likes or 0) * 0.3
                        + (row.comments or 0) * 0.2
                        + (row.engagement_rate or 0) * 0.2
                    )

                    training_data.append(
                        {
                            "caption": row.ai_caption,
                            "performance_score": performance_score,
                        }
                    )

            return training_data

    def save_models(self):
        """
        Save trained models to disk.
        """
        try:
            if self.advanced_models.engagement_model:
                joblib.dump(
                    self.advanced_models.engagement_model,
                    f"{self.model_dir}/engagement_model.pkl",
                )
            if self.advanced_models.view_model:
                joblib.dump(
                    self.advanced_models.view_model, f"{self.model_dir}/view_model.pkl"
                )
            logger.info("Models saved successfully")
        except Exception as e:
            logger.error(f"Failed to save models: {e}")

    def save_caption_model(self):
        """
        Save caption optimization model.
        """
        try:
            if self.advanced_models.caption_model:
                self.advanced_models.caption_model.save_pretrained(
                    f"{self.model_dir}/caption_model"
                )
            logger.info("Caption model saved successfully")
        except Exception as e:
            logger.error(f"Failed to save caption model: {e}")

    async def save_model_metrics(
        self, model_name, model_version, metrics, training_samples, feature_importance
    ):
        """
        Save model performance metrics to database.
        """
        async with async_session() as session:
            model_metric = ModelMetrics(
                model_name=model_name,
                model_version=model_version,
                training_date=datetime.utcnow(),
                metrics=metrics,
                feature_importance=feature_importance,
                training_samples=training_samples,
                is_active=True,
            )
            session.add(model_metric)
            await session.commit()

    async def update_learning_data(self):
        """
        Update learning data with new predictions and feedback.
        """
        try:
            async with async_session() as session:
                # Get recent posts without learning data
                result = await session.execute(
                    """
                    SELECT p.id, p.title, p.description, p.platform, p.created_at,
                           a.views, a.likes, a.comments, a.engagement_rate
                    FROM posts p
                    LEFT JOIN analytics a ON p.id = a.post_id
                    LEFT JOIN learning_data ld ON p.id = ld.post_id
                    WHERE ld.id IS NULL
                    AND a.views IS NOT NULL
                    AND p.created_at >= ?
                """,
                    (datetime.utcnow() - timedelta(days=7),),
                )

                for row in result.fetchall():
                    features = self.extract_features(row)
                    actual_performance = {
                        "views": row.views or 0,
                        "likes": row.likes or 0,
                        "comments": row.comments or 0,
                        "engagement_rate": row.engagement_rate or 0,
                    }

                    learning_data = LearningData(
                        post_id=row.id,
                        features=features,
                        actual_performance=actual_performance,
                        predicted_performance={},  # Will be filled by prediction
                        feedback_score=0.0,
                        learning_insights={},
                    )
                    session.add(learning_data)

                await session.commit()
                logger.info("Learning data updated successfully")

        except Exception as e:
            logger.error(f"Failed to update learning data: {e}")


@celery_app.task
def train_all_models():
    """
    Celery task to train all ML models.
    """
    trainer = ModelTrainer()

    async def run_training():
        # Train engagement models
        engagement_success = await trainer.train_engagement_model()

        # Train caption optimizer
        caption_success = await trainer.train_caption_optimizer()

        # Update learning data
        await trainer.update_learning_data()

        return {
            "engagement_training": engagement_success,
            "caption_training": caption_success,
            "timestamp": datetime.utcnow().isoformat(),
        }

    # Run async training
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(run_training())
    loop.close()

    return result


@celery_app.task
def train_engagement_model():
    """
    Celery task to train only engagement models.
    """
    trainer = ModelTrainer()

    async def run():
        return await trainer.train_engagement_model()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(run())
    loop.close()

    return result


@celery_app.task
def update_learning_feedback():
    """
    Celery task to update learning feedback from recent performance.
    """
    trainer = ModelTrainer()

    async def run():
        await trainer.update_learning_data()
        return True

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(run())
    loop.close()

    return result
