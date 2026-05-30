"""Alert domain unit tests."""
import pytest


@pytest.mark.asyncio
async def test_alert_api_create(client):
    """Test POST /api/v1/alerts creates alert."""
    resp = await client.post("/api/v1/alerts", json={
        "title": "Test alert",
        "severity": "critical",
        "context": "{\"cpu\": 95}",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == 0
    assert data["data"]["title"] == "Test alert"
    alert_id = data["data"]["id"]

    # Acknowledge
    resp = await client.post(f"/api/v1/alerts/{alert_id}/acknowledge")
    assert resp.status_code == 200

    # Resolve
    resp = await client.post(f"/api/v1/alerts/{alert_id}/resolve")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_alert_rule_list(client):
    """Test alert rules listing."""
    resp = await client.get("/api/v1/alert-rules")
    assert resp.status_code == 200
    assert resp.json()["code"] == 0