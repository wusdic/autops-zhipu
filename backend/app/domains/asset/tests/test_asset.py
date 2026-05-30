"""Asset domain unit tests."""
import pytest
from app.domains.asset.models import Asset


@pytest.mark.asyncio
async def test_asset_model_creation():
    """Test asset model can be instantiated."""
    asset = Asset(name="test", asset_type="linux_server")
    assert asset.name == "test"
    assert asset.asset_type == "linux_server"


@pytest.mark.asyncio
async def test_asset_api_create(client):
    """Test POST /api/v1/assets creates asset."""
    resp = await client.post("/api/v1/assets", json={
        "name": "test-linux-01",
        "asset_type": "linux_server",
        "ip_address": "10.0.0.1",
        "os_type": "linux",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == 0
    assert data["data"]["name"] == "test-linux-01"
    assert data["data"]["asset_type"] == "linux_server"


@pytest.mark.asyncio
async def test_asset_api_list(client):
    """Test GET /api/v1/assets returns list."""
    resp = await client.get("/api/v1/assets")
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == 0
    assert "items" in data["data"]


@pytest.mark.asyncio
async def test_asset_group_create_and_list(client):
    """Test asset group create and list."""
    # Create
    resp = await client.post("/api/v1/asset-groups", json={
        "name": "Test Group",
        "description": "Test description",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == 0

    # List
    resp = await client.get("/api/v1/asset-groups")
    assert resp.status_code == 200
    assert resp.json()["code"] == 0