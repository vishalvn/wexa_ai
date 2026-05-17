import structlog
from app.tasks.celery_app import celery_app

logger = structlog.get_logger()


@celery_app.task(
    name="app.tasks.event_tasks.process_events_task",
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # seconds
)
def process_events_task(self, org_id: int, event_ids: list[int]):
    try:
        logger.info("processing_events", org_id=org_id, count=len(event_ids))
        # TODO: invalidate Redis cache keys for this org's dashboards
        # TODO: publish to WebSocket channel
        logger.info("events_processed", org_id=org_id, count=len(event_ids))
    except Exception as exc:
        logger.error("event_processing_failed", error=str(exc))
        # Exponential backoff retry: 60s, 120s, 240s
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@celery_app.task(name="app.tasks.event_tasks.cleanup_old_events")
def cleanup_old_events():
    from datetime import datetime, timedelta, timezone
    cutoff = datetime.now(timezone.utc) - timedelta(days=90)
    logger.info("cleanup_started", cutoff=cutoff.isoformat())
    # TODO: DB delete via sync SQLAlchemy session
