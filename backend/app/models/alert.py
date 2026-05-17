import enum
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, Integer, Float, JSON, Enum as SAEnum, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class AlertStatus(str, enum.Enum):
    ACTIVE = "active"
    TRIGGERED = "triggered"
    RESOLVED = "resolved"
    MUTED = "muted"


class AlertCondition(str, enum.Enum):
    GREATER_THAN = "gt"
    LESS_THAN = "lt"
    EQUALS = "eq"
    NOT_EQUALS = "neq"


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False, index=True
    )
    created_by_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # What to measure
    metric_name: Mapped[str] = mapped_column(String(255), nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)

    # Threshold rule
    condition: Mapped[AlertCondition] = mapped_column(
        SAEnum(AlertCondition, name="alertcondition"), nullable=False
    )
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    evaluation_window_minutes: Mapped[int] = mapped_column(Integer, default=5)

    # Current status
    status: Mapped[AlertStatus] = mapped_column(
        SAEnum(AlertStatus, name="alertstatus"), default=AlertStatus.ACTIVE
    )

    # Notification channels config
    # e.g. {"email": ["user@co.com"], "webhook": "https://hooks.slack.com/..."}
    notification_channels: Mapped[dict] = mapped_column(JSON, default=dict)

    # Mute until (for snooze feature)
    muted_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    last_evaluated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_triggered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_triggered_value: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    organization: Mapped["Organization"] = relationship("Organization", back_populates="alerts")
    created_by: Mapped["User"] = relationship("User")
    history: Mapped[list["AlertHistory"]] = relationship("AlertHistory", back_populates="alert", cascade="all, delete-orphan")


class AlertHistory(Base):
    __tablename__ = "alert_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    alert_id: Mapped[int] = mapped_column(Integer, ForeignKey("alerts.id"), nullable=False, index=True)
    triggered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    triggered_value: Mapped[float] = mapped_column(Float, nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    alert: Mapped["Alert"] = relationship("Alert", back_populates="history")
