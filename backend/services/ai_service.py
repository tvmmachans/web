import asyncio
import json
import logging
import os
import tempfile
from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.database import LearningData, async_session

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None
try:
    from transformers import pipeline
except ImportError:
    pipeline = None

try:
    from ai_engine.advanced_models import AdvancedMLModels
except ImportError:
    AdvancedMLModels = None
from ai_engine.learning_manager import LearningManager

try:
    from services.speech_recognition import speech_recognition_service, STTProvider
except ImportError:
    speech_recognition_service = None
    STTProvider = None

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if OpenAI and OPENAI_API_KEY:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
else:
    openai_client = None

# Initialize learning manager and advanced models
learning_manager = LearningManager()

# Advanced models with robust error handling
advanced_models = None
try:
    # First try the original import
    from backend.models.advanced_models import AdvancedMLModels

    advanced_models = AdvancedMLModels()
    print("Advanced models initialized successfully")
except ImportError:
    # If that fails, check what's available and use alternatives
    try:
        import backend.models.advanced_models as am

        available_classes = [
            x for x in dir(am) if not x.startswith("_") and x[0].isupper()
        ]
        print(f"Available classes in advanced_models: {available_classes}")

        # Try common alternative class names
        if "AdvancedModel" in available_classes:
            from backend.models.advanced_models import AdvancedModel

            advanced_models = AdvancedModel()
            print("Using AdvancedModel as alternative")
        elif "MLModel" in available_classes:
            from backend.models.advanced_models import MLModel

            advanced_models = MLModel()
            print("Using MLModel as alternative")
        else:
            print("No suitable advanced model class found")

    except Exception as e:
        print(f"Could not find alternative advanced models: {e}")
except Exception as e:
    print(f"Advanced models initialization failed: {e}")

# Emotion analysis pipeline for Malayalam content
emotion_analyzer = None  # Temporarily disabled due to model access issues
# emotion_analyzer = pipeline(
#     "text-classification",
#     model="j-hartmann/emotion-english-distilroberta-base-0.2",
#     return_all_scores=True,
# ) if pipeline else None


async def generate_caption_service(video_path: str, language: str = "ml") -> str:
    """
    Generate AI caption for video using OpenAI.
    Supports Malayalam (ml) and other languages.
    """
    if openai_client is None:
        return f"Default caption for {language}: Engaging content!"

    # Transcribe video to text
    transcription = transcribe_video(video_path, language)

    # Generate caption using OpenAI
    prompt = f"Generate an engaging social media caption in {language} for this video content: {transcription}"
    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=150,
    )
    return response.choices[0].message.content.strip()


async def generate_subtitles_service(
    video_path: str, language: str = "ml"
) -> List[Dict]:
    """
    Generate subtitles for video using alternative speech recognition.
    Returns list of subtitle segments with timestamps.
    """
    # Extract audio from video first
    import moviepy.editor as mp

    try:
        video = mp.VideoFileClip(video_path)
        audio_path = video_path.replace(".mp4", "_temp.wav")
        video.audio.write_audiofile(audio_path, verbose=False, logger=None)

        # Read audio data
        with open(audio_path, "rb") as f:
            audio_data = f.read()

        # Transcribe using alternative service
        result = await speech_recognition_service.transcribe_audio(
            audio_data, language=_map_language_code(language)
        )

        # Clean up temp file
        os.unlink(audio_path)

        # Format subtitles
        subtitles = []
        if result.get("segments"):
            for segment in result["segments"]:
                subtitles.append(
                    {
                        "start": segment.get("start_time", 0),
                        "end": segment.get("end_time", 0),
                        "text": segment.get("word", ""),
                    }
                )
        else:
            # Fallback: create single subtitle from full text
            duration = video.duration if video else 10
            subtitles = [{"start": 0, "end": duration, "text": result.get("text", "")}]

        return subtitles

    except Exception as e:
        logger.error(f"Subtitle generation failed: {e}")
        return []


async def transcribe_video_async(video_path: str, language: str = "ml") -> str:
    """
    Transcribe video audio to text using alternative speech recognition.
    """
    # Extract audio from video
    import moviepy.editor as mp

    try:
        video = mp.VideoFileClip(video_path)
        audio_path = video_path.replace(".mp4", "_temp.wav")
        video.audio.write_audiofile(audio_path, verbose=False, logger=None)

        # Read audio data
        with open(audio_path, "rb") as f:
            audio_data = f.read()

        # Transcribe using alternative service
        result = await speech_recognition_service.transcribe_audio(
            audio_data, language=_map_language_code(language)
        )

        # Clean up temp file
        os.unlink(audio_path)

        return result.get("text", "")

    except Exception as e:
        logger.error(f"Video transcription failed: {e}")
        return ""


def transcribe_video(video_path: str, language: str = "ml") -> str:
    """
    Synchronous wrapper for video transcription.
    """
    # Run async transcription in event loop
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(transcribe_video_async(video_path, language))
        loop.close()
        return result
    except Exception as e:
        logger.error(f"Transcription wrapper failed: {e}")
        return ""


def _map_language_code(language: str) -> str:
    """Map simple language codes to full codes expected by STT services."""
    language_map = {
        "ml": "ml-IN",  # Malayalam
        "en": "en-US",  # English
        "hi": "hi-IN",  # Hindi
        "ta": "ta-IN",  # Tamil
        "te": "te-IN",  # Telugu
    }
    return language_map.get(language, "en-US")


async def generate_adaptive_caption_service(
    video_path: str, language: str = "ml", trend_context: Optional[Dict] = None
) -> str:
    """
    Generate adaptive caption using learning manager with trend context.
    """
    try:
        # Use learning manager for adaptive caption generation
        trend_context = trend_context or {}
        caption = await learning_manager.generate_adaptive_caption(
            video_path, trend_context
        )

        logger.info(f"Generated adaptive caption for {language} content")
        return caption

    except Exception as e:
        logger.error(f"Adaptive caption generation failed: {e}")
        # Fallback to basic caption generation
        return await generate_caption_service(video_path, language)


async def generate_emotion_aware_caption_service(
    video_path: str, language: str = "ml", target_emotion: Optional[str] = None
) -> str:
    """
    Generate emotion-aware caption based on content analysis.
    """
    try:
        # Transcribe video
        transcription = transcribe_video(video_path, language)

        # Analyze emotion in transcription (fallback to English emotion analysis)
        # Note: This is a simplified approach - in production, you'd want Malayalam-specific emotion analysis
        emotion_scores = emotion_analyzer(transcription[:512])  # Limit text length
        dominant_emotion = max(emotion_scores[0], key=lambda x: x["score"])["label"]

        # Generate caption with emotion context
        emotion_prompts = {
            "joy": "Create a joyful, celebratory caption",
            "sadness": "Create an empathetic, comforting caption",
            "anger": "Create a passionate, motivational caption",
            "fear": "Create a reassuring, supportive caption",
            "surprise": "Create an exciting, intriguing caption",
        }

        prompt_type = emotion_prompts.get(
            target_emotion or dominant_emotion,
            "Create an engaging social media caption",
        )

        prompt = f"{prompt_type} in {language} for this video content: {transcription}"

        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
        )

        caption = response.choices[0].message.content.strip()

        # Add Malayalam-specific emotion indicators
        if language == "ml":
            emotion_indicators = {
                "joy": " 😊 #സന്തോഷം",
                "sadness": " 💙 #സ്നേഹം",
                "anger": " 🔥 #പ്രചോദനം",
                "fear": " 🤝 #സഹായം",
                "surprise": " 😲 #ആശ്ചര്യം",
            }
            caption += emotion_indicators.get(
                target_emotion or dominant_emotion, " 📱 #മലയാളം"
            )

        logger.info(f"Generated emotion-aware caption with emotion: {dominant_emotion}")
        return caption

    except Exception as e:
        logger.error(f"Emotion-aware caption generation failed: {e}")
        return await generate_caption_service(video_path, language)


async def learn_from_engagement_feedback(
    post_id: int, actual_performance: Dict[str, Any]
):
    """
    Learn from engagement feedback to improve future captions.
    """
    try:
        await learning_manager.collect_learning_data(post_id, actual_performance)
        logger.info(f"Collected learning data for post {post_id}")

    except Exception as e:
        logger.error(f"Failed to learn from engagement feedback: {e}")


async def get_caption_suggestions(
    video_path: str, language: str = "ml", count: int = 3
) -> List[str]:
    """
    Generate multiple caption suggestions using learning insights.
    """
    try:
        transcription = transcribe_video(video_path, language)

        # Get learning insights for caption generation
        async with async_session() as session:
            # Get recent successful captions
            result = await session.execute(
                """
                SELECT ai_caption, analytics.engagement_rate
                FROM posts p
                JOIN analytics ON p.id = analytics.post_id
                WHERE p.ai_caption IS NOT NULL
                AND analytics.engagement_rate > 0.02
                ORDER BY analytics.engagement_rate DESC
                LIMIT 5
            """
            )

            successful_captions = result.fetchall()

        # Generate varied prompts based on successful patterns
        suggestions = []
        base_prompt = (
            f"Generate a social media caption in {language} for: {transcription}"
        )

        prompts = [
            base_prompt,
            f"{base_prompt} (make it humorous)",
            f"{base_prompt} (focus on emotional connection)",
            f"{base_prompt} (highlight key moments)",
        ]

        for prompt in prompts[:count]:
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
            )
            suggestion = response.choices[0].message.content.strip()
            suggestions.append(suggestion)

        logger.info(f"Generated {len(suggestions)} caption suggestions")
        return suggestions

    except Exception as e:
        logger.error(f"Caption suggestions generation failed: {e}")
        return [await generate_caption_service(video_path, language)]


async def analyze_content_sentiment(text: str) -> Dict[str, float]:
    """
    Analyze sentiment of Malayalam content with ML enhancement.
    """
    try:
        # Use learning manager for enhanced sentiment analysis
        ml_sentiment = learning_manager.analyze_sentiment(text)

        # Fallback to emotion analyzer if ML fails
        if ml_sentiment.get("confidence", 0) < 0.3:
            sentiment_scores = emotion_analyzer(text[:512])

            # Convert to simplified sentiment scores
            sentiment_map = {}
            for score in sentiment_scores[0]:
                sentiment_map[score["label"].lower()] = score["score"]

            # Calculate overall sentiment
            positive_score = sentiment_map.get("joy", 0) + sentiment_map.get(
                "surprise", 0
            )
            negative_score = (
                sentiment_map.get("sadness", 0)
                + sentiment_map.get("anger", 0)
                + sentiment_map.get("fear", 0)
            )

            emotion_result = {
                "positive": positive_score,
                "negative": negative_score,
                "neutral": sentiment_map.get("neutral", 0.5),
                "dominant_emotion": max(sentiment_map.items(), key=lambda x: x[1])[0],
            }

            # Combine ML and emotion analysis
            combined_confidence = (ml_sentiment.get("confidence", 0) + 0.5) / 2
            sentiment = ml_sentiment.get(
                "sentiment", emotion_result.get("dominant_emotion", "neutral")
            )

            return {
                "sentiment": sentiment,
                "confidence": combined_confidence,
                "positive": emotion_result["positive"],
                "negative": emotion_result["negative"],
                "neutral": emotion_result["neutral"],
                "dominant_emotion": emotion_result["dominant_emotion"],
                "ml_contribution": ml_sentiment.get("confidence", 0),
                "emotion_contribution": 0.5,
            }
        else:
            return ml_sentiment

    except Exception as e:
        logger.error(f"Sentiment analysis failed: {e}")
        return {
            "positive": 0.5,
            "negative": 0.5,
            "neutral": 0.5,
            "dominant_emotion": "neutral",
        }


async def optimize_posting_schedule(content_features: Dict, platform: str) -> Dict:
    """
    Optimize posting schedule using ML predictions.
    """
    try:
        if advanced_models.engagement_model:
            # Predict best times based on content features
            predictions = []

            # Test different time slots
            for hour in range(24):
                for day in range(7):
                    test_features = content_features.copy()
                    test_features.update(
                        {
                            "hour_posted": hour,
                            "day_of_week": day,
                            "is_weekend": day >= 5,
                        }
                    )

                    feature_vector = list(test_features.values())
                    predicted_engagement = advanced_models.predict_engagement(
                        [feature_vector]
                    )[0]

                    predictions.append(
                        {
                            "hour": hour,
                            "day": day,
                            "predicted_engagement": predicted_engagement,
                        }
                    )

            # Find optimal time
            best_prediction = max(predictions, key=lambda x: x["predicted_engagement"])

            return {
                "optimal_hour": best_prediction["hour"],
                "optimal_day": best_prediction["day"],
                "predicted_engagement": best_prediction["predicted_engagement"],
                "confidence": 0.8,  # Placeholder confidence
            }
        else:
            # Fallback to basic optimization
            return {
                "optimal_hour": 18,  # 6 PM
                "optimal_day": 2,  # Wednesday
                "predicted_engagement": 0.6,
                "confidence": 0.5,
            }

    except Exception as e:
        logger.error(f"Error optimizing schedule: {e}")
        return {
            "optimal_hour": 18,
            "optimal_day": 2,
            "predicted_engagement": 0.5,
            "confidence": 0.3,
        }


async def get_caption_performance_feedback(
    caption: str, actual_engagement: float
) -> Dict:
    """
    Analyze caption performance and provide feedback for learning.
    """
    try:
        # Find the caption in history (if stored)
        # For now, provide basic feedback based on engagement
        feedback = {
            "performance_score": min(actual_engagement, 2.0),  # Cap at 2.0
            "actual_engagement": actual_engagement,
            "improvement_needed": actual_engagement < 0.5,
            "recommendations": [],
        }

        if actual_engagement < 0.3:
            feedback["recommendations"].append("Try more engaging language")
        if actual_engagement < 0.5:
            feedback["recommendations"].append("Consider adding emojis or questions")
        if actual_engagement > 1.0:
            feedback["recommendations"].append("This caption style works well!")

        return feedback

    except Exception as e:
        logger.error(f"Error getting caption feedback: {e}")
        return {"feedback": "Error analyzing performance", "score": 0.5}
