from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, text
from app.repositories.base import BaseRepository
from app.models.event import Event


class EventRepository(BaseRepository[Event]):
    def __init__(self, db: AsyncSession):
        super().__init__(Event, db)

    async def bulk_insert(self, events: list[Event]) -> int:
        """Insert multiple events efficiently."""
        for event in events:
            self.db.add(event)
        await self.db.flush()
        return len(events)

    async def get_by_org_and_timerange(
        self,
        org_id: int,
        start_time: datetime,
        end_time: datetime,
        event_type: str | None = None,
        limit: int = 1000,
    ) -> list[Event]:

        filters = [
            Event.organization_id == org_id,
            Event.timestamp >= start_time,
            Event.timestamp <= end_time,
        ]
        if event_type:
            filters.append(Event.event_type == event_type)

        result = await self.db.execute(
            select(Event)
            .where(and_(*filters))
            .order_by(Event.timestamp.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_type(
        self,
        org_id: int,
        start_time: datetime,
        end_time: datetime,
    ) -> list[dict]:

        result = await self.db.execute(
            select(Event.event_type, func.count(Event.id).label("count"))
            .where(
                Event.organization_id == org_id,
                Event.timestamp >= start_time,
                Event.timestamp <= end_time,
            )
            .group_by(Event.event_type)
            .order_by(func.count(Event.id).desc())
        )
        return [{"event_type": row.event_type, "count": row.count} for row in result.all()]

    async def time_series_count(
        self,
        org_id: int,
        event_type: str,
        start_time: datetime,
        end_time: datetime,
        interval: str = "1h",
    ) -> list[dict]:

        # Map our interval strings to PostgreSQL date_trunc values
        interval_map = {
            "1m": "minute", "5m": "minute", "15m": "minute",
            "1h": "hour", "6h": "hour",
            "1d": "day", "7d": "day",
        }
        trunc_unit = interval_map.get(interval, "hour")

        result = await self.db.execute(
            text("""
                SELECT
                    date_trunc(:trunc_unit, timestamp) AS bucket,
                    COUNT(*) AS count
                FROM events
                WHERE
                    organization_id = :org_id
                    AND event_type = :event_type
                    AND timestamp >= :start_time
                    AND timestamp <= :end_time
                GROUP BY bucket
                ORDER BY bucket ASC
            """),
            {
                "trunc_unit": trunc_unit,
                "org_id": org_id,
                "event_type": event_type,
                "start_time": start_time,
                "end_time": end_time,
            }
        )
        return [{"timestamp": row.bucket, "value": float(row.count)} for row in result.all()]

    async def get_latest_events(self, org_id: int, limit: int = 50) -> list[Event]:
        result = await self.db.execute(
            select(Event)
            .where(Event.organization_id == org_id)
            .order_by(Event.timestamp.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
