import os
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import json
import re
from collections import defaultdict

import numpy as np
import pandas as pd
from prophet import Prophet
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_similarity

from backend.database import async_session, Trends, Post, Analytics
from ai_engine.advanced_models import AdvancedMLModels

logger = logging.getLogger(__name__)

class TrendPredictor:
    """
    Advanced trend prediction system for Malayalam social media content.
    """

    def __init__(self):
        self.malayalam_keywords = self._load_malayalam_keywords()
        self.trend_patterns = self._load_trend_patterns()
        self.platform_apis = {
            'youtube': self._fetch_youtube_trends,
            'instagram': self._fetch_instagram_trends
        }

    def _load_malayalam_keywords(self) -> List[str]:
        """
        Load Malayalam-specific trending keywords and phrases.
        """
        return [
            # Entertainment & Media
            "സിനിമ", "സീരിയൽ", "ഗാനം", "നൃത്തം", "സംഗീതം",
            # Sports
            "ക്രിക്കറ്റ്", "ഫുട്ബോൾ", "കബഡി", "വോളിബോൾ", "ബാഡ്മിന്റൺ",
            # Politics & Current Affairs
            "തിരഞ്ഞെടുപ്പ്", "സർക്കാർ", "നയം", "വാർത്ത", "രാഷ്ട്രീയം",
            # Lifestyle
            "സുന്ദരി", "ആരോഗ്യം", "ഭക്ഷണം", "യാത്ര", "കല്യാണം",
            # Technology
            "ടെക്നോളജി", "മൊബൈൽ", "ഇന്റർനെറ്റ്", "ആപ്പ്", "ഗെയിം",
            # Education
            "പഠനം", "വിദ്യാഭ്യാസം", "പരീക്ഷ", "കോളേജ്", "വിദ്യാർഥി",
            # Religion & Culture
            "ക്ഷേത്രം", "പൂജ", "ഉത്സവം", "സംസ്കാരം", "മതം",
            # Business & Economy
            "ബിസിനസ്", "ജോലി", "സംഭാവന", "വില", "ആദായം"
        ]

    def _load_trend_patterns(self) -> Dict[str, Any]:
        """
        Load trend detection patterns and rules.
        """
        return {
            'velocity_threshold': 0.3,  # Minimum velocity for trending
            'cross_platform_bonus': 0.2,  # Bonus for cross-platform presence
            'freshness_decay': 0.1,  # Daily freshness decay
            'seasonal_multipliers': {
                'monday': 1.1,  # Start of week boost
                'friday': 1.3,  # Weekend anticipation
                'saturday': 1.4,  # Weekend peak
                'sunday': 1.2,   # Weekend continuation
            },
            'time_multipliers': {
                'morning': 1.0,   # 6-12
                'afternoon': 1.2, # 12-18
                'evening': 1.5,   # 18-22
                'night': 0.8      # 22-6
            }
        }

    async def predict_weekly_trends(self, platform: str = "youtube", days: int = 7) -> List[Dict[str, Any]]:
        """
        Predict trending topics for the next week using advanced algorithms.
        """
        try:
            logger.info(f"Predicting {days}-day trends for {platform}")

            # Gather current trend data
            current_trends = await self._gather_current_trends(platform)

            # Analyze historical patterns
            historical_patterns = await self._analyze_historical_patterns(platform)

            # Generate trend predictions
            predictions = await self._generate_trend_predictions(
                current_trends, historical_patterns, platform, days
            )

            # Apply Malayalam-specific optimizations
            predictions = self._apply_malayalam_optimizations(predictions)

            # Sort by predicted strength
            predictions.sort(key=lambda x: x['predicted_strength'], reverse=True)

            logger.info(f"Generated {len(predictions)} trend predictions")
            return predictions[:20]  # Return top 20 predictions

        except Exception as e:
            logger.error(f"Trend prediction failed: {e}")
            return self._fallback_trend_predictions(platform, days)

    async def _gather_current_trends(self, platform: str) -> List[Dict[str, Any]]:
        """
        Gather current trending topics from platform APIs and database.
        """
        trends = []

        try:
            # Get trends from platform API
            api_trends = await self.platform_apis.get(platform, self._fetch_mock_trends)(platform)
            trends.extend(api_trends)

            # Get trends from database
            async with async_session() as session:
                result = await session.execute("""
                    SELECT topic, trend_strength, velocity, cross_platform_count,
                           freshness, created_at
                    FROM trends
                    WHERE platform = $1 AND created_at >= $2
                    ORDER BY trend_strength DESC
                    LIMIT 50
                """, (platform, datetime.utcnow() - timedelta(days=7)))

                db_trends = result.fetchall()
                for row in db_trends:
                    trends.append({
                        'topic': row.topic,
                        'strength': float(row.trend_strength),
                        'velocity': float(row.velocity),
                        'cross_platform': row.cross_platform_count,
                        'freshness': float(row.freshness),
                        'source': 'database'
                    })

        except Exception as e:
            logger.error(f"Failed to gather current trends: {e}")

        return trends

    async def _analyze_historical_patterns(self, platform: str) -> Dict[str, Any]:
        """
        Analyze historical trend patterns for better predictions.
        """
        patterns = {
            'seasonal_patterns': {},
            'topic_clusters': {},
            'velocity_patterns': {},
            'platform_correlations': {}
        }

        try:
            async with async_session() as session:
                # Analyze seasonal patterns
                result = await session.execute("""
                    SELECT EXTRACT(DOW FROM created_at) as day_of_week,
                           EXTRACT(HOUR FROM created_at) as hour,
                           AVG(trend_strength) as avg_strength,
                           COUNT(*) as trend_count
                    FROM trends
                    WHERE platform = $1 AND created_at >= $2
                    GROUP BY day_of_week, hour
                """, (platform, datetime.utcnow() - timedelta(days=90)))

                seasonal_data = result.fetchall()
                for row in seasonal_data:
                    day = int(row.day_of_week)
                    hour = int(row.hour)
                    patterns['seasonal_patterns'][f"{day}_{hour}"] = {
                        'avg_strength': float(row.avg_strength),
                        'trend_count': row.trend_count
                    }

                # Analyze topic clusters
                result = await session.execute("""
                    SELECT topic, trend_strength, velocity
                    FROM trends
                    WHERE platform = $1 AND created_at >= $2
                    ORDER BY created_at DESC
                    LIMIT 200
                """, (platform, datetime.utcnow() - timedelta(days=30)))

                topics_data = result.fetchall()
                if topics_data:
                    patterns['topic_clusters'] = self._cluster_topics(topics_data)

        except Exception as e:
            logger.error(f"Failed to analyze historical patterns: {e}")

        return patterns

    def _cluster_topics(self, topics_data: List[Any]) -> Dict[str, List[str]]:
        """
        Cluster similar topics using text similarity.
        """
        try:
            topics = [row.topic for row in topics_data]

            # Create TF-IDF vectors
            vectorizer = TfidfVectorizer(max_features=100, ngram_range=(1, 2))
            tfidf_matrix = vectorizer.fit_transform(topics)

            # Cluster using DBSCAN
            clustering = DBSCAN(eps=0.3, min_samples=2, metric='cosine')
            clusters = clustering.fit_predict(tfidf_matrix)

            # Group topics by cluster
            topic_clusters = defaultdict(list)
            for topic, cluster_id in zip(topics, clusters):
                if cluster_id != -1:  # Ignore noise
                    topic_clusters[f"cluster_{cluster_id}"].append(topic)

            return dict(topic_clusters)

        except Exception as e:
            logger.error(f"Topic clustering failed: {e}")
            return {}

    async def _generate_trend_predictions(self, current_trends: List[Dict[str, Any]],
                                        patterns: Dict[str, Any], platform: str,
                                        days: int) -> List[Dict[str, Any]]:
        """
        Generate trend predictions using ML models and pattern analysis.
        """
        predictions = []

        try:
            # Use Prophet for time-series forecasting
            prophet_predictions = await self._prophet_forecast(current_trends, days)

            # Combine with current trends and patterns
            for trend in current_trends:
                topic = trend['topic']

                # Calculate predicted strength
                base_strength = trend.get('strength', 0.5)
                velocity = trend.get('velocity', 0.1)
                freshness = trend.get('freshness', 1.0)

                # Apply seasonal multipliers
                seasonal_multiplier = self._calculate_seasonal_multiplier()

                # Apply velocity decay
                velocity_decay = self._calculate_velocity_decay(velocity, days)

                # Calculate final predicted strength
                predicted_strength = (
                    base_strength * seasonal_multiplier * velocity_decay * freshness
                )

                # Add cross-platform bonus
                if trend.get('cross_platform', 0) > 1:
                    predicted_strength *= (1 + self.trend_patterns['cross_platform_bonus'])

                # Get trend category
                category = self._categorize_trend(topic)

                predictions.append({
                    'topic': topic,
                    'predicted_strength': min(predicted_strength, 1.0),
                    'trend_category': category,
                    'platform': platform,
                    'prediction_days': days,
                    'confidence': self._calculate_confidence(trend, patterns),
                    'peak_date': self._predict_peak_date(topic, patterns),
                    'related_topics': self._find_related_topics(topic, current_trends)
                })

            # Add prophet-based predictions
            predictions.extend(prophet_predictions)

        except Exception as e:
            logger.error(f"Failed to generate predictions: {e}")

        return predictions

    async def _prophet_forecast(self, trends: List[Dict[str, Any]], days: int) -> List[Dict[str, Any]]:
        """
        Use Prophet for time-series trend forecasting.
        """
        try:
            if not trends:
                return []

            # Prepare data for Prophet
            df_data = []
            for trend in trends:
                # Create synthetic time series data
                base_date = datetime.utcnow() - timedelta(days=7)
                for i in range(7):
                    date = base_date + timedelta(days=i)
                    strength = trend.get('strength', 0.5) * (0.8 + 0.4 * np.random.random())
                    df_data.append({
                        'ds': date,
                        'y': strength,
                        'topic': trend['topic']
                    })

            if not df_data:
                return []

            df = pd.DataFrame(df_data)

            # Group by topic and forecast
            prophet_predictions = []
            for topic in df['topic'].unique():
                topic_df = df[df['topic'] == topic][['ds', 'y']]

                if len(topic_df) < 3:
                    continue

                # Fit Prophet model
                model = Prophet(
                    daily_seasonality=True,
                    weekly_seasonality=True,
                    yearly_seasonality=False,
                    changepoint_prior_scale=0.05
                )

                model.fit(topic_df)

                # Make future predictions
                future = model.make_future_dataframe(periods=days)
                forecast = model.predict(future)

                # Get predictions for next days
                future_predictions = forecast.tail(days)
                avg_prediction = future_predictions['yhat'].mean()

                prophet_predictions.append({
                    'topic': f"{topic}_forecast",
                    'predicted_strength': float(avg_prediction),
                    'trend_category': 'forecast',
                    'platform': 'combined',
                    'prediction_days': days,
                    'confidence': 0.7,
                    'peak_date': None,
                    'related_topics': [topic]
                })

            return prophet_predictions

        except Exception as e:
            logger.error(f"Prophet forecasting failed: {e}")
            return []

    def _calculate_seasonal_multiplier(self) -> float:
        """
        Calculate seasonal multiplier based on current date/time.
        """
        now = datetime.utcnow()
        day_name = now.strftime('%A').lower()
        hour = now.hour

        # Day multiplier
        day_multiplier = self.trend_patterns['seasonal_multipliers'].get(day_name, 1.0)

        # Time multiplier
        if 6 <= hour < 12:
            time_multiplier = self.trend_patterns['time_multipliers']['morning']
        elif 12 <= hour < 18:
            time_multiplier = self.trend_patterns['time_multipliers']['afternoon']
        elif 18 <= hour < 22:
            time_multiplier = self.trend_patterns['time_multipliers']['evening']
        else:
            time_multiplier = self.trend_patterns['time_multipliers']['night']

        return day_multiplier * time_multiplier

    def _calculate_velocity_decay(self, velocity: float, days: int) -> float:
        """
        Calculate velocity decay over prediction period.
        """
        # Exponential decay based on velocity
        decay_rate = 0.1  # Daily decay rate
        return velocity * np.exp(-decay_rate * days) + (1 - velocity)

    def _categorize_trend(self, topic: str) -> str:
        """
        Categorize trend topic into predefined categories.
        """
        topic_lower = topic.lower()

        categories = {
            'entertainment': ['സിനിമ', 'സീരിയൽ', 'ഗാനം', 'നൃത്തം', 'സംഗീതം'],
            'sports': ['ക്രിക്കറ്റ്', 'ഫുട്ബോൾ', 'കബഡി', 'വോളിബോൾ'],
            'politics': ['തിരഞ്ഞെടുപ്പ്', 'സർക്കാർ', 'രാഷ്ട്രീയം'],
            'lifestyle': ['സുന്ദരി', 'ആരോഗ്യം', 'ഭക്ഷണം', 'യാത്ര'],
            'technology': ['ടെക്നോളജി', 'മൊബൈൽ', 'ഇന്റർനെറ്റ്'],
            'education': ['പഠനം', 'വിദ്യാഭ്യാസം', 'പരീക്ഷ'],
            'religion': ['ക്ഷേത്രം', 'പൂജ', 'ഉത്സവം'],
            'business': ['ബിസിനസ്', 'ജോലി', 'സംഭാവന']
        }

        for category, keywords in categories.items():
            if any(keyword in topic_lower for keyword in keywords):
                return category

        return 'general'

    def _calculate_confidence(self, trend: Dict[str, Any], patterns: Dict[str, Any]) -> float:
        """
        Calculate prediction confidence score.
        """
        confidence = 0.5  # Base confidence

        # Higher confidence for stronger current trends
        if trend.get('strength', 0) > 0.7:
            confidence += 0.2

        # Higher confidence for high velocity
        if trend.get('velocity', 0) > 0.3:
            confidence += 0.1

        # Higher confidence for cross-platform presence
        if trend.get('cross_platform', 0) > 1:
            confidence += 0.1

        # Higher confidence for fresh trends
        if trend.get('freshness', 0) > 0.8:
            confidence += 0.1

        return min(confidence, 1.0)

    def _predict_peak_date(self, topic: str, patterns: Dict[str, Any]) -> Optional[str]:
        """
        Predict when the trend will peak.
        """
        # Simple prediction based on trend category
        category = self._categorize_trend(topic)

        # Different categories peak at different times
        peak_days = {
            'entertainment': 2,  # Quick peaks
            'sports': 1,        # Very quick for live events
            'politics': 3,      # Sustained interest
            'lifestyle': 2,     # Moderate duration
            'technology': 4,    # Longer interest
            'education': 5,     # Sustained interest
            'religion': 3,      # Cultural timing
            'business': 3       # Economic timing
        }

        peak_day = peak_days.get(category, 2)
        peak_date = datetime.utcnow() + timedelta(days=peak_day)
        return peak_date.strftime('%Y-%m-%d')

    def _find_related_topics(self, topic: str, trends: List[Dict[str, Any]]) -> List[str]:
        """
        Find related trending topics.
        """
        related = []
        topic_lower = topic.lower()

        for trend in trends:
            other_topic = trend['topic'].lower()
            if other_topic != topic_lower:
                # Simple similarity check
                if len(set(topic_lower.split()) & set(other_topic.split())) > 0:
                    related.append(trend['topic'])

        return related[:3]  # Return up to 3 related topics

    def _apply_malayalam_optimizations(self, predictions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply Malayalam-specific optimizations to predictions.
        """
        for prediction in predictions:
            topic = prediction['topic']

            # Boost Malayalam language content
            if any(char in topic for char in 'അആഇഈഉഊഋഌഎഏഐഒഓഔകഖഗഘങചഛജഝഞടഠഡഢണതഥദധനപഫബഭമയരറലളഴവശഷസഹ'):
                prediction['predicted_strength'] *= 1.2

            # Add Malayalam-specific hashtags
            if prediction['trend_category'] == 'entertainment':
                prediction['suggested_hashtags'] = ['#MalayalamCinema', '#സിനിമ', '#KeralaFilm']
            elif prediction['trend_category'] == 'sports':
                prediction['suggested_hashtags'] = ['#KeralaSports', '#ക്രിക്കറ്റ്', '#SportsKerala']

        return predictions

    async def _fetch_youtube_trends(self, platform: str) -> List[Dict[str, Any]]:
        """
        Fetch trending topics from YouTube API.
        """
        # Mock implementation - replace with actual YouTube API calls
        return [
            {'topic': 'സിനിമ', 'strength': 0.8, 'velocity': 0.4, 'source': 'youtube'},
            {'topic': 'ക്രിക്കറ്റ്', 'strength': 0.7, 'velocity': 0.3, 'source': 'youtube'},
            {'topic': 'ഗാനം', 'strength': 0.6, 'velocity': 0.2, 'source': 'youtube'}
        ]

    async def _fetch_instagram_trends(self, platform: str) -> List[Dict[str, Any]]:
        """
        Fetch trending topics from Instagram API.
        """
        # Mock implementation - replace with actual Instagram API calls
        return [
            {'topic': 'ഫോട്ടോഗ്രാഫി', 'strength': 0.7, 'velocity': 0.3, 'source': 'instagram'},
            {'topic': 'ഭക്ഷണം', 'strength': 0.6, 'velocity': 0.2, 'source': 'instagram'},
            {'topic': 'യാത്ര', 'strength': 0.5, 'velocity': 0.1, 'source': 'instagram'}
        ]

    async def _fetch_mock_trends(self, platform: str) -> List[Dict[str, Any]]:
        """
        Fallback mock trend data.
        """
        return [
            {'topic': 'സാധാരണ', 'strength': 0.5, 'velocity': 0.1, 'source': 'mock'},
            {'topic': 'പുതിയ', 'strength': 0.4, 'velocity': 0.1, 'source': 'mock'}
        ]

    def _fallback_trend_predictions(self, platform: str, days: int) -> List[Dict[str, Any]]:
        """
        Fallback trend predictions when main prediction fails.
        """
        predictions = []

        for keyword in self.malayalam_keywords[:10]:
            predictions.append({
                'topic': keyword,
                'predicted_strength': 0.5 + np.random.random() * 0.3,
                'trend_category': self._categorize_trend(keyword),
                'platform': platform,
                'prediction_days': days,
                'confidence': 0.4,
                'peak_date': None,
                'related_topics': []
            })

        return predictions

    async def save_predictions(self, predictions: List[Dict[str, Any]]):
        """
        Save trend predictions to database.
        """
        try:
            async with async_session() as session:
                for prediction in predictions:
                    # Create trend record
                    trend = Trends(
                        topic=prediction['topic'],
                        platform=prediction['platform'],
                        trend_strength=prediction['predicted_strength'],
                        velocity=0.1,  # Default velocity
                        cross_platform_count=1,
                        language='ml',
                        freshness=1.0,
                        predicted_peak=datetime.strptime(prediction.get('peak_date'), '%Y-%m-%d') if prediction.get('peak_date') else None
                    )

                    session.add(trend)

                await session.commit()
                logger.info(f"Saved {len(predictions)} trend predictions")

        except Exception as e:
            logger.error(f"Failed to save predictions: {e}")
