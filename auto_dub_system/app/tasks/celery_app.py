"""
Celery config.
"""

from celery import Celery
from app.config import settings

broker_url = settings.CELERY_BROKER_URL or settings.REDIS_URL
backend_url = settings.CELERY_RESULT_BACKEND or settings.REDIS_URL

celery_app = Celery(
    "auto_dub_system",
    broker=broker_url,
    backend=backend_url,
    include=[
        "app.tasks.stage1_tasks",
        "app.tasks.stage2_tasks",
        "app.tasks.stage3_tasks",
        "app.tasks.stage4_tasks",
    ]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Optional but recommended
    task_track_started=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)
