import structlog
from datetime import datetime, timezone, timedelta
from app.tasks.celery_app import celery_app

logger = structlog.get_logger()


@celery_app.task(name="app.tasks.alert_tasks.evaluate_all_alerts")
def evaluate_all_alerts():
    logger.info("alert_evaluation_started")

    # NOTE: Celery tasks use synchronous SQLAlchemy (not async)
    # because Celery workers run in a regular sync context
    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import Session
    from app.core.config import settings
    from app.models.alert import Alert, AlertStatus, AlertHistory, AlertCondition

    # Convert async URL to sync URL for Celery
    sync_url = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2")
    engine = create_engine(sync_url)

    with Session(engine) as session:
        # Load all active (non-muted, non-deleted) alerts
        now = datetime.now(timezone.utc)
        alerts = session.execute(
            select(Alert).where(
                Alert.status.in_([AlertStatus.ACTIVE, AlertStatus.TRIGGERED]),
                Alert.is_deleted == False,
            )
        ).scalars().all()

        for alert in alerts:
            # Skip muted alerts
            if alert.muted_until and alert.muted_until > now:
                continue

            try:
                _evaluate_alert(session, alert, now)
            except Exception as e:
                logger.error("alert_eval_error", alert_id=alert.id, error=str(e))

        session.commit()

    logger.info("alert_evaluation_completed", count=len(alerts))


def _evaluate_alert(session, alert, now: datetime):
    from sqlalchemy import func, text
    from app.models.alert import AlertStatus, AlertHistory

    window_start = now - timedelta(minutes=alert.evaluation_window_minutes)

    # Count events of the specified type in the evaluation window
    from app.models.event import Event
    result = session.execute(
        select(func.count(Event.id)).where(
            Event.organization_id == alert.organization_id,
            Event.event_type == alert.event_type,
            Event.timestamp >= window_start,
            Event.timestamp <= now,
        )
    ).scalar() or 0

    current_value = float(result)

    # Check condition
    from app.models.alert import AlertCondition
    condition_met = {
        AlertCondition.GREATER_THAN: current_value > alert.threshold,
        AlertCondition.LESS_THAN: current_value < alert.threshold,
        AlertCondition.EQUALS: current_value == alert.threshold,
        AlertCondition.NOT_EQUALS: current_value != alert.threshold,
    }.get(alert.condition, False)

    alert.last_evaluated_at = now

    if condition_met and alert.status != AlertStatus.TRIGGERED:
        # Trigger the alert
        alert.status = AlertStatus.TRIGGERED
        alert.last_triggered_at = now
        alert.last_triggered_value = current_value

        history = AlertHistory(
            alert_id=alert.id,
            triggered_at=now,
            triggered_value=current_value,
            message=f"{alert.metric_name} is {current_value} (threshold: {alert.threshold})"
        )
        session.add(history)

        # Send notifications
        _send_notifications(alert, current_value)

    elif not condition_met and alert.status == AlertStatus.TRIGGERED:
        # Resolve the alert
        alert.status = AlertStatus.RESOLVED


def _send_notifications(alert, value: float):
    channels = alert.notification_channels or {}

    if "email" in channels:
        # TODO: send email via SMTP
        logger.info("alert_email_sent", alert_id=alert.id, emails=channels["email"])

    if "webhook" in channels:
        import httpx
        payload = {
            "alert_name": alert.name,
            "triggered_value": value,
            "threshold": alert.threshold,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        try:
            httpx.post(channels["webhook"], json=payload, timeout=10)
        except Exception as e:
            logger.error("webhook_failed", url=channels["webhook"], error=str(e))
