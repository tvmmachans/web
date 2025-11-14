from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from datetime import datetime, timedelta
from typing import Dict, Any
import asyncio
import logging
from sqlalchemy import select, text, desc
from services.youtube_service import upload_to_youtube
from services.instagram_service import upload_to_instagram
from database import async_session, PostingOptimization
from ai_engine.learning_manager import LearningManager
import os
import tempfile
import requests

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()
learning_manager = LearningManager()


async def upload_scheduled_post(
    post_id: int, platform: str, title: str, description: str, tags: list = None
):
    """
    Upload a scheduled post to the specified platform.
    """
    async with async_session() as session:
        from database import Post, Analytics

        # Get post from database
        post = await session.get(Post, post_id)
        if not post:
            print(f"Post {post_id} not found")
            return

        try:
            if platform == "youtube":
                # Download video from S3
                response = requests.get(post.video_url)
                if response.status_code != 200:
                    raise Exception("Failed to download video")

                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=".mp4"
                ) as temp_file:
                    temp_file.write(response.content)
                    temp_path = temp_file.name

                try:
                    # Upload to YouTube
                    video_id = await upload_to_youtube(
                        video_path=temp_path,
                        title=title,
                        description=description,
                        tags=tags,
                    )

                    # Update post
                    post.status = "posted"
                    post.posted_at = datetime.utcnow()

                    # Create analytics
                    analytics = Analytics(
                        post_id=post.id,
                        platform="youtube",
                        views=0,
                        likes=0,
                        comments=0,
                    )
                    session.add(analytics)
                    await session.commit()

                    print(f"Successfully uploaded to YouTube: {video_id}")

                finally:
                    os.unlink(temp_path)

            elif platform == "instagram":
                # Upload to Instagram
                result = await upload_to_instagram(
                    video_path=post.video_url, caption=description
                )

                # Update post
                post.status = "posted"
                post.posted_at = datetime.utcnow()

                # Create analytics
                analytics = Analytics(
                    post_id=post.id, platform="instagram", views=0, likes=0, comments=0
                )
                session.add(analytics)
                await session.commit()

                print(f"Successfully uploaded to Instagram: {result.get('id')}")

        except Exception as e:
            print(f"Failed to upload post {post_id}: {str(e)}")
            post.status = "failed"
            await session.commit()


def schedule_upload(
    post_id: int,
    platform: str,
    scheduled_time: datetime,
    title: str,
    description: str,
    tags: list = None,
):
    """
    Schedule a post upload.
    """
    job_id = f"{platform}_{post_id}_{scheduled_time.timestamp()}"
    scheduler.add_job(
        upload_scheduled_post,
        trigger=DateTrigger(run_date=scheduled_time),
        args=[post_id, platform, title, description, tags],
        id=job_id,
        replace_existing=True,
    )
    return job_id


def get_scheduled_jobs():
    """
    Get list of scheduled jobs.
    """
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append(
            {
                "id": job.id,
                "next_run_time": (
                    job.next_run_time.isoformat() if job.next_run_time else None
                ),
                "args": job.args,
            }
        )
    return jobs


def cancel_job(job_id: str):
    """
    Cancel a scheduled job.
    """
    try:
        scheduler.remove_job(job_id)
        return True
    except Exception:
        return False


def start_scheduler():
    """
    Start the scheduler.
    """
    if not scheduler.running:
        scheduler.start()


def shutdown_scheduler():
    """
    Shutdown the scheduler.
    """
    if scheduler.running:
        scheduler.shutdown()


async def get_optimal_posting_time(platform: str, language: str = "ml") -> datetime:
    """
    Get optimal posting time based on learning data.
    """
    try:
        async with async_session() as session:
            # Get optimization data
            query = (
                select(PostingOptimization)
                .where(
                    PostingOptimization.platform == platform,
                    PostingOptimization.language == language,
                )
                .order_by(desc(PostingOptimization.engagement_score))
                .limit(1)
            )

            result = await session.execute(query)
            optimization = result.scalar_one_or_none()

            if optimization:
                # Calculate next optimal time
                now = datetime.utcnow()
                optimal_time = now.replace(
                    hour=optimization.optimal_hour, minute=0, second=0, microsecond=0
                )

                # If optimal time has passed today, schedule for tomorrow
                if optimal_time <= now:
                    optimal_time += timedelta(days=1)

                # Adjust day of week if specified
                if optimization.optimal_day != now.weekday():
                    days_ahead = (optimization.optimal_day - now.weekday()) % 7
                    if days_ahead == 0 and optimal_time <= now:
                        days_ahead = 7
                    optimal_time += timedelta(days=days_ahead)

                logger.info(f"Optimal posting time for {platform}: {optimal_time}")
                return optimal_time

            # Fallback to Malayalam-specific defaults
            return get_default_optimal_time(platform)

    except Exception as e:
        logger.error(f"Failed to get optimal posting time: {e}")
        return get_default_optimal_time(platform)


def get_default_optimal_time(platform: str) -> datetime:
    """
    Get default optimal posting times for Malayalam content.
    """
    now = datetime.utcnow()
    defaults = {
        "youtube": 19,  # 7 PM IST (Malayalam prime time)
        "instagram": 18,  # 6 PM IST
        "facebook": 20,  # 8 PM IST
    }

    hour = defaults.get(platform, 18)
    optimal_time = now.replace(hour=hour, minute=0, second=0, microsecond=0)

    # If time has passed, schedule for tomorrow
    if optimal_time <= now:
        optimal_time += timedelta(days=1)

    return optimal_time


async def optimize_scheduled_posts():
    """
    Review and optimize existing scheduled posts based on learning data.
    """
    try:
        logger.info("Starting scheduled posts optimization")

        # Get all scheduled jobs
        jobs = get_scheduled_jobs()

        for job in jobs:
            job_id = job["id"]
            args = job["args"]

            if len(args) >= 2:
                post_id = args[0]
                platform = args[1]

                # Get current optimal time
                optimal_time = await get_optimal_posting_time(platform)

                # Reschedule if significantly different
                current_time = datetime.fromisoformat(job["next_run_time"])
                time_diff = abs((optimal_time - current_time).total_seconds())

                # If difference is more than 2 hours, reschedule
                if time_diff > 7200:  # 2 hours in seconds
                    logger.info(
                        f"Rescheduling post {post_id} from {current_time} to {optimal_time}"
                    )

                    # Cancel old job
                    cancel_job(job_id)

                    # Schedule new job with same parameters
                    schedule_upload(*args)

        logger.info("Scheduled posts optimization completed")

    except Exception as e:
        logger.error(f"Scheduled posts optimization failed: {e}")


async def dynamic_scheduling_adjustment():
    """
    Dynamically adjust scheduling based on real-time performance.
    """
    try:
        # This would run periodically to adjust upcoming posts
        # based on current engagement patterns and trends

        logger.info("Running dynamic scheduling adjustment")

        # Get recent performance data
        recent_performance = await get_recent_performance_data()

        # Adjust future scheduling based on patterns
        await adjust_future_scheduling(recent_performance)

        logger.info("Dynamic scheduling adjustment completed")

    except Exception as e:
        logger.error(f"Dynamic scheduling adjustment failed: {e}")


async def get_recent_performance_data() -> Dict[str, Any]:
    """
    Get recent performance data for scheduling adjustments.
    """
    try:
        async with async_session() as session:
            # Get performance data from last 7 days
            seven_days_ago = datetime.utcnow() - timedelta(days=7)

            result = await session.execute(
                text(
                    """
                    SELECT platform, AVG(engagement_rate) as avg_engagement,
                           COUNT(*) as post_count,
                           EXTRACT(hour from posted_at) as hour
                    FROM analytics a
                    JOIN posts p ON a.post_id = p.id
                    WHERE p.posted_at >= :start_date
                    GROUP BY platform, EXTRACT(hour from posted_at)
                    ORDER BY avg_engagement DESC
                """
                ),
                {"start_date": seven_days_ago},
            )

            performance_data = result.fetchall()

            # Group by platform
            platform_performance = {}
            for row in performance_data:
                platform = row.platform
                if platform not in platform_performance:
                    platform_performance[platform] = []
                platform_performance[platform].append(
                    {
                        "hour": int(row.hour),
                        "avg_engagement": float(row.avg_engagement),
                        "post_count": row.post_count,
                    }
                )

            return platform_performance

    except Exception as e:
        logger.error(f"Failed to get recent performance data: {e}")
        return {}


async def adjust_future_scheduling(performance_data: Dict[str, Any]):
    """
    Adjust future post scheduling based on performance data.
    """
    try:
        # Update posting optimization table with new insights
        async with async_session() as session:
            for platform, data in performance_data.items():
                if data:
                    # Find best performing hour
                    best_hour = max(data, key=lambda x: x["avg_engagement"])["hour"]

                    # Update or create optimization record
                    query = select(PostingOptimization).where(
                        PostingOptimization.platform == platform,
                        PostingOptimization.language == "ml",
                    )
                    existing = await session.execute(query)
                    optimization = existing.scalar_one_or_none()
                    if not optimization:
                        optimization = PostingOptimization(
                            platform=platform,
                            language="ml",
                            optimal_hour=best_hour,
                            optimal_day=datetime.utcnow().weekday(),
                            engagement_score=max(d["avg_engagement"] for d in data),
                            confidence=0.8,  # Default confidence
                        )
                        session.add(optimization)
                    else:
                        optimization.optimal_hour = best_hour
                        optimization.engagement_score = max(
                            d["avg_engagement"] for d in data
                        )
                        optimization.last_updated = datetime.utcnow()

                    await session.commit()

        logger.info("Future scheduling adjusted based on performance data")

    except Exception as e:
        logger.error(f"Failed to adjust future scheduling: {e}")


def schedule_malayalam_specific_optimization():
    """
    Schedule Malayalam-specific optimization tasks.
    """
    # Schedule daily optimization review
    scheduler.add_job(
        optimize_scheduled_posts,
        trigger="cron",
        hour=6,  # 6 AM daily
        id="daily_optimization_review",
        replace_existing=True,
    )

    # Schedule hourly dynamic adjustments
    scheduler.add_job(
        dynamic_scheduling_adjustment,
        trigger="cron",
        minute=0,  # Every hour
        id="hourly_dynamic_adjustment",
        replace_existing=True,
    )

    logger.info("Malayalam-specific optimization tasks scheduled")
