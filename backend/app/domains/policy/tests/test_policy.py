"""Policy domain unit tests."""
import pytest


@pytest.mark.asyncio
async def test_policy_api_list(client):
    """Test GET /api/v1/policies returns list."""
    resp = await client.get("/api/v1/policies")
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == 0
    assert "items" in data["data"]


@pytest.mark.asyncio
async def test_policy_simulate(client):
    """Test policy simulation."""
    # Get a policy first
    resp = await client.get("/api/v1/policies")
    items = resp.json()["data"]["items"]
    if items:
        policy_id = items[0]["id"]
        resp = await client.post(f"/api/v1/policies/{policy_id}/simulate", json={
            "trigger_event": "disk_usage_high",
            "asset_ids": ["test-asset"],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert "policy_name" in data["data"]


@pytest.mark.asyncio
async def test_policy_model():
    """Test policy model."""
    from app.domains.policy.models import Policy
    p = Policy(name="test-policy", risk_level="low", requires_approval=False)
    assert p.name == "test-policy"
    assert p.risk_level == "low"