import csv
import io
from datetime import datetime, timezone
from fastapi import HTTPException, status, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event
from app.repositories.event_repo import EventRepository
from app.schemas.event import EventIngestionRequest, BatchEventRequest, EventQueryRequest
from app.tasks.event_tasks import process_events_task


class EventService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = EventRepository(db)

    async def ingest_single(
        self, data: EventIngestionRequest, org_id: int
    ) -> Event:
        event = Event(
            organization_id=org_id,
            event_type=data.event_type,
            user_id=data.user_id,
            session_id=data.session_id,
            properties=data.properties,
            timestamp=data.timestamp or datetime.now(timezone.utc),
            source="api",
        )
        created = await self.repo.create(event)

        # Fire-and-forget background task (e.g., update aggregation cache)
        process_events_task.delay(org_id, [created.id])

        return created

    async def ingest_batch(
        self, data: BatchEventRequest, org_id: int
    ) -> dict:
        events = [
            Event(
                organization_id=org_id,
                event_type=e.event_type,
                user_id=e.user_id,
                session_id=e.session_id,
                properties=e.properties,
                timestamp=e.timestamp or datetime.now(timezone.utc),
                source="api",
            )
            for e in data.events
        ]

        count = await self.repo.bulk_insert(events)

        # Offload post-processing to Celery
        event_ids = [e.id for e in events if e.id]
        if event_ids:
            process_events_task.delay(org_id, event_ids)

        return {"accepted": count, "rejected": 0}

    async def ingest_csv(self, file: UploadFile, org_id: int) -> dict:
        content = await file.read()

        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CSV file must be UTF-8 encoded"
            )

        reader = csv.DictReader(io.StringIO(text))

        if "event_type" not in (reader.fieldnames or []):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CSV must have an 'event_type' column"
            )

        events = []
        errors = []

        for i, row in enumerate(reader):
            try:
                # Known columns are extracted; everything else becomes properties
                event_type = row.pop("event_type").strip().lower()
                user_id = row.pop("user_id", None)
                ts_str = row.pop("timestamp", None)
                timestamp = datetime.fromisoformat(ts_str) if ts_str else datetime.now(timezone.utc)

                events.append(Event(
                    organization_id=org_id,
                    event_type=event_type,
                    user_id=user_id,
                    properties=dict(row),  # remaining columns as properties
                    timestamp=timestamp,
                    source="csv",
                ))
            except Exception as e:
                errors.append({"row": i + 2, "error": str(e)})

        if events:
            await self.repo.bulk_insert(events)

        return {
            "accepted": len(events),
            "rejected": len(errors),
            "errors": errors[:10],  # return first 10 errors only
        }

    async def query_time_series(
        self, query: EventQueryRequest, org_id: int
    ) -> list[dict]:
        return await self.repo.time_series_count(
            org_id=org_id,
            event_type=query.event_type,
            start_time=query.start_time,
            end_time=query.end_time,
            interval=query.interval,
        )

    async def get_event_summary(
        self, org_id: int, start_time: datetime, end_time: datetime
    ) -> list[dict]:
        return await self.repo.count_by_type(org_id, start_time, end_time)

    async def get_live_stream(self, org_id: int, limit: int = 50) -> list[Event]:
        return await self.repo.get_latest_events(org_id, limit)
