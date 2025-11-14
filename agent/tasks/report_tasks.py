"""
Celery tasks for report generation.
"""

import logging

from agent.celery_app import celery_app
from agent.services.report_generator import ReportGenerator

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="agent.tasks.report_tasks.generate_weekly_report")
def generate_weekly_report(self):
    """
    Generate weekly performance report.
    """
    try:
        logger.info("Starting scheduled weekly report generation")

        report_generator = ReportGenerator()

        import asyncio

        report = asyncio.run(report_generator.generate_weekly_report())

        logger.info("Completed scheduled weekly report generation")
        return {"status": "success", "report": report}

    except Exception as e:
        logger.error(f"Error in scheduled weekly report generation: {e}")
        self.retry(countdown=3600, max_retries=3)  # Retry after 1 hour
        return {"status": "error", "message": str(e)}


@celery_app.task(bind=True, name="agent.tasks.report_tasks.generate_custom_report")
def generate_custom_report(self, report_type: str, days: int = 7):
    """
    Generate custom report for specified period.
    """
    try:
        logger.info(f"Generating {report_type} report for {days} days")

        report_generator = ReportGenerator()

        import asyncio

        if report_type == "weekly":
            report = asyncio.run(report_generator.generate_weekly_report())
        else:
            # For other report types, could implement additional methods
            report = {"error": f"Report type {report_type} not implemented"}

        return {"status": "success", "report": report}

    except Exception as e:
        logger.error(f"Error generating {report_type} report: {e}")
        return {"status": "error", "message": str(e)}


@celery_app.task(bind=True, name="agent.tasks.report_tasks.send_notification")
def send_notification(self, report_data: dict, notification_type: str):
    """
    Send report notification via email/WhatsApp.
    """
    try:
        logger.info(f"Sending {notification_type} notification")

        report_generator = ReportGenerator()

        # Format report summary
        summary = report_generator._format_report_summary(report_data)

        import asyncio

        if notification_type == "email":
            asyncio.run(report_generator._send_email_report(summary))
        elif notification_type == "whatsapp":
            asyncio.run(report_generator._send_whatsapp_report(summary))
        else:
            return {
                "status": "error",
                "message": f"Unknown notification type: {notification_type}",
            }

        return {"status": "success", "type": notification_type}

    except Exception as e:
        logger.error(f"Error sending {notification_type} notification: {e}")
        return {"status": "error", "message": str(e)}
