"""
Platform Orchestrator - Cross-platform automation and management
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from agent.services.smart_publisher import SmartPublisher

logger = logging.getLogger(__name__)


class PlatformOrchestrator:
    """Orchestrates multi-platform posting and management."""

    def __init__(self):
        self.publisher = SmartPublisher()

    async def simultaneous_posting(
        self,
        video_data: Dict[str, Any],
        platforms: List[str] = ["youtube", "instagram"],
    ) -> Dict[str, Any]:
        """Post to multiple platforms simultaneously."""
        try:
            # Post to all platforms in parallel
            tasks = []
            for platform in platforms:
                task = self._post_to_platform(video_data, platform)
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Compile results
            posting_results = {}
            for platform, result in zip(platforms, results):
                if isinstance(result, Exception):
                    posting_results[platform] = {
                        "status": "failed",
                        "error": str(result),
                    }
                else:
                    posting_results[platform] = result

            return {
                "posted_platforms": [
                    p for p, r in posting_results.items() if r.get("status") == "published"
                ],
                "failed_platforms": [
                    p for p, r in posting_results.items() if r.get("status") == "failed"
                ],
                "results": posting_results,
                "posted_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Simultaneous posting failed: {e}")
            return {"error": str(e), "status": "failed"}

    async def _post_to_platform(
        self, video_data: Dict[str, Any], platform: str
    ) -> Dict[str, Any]:
        """Post to a single platform."""
        return await self.publisher.publish_content(
            video_data, platforms=[platform], auto_schedule=True
        )

    async def platform_specific_optimizer(
        self, content: Dict[str, Any], platform: str
    ) -> Dict[str, Any]:
        """Optimize content for specific platform."""
        optimizations = {
            "youtube": {
                "title_length": 60,
                "description_length": 5000,
                "tags_count": 10,
                "thumbnail_ratio": "16:9",
            },
            "instagram": {
                "caption_length": 2200,
                "hashtags_count": 30,
                "thumbnail_ratio": "1:1",
                "video_ratio": "9:16",
            },
        }

        platform_specs = optimizations.get(platform, {})
        optimized_content = content.copy()

        # Apply optimizations
        if "title" in optimized_content:
            title = optimized_content["title"]
            max_length = platform_specs.get("title_length", 100)
            if len(title) > max_length:
                optimized_content["title"] = title[:max_length - 3] + "..."

        return {
            "original_content": content,
            "optimized_content": optimized_content,
            "platform": platform,
            "optimizations_applied": platform_specs,
        }

    async def cross_promotion_engine(
        self, primary_content: Dict[str, Any], platforms: List[str]
    ) -> Dict[str, Any]:
        """Promote content across multiple platforms."""
        promotion_results = {}

        for platform in platforms:
            try:
                # Create platform-specific promotion
                promotion = await self._create_promotion(primary_content, platform)

                # Post promotion
                result = await self._post_promotion(promotion, platform)

                promotion_results[platform] = {
                    "promotion": promotion,
                    "result": result,
                    "status": "posted" if result.get("status") == "published" else "failed",
                }
            except Exception as e:
                logger.error(f"Cross-promotion failed for {platform}: {e}")
                promotion_results[platform] = {"status": "failed", "error": str(e)}

        return {
            "primary_content": primary_content,
            "promotion_results": promotion_results,
            "promoted_at": datetime.utcnow().isoformat(),
        }

    async def _create_promotion(
        self, content: Dict[str, Any], platform: str
    ) -> Dict[str, Any]:
        """Create platform-specific promotion."""
        return {
            "type": "cross_promotion",
            "original_content_url": content.get("video_url"),
            "platform": platform,
            "message": f"Check out our latest content! {content.get('title', '')}",
        }

    async def _post_promotion(
        self, promotion: Dict[str, Any], platform: str
    ) -> Dict[str, Any]:
        """Post promotion to platform."""
        # Placeholder - would use platform APIs
        return {"status": "published", "platform": platform}


class CommentManagementAI:
    """AI-powered comment management and auto-responses."""

    def __init__(self):
        from openai import OpenAI
        import os

        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def auto_respond_to_comments(
        self, comments: List[Dict[str, Any]], post_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Automatically respond to comments using AI."""
        responses = []

        for comment in comments:
            try:
                # Generate response
                response = await self._generate_comment_response(
                    comment, post_context
                )

                responses.append(
                    {
                        "comment_id": comment.get("id"),
                        "original_comment": comment.get("text"),
                        "ai_response": response,
                        "sentiment": self._analyze_sentiment(comment.get("text", "")),
                    }
                )
            except Exception as e:
                logger.error(f"Comment response generation failed: {e}")

        return responses

    async def _generate_comment_response(
        self, comment: Dict[str, Any], post_context: Dict[str, Any]
    ) -> str:
        """Generate AI response to comment."""
        try:
            prompt = f"""Generate a friendly, engaging response in Malayalam to this comment on our social media post:

Comment: {comment.get('text', '')}
Post Title: {post_context.get('title', '')}

Requirements:
- Respond in Malayalam
- Be friendly and engaging
- Keep it brief (1-2 sentences)
- Thank them if positive, address concerns if negative
- Include relevant emoji if appropriate"""

            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.7,
            )

            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            return "നന്ദി! 🙏"

    def _analyze_sentiment(self, text: str) -> str:
        """Analyze comment sentiment."""
        positive_words = ["നല്ല", "അതിഭംഗം", "സൂപ്പർ", "ലൈക്ക്"]
        negative_words = ["മോശം", "ഇഷ്ടമല്ല", "വിമർശനം"]

        text_lower = text.lower()
        if any(word in text_lower for word in positive_words):
            return "positive"
        elif any(word in text_lower for word in negative_words):
            return "negative"
        else:
            return "neutral"

