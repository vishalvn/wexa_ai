import enum
from datetime import datetime, timezone
from sqlalchemy import (
    String, Boolean, DateTime, ForeignKey, Integer, JSON, Enum as SAEnum, Text
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class WidgetType(str, enum.Enum):
    LINE_CHART = "line_chart"
    BAR_CHART = "bar_chart"
    PIE_CHART = "pie_chart"
    KPI_CARD = "kpi_card"
    TABLE = "table"


class Dashboard(Base):
    __tablename__ = "dashboards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False, index=True
    )
    created_by_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    public_token: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    refresh_interval: Mapped[int] = mapped_column(Integer, default=0)  # seconds; 0 = no auto-refresh
    layout: Mapped[dict] = mapped_column(JSON, default=dict)  # widget positions for drag-and-drop
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)  # soft delete
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="dashboards")
    widgets: Mapped[list["Widget"]] = relationship("Widget", back_populates="dashboard", cascade="all, delete-orphan")
    created_by: Mapped["User"] = relationship("User")


class Widget(Base):
    __tablename__ = "widgets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    dashboard_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dashboards.id"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    widget_type: Mapped[WidgetType] = mapped_column(
        SAEnum(WidgetType, name="widgettype"), nullable=False
    )
    # Query configuration: event_type, aggregation (count/sum/avg), group_by, time_range
    query_config: Mapped[dict] = mapped_column(JSON, default=dict)
    # Visual configuration: colors, labels, axes
    display_config: Mapped[dict] = mapped_column(JSON, default=dict)
    position_x: Mapped[int] = mapped_column(Integer, default=0)
    position_y: Mapped[int] = mapped_column(Integer, default=0)
    width: Mapped[int] = mapped_column(Integer, default=6)   # grid columns (out of 12)
    height: Mapped[int] = mapped_column(Integer, default=4)  # grid rows
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    dashboard: Mapped["Dashboard"] = relationship("Dashboard", back_populates="widgets")
