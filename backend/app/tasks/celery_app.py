"""Celery application — broker is Redis, result backend is also Redis (DB 1)."""

from celery import Celery

from app.core.config import settings


celery_app = Celery(
    "legalease",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=10 * 60,    # hard kill at 10 minutes
    task_soft_time_limit=8 * 60,
)

# Auto-discover tasks in registered modules
celery_app.autodiscover_tasks(["app.tasks"])
