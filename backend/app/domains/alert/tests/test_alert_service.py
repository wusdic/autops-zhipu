"""告警中心 Service 单元测试."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.common.exceptions import NotFoundError
from app.domains.alert.models import Alert, AlertRule
from app.domains.alert.service import AlertService


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
def mock_alert_repo():
    repo = AsyncMock()
    repo.create = AsyncMock()
    repo.get_by_id = AsyncMock()
    return repo


@pytest.fixture
def mock_rule_repo():
    repo = AsyncMock()
    repo.create = AsyncMock()
    repo.get_by_id = AsyncMock()
    return repo


@pytest.fixture
def service(mock_session, mock_alert_repo, mock_rule_repo):
    with patch("app.domains.alert.service.BaseRepository") as BR:
        def make_repo(sess, model):
            if model is Alert:
                return mock_alert_repo
            if model is AlertRule:
                return mock_rule_repo
            return AsyncMock()
        BR.side_effect = make_repo
        svc = AlertService(mock_session)
    svc._alert_repo = mock_alert_repo
    svc._rule_repo = mock_rule_repo
    return svc


def _make_alert(**overrides) -> Alert:
    defaults = dict(
        id="alert-001",
        title="CPU usage high",
        severity="warning",
        status="firing",
        rule_id=None,
        asset_ids=None,
        acknowledged_by=None,
        acknowledged_at=None,
        resolved_by=None,
        resolved_at=None,
    )
    defaults.update(overrides)
    a = MagicMock(spec=Alert)
    for k, v in defaults.items():
        setattr(a, k, v)
    return a


def _make_rule(**overrides) -> AlertRule:
    defaults = dict(
        id="rule-001",
        name="cpu-high-rule",
        description="CPU high alert",
        event_types='["state.status_changed"]',
        conditions='{"metric": "cpu", "threshold": 90}',
        severity="warning",
        suppress_duration=0,
        enabled=True,
    )
    defaults.update(overrides)
    r = MagicMock(spec=AlertRule)
    for k, v in defaults.items():
        setattr(r, k, v)
    return r


# ---------------------------------------------------------------------------
# Test: create_alert
# ---------------------------------------------------------------------------

class TestCreateAlert:
    async def test_create_success(self, service, mock_alert_repo):
        alert = _make_alert()
        mock_alert_repo.create.return_value = alert

        result = await service.create_alert(
            title="CPU usage high", severity="warning"
        )

        assert result.title == "CPU usage high"
        assert result.severity == "warning"
        mock_alert_repo.create.assert_called_once_with(
            title="CPU usage high", severity="warning"
        )

    async def test_create_with_context(self, service, mock_alert_repo):
        alert = _make_alert()
        mock_alert_repo.create.return_value = alert

        result = await service.create_alert(
            title="Disk full", severity="critical", rule_id="rule-001"
        )
        assert result is not None


# ---------------------------------------------------------------------------
# Test: get_alert
# ---------------------------------------------------------------------------

class TestGetAlert:
    async def test_get_existing(self, service, mock_alert_repo):
        alert = _make_alert()
        mock_alert_repo.get_by_id.return_value = alert

        result = await service.get_alert("alert-001")
        assert result.title == "CPU usage high"

    async def test_get_not_found(self, service, mock_alert_repo):
        mock_alert_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError, match="不存在"):
            await service.get_alert("nonexistent")


# ---------------------------------------------------------------------------
# Test: list_alerts
# ---------------------------------------------------------------------------

class TestListAlerts:
    async def test_list_default(self, service, mock_session):
        # Mock two execute calls: count and data
        mock_session.execute.side_effect = [
            MagicMock(scalar=MagicMock(return_value=1)),  # count
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[_make_alert()])))),
        ]

        items, total = await service.list_alerts()
        assert total == 1
        assert len(items) == 1

    async def test_list_with_filters(self, service, mock_session):
        mock_session.execute.side_effect = [
            MagicMock(scalar=MagicMock(return_value=0)),  # count
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))),
        ]

        items, total = await service.list_alerts(status="firing", severity="critical")
        assert total == 0


# ---------------------------------------------------------------------------
# Test: acknowledge (lifecycle)
# ---------------------------------------------------------------------------

class TestAcknowledge:
    async def test_acknowledge_success(self, service, mock_alert_repo):
        alert = _make_alert()
        mock_alert_repo.get_by_id.return_value = alert

        result = await service.acknowledge("alert-001", user_id="user-001")
        assert alert.status == "acknowledged"
        assert alert.acknowledged_by == "user-001"
        assert alert.acknowledged_at is not None

    async def test_acknowledge_not_found(self, service, mock_alert_repo):
        mock_alert_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError, match="不存在"):
            await service.acknowledge("nonexistent")


# ---------------------------------------------------------------------------
# Test: resolve (lifecycle)
# ---------------------------------------------------------------------------

class TestResolve:
    async def test_resolve_success(self, service, mock_alert_repo):
        alert = _make_alert()
        mock_alert_repo.get_by_id.return_value = alert

        result = await service.resolve("alert-001", user_id="user-001")
        assert alert.status == "resolved"
        assert alert.resolved_by == "user-001"
        assert alert.resolved_at is not None

    async def test_resolve_not_found(self, service, mock_alert_repo):
        mock_alert_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError, match="不存在"):
            await service.resolve("nonexistent")


# ---------------------------------------------------------------------------
# Test: lifecycle (create -> acknowledge -> resolve)
# ---------------------------------------------------------------------------

class TestAlertLifecycle:
    async def test_full_lifecycle(self, service, mock_alert_repo):
        alert = _make_alert()
        mock_alert_repo.create.return_value = alert
        mock_alert_repo.get_by_id.return_value = alert

        # Create
        created = await service.create_alert("Test", "warning")
        assert created.status == "firing"

        # Acknowledge
        acked = await service.acknowledge("alert-001", user_id="user-001")
        assert acked.status == "acknowledged"

        # Resolve
        resolved = await service.resolve("alert-001", user_id="user-001")
        assert resolved.status == "resolved"


# ---------------------------------------------------------------------------
# Test: escalate
# ---------------------------------------------------------------------------

class TestEscalate:
    async def test_escalate_success(self, service, mock_alert_repo):
        alert = _make_alert()
        mock_alert_repo.get_by_id.return_value = alert

        result = await service.escalate("alert-001", escalate_to="admin")
        assert alert.status == "escalated"

    async def test_escalate_not_found(self, service, mock_alert_repo):
        mock_alert_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError, match="不存在"):
            await service.escalate("nonexistent")


# ---------------------------------------------------------------------------
# Test: rules CRUD
# ---------------------------------------------------------------------------

class TestAlertRules:
    async def test_create_rule(self, service, mock_rule_repo):
        rule = _make_rule()
        mock_rule_repo.create.return_value = rule

        result = await service.create_rule(
            name="cpu-high", conditions='{"metric":"cpu"}', severity="warning"
        )
        assert result.name == "cpu-high-rule"

    async def test_update_rule(self, service, mock_rule_repo):
        rule = _make_rule()
        mock_rule_repo.get_by_id.return_value = rule

        result = await service.update_rule("rule-001", name="updated-rule")
        assert rule.name == "updated-rule"

    async def test_update_rule_not_found(self, service, mock_rule_repo):
        mock_rule_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError, match="不存在"):
            await service.update_rule("nonexistent", name="x")

    async def test_test_rule(self, service, mock_rule_repo):
        rule = _make_rule()
        mock_rule_repo.get_by_id.return_value = rule

        result = await service.test_rule("rule-001")
        assert result["simulated"] is True
        assert result["matched"] is True

    async def test_test_rule_not_found(self, service, mock_rule_repo):
        mock_rule_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError, match="不存在"):
            await service.test_rule("nonexistent")

    async def test_list_rules(self, service, mock_session):
        mock_session.execute.return_value = MagicMock(
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[_make_rule()])))
        )

        rules = await service.list_rules()
        assert len(rules) == 1

    async def test_list_rules_enabled_filter(self, service, mock_session):
        mock_session.execute.return_value = MagicMock(
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        )

        rules = await service.list_rules(enabled=True)
        assert len(rules) == 0
