"""Automation domain unit tests."""
import pytest


@pytest.mark.asyncio
async def test_script_api_list(client):
    """Test GET /api/v1/scripts returns list."""
    resp = await client.get("/api/v1/scripts")
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == 0


@pytest.mark.asyncio
async def test_execution_api_dry_run(client):
    """Test execution with dry-run."""
    # Get a script first
    resp = await client.get("/api/v1/scripts")
    items = resp.json()["data"]["items"]
    if items:
        script_id = items[0]["id"]
        resp = await client.post("/api/v1/executions", json={
            "execution_type": "script",
            "target_id": script_id,
            "asset_ids": ["test"],
            "is_dry_run": True,
        })
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "dry_run"
        assert resp.json()["data"]["is_dry_run"] is True