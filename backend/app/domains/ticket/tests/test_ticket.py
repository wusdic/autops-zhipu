"""Ticket domain unit tests."""
import pytest


@pytest.mark.asyncio
async def test_ticket_create_and_list(client):
    """Test ticket create and list."""
    resp = await client.post("/api/v1/tickets", json={
        "title": "Test ticket",
        "ticket_type": "incident",
        "description": "Unit test ticket",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == 0
    ticket_id = data["data"]["id"]

    # List
    resp = await client.get("/api/v1/tickets")
    assert resp.status_code == 200

    # Get single
    resp = await client.get(f"/api/v1/tickets/{ticket_id}")
    assert resp.status_code == 200

    # Add comment
    resp = await client.post(f"/api/v1/tickets/{ticket_id}/comments", json={
        "content": "Test comment",
    })
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_ticket_model():
    """Test ticket model."""
    from app.domains.ticket.models import Ticket
    t = Ticket(title="Test")
    assert t.title == "Test"
