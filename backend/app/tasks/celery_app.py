from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "datapulse",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.event_tasks",
        "app.tasks.alert_tasks",
    ],
)

celery_app.conf.update(
    # Serialize tasks as JSON (not Python pickle — safer)
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,

    # Retry failed tasks up to 3 times with exponential backoff
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # Celery Beat schedule for periodic tasks
    beat_schedule={
        # Evaluate all alert rules every minute
        "evaluate-alerts-every-minute": {
            "task": "app.tasks.alert_tasks.evaluate_all_alerts",
            "schedule": crontab(minute="*"),  # every minute
        },
        # Clean up old events older than 90 days (daily at 2am UTC)
        "cleanup-old-events": {
            "task": "app.tasks.event_tasks.cleanup_old_events",
            "schedule": crontab(hour=2, minute=0),
        },
    },
)
