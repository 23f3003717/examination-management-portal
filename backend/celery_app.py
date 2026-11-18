import os

from celery import Celery
from celery.schedules import crontab
from config import Config


def make_celery():
    broker_url = os.getenv("CELERY_BROKER_URL", Config.CELERY_BROKER_URL)
    result_backend = os.getenv("CELERY_RESULT_BACKEND", Config.CELERY_RESULT_BACKEND)
    timezone = os.getenv("TIMEZONE", Config.TIMEZONE)

    daily_reminder_hour = int(os.getenv("DAILY_REMINDER_HOUR", str(Config.DAILY_REMINDER_HOUR)))
    daily_reminder_minute = int(os.getenv("DAILY_REMINDER_MINUTE", str(Config.DAILY_REMINDER_MINUTE)))
    monthly_report_hour = int(os.getenv("MONTHLY_REPORT_HOUR", str(Config.MONTHLY_REPORT_HOUR)))
    monthly_report_minute = int(os.getenv("MONTHLY_REPORT_MINUTE", str(Config.MONTHLY_REPORT_MINUTE)))

    app = Celery("examination_portal", broker=broker_url, backend=result_backend)
    app.conf.update(
        task_serializer="json", result_serializer="json", accept_content=["json"],
        timezone=timezone, enable_utc=True,
        beat_schedule={
            "daily-exam-reminders": {
                "task": "tasks.daily_exam_reminders",
                "schedule": crontab(hour=daily_reminder_hour, minute=daily_reminder_minute),
            },
            "monthly-exam-report": {
                "task": "tasks.monthly_exam_report",
                "schedule": crontab(day_of_month=1, hour=monthly_report_hour, minute=monthly_report_minute),
            },
        }
    )
    return app


celery = make_celery()
import tasks