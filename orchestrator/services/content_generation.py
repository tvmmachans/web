"""
Content blueprint generation service.
"""

import json
import logging
from typing import Dict, Any, List, Optional
import httpx
from datetime import datetime
import re

from orchestrator.config.settings import settings
from orchestrator.services.ml_prediction import MLPredictionService

logger = logging.getLogger(__name__)

class ContentGenerationService:
    """Service for generating content blueprints from trends."""

    def __init__(self):
        self.openai_api_key = settings.OPENAI_API_KEY
        self.voice_engine_url = settings.VOICE_ENGINE_URL
        self.backend_url = settings.BACKEND_BASE_URL
        self.ml_service = MLPredictionService()

    async def generate_blueprint(self, trend_data: Dict[str, Any], source_video_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a complete content blueprint from trend data.

        Args:
            trend_data: Trend information from database
            source_video_url: Optional URL to source video for clip extraction

        Returns:
            Complete blueprint dictionary
        """
        try:
            # Generate content elements using GPT
            content_elements = await self._generate_content_elements(trend_data)

            # Extract clip timestamps if video provided
            clip_timestamps = []
            if source_video_url:
                clip_timestamps = await self._extract_clip_timestamps(source_video_url, content_elements['script'])

            # Generate voiceover
            voiceover_result = await self._generate_voiceover(content_elements['voiceover_text'])

            # Get ML predictions
            features = self._prepare_prediction_features(trend_data, content_elements)
            predictions = self.ml_service.predict_engagement(features)

            # Calculate ROI score
            roi_score = self.ml_service.calculate_roi_score(predictions, trend_data.get('trend_strength', 0))

            # Create blueprint
            blueprint = {
                "blueprint_id": f"bp_{trend_data['id']}_{int(datetime.utcnow().timestamp())}",
                "trend_id": trend_data['id'],
                "title": content_elements['title'],
                "hook": content_elements['hook'],
                "script": content_elements['script'],
                "voiceover_text": content_elements['voiceover_text'],
                "captions": content_elements['captions'],
                "hashtags": content_elements['hashtags'],
                "video_url": source_video_url,
                "clip_timestamps": clip_timestamps,
                "audio_url": voiceover_result.get('audio_url'),
                "thumbnail_prompt": content_elements['thumbnail_prompt'],
                "predicted_views": predictions['predicted_views'],
                "predicted_likes": predictions['predicted_likes'],
                "predicted_ctr": predictions['predicted_ctr'],
                "confidence_score": predictions['confidence_score'],
                "roi_score": roi_score,
                "generation_params": features,
                "created_at": datetime.utcnow().isoformat()
            }

            return blueprint

        except Exception as e:
            logger.error(f"Blueprint generation failed: {e}")
            raise

    async def _generate_content_elements(self, trend_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate content elements using GPT-4."""
        prompt = self._build_content_prompt(trend_data)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-4",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.7,
                        "max_tokens": 1000
                    },
                    timeout=30
                )

                response.raise_for_status()
                result = response.json()

                content_text = result['choices'][0]['message']['content']

                # Parse the structured response
                return self._parse_content_response(content_text)

        except Exception as e:
            logger.error(f"GPT content generation failed: {e}")
            # Fallback to template-based generation
            return self._generate_fallback_content(trend_data)

    def _build_content_prompt(self, trend_data: Dict[str, Any]) -> str:
        """Build the GPT prompt for content generation."""
        trend_title = trend_data.get('title', '')
        trend_description = trend_data.get('description', '')
        source = trend_data.get('source', '')

        prompt = f"""You are a viral Malayalam short-form content writer. Given this trending topic, produce engaging content for a 30-60 second Reels/Shorts video.

Trend Topic: {trend_title}
Trend Description: {trend_description}
Source: {source}

Produce content in this exact JSON format:
{{
  "hook": "one-line Malayalam hook (5-10 words, emoji allowed)",
  "script": "2-4 short Malayalam sentences for 30s video with visual cues like [cut to reaction], [caption: punchline]",
  "hashtags": ["6-10", "mixed", "malayalam", "english", "tags"],
  "voiceover_text": "clean Malayalam script for TTS",
  "thumbnail_prompt": "3-word punchline for thumbnail",
  "title": "video title in Malayalam"
}}

Make it optimized for short-form attention, include Malayalam emojis, and ensure cultural relevance."""

        return prompt

    def _parse_content_response(self, content_text: str) -> Dict[str, Any]:
        """Parse GPT response into structured content elements."""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', content_text, re.DOTALL)
            if json_match:
                content_json = json.loads(json_match.group())
                return content_json
            else:
                raise ValueError("No JSON found in response")
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse GPT response: {e}")
            # Fallback parsing
            return self._parse_fallback_response(content_text)

    def _parse_fallback_response(self, content_text: str) -> Dict[str, Any]:
        """Fallback parsing for non-JSON GPT responses."""
        lines = content_text.split('\n')

        content = {
            "hook": "വിസ്മയകരമായ വിവരം! 🤩",
            "script": "ഇന്നത്തെ ട്രെൻഡിങ്ങ് വിഷയം നോക്കൂ. [ക്യാപ്ഷൻ: അത്ഭുതം] ഇത്രയും രസകരമായിരിക്കും എന്ന് കരുതിയില്ല.",
            "hashtags": ["malayalam", "trending", "kerala", "shorts", "reels"],
            "voiceover_text": "ഇന്നത്തെ ട്രെൻഡിങ്ങ് വിഷയം നോക്കൂ. അത്ഭുതം!",
            "thumbnail_prompt": "വിസ്മയ വിവരം",
            "title": "ട്രെൻഡിങ്ങ് വിഷയം"
        }

        # Try to extract meaningful parts
        for line in lines:
            if 'hook' in line.lower() and ':' in line:
                content['hook'] = line.split(':', 1)[1].strip()
            elif 'script' in line.lower() and ':' in line:
                content['script'] = line.split(':', 1)[1].strip()

        return content

    def _generate_fallback_content(self, trend_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fallback content when GPT fails."""
        title = trend_data.get('title', 'ട്രെൻഡിങ്ങ് വിഷയം')

        return {
            "hook": f"{title[:20]}... 🤩",
            "script": f"ഇന്നത്തെ ട്രെൻഡിങ്ങ് വിഷയം: {title}. [ക്യാപ്ഷൻ: രസകരം] നിങ്ങൾക്ക് ഇഷ്ടമാകും!",
            "hashtags": ["malayalam", "trending", "kerala", "shorts", "reels", "ദക്ഷിണേന്ത്യൻ"],
            "voiceover_text": f"ഇന്നത്തെ ട്രെൻഡിങ്ങ് വിഷയം {title} നോക്കൂ",
            "thumbnail_prompt": "ട്രെൻഡിങ്ങ് വിഷയം",
            "title": title
        }

    async def _extract_clip_timestamps(self, video_url: str, script: str) -> List[Dict[str, float]]:
        """Extract relevant clip timestamps from source video."""
        # This would integrate with video processing service
        # For now, return default timestamps
        return [
            {"start": 0.0, "end": 30.0, "description": "opening hook"},
            {"start": 30.0, "end": 60.0, "description": "main content"}
        ]

    async def _generate_voiceover(self, text: str) -> Dict[str, Any]:
        """Generate voiceover audio using voice engine."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.voice_engine_url}/voice_engine/generate",
                    json={
                        "text": text,
                        "language": "ml",
                        "voice": "malayalam_female_1"  # Default voice
                    },
                    timeout=60
                )

                if response.status_code == 200:
                    result = response.json()
                    return {
                        "audio_url": result.get('audio_url'),
                        "duration": result.get('duration', 30.0)
                    }
                else:
                    logger.warning(f"Voice generation failed: {response.status_code}")
                    return {"audio_url": None, "error": "voice_generation_failed"}

        except Exception as e:
            logger.error(f"Voice generation error: {e}")
            return {"audio_url": None, "error": str(e)}

    def _prepare_prediction_features(self, trend_data: Dict[str, Any], content_elements: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare features for ML prediction."""
        return {
            'trend_velocity': trend_data.get('velocity', 0),
            'trend_freshness': trend_data.get('freshness_score', 0.5),
            'cross_platform_count': trend_data.get('cross_platform_count', 1),
            'creator_followers': 10000.0,  # Would come from user profile
            'past_avg_views': 5000.0,     # Would come from analytics
            'posting_hour': 14.0,         # Default afternoon
            'day_of_week': datetime.utcnow().weekday(),
            'video_category_score': 0.5,  # Default
            'has_faces': 1.0,             # Assume has faces
            'language_match': 1.0,        # Malayalam content
            'title_length': len(content_elements.get('title', '')),
            'has_emojis': 1.0 if '🤩' in content_elements.get('hook', '') else 0.0
        }

    async def validate_content(self, blueprint: Dict[str, Any]) -> Dict[str, Any]:
        """Validate generated content for safety and quality."""
        issues = []

        # Content filter checks
        if settings.CONTENT_FILTER_ENABLED:
            text_content = f"{blueprint['title']} {blueprint['script']} {blueprint['voiceover_text']}"
            filter_result = await self._check_content_filter(text_content)
            if not filter_result['safe']:
                issues.extend(filter_result['issues'])

        # Quality checks
        if len(blueprint['script']) < 50:
            issues.append("Script too short")

        if len(blueprint['hashtags']) < 5:
            issues.append("Insufficient hashtags")

        if not blueprint.get('audio_url'):
            issues.append("Voiceover generation failed")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "blueprint": blueprint
        }

    async def _check_content_filter(self, text: str) -> Dict[str, Any]:
        """Check content against safety filters."""
        # This would integrate with OpenAI content policy or custom filters
        # For now, basic checks
        blocked_words = ["hate", "violence", "inappropriate"]  # Would be more comprehensive

        issues = []
        for word in blocked_words:
            if word.lower() in text.lower():
                issues.append(f"Contains blocked word: {word}")

        return {
            "safe": len(issues) == 0,
            "issues": issues
        }
