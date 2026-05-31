"""配置中心 Service 单元测试."""
import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.common.exceptions import DuplicateError, NotFoundError
from app.domains.config.models import (
    ConfigBinding, ConfigDefinition, ConfigVersion, Credential, CredentialBinding,
)
from app.domains.config.service import ConfigService


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
    session.get = AsyncMock()
    return session


@pytest.fixture
def mock_def_repo():
    repo = AsyncMock()
    repo.create = AsyncMock()
    repo.get_by_id = AsyncMock()
    return repo


@pytest.fixture
def mock_ver_repo():
    repo = AsyncMock()
    repo.create = AsyncMock()
    repo.get_by_id = AsyncMock()
    return repo


@pytest.fixture
def mock_bind_repo():
    repo = AsyncMock()
    repo.create = AsyncMock()
    return repo


@pytest.fixture
def mock_cred_repo():
    repo = AsyncMock()
    repo.create = AsyncMock()
    repo.get_by_id = AsyncMock()
    return repo


@pytest.fixture
def mock_cred_bind_repo():
    repo = AsyncMock()
    repo.create = AsyncMock()
    return repo


@pytest.fixture
def service(mock_session, mock_def_repo, mock_ver_repo, mock_bind_repo,
            mock_cred_repo, mock_cred_bind_repo):
    with patch("app.domains.config.service.BaseRepository") as BR:
        def make_repo(sess, model):
            if model is ConfigDefinition:
                return mock_def_repo
            if model is ConfigVersion:
                return mock_ver_repo
            if model is ConfigBinding:
                return mock_bind_repo
            if model is Credential:
                return mock_cred_repo
            if model is CredentialBinding:
                return mock_cred_bind_repo
            return AsyncMock()
        BR.side_effect = make_repo
        svc = ConfigService(mock_session)
    svc._def_repo = mock_def_repo
    svc._ver_repo = mock_ver_repo
    svc._bind_repo = mock_bind_repo
    svc._cred_repo = mock_cred_repo
    svc._cred_bind_repo = mock_cred_bind_repo
    return svc


def _make_definition(**overrides) -> ConfigDefinition:
    defaults = dict(
        id="def-001",
        name="collector-config",
        config_type="collector_template",
        description="Test config",
        schema_def=None,
        is_deleted=False,
    )
    defaults.update(overrides)
    d = MagicMock(spec=ConfigDefinition)
    for k, v in defaults.items():
        setattr(d, k, v)
    return d


def _make_version(**overrides) -> ConfigVersion:
    defaults = dict(
        id="ver-001",
        definition_id="def-001",
        version=1,
        content='{"key": "value"}',
        status="draft",
        published_by=None,
        published_at=None,
    )
    defaults.update(overrides)
    v = MagicMock(spec=ConfigVersion)
    for k, v_ in defaults.items():
        setattr(v, k, v_)
    return v


# ---------------------------------------------------------------------------
# Test: ConfigDefinition CRUD
# ---------------------------------------------------------------------------

class TestConfigDefinitionCRUD:
    async def test_create_definition(self, service, mock_def_repo, mock_session):
        mock_session.execute.return_value = MagicMock(scalar=MagicMock(return_value=None))
        defn = _make_definition()
        mock_def_repo.create.return_value = defn

        result = await service.create_definition(
            name="collector-config", config_type="collector_template"
        )
        assert result.name == "collector-config"

    async def test_create_definition_duplicate(self, service, mock_session):
        mock_session.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=_make_definition())
        )

        with pytest.raises(DuplicateError, match="已存在"):
            await service.create_definition(
                name="collector-config", config_type="collector_template"
            )

    async def test_get_definition(self, service, mock_def_repo):
        defn = _make_definition()
        mock_def_repo.get_by_id.return_value = defn

        result = await service.get_definition("def-001")
        assert result.name == "collector-config"

    async def test_get_definition_not_found(self, service, mock_def_repo):
        mock_def_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError, match="不存在"):
            await service.get_definition("nonexistent")

    async def test_get_definition_deleted(self, service, mock_def_repo):
        defn = _make_definition(is_deleted=True)
        mock_def_repo.get_by_id.return_value = defn

        with pytest.raises(NotFoundError, match="不存在"):
            await service.get_definition("def-001")

    async def test_list_definitions(self, service, mock_session):
        mock_session.execute.side_effect = [
            MagicMock(scalar=MagicMock(return_value=1)),  # count
            MagicMock(scalars=MagicMock(return_value=MagicMock(
                all=MagicMock(return_value=[_make_definition()])
            ))),
        ]

        items, total = await service.list_definitions()
        assert total == 1
        assert len(items) == 1


# ---------------------------------------------------------------------------
# Test: ConfigVersion
# ---------------------------------------------------------------------------

class TestConfigVersion:
    async def test_create_version(self, service, mock_def_repo, mock_ver_repo, mock_session):
        mock_def_repo.get_by_id.return_value = _make_definition()
        # max version query returns 0 (no existing versions)
        mock_session.execute.return_value = MagicMock(scalar=MagicMock(return_value=None))
        ver = _make_version()
        mock_ver_repo.create.return_value = ver

        result = await service.create_version("def-001", content='{"key":"value"}')
        assert result is not None

        # Verify version number is max+1
        call_kwargs = mock_ver_repo.create.call_args.kwargs
        assert call_kwargs["version"] == 1

    async def test_create_version_increments(self, service, mock_def_repo, mock_ver_repo, mock_session):
        mock_def_repo.get_by_id.return_value = _make_definition()
        # max version = 3
        mock_session.execute.return_value = MagicMock(scalar=MagicMock(return_value=3))
        ver = _make_version(version=4)
        mock_ver_repo.create.return_value = ver

        result = await service.create_version("def-001", content='{"key":"v4"}')
        call_kwargs = mock_ver_repo.create.call_args.kwargs
        assert call_kwargs["version"] == 4

    async def test_publish_version(self, service, mock_ver_repo, mock_session):
        ver = _make_version()
        mock_ver_repo.get_by_id.return_value = ver
        # No previously published versions
        mock_session.execute.return_value = MagicMock(
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        )

        result = await service.publish_version("ver-001", user_id="admin")
        assert ver.status == "published"
        assert ver.published_by == "admin"

    async def test_publish_version_archives_old(self, service, mock_ver_repo, mock_session):
        ver = _make_version()
        mock_ver_repo.get_by_id.return_value = ver
        old_published = _make_version(id="ver-old", status="published")
        mock_session.execute.return_value = MagicMock(
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[old_published])))
        )

        result = await service.publish_version("ver-001")
        assert old_published.status == "archived"
        assert ver.status == "published"

    async def test_publish_version_not_found(self, service, mock_ver_repo):
        mock_ver_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError, match="不存在"):
            await service.publish_version("nonexistent")

    async def test_list_versions(self, service, mock_session):
        mock_session.execute.return_value = MagicMock(
            scalars=MagicMock(return_value=MagicMock(
                all=MagicMock(return_value=[_make_version()])
            ))
        )

        versions = await service.list_versions("def-001")
        assert len(versions) == 1


# ---------------------------------------------------------------------------
# Test: diff_versions
# ---------------------------------------------------------------------------

class TestDiffVersions:
    async def test_diff_with_changes(self, service, mock_session):
        va = _make_version(id="ver-a", version=1, content='{"key": "old"}')
        vb = _make_version(id="ver-b", version=2, content='{"key": "new"}')

        def mock_get(model, pk):
            if pk == "ver-a":
                return va
            if pk == "ver-b":
                return vb
            return None

        mock_session.get.side_effect = mock_get

        result = await service.diff_versions("def-001", "ver-a", "ver-b")
        assert result["has_changes"] is True
        assert result["version_a"]["version"] == 1
        assert result["version_b"]["version"] == 2
        assert len(result["diff"]) > 0

    async def test_diff_no_changes(self, service, mock_session):
        va = _make_version(id="ver-a", version=1, content='{"key": "same"}')
        vb = _make_version(id="ver-b", version=2, content='{"key": "same"}')

        def mock_get(model, pk):
            if pk == "ver-a":
                return va
            if pk == "ver-b":
                return vb
            return None

        mock_session.get.side_effect = mock_get

        result = await service.diff_versions("def-001", "ver-a", "ver-b")
        assert result["has_changes"] is False

    async def test_diff_version_not_found(self, service, mock_session):
        mock_session.get.return_value = None

        with pytest.raises(NotFoundError, match="不存在"):
            await service.diff_versions("def-001", "ver-a", "ver-b")


# ---------------------------------------------------------------------------
# Test: rollback_version
# ---------------------------------------------------------------------------

class TestRollbackVersion:
    async def test_rollback_success(self, service, mock_session):
        target = _make_version(id="ver-001", version=1, content='{"key":"original"}')
        # First call: session.get for target version
        # Second call: session.execute for max version
        mock_session.get.return_value = target
        mock_session.execute.return_value = MagicMock(scalar=MagicMock(return_value=3))

        result = await service.rollback_version("def-001", "ver-001")
        mock_session.add.assert_called_once()

    async def test_rollback_version_not_found(self, service, mock_session):
        mock_session.get.return_value = None

        with pytest.raises(NotFoundError, match="不存在"):
            await service.rollback_version("def-001", "nonexistent")

    async def test_rollback_wrong_definition(self, service, mock_session):
        target = _make_version(definition_id="other-def")
        # str(target.definition_id) != definition_id
        mock_session.get.return_value = target

        with pytest.raises(NotFoundError, match="不属于该配置定义"):
            await service.rollback_version("def-001", "ver-001")


# ---------------------------------------------------------------------------
# Test: detect_drift
# ---------------------------------------------------------------------------

class TestDetectDrift:
    async def test_no_drift(self, service, mock_session):
        latest = _make_version(id="ver-latest", version=2)
        # First execute: get latest published version
        # Second execute: get bindings
        mock_session.execute.side_effect = [
            MagicMock(scalar_one_or_none=MagicMock(return_value=latest)),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))),
        ]

        result = await service.detect_drift("def-001")
        assert result["has_drift"] is False

    async def test_drift_detected(self, service, mock_session):
        latest = _make_version(id="ver-latest", version=2)
        binding = MagicMock(spec=ConfigBinding)
        binding.id = "bind-001"
        binding.version_id = "ver-old"  # Not the latest
        binding.target_type = "asset"
        binding.target_id = "asset-001"

        mock_session.execute.side_effect = [
            MagicMock(scalar_one_or_none=MagicMock(return_value=latest)),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[binding])))),
        ]

        result = await service.detect_drift("def-001")
        assert result["has_drift"] is True
        assert len(result["drifted_bindings"]) == 1

    async def test_no_published_version(self, service, mock_session):
        mock_session.execute.side_effect = [
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),
        ]

        result = await service.detect_drift("def-001")
        assert result["has_drift"] is False
        assert "无已发布版本" in result["message"]


# ---------------------------------------------------------------------------
# Test: Credential
# ---------------------------------------------------------------------------

class TestCredential:
    async def test_create_credential(self, service, mock_cred_repo, mock_session):
        mock_session.execute.return_value = MagicMock(scalar=MagicMock(return_value=None))
        cred = MagicMock(spec=Credential)
        mock_cred_repo.create.return_value = cred

        with patch("app.domains.config.service.encrypt_credential", return_value="encrypted"):
            result = await service.create_credential(
                name="ssh-key", cred_type="ssh_key", data="private-key-data"
            )
        mock_cred_repo.create.assert_called_once()

    async def test_create_credential_duplicate(self, service, mock_session):
        mock_session.execute.return_value = MagicMock(
            scalar=MagicMock(return_value=MagicMock(spec=Credential))
        )

        with pytest.raises(DuplicateError, match="已存在"):
            await service.create_credential(
                name="ssh-key", cred_type="ssh_key", data="data"
            )

    async def test_get_credential(self, service, mock_cred_repo):
        cred = MagicMock(spec=Credential)
        cred.is_deleted = False
        mock_cred_repo.get_by_id.return_value = cred

        result = await service.get_credential("cred-001")
        assert result is cred

    async def test_get_credential_not_found(self, service, mock_cred_repo):
        mock_cred_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError, match="不存在"):
            await service.get_credential("nonexistent")

    async def test_get_credential_deleted(self, service, mock_cred_repo):
        cred = MagicMock(spec=Credential)
        cred.is_deleted = True
        mock_cred_repo.get_by_id.return_value = cred

        with pytest.raises(NotFoundError, match="不存在"):
            await service.get_credential("cred-001")

    async def test_bind_credential(self, service, mock_cred_bind_repo):
        binding = MagicMock(spec=CredentialBinding)
        mock_cred_bind_repo.create.return_value = binding

        result = await service.bind_credential("cred-001", "asset-001")
        mock_cred_bind_repo.create.assert_called_once_with(
            credential_id="cred-001", asset_id="asset-001"
        )
