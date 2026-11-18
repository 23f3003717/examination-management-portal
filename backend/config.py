
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"
PROJECT_ROOT = BASE_DIR.parent


def resolve_database_path(raw_path):
    if not raw_path:
        return str(INSTANCE_DIR / "examination_portal.sqlite")

    candidate = Path(raw_path)

    if candidate.is_absolute():
        return str(candidate.resolve())

    raw_path = str(raw_path).replace("\\", "/")

    if raw_path.startswith("backend/"):
        return str((PROJECT_ROOT / candidate).resolve())

    if raw_path.startswith("instance/") or "/" not in raw_path:
        return str((BASE_DIR / candidate).resolve())

    return str((PROJECT_ROOT / candidate).resolve())


class Config:
    # Flask security
    SECRET_KEY = os.getenv(
        "FLASK_SECRET_KEY",
        "dev-only-change-this-secret"
    )

    # SQLite database
    DATABASE_PATH = resolve_database_path(
        os.getenv(
            "DATABASE_PATH",
            str(INSTANCE_DIR / "examination_portal.sqlite")
        )
    )

    # Redis
    REDIS_URL = os.getenv(
        "REDIS_URL",
        "redis://localhost:6379/0"
    )

    # Celery
    CELERY_BROKER_URL = os.getenv(
        "CELERY_BROKER_URL",
        REDIS_URL
    )

    CELERY_RESULT_BACKEND = os.getenv(
        "CELERY_RESULT_BACKEND",
        REDIS_URL
    )

    # Frontend
    FRONTEND_ORIGIN = os.getenv(
        "FRONTEND_ORIGIN",
        "http://localhost:8080"
    )

    # Default Admin
    ADMIN_NAME = os.getenv(
        "ADMIN_NAME",
        "Portal Administrator"
    )

    ADMIN_EMAIL = os.getenv(
        "ADMIN_EMAIL",
        "admin@example.com"
    )

    ADMIN_PASSWORD = os.getenv(
        "ADMIN_PASSWORD",
        "admin@1234"
    )

    # Email / SMTP
    SMTP_HOST = os.getenv("SMTP_HOST", "")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM = os.getenv("SMTP_FROM", "")

    # Timezone
    TIMEZONE = os.getenv(
        "TIMEZONE",
        "Asia/Kolkata"
    )

    # Export files
    EXPORT_DIR = os.getenv(
        "EXPORT_DIR",
        str(INSTANCE_DIR / "exports")
    )

    # Cache
    CACHE_TTL = int(
        os.getenv("CACHE_TTL", "120")
    )

    # Celery Beat schedules
    DAILY_REMINDER_HOUR = int(os.getenv("DAILY_REMINDER_HOUR", "8"))
    DAILY_REMINDER_MINUTE = int(os.getenv("DAILY_REMINDER_MINUTE", "0"))
    MONTHLY_REPORT_HOUR = int(os.getenv("MONTHLY_REPORT_HOUR", "8"))
    MONTHLY_REPORT_MINUTE = int(os.getenv("MONTHLY_REPORT_MINUTE", "0"))
