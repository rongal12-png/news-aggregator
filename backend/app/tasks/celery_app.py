from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "news_aggregator",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.fetch_task",
        "app.tasks.cluster_task",
        "app.tasks.summarize_task",
        "app.tasks.enhancement_task",
    ],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutes max per task
    task_soft_time_limit=540,  # Soft limit at 9 minutes
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

# Beat schedule for periodic tasks (every hour)
celery_app.conf.beat_schedule = {
    "fetch-feeds-every-hour": {
        "task": "app.tasks.fetch_task.fetch_feeds",
        "schedule": crontab(minute=0),  # Every hour at :00
    },
    "cluster-stories-every-hour": {
        "task": "app.tasks.cluster_task.cluster_stories",
        "schedule": crontab(minute=5),  # Every hour at :05
    },
    "warm-summaries-every-hour": {
        "task": "app.tasks.summarize_task.warm_top_summaries",
        "schedule": crontab(minute=10),  # Every hour at :10
    },
    "enhance-stories-every-hour": {
        "task": "app.tasks.enhancement_task.enhance_top_stories",
        "schedule": crontab(minute=15),  # Every hour at :15
        "kwargs": {"language": "en"},
    },
    "enhance-stories-hebrew-every-hour": {
        "task": "app.tasks.enhancement_task.enhance_top_stories",
        "schedule": crontab(minute=20),  # Every hour at :20
        "kwargs": {"language": "he"},
    },
}
