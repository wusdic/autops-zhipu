"""Governance domain unit tests."""
import pytest


@pytest.mark.asyncio
async def test_health_check(client):
    """Test GET /health."""
    resp = await client.get("/health")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_ready_check(client):
    """Test GET /ready."""
    resp = await client.get("/ready")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_auth_login(client):
    """Test POST /api/v1/auth/login."""
    resp = await client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "admin123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == 0
    assert "access_token" in data["data"]


@pytest.mark.asyncio
async def test_auth_login_wrong_password(client):
    """Test login with wrong password returns error."""
    resp = await client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "wrong_password",
    })
    data = resp.json()
    assert data.get("code", -1) != 0


@pytest.mark.asyncio
async def test_auth_me(client):
    """Test GET /api/v1/auth/me with valid token."""
    resp = await client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "admin123",
    })
    token = resp.json()["data"]["access_token"]

    resp = await client.get(f"/api/v1/auth/me?token={token}")
    assert resp.status_code == 200
    assert resp.json()["code"] == 0
