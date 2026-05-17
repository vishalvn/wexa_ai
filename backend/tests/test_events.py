import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_ingest_single_event(authenticated_client: AsyncClient):
    response = await authenticated_client.post("/api/v1/events/", json={
        "event_type": "page_view",
        "user_id": "user_123",
        "properties": {"page": "/home", "browser": "Chrome"},
    })
    assert response.status_code == 201
    data = response.json()
    assert data["event_type"] == "page_view"
    assert data["source"] == "api"


@pytest.mark.asyncio
async def test_ingest_batch_events(authenticated_client: AsyncClient):
    """Should accept a batch of events."""
    response = await authenticated_client.post("/api/v1/events/batch", json={
        "events": [
            {"event_type": "click", "properties": {"button": "signup"}},
            {"event_type": "page_view", "properties": {"page": "/pricing"}},
            {"event_type": "purchase", "user_id": "u_456", "properties": {"amount": 99}},
        ]
    })
    assert response.status_code == 202
    data = response.json()
    assert data["accepted"] == 3
    assert data["rejected"] == 0


@pytest.mark.asyncio
async def test_batch_over_1000_rejected(authenticated_client: AsyncClient):
    events = [{"event_type": "click"} for _ in range(1001)]
    response = await authenticated_client.post("/api/v1/events/batch", json={"events": events})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_event_type_normalized(authenticated_client: AsyncClient):
    response = await authenticated_client.post("/api/v1/events/", json={
        "event_type": "Button Click",  # should become "button_click"
    })
    assert response.status_code == 201
    assert response.json()["event_type"] == "button_click"


@pytest.mark.asyncio
async def test_event_summary(authenticated_client: AsyncClient):
    # Ingest some events first
    for etype in ["click", "click", "page_view"]:
        await authenticated_client.post("/api/v1/events/", json={"event_type": etype})

    response = await authenticated_client.get("/api/v1/events/summary?hours=1")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_unauthenticated_ingestion_rejected(client: AsyncClient):
    response = await client.post("/api/v1/events/", json={"event_type": "test"})
    assert response.status_code in (401, 403)
