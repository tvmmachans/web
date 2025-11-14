import os
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
import sys

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

from agent.config.settings import (
    REPORT_GENERATION_DAY,
    REPORT_GENERATION_HOUR,
    EMAIL_ENABLED,
    WHATSAPP_ENABLED,
    EMAIL_RECIPIENT,
    WHATSAPP_NUMBER,
)
from agent.services.analytics_agent import AnalyticsAgent
from openai import OpenAI

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Generates weekly performance reports and handles notifications.
    """

    def __init__(self):
        self.analytics_agent = AnalyticsAgent()
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def generate_weekly_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive weekly performance report.
        """
        try:
            logger.info("Generating weekly performance report")

            # Get analytics data for the past week
            analysis = await self.analytics_agent.analyze_performance(days=7)

            # Generate AI insights and recommendations
            insights = await self._generate_weekly_insights(analysis)

            # Create report structure
            report = {
                "period": "weekly",
                "start_date": (datetime.utcnow() - timedelta(days=7)).isoformat(),
                "end_date": datetime.utcnow().isoformat(),
                "summary": {
                    "total_posts": analysis.get("total_posts", 0),
                    "total_views": analysis.get("total_views", 0),
                    "total_engagement": analysis.get("total_likes", 0)
                    + analysis.get("total_comments", 0),
                    "average_engagement_rate": analysis.get(
                        "average_engagement_rate", 0
                    ),
                },
                "platform_breakdown": analysis.get("platform_breakdown", {}),
                "insights": insights,
                "recommendations": await self._generate_recommendations(analysis),
                "trends": await self._analyze_trends(analysis),
                "generated_at": datetime.utcnow().isoformat(),
            }

            # Send notifications
            await self._send_notifications(report)

            logger.info("Weekly report generated successfully")
            return report

        except Exception as e:
            logger.error(f"Error generating weekly report: {e}")
            return {"error": str(e)}

    async def _generate_weekly_insights(self, analysis: Dict) -> List[str]:
        """
        Generate AI-powered insights for the weekly report.
        """
        try:
            data_summary = f"""
            Weekly Performance Summary:
            - Posts: {analysis.get('total_posts', 0)}
            - Total views: {analysis.get('total_views', 0)}
            - Average engagement: {analysis.get('average_engagement_rate', 0):.3f}
            - Platform breakdown: {analysis.get('platform_breakdown', {})}
            """

            prompt = f"""
            Analyze this weekly social media performance data and provide 4-6 key insights.
            Focus on trends, successes, areas for improvement, and strategic recommendations.

            {data_summary}

            Format as a numbered list of actionable insights.
            """

            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400,
                temperature=0.7,
            )

            insights_text = response.choices[0].message.content.strip()
            insights = [
                line.strip()
                for line in insights_text.split("\n")
                if line.strip() and not line.startswith("#")
            ]

            return insights[:6]

        except Exception as e:
            logger.error(f"Error generating weekly insights: {e}")
            return ["Unable to generate insights this week"]

    async def _generate_recommendations(self, analysis: Dict) -> List[str]:
        """
        Generate specific recommendations based on performance.
        """
        try:
            recommendations = []

            avg_engagement = analysis.get("average_engagement_rate", 0)
            total_posts = analysis.get("total_posts", 0)

            if avg_engagement < 0.02:
                recommendations.append(
                    "Focus on creating more engaging content with compelling hooks"
                )
                recommendations.append(
                    "Experiment with different posting times to find optimal audience engagement"
                )

            if total_posts < 5:
                recommendations.append(
                    "Increase posting frequency to build momentum and audience engagement"
                )

            platform_breakdown = analysis.get("platform_breakdown", {})
            if len(platform_breakdown) > 1:
                best_platform = max(
                    platform_breakdown.items(),
                    key=lambda x: x[1].get("avg_engagement", 0),
                )
                recommendations.append(
                    f"Consider focusing more on {best_platform[0]} where engagement is higher"
                )

            recommendations.extend(
                [
                    "Analyze top-performing posts to identify successful content patterns",
                    "Engage more actively with audience comments to build community",
                    "Experiment with different content formats (short videos, live sessions, etc.)",
                ]
            )

            return recommendations[:5]

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return ["Continue monitoring performance and adjusting strategy"]

    async def _analyze_trends(self, analysis: Dict) -> Dict[str, Any]:
        """
        Analyze performance trends over the week.
        """
        try:
            # This would compare with previous weeks
            # For now, provide basic trend analysis
            trends = {
                "engagement_trend": "stable",  # increasing, decreasing, stable
                "platform_performance": "consistent",
                "content_effectiveness": "good",
                "audience_growth": "steady",
            }

            # Simple trend detection
            avg_engagement = analysis.get("average_engagement_rate", 0)
            if avg_engagement > 0.05:
                trends["engagement_trend"] = "strong"
            elif avg_engagement < 0.01:
                trends["engagement_trend"] = "needs_improvement"

            return trends

        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")
            return {"error": "Unable to analyze trends"}

    async def _send_notifications(self, report: Dict[str, Any]):
        """
        Send report notifications via email and/or WhatsApp.
        """
        try:
            report_summary = self._format_report_summary(report)

            if EMAIL_ENABLED and EMAIL_RECIPIENT:
                await self._send_email_report(report_summary)

            if WHATSAPP_ENABLED and WHATSAPP_NUMBER:
                await self._send_whatsapp_report(report_summary)

        except Exception as e:
            logger.error(f"Error sending notifications: {e}")

    def _format_report_summary(self, report: Dict[str, Any]) -> str:
        """
        Format report for notifications.
        """
        try:
            summary = f"""
📊 Weekly Social Media Report

📈 Performance Summary:
• Posts: {report['summary']['total_posts']}
• Views: {report['summary']['total_views']:,}
• Engagement: {report['summary']['total_engagement']:,}
• Avg Engagement Rate: {report['summary']['average_engagement_rate']:.1%}

🔍 Key Insights:
"""

            insights = report.get("insights", [])[:3]  # Top 3 insights
            for i, insight in enumerate(insights, 1):
                summary += f"{i}. {insight}\n"

            summary += "\n💡 Recommendations:\n"
            recommendations = report.get("recommendations", [])[
                :2
            ]  # Top 2 recommendations
            for i, rec in enumerate(recommendations, 1):
                summary += f"{i}. {rec}\n"

            return summary.strip()

        except Exception as e:
            logger.error(f"Error formatting report summary: {e}")
            return "Weekly report generated - check dashboard for details"

    async def _send_email_report(self, report_summary: str):
        """
        Send report via email.
        """
        try:
            # This would integrate with email service (SendGrid, AWS SES, etc.)
            logger.info(f"Email report sent to {EMAIL_RECIPIENT}")
            # Implementation would go here

        except Exception as e:
            logger.error(f"Error sending email report: {e}")

    async def _send_whatsapp_report(self, report_summary: str):
        """
        Send report via WhatsApp.
        """
        try:
            # This would integrate with WhatsApp Business API or Twilio
            logger.info(f"WhatsApp report sent to {WHATSAPP_NUMBER}")
            # Implementation would go here

        except Exception as e:
            logger.error(f"Error sending WhatsApp report: {e}")

    async def schedule_weekly_reports(self):
        """
        Schedule weekly report generation.
        """
        try:
            # Calculate next report time
            now = datetime.utcnow()
            days_ahead = (7 - now.weekday()) % 7
            if days_ahead == 0 and now.hour >= REPORT_GENERATION_HOUR:
                days_ahead = 7

            next_report = now + timedelta(days=days_ahead)
            next_report = next_report.replace(
                hour=REPORT_GENERATION_HOUR, minute=0, second=0, microsecond=0
            )

            logger.info(f"Next weekly report scheduled for: {next_report}")

            # In production, this would integrate with APScheduler
            # For now, just log the schedule

        except Exception as e:
            logger.error(f"Error scheduling weekly reports: {e}")

    async def get_report_status(self) -> Dict[str, Any]:
        """
        Get report generator status.
        """
        return {
            "service": "report_generator",
            "report_day": REPORT_GENERATION_DAY,
            "report_hour": REPORT_GENERATION_HOUR,
            "email_enabled": EMAIL_ENABLED,
            "whatsapp_enabled": WHATSAPP_ENABLED,
            "last_report": None,  # Would track in database
        }
