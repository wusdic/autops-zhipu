"""自动化执行中心 Service 单元测试."""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.common.exceptions import NotFoundError
from app.domains.automation.models import Execution, ExecutionStep, Playbook, Script
from app.domains.automation.schemas import ExecutionCreate
from app.domains.automation.service import AutomationService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    session.execute = AsyncMock()
    session.delete = AsyncMock()
    return session


@pytest.fixture
def mock_script_repo():
    repo = AsyncMock()
    repo.create = AsyncMock()
    repo.get_by_id = AsyncMock()
    return repo


@pytest.fixture
def mock_playbook_repo():
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
def mock_step_repo():
    repo = AsyncMock()
    repo.create = AsyncMock()
    return repo


@pytest.fixture
def service(mock_session, mock_script_repo, mock_playbook_repo, mock_exec_repo, mock_step_repo):
    with patch("app.domains.automation.service.BaseRepository") as BR:
        def make_repo(sess, model):
            if model is Script:
                return mock_script_repo
            if model is Playbook:
                return mock_playbook_repo
            if model is Execution:
                return mock_exec_repo
            if model is ExecutionStep:
                return mock_step_repo
            return AsyncMock()
        BR.side_effect = make_repo
        svc = AutomationService(mock_session)
    svc._script_repo = mock_script_repo
    svc._playbook_repo = mock_playbook_repo
    svc._exec_repo = mock_exec_repo
    svc._step_repo = mock_step_repo
    return svc


def _make_script(**overrides) -> Script:
    defaults = dict(
        id="script-001",
        name="restart-nginx",
        description="Restart nginx service",
        script_type="shell",
        content="systemctl restart nginx",
        parameters=None,
        timeout=300,
        risk_level="low",
        is_blocked=False,
        version=1,
    )
    defaults.update(overrides)
    s = MagicMock(spec=Script)
    for k, v in defaults.items():
        setattr(s, k, v)
    return s


def _make_playbook(**overrides) -> Playbook:
    defaults = dict(
        id="pb-001",
        name="restart-stack",
        description="Restart full stack",
        steps=json.dumps([{"script_id": "script-001"}]),
        risk_level="low",
        version=1,
    )
    defaults.update(overrides)
    pb = MagicMock(spec=Playbook)
    for k, v in defaults.items():
        setattr(pb, k, v)
    return pb


def _make_execution(**overrides) -> Execution:
    defaults = dict(
        id="exec-001",
        execution_type="script",
        target_id="script-001",
        asset_ids=json.dumps(["asset-001"]),
        parameters=None,
        status="pending",
        trigger_source="manual",
        trigger_source_id=None,
        is_dry_run=False,
        risk_level="low",
        approved_by=None,
        approved_at=None,
        started_at=None,
        completed_at=None,
        result=None,
        error_message=None,
    )
    defaults.update(overrides)
    e = MagicMock(spec=Execution)
    for k, v in defaults.items():
        setattr(e, k, v)
    return e


# ---------------------------------------------------------------------------
# Test: create_script / blocked commands
# ---------------------------------------------------------------------------

class TestScriptCRUD:
    async def test_create_script(self, service, mock_script_repo, mock_session):
        mock_session.execute.return_value = MagicMock(scalar=MagicMock(return_value=None))
        script = _make_script()
        mock_script_repo.create.return_value = script

        result = await service.create_script(
            name="restart-nginx", content="systemctl restart nginx",
            script_type="shell",
        )
        assert result.name == "restart-nginx"

    async def test_create_script_duplicate(self, service, mock_session):
        mock_session.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=_make_script())
        )

        from app.common.exceptions import DuplicateError
        with pytest.raises(DuplicateError, match="已存在"):
            await service.create_script(
                name="restart-nginx", content="x", script_type="shell"
            )

    async def test_create_script_blocked_command(self, service, mock_script_repo, mock_session):
        mock_session.execute.return_value = MagicMock(scalar=MagicMock(return_value=None))
        script = _make_script(is_blocked=True)
        mock_script_repo.create.return_value = script

        result = await service.create_script(
            name="danger", content="rm -rf /", script_type="shell"
        )
        # Verify is_blocked was set
        call_kwargs = mock_script_repo.create.call_args.kwargs
        assert call_kwargs.get("is_blocked") is True

    async def test_update_script(self, service, mock_script_repo):
        script = _make_script()
        mock_script_repo.get_by_id.return_value = script

        result = await service.update_script("script-001", description="new desc")
        assert script.description == "new desc"

    async def test_update_script_not_found(self, service, mock_script_repo):
        mock_script_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError, match="不存在"):
            await service.update_script("nonexistent", description="x")

    async def test_update_script_blocked_content(self, service, mock_script_repo):
        script = _make_script()
        mock_script_repo.get_by_id.return_value = script

        await service.update_script("script-001", content="rm -rf /")
        assert script.is_blocked is True

    async def test_delete_script(self, service, mock_script_repo):
        script = _make_script()
        mock_script_repo.get_by_id.return_value = script

        await service.delete_script("script-001")
        mock_script_repo.get_by_id.assert_called_once_with("script-001")

    async def test_delete_script_not_found(self, service, mock_script_repo):
        mock_script_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError, match="不存在"):
            await service.delete_script("nonexistent")


# ---------------------------------------------------------------------------
# Test: blocked command detection
# ---------------------------------------------------------------------------

class TestBlockedCommands:
    def test_check_blocked_rm_rf(self, service):
        assert service._check_blocked("rm -rf /") is True

    def test_check_blocked_mkfs(self, service):
        assert service._check_blocked("mkfs.ext4 /dev/sda1") is True

    def test_check_blocked_dd(self, service):
        assert service._check_blocked("dd if=/dev/zero of=/dev/sda") is True

    def test_check_blocked_safe_command(self, service):
        assert service._check_blocked("systemctl restart nginx") is False

    def test_check_blocked_case_insensitive(self, service):
        assert service._check_blocked("RM -RF /") is True


# ---------------------------------------------------------------------------
# Test: playbook CRUD
# ---------------------------------------------------------------------------

class TestPlaybookCRUD:
    async def test_create_playbook(self, service, mock_playbook_repo, mock_session):
        mock_session.execute.return_value = MagicMock(scalar=MagicMock(return_value=None))
        pb = _make_playbook()
        mock_playbook_repo.create.return_value = pb

        result = await service.create_playbook(
            name="restart-stack", steps='[{"script_id":"script-001"}]'
        )
        assert result.name == "restart-stack"

    async def test_create_playbook_duplicate(self, service, mock_session):
        mock_session.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=_make_playbook())
        )

        from app.common.exceptions import DuplicateError
        with pytest.raises(DuplicateError, match="已存在"):
            await service.create_playbook(name="restart-stack", steps="[]")

    async def test_get_playbook(self, service, mock_playbook_repo):
        pb = _make_playbook()
        mock_playbook_repo.get_by_id.return_value = pb

        result = await service.get_playbook("pb-001")
        assert result.name == "restart-stack"

    async def test_get_playbook_not_found(self, service, mock_playbook_repo):
        mock_playbook_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError, match="不存在"):
            await service.get_playbook("nonexistent")

    async def test_update_playbook(self, service, mock_playbook_repo):
        pb = _make_playbook()
        mock_playbook_repo.get_by_id.return_value = pb

        await service.update_playbook("pb-001", description="updated")
        assert pb.description == "updated"

    async def test_delete_playbook(self, service, mock_playbook_repo):
        pb = _make_playbook()
        mock_playbook_repo.get_by_id.return_value = pb

        await service.delete_playbook("pb-001")
        service.session.delete.assert_called_once_with(pb)


# ---------------------------------------------------------------------------
# Test: create_execution / dry-run / status transitions
# ---------------------------------------------------------------------------

class TestExecutionCreate:
    async def test_create_execution_script(self, service, mock_script_repo, mock_exec_repo):
        script = _make_script()
        mock_script_repo.get_by_id.return_value = script
        mock_exec_repo.create.return_value = _make_execution()

        data = ExecutionCreate(
            execution_type="script",
            target_id="script-001",
            asset_ids=["asset-001"],
        )
        with patch.object(service, "_check_concurrent_lock", return_value=False):
            result = await service.create_execution(data)
        assert result is not None

    async def test_create_execution_dry_run(self, service, mock_script_repo, mock_exec_repo):
        script = _make_script()
        mock_script_repo.get_by_id.return_value = script
        mock_exec_repo.create.return_value = _make_execution(status="dry_run", is_dry_run=True)

        data = ExecutionCreate(
            execution_type="script",
            target_id="script-001",
            asset_ids=["asset-001"],
            is_dry_run=True,
        )
        # dry_run skips concurrent lock check
        result = await service.create_execution(data)

        # Verify dry_run status was passed
        call_kwargs = mock_exec_repo.create.call_args.kwargs
        assert call_kwargs["status"] == "dry_run"
        assert call_kwargs["is_dry_run"] is True

    async def test_create_execution_high_risk_needs_approval(
        self, service, mock_script_repo, mock_exec_repo
    ):
        script = _make_script(risk_level="high")
        mock_script_repo.get_by_id.return_value = script
        mock_exec_repo.create.return_value = _make_execution(status="awaiting_approval")

        data = ExecutionCreate(
            execution_type="script",
            target_id="script-001",
            asset_ids=["asset-001"],
        )
        with patch.object(service, "_check_concurrent_lock", return_value=False):
            result = await service.create_execution(data)

        call_kwargs = mock_exec_repo.create.call_args.kwargs
        assert call_kwargs["status"] == "awaiting_approval"

    async def test_create_execution_blocked_script(
        self, service, mock_script_repo, mock_exec_repo
    ):
        script = _make_script(is_blocked=True)
        mock_script_repo.get_by_id.return_value = script

        data = ExecutionCreate(
            execution_type="script",
            target_id="script-001",
            asset_ids=["asset-001"],
        )

        with pytest.raises(ValueError, match="已被阻断"):
            await service.create_execution(data)

    async def test_create_execution_playbook(self, service, mock_playbook_repo, mock_exec_repo):
        pb = _make_playbook()
        mock_playbook_repo.get_by_id.return_value = pb
        mock_exec_repo.create.return_value = _make_execution(execution_type="playbook")

        data = ExecutionCreate(
            execution_type="playbook",
            target_id="pb-001",
            asset_ids=["asset-001"],
        )
        with patch.object(service, "_check_concurrent_lock", return_value=False):
            result = await service.create_execution(data)
        assert result is not None

    async def test_create_execution_concurrent_lock_blocked(
        self, service, mock_script_repo, mock_exec_repo
    ):
        script = _make_script()
        mock_script_repo.get_by_id.return_value = script

        data = ExecutionCreate(
            execution_type="script",
            target_id="script-001",
            asset_ids=["asset-001"],
        )
        with patch.object(service, "_check_concurrent_lock", return_value=True):
            with pytest.raises(ValueError, match="正在运行的执行任务"):
                await service.create_execution(data)


# ---------------------------------------------------------------------------
# Test: approve_execution
# ---------------------------------------------------------------------------

class TestApproveExecution:
    async def test_approve_success(self, service, mock_exec_repo):
        exe = _make_execution(status="awaiting_approval")
        mock_exec_repo.get_by_id.return_value = exe

        result = await service.approve_execution("exec-001", user_id="admin")
        assert exe.status == "approved"
        assert exe.approved_by == "admin"

    async def test_approve_not_found(self, service, mock_exec_repo):
        mock_exec_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError, match="不存在"):
            await service.approve_execution("nonexistent")

    async def test_approve_wrong_status(self, service, mock_exec_repo):
        exe = _make_execution(status="running")
        mock_exec_repo.get_by_id.return_value = exe

        with pytest.raises(ValueError, match="不允许审批"):
            await service.approve_execution("exec-001")


# ---------------------------------------------------------------------------
# Test: cancel_execution
# ---------------------------------------------------------------------------

class TestCancelExecution:
    async def test_cancel_pending(self, service, mock_exec_repo):
        exe = _make_execution(status="pending")
        mock_exec_repo.get_by_id.return_value = exe

        result = await service.cancel_execution("exec-001")
        assert exe.status == "cancelled"
        assert exe.completed_at is not None

    async def test_cancel_running(self, service, mock_exec_repo):
        exe = _make_execution(status="running")
        mock_exec_repo.get_by_id.return_value = exe

        result = await service.cancel_execution("exec-001")
        assert exe.status == "cancelled"

    async def test_cancel_wrong_status(self, service, mock_exec_repo):
        exe = _make_execution(status="completed")
        mock_exec_repo.get_by_id.return_value = exe

        with pytest.raises(ValueError, match="不允许取消"):
            await service.cancel_execution("exec-001")

    async def test_cancel_not_found(self, service, mock_exec_repo):
        mock_exec_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError, match="不存在"):
            await service.cancel_execution("nonexistent")


# ---------------------------------------------------------------------------
# Test: rollback_execution
# ---------------------------------------------------------------------------

class TestRollbackExecution:
    async def test_rollback_completed(self, service, mock_exec_repo):
        exe = _make_execution(status="completed")
        mock_exec_repo.get_by_id.return_value = exe

        result = await service.rollback_execution("exec-001")
        assert exe.status == "rolled_back"

    async def test_rollback_failed(self, service, mock_exec_repo):
        exe = _make_execution(status="failed")
        mock_exec_repo.get_by_id.return_value = exe

        result = await service.rollback_execution("exec-001")
        assert exe.status == "rolled_back"

    async def test_rollback_wrong_status(self, service, mock_exec_repo):
        exe = _make_execution(status="running")
        mock_exec_repo.get_by_id.return_value = exe

        with pytest.raises(ValueError, match="只能回滚已完成或失败的执行"):
            await service.rollback_execution("exec-001")


# ---------------------------------------------------------------------------
# Test: concurrent lock
# ---------------------------------------------------------------------------

class TestConcurrentLock:
    async def test_no_concurrent_lock(self, service, mock_session):
        mock_session.execute.return_value = MagicMock(
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        )

        result = await service._check_concurrent_lock(["asset-001"])
        assert result is False

    async def test_concurrent_lock_detected(self, service, mock_session):
        running_exe = _make_execution(
            status="running",
            asset_ids=["asset-001", "asset-002"],
        )
        # Asset IDs in Execution model are stored as JSON string
        # But the code checks isinstance(asset_ids, list)
        running_exe.asset_ids = ["asset-001", "asset-002"]
        mock_session.execute.return_value = MagicMock(
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[running_exe])))
        )

        result = await service._check_concurrent_lock(["asset-001"])
        assert result is True

    async def test_no_lock_different_assets(self, service, mock_session):
        running_exe = _make_execution(status="running")
        running_exe.asset_ids = ["asset-999"]
        mock_session.execute.return_value = MagicMock(
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[running_exe])))
        )

        result = await service._check_concurrent_lock(["asset-001"])
        assert result is False


# ---------------------------------------------------------------------------
# Test: list executions
# ---------------------------------------------------------------------------

class TestListExecutions:
    async def test_list_default(self, service, mock_session):
        mock_session.execute.side_effect = [
            MagicMock(scalar=MagicMock(return_value=1)),
            MagicMock(scalars=MagicMock(return_value=MagicMock(
                all=MagicMock(return_value=[_make_execution()])
            ))),
        ]

        items, total = await service.list_executions()
        assert total == 1

    async def test_list_with_status_filter(self, service, mock_session):
        mock_session.execute.side_effect = [
            MagicMock(scalar=MagicMock(return_value=0)),
            MagicMock(scalars=MagicMock(return_value=MagicMock(
                all=MagicMock(return_value=[])
            ))),
        ]

        items, total = await service.list_executions(status="completed")
        assert total == 0
