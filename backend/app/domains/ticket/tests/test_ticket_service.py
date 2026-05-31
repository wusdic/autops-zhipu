"""工单中心 Service 单元测试."""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.common.exceptions import NotFoundError
from app.domains.ticket.models import Ticket, TicketComment
from app.domains.ticket.schemas import TicketCreate, TicketUpdate
from app.domains.ticket.service import TicketService, TICKET_TRANSITIONS


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def mock_ticket_repo():
    repo = AsyncMock()
    repo.create = AsyncMock()
    repo.get_by_id = AsyncMock()
    return repo


@pytest.fixture
def mock_comment_repo():
    repo = AsyncMock()
    repo.create = AsyncMock()
    return repo


@pytest.fixture
def service(mock_session, mock_ticket_repo, mock_comment_repo):
    with patch("app.domains.ticket.service.BaseRepository") as BR:
        def make_repo(sess, model):
            if model is Ticket:
                return mock_ticket_repo
            if model is TicketComment:
                return mock_comment_repo
            return AsyncMock()
        BR.side_effect = make_repo
        svc = TicketService(mock_session)
    svc._ticket_repo = mock_ticket_repo
    svc._comment_repo = mock_comment_repo
    return svc


def _make_ticket(**overrides) -> Ticket:
    defaults = dict(
        id="ticket-001",
        title="Server down",
        ticket_type="incident",
        status="open",
        priority="high",
        description="Server is not responding",
        context=None,
        alert_ids=None,
        execution_ids=None,
        assigned_to=None,
        created_by="user-001",
        resolved_by=None,
        resolved_at=None,
        closed_by=None,
        closed_at=None,
    )
    defaults.update(overrides)
    t = MagicMock(spec=Ticket)
    for k, v in defaults.items():
        setattr(t, k, v)
    return t


# ---------------------------------------------------------------------------
# Test: create_ticket
# ---------------------------------------------------------------------------

class TestCreateTicket:
    async def test_create_success(self, service, mock_ticket_repo):
        ticket = _make_ticket()
        mock_ticket_repo.create.return_value = ticket

        data = TicketCreate(title="Server down", ticket_type="incident")
        result = await service.create_ticket(data, user_id="user-001")

        assert result.title == "Server down"
        mock_ticket_repo.create.assert_called_once()

    async def test_create_with_all_fields(self, service, mock_ticket_repo):
        ticket = _make_ticket()
        mock_ticket_repo.create.return_value = ticket

        data = TicketCreate(
            title="DB slow",
            ticket_type="incident",
            priority="critical",
            description="Database queries are slow",
            assigned_to="admin-001",
        )
        result = await service.create_ticket(data, user_id="user-001")
        assert result is not None


# ---------------------------------------------------------------------------
# Test: get_ticket
# ---------------------------------------------------------------------------

class TestGetTicket:
    async def test_get_existing(self, service, mock_ticket_repo):
        ticket = _make_ticket()
        mock_ticket_repo.get_by_id.return_value = ticket

        result = await service.get_ticket("ticket-001")
        assert result.title == "Server down"

    async def test_get_not_found(self, service, mock_ticket_repo):
        mock_ticket_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError, match="不存在"):
            await service.get_ticket("nonexistent")


# ---------------------------------------------------------------------------
# Test: update_ticket
# ---------------------------------------------------------------------------

class TestUpdateTicket:
    async def test_update_fields(self, service, mock_ticket_repo):
        ticket = _make_ticket()
        mock_ticket_repo.get_by_id.return_value = ticket

        data = TicketUpdate(title="Updated title")
        result = await service.update_ticket("ticket-001", data)

        assert ticket.title == "Updated title"

    async def test_update_status_to_resolved(self, service, mock_ticket_repo):
        ticket = _make_ticket(status="in_progress")
        mock_ticket_repo.get_by_id.return_value = ticket

        data = TicketUpdate(status="resolved")
        await service.update_ticket("ticket-001", data, user_id="user-001")

        assert ticket.status == "resolved"
        assert ticket.resolved_by == "user-001"
        assert ticket.resolved_at is not None

    async def test_update_status_to_closed(self, service, mock_ticket_repo):
        ticket = _make_ticket(status="resolved")
        mock_ticket_repo.get_by_id.return_value = ticket

        data = TicketUpdate(status="closed")
        await service.update_ticket("ticket-001", data, user_id="admin")

        assert ticket.status == "closed"
        assert ticket.closed_by == "admin"
        assert ticket.closed_at is not None

    async def test_update_not_found(self, service, mock_ticket_repo):
        mock_ticket_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError, match="不存在"):
            await service.update_ticket("nonexistent", TicketUpdate(title="x"))


# ---------------------------------------------------------------------------
# Test: list_tickets
# ---------------------------------------------------------------------------

class TestListTickets:
    async def test_list_default(self, service, mock_session):
        mock_session.execute.side_effect = [
            MagicMock(scalar=MagicMock(return_value=1)),
            MagicMock(scalars=MagicMock(return_value=MagicMock(
                all=MagicMock(return_value=[_make_ticket()])
            ))),
        ]

        items, total = await service.list_tickets()
        assert total == 1

    async def test_list_with_filters(self, service, mock_session):
        mock_session.execute.side_effect = [
            MagicMock(scalar=MagicMock(return_value=0)),
            MagicMock(scalars=MagicMock(return_value=MagicMock(
                all=MagicMock(return_value=[])
            ))),
        ]

        items, total = await service.list_tickets(
            status="open", ticket_type="incident", assigned_to="user-001"
        )
        assert total == 0


# ---------------------------------------------------------------------------
# Test: state machine transitions
# ---------------------------------------------------------------------------

class TestStateMachineTransitions:
    """Test valid transitions defined in TICKET_TRANSITIONS."""

    async def test_open_to_assigned(self, service, mock_ticket_repo):
        ticket = _make_ticket(status="open")
        mock_ticket_repo.get_by_id.return_value = ticket

        result = await service.transition_ticket("ticket-001", "assigned")
        assert ticket.status == "assigned"

    async def test_assigned_to_in_progress(self, service, mock_ticket_repo):
        ticket = _make_ticket(status="assigned")
        mock_ticket_repo.get_by_id.return_value = ticket

        result = await service.transition_ticket("ticket-001", "in_progress")
        assert ticket.status == "in_progress"

    async def test_in_progress_to_resolved(self, service, mock_ticket_repo):
        ticket = _make_ticket(status="in_progress")
        mock_ticket_repo.get_by_id.return_value = ticket

        result = await service.transition_ticket("ticket-001", "resolved")
        assert ticket.status == "resolved"
        assert ticket.resolved_by is not None

    async def test_resolved_to_closed(self, service, mock_ticket_repo):
        ticket = _make_ticket(status="resolved")
        mock_ticket_repo.get_by_id.return_value = ticket

        result = await service.transition_ticket("ticket-001", "closed")
        assert ticket.status == "closed"
        assert ticket.closed_by is not None

    async def test_full_lifecycle(self, service, mock_ticket_repo):
        """open → assigned → in_progress → resolved → closed"""
        ticket = _make_ticket(status="open")
        mock_ticket_repo.get_by_id.return_value = ticket

        await service.transition_ticket("ticket-001", "assigned")
        assert ticket.status == "assigned"

        await service.transition_ticket("ticket-001", "in_progress")
        assert ticket.status == "in_progress"

        await service.transition_ticket("ticket-001", "resolved")
        assert ticket.status == "resolved"

        await service.transition_ticket("ticket-001", "closed")
        assert ticket.status == "closed"


class TestStateMachineInvalidTransitions:
    """Test that illegal transitions are rejected."""

    async def test_open_to_resolved_invalid(self, service, mock_ticket_repo):
        ticket = _make_ticket(status="open")
        mock_ticket_repo.get_by_id.return_value = ticket

        with pytest.raises(ValueError, match="不允许的状态转换"):
            await service.transition_ticket("ticket-001", "resolved")

    async def test_closed_to_any_invalid(self, service, mock_ticket_repo):
        ticket = _make_ticket(status="closed")
        mock_ticket_repo.get_by_id.return_value = ticket

        with pytest.raises(ValueError, match="不允许的状态转换"):
            await service.transition_ticket("ticket-001", "open")

    async def test_closed_is_terminal(self):
        """closed state has no allowed transitions."""
        assert TICKET_TRANSITIONS["closed"] == []

    async def test_in_progress_to_open_invalid(self, service, mock_ticket_repo):
        ticket = _make_ticket(status="in_progress")
        mock_ticket_repo.get_by_id.return_value = ticket

        with pytest.raises(ValueError, match="不允许的状态转换"):
            await service.transition_ticket("ticket-001", "open")


# ---------------------------------------------------------------------------
# Test: create_from_alert
# ---------------------------------------------------------------------------

class TestCreateFromAlert:
    async def test_create_from_alert_critical(self, service, mock_ticket_repo):
        ticket = _make_ticket()
        mock_ticket_repo.create.return_value = ticket

        result = await service.create_from_alert(
            alert_id="alert-001",
            title="Critical alert",
            severity="critical",
        )
        assert result is not None
        # Verify TicketCreate was called with incident type
        call_kwargs = mock_ticket_repo.create.call_args.kwargs
        assert call_kwargs.get("ticket_type") == "incident"
        assert call_kwargs.get("priority") == "critical"

    async def test_create_from_alert_warning(self, service, mock_ticket_repo):
        ticket = _make_ticket()
        mock_ticket_repo.create.return_value = ticket

        result = await service.create_from_alert(
            alert_id="alert-001",
            title="Warning alert",
            severity="warning",
        )
        call_kwargs = mock_ticket_repo.create.call_args.kwargs
        assert call_kwargs.get("priority") == "high"

    async def test_create_from_alert_info(self, service, mock_ticket_repo):
        ticket = _make_ticket()
        mock_ticket_repo.create.return_value = ticket

        result = await service.create_from_alert(
            alert_id="alert-001",
            title="Info alert",
            severity="info",
        )
        call_kwargs = mock_ticket_repo.create.call_args.kwargs
        assert call_kwargs.get("priority") == "medium"

    async def test_create_from_alert_with_context(self, service, mock_ticket_repo):
        ticket = _make_ticket()
        mock_ticket_repo.create.return_value = ticket

        result = await service.create_from_alert(
            alert_id="alert-001",
            title="Alert with context",
            severity="warning",
            context={"key": "value"},
        )
        assert result is not None


# ---------------------------------------------------------------------------
# Test: comments
# ---------------------------------------------------------------------------

class TestComments:
    async def test_add_comment(self, service, mock_comment_repo):
        comment = MagicMock(spec=TicketComment)
        mock_comment_repo.create.return_value = comment

        result = await service.add_comment("ticket-001", "user-001", "some comment")
        mock_comment_repo.create.assert_called_once_with(
            ticket_id="ticket-001", user_id="user-001", content="some comment"
        )

    async def test_get_comments(self, service, mock_session):
        mock_session.execute.return_value = MagicMock(
            scalars=MagicMock(return_value=MagicMock(
                all=MagicMock(return_value=[MagicMock(spec=TicketComment)])
            ))
        )

        comments = await service.get_comments("ticket-001")
        assert len(comments) == 1


# ---------------------------------------------------------------------------
# Test: convert_to_knowledge_draft
# ---------------------------------------------------------------------------

class TestConvertToKnowledge:
    async def test_convert_closed_ticket(self, service, mock_ticket_repo):
        ticket = _make_ticket(status="closed", title="Server issue")
        mock_ticket_repo.get_by_id.return_value = ticket

        result = await service.convert_to_knowledge_draft("ticket-001")
        assert "Server issue" in result["title"]
        assert result["article_type"] == "incident_summary"
        assert result["source"] == "ticket_closure"

    async def test_convert_non_closed_ticket(self, service, mock_ticket_repo):
        ticket = _make_ticket(status="open")
        mock_ticket_repo.get_by_id.return_value = ticket

        with pytest.raises(ValueError, match="只有已关闭的工单"):
            await service.convert_to_knowledge_draft("ticket-001")
