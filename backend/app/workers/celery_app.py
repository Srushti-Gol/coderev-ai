from celery import Celery
from celery.schedules import crontab
from app.config import settings

celery_app = Celery(
    "coderev-ai",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.workers.tasks"],
)

# Configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_soft_time_limit=300,  # 5 minutes soft limit
    task_time_limit=600,       # 10 minutes hard limit
    result_expires=3600,       # Results expire after 1 hour
    worker_max_tasks_per_child=100,  # Restart worker after 100 tasks
)

# Scheduled tasks (Celery Beat)
celery_app.conf.beat_schedule = {
    "sync-open-prs-hourly": {
        "task": "app.workers.tasks.sync_open_prs",
        "schedule": crontab(minute=0),  # Every hour
    },
    "cleanup-old-results-daily": {
        "task": "app.workers.tasks.cleanup_old_results",
        "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    "recalculate-debt-scores-daily": {
        "task": "app.workers.tasks.recalculate_debt_scores",
        "schedule": crontab(hour=3, minute=0),  # Daily at 3 AM
    },
}
