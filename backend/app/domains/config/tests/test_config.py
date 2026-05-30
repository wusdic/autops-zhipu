"""Config domain unit tests."""
import pytest


@pytest.mark.asyncio
async def test_config_definition_api(client):
    """Test config definition CRUD."""
    resp = await client.post("/api/v1/configs/definitions", json={
        "name": "test.timeout",
        "config_type": "system",
        "description": "Test timeout config",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == 0


@pytest.mark.asyncio
async def test_config_definition_list(client):
    """Test config definition listing."""
    resp = await client.get("/api/v1/configs/definitions")
    assert resp.status_code == 200
    assert resp.json()["code"] == 0


@pytest.mark.asyncio
async def test_credential_api(client):
    """Test credential CRUD."""
    resp = await client.post("/api/v1/credentials", json={
        "name": "test-ssh-key",
        "cred_type": "ssh_key",
        "data": "{\"username\": \"root\", \"private_key\": \"test-key\"}",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == 0
