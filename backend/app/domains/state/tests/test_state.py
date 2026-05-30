"""State domain unit tests."""
import pytest
from datetime import datetime


@pytest.mark.asyncio
async def test_state_snapshot_model():
    """Test state snapshot model."""
    from app.domains.state.models import StateSnapshot
    s = StateSnapshot(
        asset_id="test-id",
        state_type="cpu_usage",
        status="normal",
        collected_at=datetime.now(),
    )
    assert s.asset_id == "test-id"
    assert s.state_type == "cpu_usage"


@pytest.mark.asyncio
async def test_state_api_latest(client):
    """Test latest state by asset_id."""
    resp = await client.get("/api/v1/states/latest/test-asset-id")
    assert resp.status_code in (200, 404)
