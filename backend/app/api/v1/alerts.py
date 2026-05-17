from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, ConfigDict

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models.user import User
from app.models.alert import Alert, AlertStatus, AlertCondition, AlertHistory

router = APIRouter(prefix="/alerts", tags=["Alerts"])


# ─── Schemas ──────────────────────────────────────────────────────────────────

class AlertCreate(BaseModel):
    name: str
    description: Optional[str] = None
    event_type: str
    metric_name: str
    condition: AlertCondition
    threshold: float
    evaluation_window_minutes: int = 5
    notification_channels: dict = {}


class AlertUpdate(BaseModel):
    name: Optional[str] = None
    threshold: Optional[float] = None
    evaluation_window_minutes: Optional[int] = None
    notification_channels: Optional[dict] = None


class SnoozeRequest(BaseModel):
    minutes: int  # snooze for this many minutes


# ─── Routes ──────────────────────────────────────────────────────────────────

@router.get("/")
async def list_alerts(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List all alert rules for the organization."""
    result = await db.execute(
        select(Alert)
        .where(
            Alert.organization_id == current_user.organization_id,
            Alert.is_deleted == False,
        )
        .order_by(Alert.created_at.desc())
    )
    return result.scalars().all()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_alert(
    data: AlertCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new alert rule."""
    alert = Alert(
        organization_id=current_user.organization_id,
        created_by_id=current_user.id,
        **data.model_dump()
    )
    db.add(alert)
    await db.flush()
    await db.refresh(alert)
    return alert


@router.patch("/{alert_id}")
async def update_alert(
    alert_id: int,
    data: AlertUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Alert).where(
            Alert.id == alert_id,
            Alert.organization_id == current_user.organization_id,
        )
    )
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(alert, field, value)

    await db.flush()
    return alert


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(
    alert_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Alert).where(
            Alert.id == alert_id,
            Alert.organization_id == current_user.organization_id,
        )
    )
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.is_deleted = True


@router.post("/{alert_id}/snooze")
async def snooze_alert(
    alert_id: int,
    data: SnoozeRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Alert).where(
            Alert.id == alert_id,
            Alert.organization_id == current_user.organization_id,
        )
    )
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.muted_until = datetime.now(timezone.utc) + timedelta(minutes=data.minutes)
    alert.status = AlertStatus.MUTED
    await db.flush()
    return {"muted_until": alert.muted_until}


@router.post("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Alert).where(
            Alert.id == alert_id,
            Alert.organization_id == current_user.organization_id,
        )
    )
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = AlertStatus.RESOLVED
    await db.flush()
    return {"status": alert.status}


@router.get("/{alert_id}/history")
async def get_alert_history(
    alert_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AlertHistory)
        .join(Alert)
        .where(
            AlertHistory.alert_id == alert_id,
            Alert.organization_id == current_user.organization_id,
        )
        .order_by(AlertHistory.triggered_at.desc())
        .limit(100)
    )
    return result.scalars().all()
