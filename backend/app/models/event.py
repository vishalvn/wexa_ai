from datetime import datetime, timezone
from sqlalchemy import (
    String, DateTime, ForeignKey, Integer, JSON, Index, BigInteger
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    source: Mapped[str] = mapped_column(String(50), default="api")  # api, csv, webhook
    user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)   # client user identifier
    session_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    properties: Mapped[dict] = mapped_column(JSON, default=dict)   # flexible event data
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationship
    organization: Mapped["Organization"] = relationship("Organization", back_populates="events")

    # Composite indexes for time-series query performance
    __table_args__ = (
        Index("ix_events_org_timestamp", "organization_id", "timestamp"),
        Index("ix_events_org_type", "organization_id", "event_type"),
    )
