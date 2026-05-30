"""Log domain unit tests."""
import pytest


@pytest.mark.asyncio
async def test_execution_log_api(client):
    """Test execution log by execution_id."""
    resp = await client.get("/api/v1/logs/execution/test-exec-id")
    assert resp.status_code in (200, 404)


@pytest.mark.asyncio
async def test_log_model():
    """Test execution log model."""
    from app.domains.log.models import ExecutionLog
    log = ExecutionLog(execution_id="test-exec")
    assert log.execution_id == "test-exec"
