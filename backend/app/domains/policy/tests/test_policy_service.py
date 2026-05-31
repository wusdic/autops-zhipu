"""策略中心 Service 单元测试."""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.common.exceptions import DuplicateError, NotFoundError
from app.domains.policy.models import Policy, PolicyExecution
from app.domains.policy.service import PolicyService


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
def mock_policy_repo():
    repo = AsyncMock()
    repo.create = AsyncMock()
    repo.get_by_id = AsyncMock()
    return repo


@pytest.fixture
def mock_exec_repo():
    repo = AsyncMock()
    repo.create = AsyncMock()
    repo.get_by_id = AsyncMock()
    return repo


@pytest.fixture
def service(mock_session, mock_policy_repo, mock_exec_repo):
    with patch("app.domains.policy.service.BaseRepository") as BR:
        def make_repo(sess, model):
            if model is Policy:
                return mock_policy_repo
            if model is PolicyExecution:
                return mock_exec_repo
            return AsyncMock()
        BR.side_effect = make_repo
        svc = PolicyService(mock_session)
    svc._policy_repo = mock_policy_repo
    svc._exec_repo = mock_exec_repo
    return svc


def _make_policy(**overrides) -> Policy:
    defaults = dict(
        id="policy-001",
        name="restart-service",
        description="Restart service when down",
        trigger_type="event_type",
        trigger_condition=json.dumps({"event_type": "service_down"}),
        scope=None,
        action_chain=json.dumps([{"type": "script", "target_id": "script-001"}]),
        risk_level="low",
        requires_approval=False,
        max_affected_assets=10,
        verification_steps=None,
        rollback_actions=None,
        version=1,
        status="active",
        enabled=True,
    )
    defaults.update(overrides)
    p = MagicMock(spec=Policy)
    for k, v in defaults.items():
        setattr(p, k, v)
    return p


# ---------------------------------------------------------------------------
# Test: create_policy
# ---------------------------------------------------------------------------

class TestCreatePolicy:
    async def test_create_success(self, service, mock_policy_repo, mock_session):
        policy = _make_policy()
        mock_session.execute.return_value = MagicMock(scalar=MagicMock(return_value=None))
        mock_policy_repo.create.return_value = policy

        result = await service.create_policy(
            name="restart-service",
            trigger_type="event_type",
            trigger_condition=json.dumps({"event_type": "service_down"}),
            action_chain=json.dumps([{"type": "script"}]),
        )

        assert result.name == "restart-service"
        mock_policy_repo.create.assert_called_once()

    async def test_create_duplicate(self, service, mock_session):
        mock_session.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=_make_policy())
        )

        with pytest.raises(DuplicateError, match="已存在"):
            await service.create_policy(
                name="restart-service",
                trigger_type="event_type",
                trigger_condition="{}",
                action_chain="[]",
            )


# ---------------------------------------------------------------------------
# Test: get_policy
# ---------------------------------------------------------------------------

class TestGetPolicy:
    async def test_get_existing(self, service, mock_policy_repo):
        policy = _make_policy()
        mock_policy_repo.get_by_id.return_value = policy

        result = await service.get_policy("policy-001")
        assert result.name == "restart-service"

    async def test_get_not_found(self, service, mock_policy_repo):
        mock_policy_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError, match="不存在"):
            await service.get_policy("nonexistent")


# ---------------------------------------------------------------------------
# Test: update_policy
# ---------------------------------------------------------------------------

class TestUpdatePolicy:
    async def test_update_success(self, service, mock_policy_repo):
        policy = _make_policy()
        mock_policy_repo.get_by_id.return_value = policy

        result = await service.update_policy("policy-001", description="new desc")
        assert policy.description == "new desc"
        # Version should increment
        assert policy.version == 2

    async def test_update_not_found(self, service, mock_policy_repo):
        mock_policy_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError, match="不存在"):
            await service.update_policy("nonexistent", description="x")


# ---------------------------------------------------------------------------
# Test: list_policies
# ---------------------------------------------------------------------------

class TestListPolicies:
    async def test_list_default(self, service, mock_session):
        mock_session.execute.side_effect = [
            MagicMock(scalar=MagicMock(return_value=1)),  # count
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(
                return_value=[_make_policy()]
            )))),
        ]

        items, total = await service.list_policies()
        assert total == 1
        assert len(items) == 1

    async def test_list_with_filters(self, service, mock_session):
        mock_session.execute.side_effect = [
            MagicMock(scalar=MagicMock(return_value=0)),  # count
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))),
        ]

        items, total = await service.list_policies(trigger_type="event_type", status="active")
        assert total == 0


# ---------------------------------------------------------------------------
# Test: delete_policy (soft delete)
# ---------------------------------------------------------------------------

class TestDeletePolicy:
    async def test_delete(self, service, mock_policy_repo):
        policy = _make_policy()
        mock_policy_repo.get_by_id.return_value = policy

        await service.delete_policy("policy-001")
        assert policy.status == "disabled"
        assert policy.enabled is False

    async def test_delete_not_found(self, service, mock_policy_repo):
        mock_policy_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError, match="不存在"):
            await service.delete_policy("nonexistent")


# ---------------------------------------------------------------------------
# Test: simulate (dry-run / condition matching)
# ---------------------------------------------------------------------------

class TestSimulate:
    async def test_simulate_match(self, service, mock_policy_repo):
        policy = _make_policy()
        mock_policy_repo.get_by_id.return_value = policy

        result = await service.simulate(
            "policy-001",
            trigger_event="service_down",
            asset_ids=["asset-001"],
        )

        assert result["policy_id"] == "policy-001"
        assert result["trigger_matched"] is True
        assert "asset-001" in result["affected_assets"]

    async def test_simulate_no_match(self, service, mock_policy_repo):
        policy = _make_policy()
        mock_policy_repo.get_by_id.return_value = policy

        result = await service.simulate(
            "policy-001",
            trigger_event="disk_full",
        )

        assert result["trigger_matched"] is False

    async def test_simulate_with_approval_required(self, service, mock_policy_repo):
        policy = _make_policy(requires_approval=True, risk_level="high")
        mock_policy_repo.get_by_id.return_value = policy

        result = await service.simulate("policy-001", trigger_event="service_down")

        assert result["requires_approval"] is True
        assert result["risk_level"] == "high"


# ---------------------------------------------------------------------------
# Test: policy versioning
# ---------------------------------------------------------------------------

class TestPolicyVersioning:
    async def test_version_increments_on_update(self, service, mock_policy_repo):
        policy = _make_policy(version=1)
        mock_policy_repo.get_by_id.return_value = policy

        await service.update_policy("policy-001", description="update 1")
        assert policy.version == 2

        await service.update_policy("policy-001", description="update 2")
        assert policy.version == 3
