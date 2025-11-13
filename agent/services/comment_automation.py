import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
import sys

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from openai import OpenAI
from agent.config.settings import (
    COMMENT_CHECK_INTERVAL_MINUTES, MAX_COMMENTS_PER_POST,
    MALAYALAM_LANGUAGE_CODE, YOUTUBE_API_KEY, INSTAGRAM_ACCESS_TOKEN
)
from agent.utils.database import get_db_session

logger = logging.getLogger(__name__)

class CommentAutomation:
    """
    Automated comment management and AI-powered replies.
    Monitors comments and responds with contextual Malayalam/English replies.
    """

    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.youtube_api_key = YOUTUBE_API_KEY
        self.instagram_token = INSTAGRAM_ACCESS_TOKEN

    async def start_comment_monitoring(self):
        """
        Start continuous comment monitoring loop.
        """
        logger.info(f"Starting comment monitoring every {COMMENT_CHECK_INTERVAL_MINUTES} minutes")

        while True:
            try:
                await self._check_and_respond_to_comments()
                await asyncio.sleep(COMMENT_CHECK_INTERVAL_MINUTES * 60)
            except Exception as e:
                logger.error(f"Error in comment monitoring: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error

    async def _check_and_respond_to_comments(self):
        """
        Check for new comments and generate AI responses.
        """
        try:
            # Get posts that need comment checking
            async for session in get_db_session():
                posts = await self._get_posts_for_comment_check(session)
                break

            for post in posts:
                try:
                    comments = await self._fetch_comments(post)
                    if comments:
                        await self._process_comments(session, post, comments)
                except Exception as e:
                    logger.error(f"Error processing comments for post {post.id}: {e}")

        except Exception as e:
            logger.error(f"Error checking comments: {e}")

    async def _get_posts_for_comment_check(self, session) -> List:
        """
        Get posts that should be checked for comments.
        """
        try:
            from models.post import Post
            from sqlalchemy import select, and_, or_
            from datetime import datetime, timedelta

            # Get posts from last 7 days that are posted
            cutoff_date = datetime.utcnow() - timedelta(days=7)

            stmt = select(Post).where(
                and_(
                    Post.status == "posted",
                    Post.posted_at >= cutoff_date
                )
            )

            result = await session.execute(stmt)
            posts = result.scalars().all()

            return posts

        except Exception as e:
            logger.error(f"Error getting posts for comment check: {e}")
            return []

    async def _fetch_comments(self, post) -> List[Dict[str, Any]]:
        """
        Fetch comments from the appropriate platform API.
        """
        try:
            if post.platform == "youtube":
                return await self._fetch_youtube_comments(post)
            elif post.platform == "instagram":
                return await self._fetch_instagram_comments(post)
            else:
                return []

        except Exception as e:
            logger.error(f"Error fetching comments for post {post.id}: {e}")
            return []

    async def _fetch_youtube_comments(self, post) -> List[Dict[str, Any]]:
        """
        Fetch comments from YouTube API.
        """
        try:
            import requests

            # This would use YouTube Data API v3
            # For now, return mock data
            # In production, implement actual API calls

            video_id = post.video_url.split('/')[-1] if post.video_url else None
            if not video_id:
                return []

            # Mock comments for demonstration
            mock_comments = [
                {
                    "id": "mock1",
                    "text": "നല്ല വീഡിയോ! മികച്ച കോൺടെന്റ് 👍",
                    "author": "User1",
                    "published_at": datetime.utcnow().isoformat(),
                    "platform": "youtube",
                    "language": "malayalam"
                },
                {
                    "id": "mock2",
                    "text": "Great content! Keep it up!",
                    "author": "User2",
                    "published_at": datetime.utcnow().isoformat(),
                    "platform": "youtube",
                    "language": "english"
                }
            ]

            return mock_comments

        except Exception as e:
            logger.error(f"Error fetching YouTube comments: {e}")
            return []

    async def _fetch_instagram_comments(self, post) -> List[Dict[str, Any]]:
        """
        Fetch comments from Instagram Graph API.
        """
        try:
            # Mock comments for demonstration
            mock_comments = [
                {
                    "id": "mock3",
                    "text": "അടിപൊളി! 🔥",
                    "author": "User3",
                    "published_at": datetime.utcnow().isoformat(),
                    "platform": "instagram",
                    "language": "malayalam"
                }
            ]

            return mock_comments

        except Exception as e:
            logger.error(f"Error fetching Instagram comments: {e}")
            return []

    async def _process_comments(self, session, post, comments: List[Dict[str, Any]]):
        """
        Process comments and generate responses.
        """
        try:
            responded_count = 0

            for comment in comments[:MAX_COMMENTS_PER_POST]:  # Limit per post
                try:
                    # Check if we already responded to this comment
                    if await self._already_responded(session, post.id, comment["id"]):
                        continue

                    # Generate AI response
                    response = await self._generate_comment_response(post, comment)

                    if response:
                        # Post the response
                        success = await self._post_comment_response(post, comment, response)

                        if success:
                            # Record the response
                            await self._record_response(session, post.id, comment["id"], response)
                            responded_count += 1

                except Exception as e:
                    logger.error(f"Error processing comment {comment['id']}: {e}")

            logger.info(f"Processed {responded_count} comments for post {post.id}")

        except Exception as e:
            logger.error(f"Error processing comments for post {post.id}: {e}")

    async def _generate_comment_response(self, post, comment: Dict[str, Any]) -> Optional[str]:
        """
        Generate an AI-powered response to a comment.
        """
        try:
            comment_text = comment.get("text", "")
            language = comment.get("language", "english")
            platform = comment.get("platform", "youtube")

            # Determine if response is needed
            if not self._should_respond(comment_text):
                return None

            prompt = f"""
            Generate a friendly, contextual response to this social media comment.
            Post title: {post.title}
            Post description: {post.description or post.ai_caption}
            Platform: {platform}
            Language: {language}

            Comment: "{comment_text}"

            Guidelines:
            - Respond in the same language as the comment
            - Be friendly and engaging
            - Keep it concise (under 100 characters)
            - Include relevant emojis if appropriate
            - Don't be overly promotional

            Response:
            """

            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=0.8
            )

            ai_response = response.choices[0].message.content.strip()

            # Clean up response
            ai_response = ai_response.strip('"')

            logger.info(f"Generated response to comment: {ai_response}")
            return ai_response

        except Exception as e:
            logger.error(f"Error generating comment response: {e}")
            return None

    def _should_respond(self, comment_text: str) -> bool:
        """
        Determine if a comment warrants a response.
        """
        try:
            # Skip very short comments
            if len(comment_text.strip()) < 3:
                return False

            # Skip obvious spam or irrelevant comments
            skip_keywords = ["spam", "bot", "fake", "scam"]
            if any(keyword in comment_text.lower() for keyword in skip_keywords):
                return False

            # Respond to positive comments, questions, or engagement
            positive_indicators = ["നല്ല", "good", "nice", "awesome", "thanks", "thank", "?", "എങ്ങനെ", "how"]
            if any(indicator in comment_text.lower() for indicator in positive_indicators):
                return True

            # Randomly respond to some neutral comments (20% chance)
            import random
            return random.random() < 0.2

        except Exception as e:
            logger.error(f"Error checking if should respond: {e}")
            return False

    async def _post_comment_response(self, post, comment: Dict[str, Any], response: str) -> bool:
        """
        Post the response to the appropriate platform.
        """
        try:
            platform = post.platform

            if platform == "youtube":
                return await self._post_youtube_reply(comment["id"], response)
            elif platform == "instagram":
                return await self._post_instagram_reply(post, comment["id"], response)
            else:
                logger.warning(f"Unsupported platform for comment response: {platform}")
                return False

        except Exception as e:
            logger.error(f"Error posting comment response: {e}")
            return False

    async def _post_youtube_reply(self, comment_id: str, response: str) -> bool:
        """
        Post reply to YouTube comment.
        """
        try:
            # This would use YouTube Data API
            # For now, just log the response
            logger.info(f"YouTube reply to {comment_id}: {response}")
            return True

        except Exception as e:
            logger.error(f"Error posting YouTube reply: {e}")
            return False

    async def _post_instagram_reply(self, post, comment_id: str, response: str) -> bool:
        """
        Post reply to Instagram comment.
        """
        try:
            # This would use Instagram Graph API
            # For now, just log the response
            logger.info(f"Instagram reply to {comment_id}: {response}")
            return True

        except Exception as e:
            logger.error(f"Error posting Instagram reply: {e}")
            return False

    async def _already_responded(self, session, post_id: int, comment_id: str) -> bool:
        """
        Check if we already responded to this comment.
        """
        try:
            # This would check a comment_responses table
            # For now, return False (always respond)
            return False

        except Exception as e:
            logger.error(f"Error checking response history: {e}")
            return False

    async def _record_response(self, session, post_id: int, comment_id: str, response: str):
        """
        Record the response in database for tracking.
        """
        try:
            # This would insert into a comment_responses table
            # For now, just log
            logger.info(f"Recorded response for post {post_id}, comment {comment_id}")

        except Exception as e:
            logger.error(f"Error recording response: {e}")

    async def get_comment_stats(self) -> Dict[str, Any]:
        """
        Get comment automation statistics.
        """
        return {
            "service": "comment_automation",
            "check_interval_minutes": COMMENT_CHECK_INTERVAL_MINUTES,
            "max_comments_per_post": MAX_COMMENTS_PER_POST,
            "supported_languages": ["malayalam", "english"],
            "supported_platforms": ["youtube", "instagram"]
        }
