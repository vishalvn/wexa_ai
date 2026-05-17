from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, field_validator


class EventIngestionRequest(BaseModel):
    event_type: str
    user_id: str | None = None
    session_id: str | None = None
    properties: dict[str, Any] = {}
    timestamp: datetime | None = None  # If None, server uses current time

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v: str) -> str:
        if not v or len(v) > 100:
            raise ValueError("event_type must be 1-100 characters")
        return v.lower().replace(" ", "_")


class BatchEventRequest(BaseModel):
    events: list[EventIngestionRequest]

    @field_validator("events")
    @classmethod
    def validate_batch_size(cls, v):
        if len(v) > 1000:
            raise ValueError("Maximum 1000 events per batch request")
        return v


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_type: str
    user_id: str | None
    properties: dict
    timestamp: datetime
    source: str


class EventQueryRequest(BaseModel):
    event_type: str
    start_time: datetime
    end_time: datetime
    group_by: str | None = None       # e.g., "user_id", "properties.country"
    aggregation: str = "count"         # count, sum, avg
    aggregation_field: str | None = None  # field to sum/avg
    interval: str = "1h"               # 1m, 5m, 1h, 1d


class AggregatedDataPoint(BaseModel):
    timestamp: datetime
    value: float
    label: str | None = None
