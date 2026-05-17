from fastapi import APIRouter, Depends, UploadFile, File, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone, timedelta

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models.user import User
from app.schemas.event import (
    EventIngestionRequest, BatchEventRequest,
    EventResponse, EventQueryRequest, AggregatedDataPoint
)
from app.services.event_service import EventService

router = APIRouter(prefix="/events", tags=["Events & Ingestion"])


@router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def ingest_event(
    data: EventIngestionRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    service = EventService(db)
    return await service.ingest_single(data, current_user.organization_id)


@router.post("/batch", status_code=status.HTTP_202_ACCEPTED)
async def ingest_events_batch(
    data: BatchEventRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):

    service = EventService(db)
    result = await service.ingest_batch(data, current_user.organization_id)
    return result


@router.post("/upload-csv")
async def upload_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):

    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .csv files are accepted"
        )

    service = EventService(db)
    return await service.ingest_csv(file, current_user.organization_id)


@router.get("/query", response_model=list[AggregatedDataPoint])
async def query_events(
    event_type: str = Query(..., description="Filter by event type"),
    start_time: datetime = Query(default=None),
    end_time: datetime = Query(default=None),
    interval: str = Query(default="1h", regex="^(1m|5m|15m|1h|6h|1d|7d)$"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):

    now = datetime.now(timezone.utc)
    if not start_time:
        start_time = now - timedelta(hours=24)
    if not end_time:
        end_time = now

    query = EventQueryRequest(
        event_type=event_type,
        start_time=start_time,
        end_time=end_time,
        interval=interval,
    )
    service = EventService(db)
    data = await service.query_time_series(query, current_user.organization_id)
    return [AggregatedDataPoint(**d) for d in data]


@router.get("/summary")
async def get_event_summary(
    hours: int = Query(default=24, ge=1, le=720),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):

    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=hours)
    service = EventService(db)
    return await service.get_event_summary(current_user.organization_id, start, end)


@router.get("/stream", response_model=list[EventResponse])
async def get_live_stream(
    limit: int = Query(default=50, le=200),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    service = EventService(db)
    return await service.get_live_stream(current_user.organization_id, limit)
