"""资产中心 Service 单元测试."""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.common.exceptions import DuplicateError, NotFoundError
from app.domains.asset.models import (
    Asset, AssetGroup, AssetRelation, AssetTimeline,
)
from app.domains.asset.schemas import (
    AssetCreate, AssetGroupCreate, AssetRelationCreate, AssetUpdate,
)
from app.domains.asset.service import AssetService


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
    session.delete = AsyncMock()
    return session


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    repo.create = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.get_by_id_or_raise = AsyncMock()
    repo.get_by_name = AsyncMock(return_value=None)
    repo.get_by_ip = AsyncMock(return_value=None)
    repo.soft_delete = AsyncMock()
    repo.search = AsyncMock(return_value=([], 0))
    return repo


@pytest.fixture
def mock_group_repo():
    repo = AsyncMock()
    repo.create = AsyncMock()
    repo.get_by_id_or_raise = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.get_multi = AsyncMock(return_value=([], 0))
    return repo


@pytest.fixture
def mock_relation_repo():
    repo = AsyncMock()
    repo.create = AsyncMock()
    repo.get_by_asset = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def mock_timeline_repo():
    repo = AsyncMock()
    repo.create = AsyncMock()
    repo.get_by_asset = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def service(mock_session, mock_repo, mock_group_repo, mock_relation_repo, mock_timeline_repo):
    with patch("app.domains.asset.service.AssetRepository", return_value=mock_repo), \
         patch("app.domains.asset.service.AssetGroupRepository", return_value=mock_group_repo), \
         patch("app.domains.asset.service.AssetRelationRepository", return_value=mock_relation_repo), \
         patch("app.domains.asset.service.AssetTimelineRepository", return_value=mock_timeline_repo):
        svc = AssetService(mock_session)
    # Store refs for easy access in tests
    svc._repo = mock_repo
    svc._group_repo = mock_group_repo
    svc._relation_repo = mock_relation_repo
    svc._timeline_repo = mock_timeline_repo
    return svc


def _make_asset(**overrides) -> Asset:
    defaults = dict(
        id="asset-001",
        name="test-server",
        asset_type="linux_server",
        ip="10.0.0.1",
        port=22,
        hostname="test-server",
        status="active",
        health_status="healthy",
        reachability="reachable",
        is_deleted=False,
    )
    defaults.update(overrides)
    a = MagicMock(spec=Asset)
    for k, v in defaults.items():
        setattr(a, k, v)
    return a


# ---------------------------------------------------------------------------
# Test: create_asset
# ---------------------------------------------------------------------------

class TestCreateAsset:
    async def test_create_success(self, service, mock_repo, mock_timeline_repo):
        asset = _make_asset()
        mock_repo.get_by_name.return_value = None
        mock_repo.get_by_ip.return_value = None
        mock_repo.create.return_value = asset

        data = AssetCreate(name="test-server", asset_type="linux_server", ip="10.0.0.1")
        result = await service.create_asset(data)

        assert result.name == "test-server"
        mock_repo.create.assert_called_once()
        mock_timeline_repo.create.assert_called_once()

    async def test_create_duplicate_name(self, service, mock_repo):
        mock_repo.get_by_name.return_value = _make_asset(name="test-server")

        data = AssetCreate(name="test-server", asset_type="linux_server")
        with pytest.raises(DuplicateError, match="已存在"):
            await service.create_asset(data)

    async def test_create_duplicate_ip(self, service, mock_repo):
        mock_repo.get_by_name.return_value = None
        mock_repo.get_by_ip.return_value = _make_asset(ip="10.0.0.1")

        data = AssetCreate(name="new-server", asset_type="linux_server", ip="10.0.0.1")
        with pytest.raises(DuplicateError, match="已被占用"):
            await service.create_asset(data)

    async def test_create_with_tags(self, service, mock_repo, mock_timeline_repo):
        asset = _make_asset()
        mock_repo.get_by_name.return_value = None
        mock_repo.get_by_ip.return_value = None
        mock_repo.create.return_value = asset

        data = AssetCreate(name="tagged", asset_type="database", tags=["prod", "mysql"])
        result = await service.create_asset(data)

        assert result is not None
        # Verify tags were serialized to JSON
        call_kwargs = mock_repo.create.call_args
        assert call_kwargs.kwargs.get("tags") == json.dumps(["prod", "mysql"])


# ---------------------------------------------------------------------------
# Test: get_asset
# ---------------------------------------------------------------------------

class TestGetAsset:
    async def test_get_existing(self, service, mock_repo):
        asset = _make_asset()
        mock_repo.get_by_id_or_raise.return_value = asset

        result = await service.get_asset("asset-001")
        assert result.name == "test-server"

    async def test_get_not_found(self, service, mock_repo):
        mock_repo.get_by_id_or_raise.side_effect = NotFoundError("不存在")

        with pytest.raises(NotFoundError):
            await service.get_asset("nonexistent")


# ---------------------------------------------------------------------------
# Test: update_asset
# ---------------------------------------------------------------------------

class TestUpdateAsset:
    async def test_update_fields(self, service, mock_repo, mock_timeline_repo):
        asset = _make_asset()
        mock_repo.get_by_id_or_raise.return_value = asset

        data = AssetUpdate(hostname="new-hostname", description="updated")
        result = await service.update_asset("asset-001", data)

        assert result is asset
        mock_timeline_repo.create.assert_called_once()

    async def test_update_with_tags(self, service, mock_repo, mock_timeline_repo):
        asset = _make_asset()
        mock_repo.get_by_id_or_raise.return_value = asset

        data = AssetUpdate(tags=["new-tag"])
        result = await service.update_asset("asset-001", data)

        # Verify tags were serialized to JSON
        assert hasattr(asset, "tags")


# ---------------------------------------------------------------------------
# Test: delete_asset
# ---------------------------------------------------------------------------

class TestDeleteAsset:
    async def test_delete(self, service, mock_repo):
        await service.delete_asset("asset-001")
        mock_repo.soft_delete.assert_called_once_with("asset-001")


# ---------------------------------------------------------------------------
# Test: list_assets
# ---------------------------------------------------------------------------

class TestListAssets:
    async def test_list_default(self, service, mock_repo):
        assets = [_make_asset(), _make_asset(id="asset-002", name="server-2")]
        mock_repo.search.return_value = (assets, 2)

        items, total = await service.list_assets()
        assert total == 2
        assert len(items) == 2

    async def test_list_with_filters(self, service, mock_repo):
        mock_repo.search.return_value = ([_make_asset()], 1)

        items, total = await service.list_assets(asset_type="linux_server", status="active")
        mock_repo.search.assert_called_once_with(asset_type="linux_server", status="active")


# ---------------------------------------------------------------------------
# Test: import_assets
# ---------------------------------------------------------------------------

class TestImportAssets:
    async def test_import_multiple(self, service, mock_repo, mock_timeline_repo):
        from app.domains.asset.schemas import AssetImportItem
        mock_repo.get_by_name.return_value = None
        mock_repo.get_by_ip.return_value = None
        a1 = _make_asset(name="s1")
        a2 = _make_asset(id="a2", name="s2")
        mock_repo.create.side_effect = [a1, a2]

        items = [
            AssetImportItem(name="s1", asset_type="linux_server"),
            AssetImportItem(name="s2", asset_type="windows_server"),
        ]
        result = await service.import_assets(items)
        assert len(result) == 2

    async def test_import_skips_duplicates(self, service, mock_repo, mock_timeline_repo):
        from app.domains.asset.schemas import AssetImportItem
        mock_repo.get_by_name.return_value = _make_asset()
        mock_repo.create.return_value = _make_asset()

        items = [
            AssetImportItem(name="dup", asset_type="linux_server"),
            AssetImportItem(name="dup2", asset_type="linux_server"),
        ]
        result = await service.import_assets(items)
        # Both get_by_name returns existing, so create_asset raises DuplicateError
        assert len(result) == 0


# ---------------------------------------------------------------------------
# Test: relations
# ---------------------------------------------------------------------------

class TestAssetRelations:
    async def test_add_relation(self, service, mock_repo, mock_relation_repo):
        source = _make_asset()
        target = _make_asset(id="asset-002", name="target")
        mock_repo.get_by_id_or_raise.side_effect = [source, target]

        rel = MagicMock(spec=AssetRelation)
        mock_relation_repo.create.return_value = rel

        data = AssetRelationCreate(target_asset_id="asset-002", relation_type="depends_on")
        result = await service.add_relation("asset-001", data)

        assert result is rel
        mock_relation_repo.create.assert_called_once()

    async def test_get_relations(self, service, mock_repo, mock_relation_repo):
        mock_repo.get_by_id_or_raise.return_value = _make_asset()
        rels = [MagicMock(spec=AssetRelation)]
        mock_relation_repo.get_by_asset.return_value = rels

        result = await service.get_relations("asset-001")
        assert len(result) == 1

    async def test_delete_relation_not_found(self, service, mock_session):
        mock_session.get.return_value = None

        with pytest.raises(NotFoundError, match="不存在"):
            await service.delete_relation("asset-001", "rel-nonexistent")

    async def test_delete_relation_success(self, service, mock_session):
        rel = MagicMock(spec=AssetRelation)
        mock_session.get.return_value = rel

        await service.delete_relation("asset-001", "rel-001")
        mock_session.delete.assert_called_once_with(rel)


# ---------------------------------------------------------------------------
# Test: timeline
# ---------------------------------------------------------------------------

class TestAssetTimeline:
    async def test_get_timeline(self, service, mock_repo, mock_timeline_repo):
        mock_repo.get_by_id_or_raise.return_value = _make_asset()
        timeline = [MagicMock(spec=AssetTimeline)]
        mock_timeline_repo.get_by_asset.return_value = timeline

        result = await service.get_timeline("asset-001", limit=10)
        assert len(result) == 1
        mock_timeline_repo.get_by_asset.assert_called_once_with("asset-001", 10)


# ---------------------------------------------------------------------------
# Test: groups
# ---------------------------------------------------------------------------

class TestAssetGroups:
    async def test_create_group(self, service, mock_group_repo):
        group = MagicMock(spec=AssetGroup)
        mock_group_repo.create.return_value = group

        data = AssetGroupCreate(name="group-1", description="test group")
        result = await service.create_group(data)
        assert result is group

    async def test_list_groups(self, service, mock_group_repo):
        mock_group_repo.get_multi.return_value = ([MagicMock(spec=AssetGroup)], 1)

        items, total = await service.list_groups()
        assert total == 1

    async def test_add_group_member(self, service, mock_repo, mock_group_repo, mock_session):
        group = MagicMock(spec=AssetGroup)
        mock_group_repo.get_by_id_or_raise.return_value = group
        mock_repo.get_by_id_or_raise.return_value = _make_asset()

        await service.add_group_member("group-1", "asset-001")
        mock_session.add.assert_called_once()

    async def test_get_group_not_found(self, service, mock_group_repo):
        mock_group_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError, match="不存在"):
            await service.get_group("nonexistent")

    async def test_get_group_found(self, service, mock_group_repo):
        group = MagicMock(spec=AssetGroup)
        mock_group_repo.get_by_id.return_value = group

        result = await service.get_group("group-1")
        assert result is group


# ---------------------------------------------------------------------------
# Test: trigger_collection
# ---------------------------------------------------------------------------

class TestTriggerCollection:
    async def test_trigger(self, service, mock_repo):
        mock_repo.get_by_id_or_raise.return_value = _make_asset()

        result = await service.trigger_collection("asset-001")
        assert result["status"] == "triggered"
        assert result["asset_id"] == "asset-001"
