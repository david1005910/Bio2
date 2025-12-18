from celery import Celery
from celery.schedules import crontab

from app.core.config import settings


celery_app = Celery(
    "bio_rag",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.tasks"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    worker_prefetch_multiplier=1,
    worker_concurrency=4,
)

# Scheduled tasks
celery_app.conf.beat_schedule = {
    "daily-paper-crawl": {
        "task": "app.workers.tasks.daily_paper_crawl",
        "schedule": crontab(hour=2, minute=0),  # Run at 2:00 AM UTC
        "options": {"queue": "crawl"}
    },
    "weekly-embedding-refresh": {
        "task": "app.workers.tasks.refresh_embeddings",
        "schedule": crontab(day_of_week=0, hour=3, minute=0),  # Sunday 3:00 AM UTC
        "options": {"queue": "embedding"}
    },
}

# Queue routing
celery_app.conf.task_routes = {
    "app.workers.tasks.daily_paper_crawl": {"queue": "crawl"},
    "app.workers.tasks.process_paper": {"queue": "process"},
    "app.workers.tasks.generate_embeddings": {"queue": "embedding"},
}
