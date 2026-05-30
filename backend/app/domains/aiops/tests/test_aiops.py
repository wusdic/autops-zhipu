"""AIops domain unit tests."""
import pytest


@pytest.mark.asyncio
async def test_aiops_health_check(client):
    """Test GET /api/v1/aiops/health."""
    resp = await client.get("/api/v1/aiops/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == 0
    assert "available" in data["data"]


@pytest.mark.asyncio
async def test_aiops_analysis_model():
    """Test AIAnalysis model."""
    from app.domains.aiops.models import AIAnalysis
    a = AIAnalysis(analysis_type="root_cause")
    assert a.analysis_type == "root_cause"


@pytest.mark.asyncio
async def test_aiops_diagnose_graceful(client):
    """Test AI diagnose with graceful degradation."""
    resp = await client.post("/api/v1/aiops/diagnose", json={
        "question": "test question",
        "asset_type": "linux_server",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == 0