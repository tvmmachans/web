import os
import sys
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import logging

# Add backend to path to reuse models
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from database import Base, Post, Analytics, User

logger = logging.getLogger(__name__)

# Reuse database configuration from backend
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost/social_media_manager")

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db_session() -> AsyncSession:
    """
    Get database session for agent operations.
    """
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_agent_db():
    """
    Initialize database tables if they don't exist.
    """
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Agent database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize agent database: {e}")
        raise

async def get_pending_posts(session: AsyncSession, limit: int = 10):
    """
    Get posts that are in draft status and ready for agent processing.
    """
    try:
        from sqlalchemy import select
        stmt = select(Post).where(Post.status == "draft").limit(limit)
        result = await session.execute(stmt)
        posts = result.scalars().all()
        return posts
    except Exception as e:
        logger.error(f"Failed to get pending posts: {e}")
        return []

async def get_recent_analytics(session: AsyncSession, days: int = 30):
    """
    Get recent analytics data for decision making.
    """
    try:
        from sqlalchemy import select
        from datetime import datetime, timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        stmt = select(Analytics).where(Analytics.recorded_at >= cutoff_date)
        result = await session.execute(stmt)
        analytics = result.scalars().all()
        return analytics
    except Exception as e:
        logger.error(f"Failed to get recent analytics: {e}")
        return []

async def update_post_status(session: AsyncSession, post_id: int, status: str, **kwargs):
    """
    Update post status and additional fields.
    """
    try:
        post = await session.get(Post, post_id)
        if post:
            post.status = status
            for key, value in kwargs.items():
                if hasattr(post, key):
                    setattr(post, key, value)
            await session.commit()
            logger.info(f"Updated post {post_id} status to {status}")
        else:
            logger.warning(f"Post {post_id} not found for status update")
    except Exception as e:
        logger.error(f"Failed to update post {post_id} status: {e}")
        await session.rollback()

async def create_analytics_record(session: AsyncSession, post_id: int, platform: str,
                                views: int = 0, likes: int = 0, comments: int = 0,
                                shares: int = 0, engagement_rate: float = 0.0):
    """
    Create a new analytics record for a post.
    """
    try:
        analytics = Analytics(
            post_id=post_id,
            platform=platform,
            views=views,
            likes=likes,
            comments=comments,
            shares=shares,
            engagement_rate=engagement_rate
        )
        session.add(analytics)
        await session.commit()
        logger.info(f"Created analytics record for post {post_id} on {platform}")
        return analytics
    except Exception as e:
        logger.error(f"Failed to create analytics record for post {post_id}: {e}")
        await session.rollback()
        return None
