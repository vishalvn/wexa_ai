from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, ConfigDict
from typing import Optional
import secrets

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models.user import User
from app.models.dashboard import Dashboard, Widget, WidgetType

router = APIRouter(prefix="/dashboards", tags=["Dashboards"])


# ─── Schemas (inline for conciseness) ────────────────────────────────────────

class DashboardCreate(BaseModel):
    name: str
    description: Optional[str] = None
    refresh_interval: int = 0


class DashboardUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None
    refresh_interval: Optional[int] = None
    layout: Optional[dict] = None


class WidgetCreate(BaseModel):
    title: str
    widget_type: WidgetType
    query_config: dict = {}
    display_config: dict = {}
    position_x: int = 0
    position_y: int = 0
    width: int = 6
    height: int = 4


class DashboardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: Optional[str]
    is_public: bool
    public_token: Optional[str]
    refresh_interval: int
    layout: dict
    widgets: list


# ─── Routes ──────────────────────────────────────────────────────────────────

@router.get("/", response_model=list[DashboardResponse])
async def list_dashboards(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Dashboard)
        .where(
            Dashboard.organization_id == current_user.organization_id,
            Dashboard.is_deleted == False,
        )
        .options(selectinload(Dashboard.widgets))
        .order_by(Dashboard.created_at.desc())
    )
    return result.scalars().all()


@router.post("/", response_model=DashboardResponse, status_code=status.HTTP_201_CREATED)
async def create_dashboard(
    data: DashboardCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    dashboard = Dashboard(
        organization_id=current_user.organization_id,
        created_by_id=current_user.id,
        name=data.name,
        description=data.description,
        refresh_interval=data.refresh_interval,
    )
    db.add(dashboard)
    await db.flush()
    await db.refresh(dashboard)
    return dashboard


@router.get("/{dashboard_id}", response_model=DashboardResponse)
async def get_dashboard(
    dashboard_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Dashboard)
        .where(
            Dashboard.id == dashboard_id,
            Dashboard.organization_id == current_user.organization_id,
            Dashboard.is_deleted == False,
        )
        .options(selectinload(Dashboard.widgets))
    )
    dashboard = result.scalar_one_or_none()
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return dashboard


@router.patch("/{dashboard_id}", response_model=DashboardResponse)
async def update_dashboard(
    dashboard_id: int,
    data: DashboardUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Dashboard)
        .where(
            Dashboard.id == dashboard_id,
            Dashboard.organization_id == current_user.organization_id,
        )
        .options(selectinload(Dashboard.widgets))
    )
    dashboard = result.scalar_one_or_none()
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(dashboard, field, value)

    await db.flush()
    await db.refresh(dashboard)
    return dashboard


@router.delete("/{dashboard_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dashboard(
    dashboard_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Dashboard).where(
            Dashboard.id == dashboard_id,
            Dashboard.organization_id == current_user.organization_id,
        )
    )
    dashboard = result.scalar_one_or_none()
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    dashboard.is_deleted = True


@router.post("/{dashboard_id}/share")
async def toggle_public_share(
    dashboard_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Dashboard).where(
            Dashboard.id == dashboard_id,
            Dashboard.organization_id == current_user.organization_id,
        )
    )
    dashboard = result.scalar_one_or_none()
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    if dashboard.is_public:
        dashboard.is_public = False
        dashboard.public_token = None
    else:
        dashboard.is_public = True
        dashboard.public_token = secrets.token_urlsafe(16)

    await db.flush()
    return {
        "is_public": dashboard.is_public,
        "public_token": dashboard.public_token,
        "public_url": f"/shared/{dashboard.public_token}" if dashboard.public_token else None,
    }


# ─── Widget routes ────────────────────────────────────────────────────────────

@router.post("/{dashboard_id}/widgets", status_code=status.HTTP_201_CREATED)
async def add_widget(
    dashboard_id: int,
    data: WidgetCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify dashboard belongs to this org
    result = await db.execute(
        select(Dashboard).where(
            Dashboard.id == dashboard_id,
            Dashboard.organization_id == current_user.organization_id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Dashboard not found")

    widget = Widget(
        dashboard_id=dashboard_id,
        **data.model_dump()
    )
    db.add(widget)
    await db.flush()
    await db.refresh(widget)
    return widget


@router.delete("/{dashboard_id}/widgets/{widget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_widget(
    dashboard_id: int,
    widget_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Widget)
        .join(Dashboard)
        .where(
            Widget.id == widget_id,
            Widget.dashboard_id == dashboard_id,
            Dashboard.organization_id == current_user.organization_id,
        )
    )
    widget = result.scalar_one_or_none()
    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found")
    await db.delete(widget)
