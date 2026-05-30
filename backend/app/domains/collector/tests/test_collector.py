"""Collector domain unit tests."""
import pytest


@pytest.mark.asyncio
async def test_collector_api_list(client):
    """Test GET /api/v1/collectors returns list."""
    resp = await client.get("/api/v1/collectors")
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == 0


@pytest.mark.asyncio
async def test_collector_model():
    """Test collector model has required fields."""
    from app.domains.collector.models import Collector
    c = Collector(name="ssh-collector", collector_type="ssh")
    assert c.name == "ssh-collector"
    assert c.collector_type == "ssh"


@pytest.mark.asyncio
async def test_collection_job_api(client):
    """Test collection job listing."""
    resp = await client.get("/api/v1/collection-jobs")
    assert resp.status_code == 200
    assert resp.json()["code"] == 0