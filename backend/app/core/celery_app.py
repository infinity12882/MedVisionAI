"""
Celery app instance, used for long-running background work: vision model
retraining and (optionally) bulk knowledge-base reindexing. Configured
against Redis as both broker and result backend per the tech spec.

Run a worker with:
    celery -A app.core.celery_app worker --loglevel=info
"""
from __future__ import annotations

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "medvision_ai",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.training_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)
