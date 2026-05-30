"""Event domain unit tests."""
import pytest


@pytest.mark.asyncio
async def test_event_api_create(client):
    """Test POST /api/v1/events creates event."""
    resp = await client.post("/api/v1/events", json={
        "event_type": "threshold_exceeded",
        "source": "test",
        "title": "Test event",
        "severity": "warning",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == 0
    assert data["data"]["event_type"] == "threshold_exceeded"


@pytest.mark.asyncio
async def test_event_api_list(client):
    """Test GET /api/v1/events returns list."""
    resp = await client.get("/api/v1/events")
    assert resp.status_code == 200
    assert resp.json()["code"] == 0


@pytest.mark.asyncio
async def test_event_model():
    """Test event model."""
    from app.domains.event.models import Event
    e = Event(event_type="test", source="unit_test", title="Test", severity="info")
    assert e.event_type == "test"
    assert e.title == "Test"