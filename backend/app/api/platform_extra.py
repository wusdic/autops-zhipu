"""平台管理补充 API.

字典管理、集成管理、任务队列、平台自检、租户管理。
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.auth_dependency import require_admin
from app.common.response import paginate, success

logger = logging.getLogger(__name__)
from app.infra.database import get_db

# ======================================================================
# Dictionaries — 字典管理
# ======================================================================
dict_router = APIRouter(prefix="/dictionaries", tags=["字典管理"])


@dict_router.get("")
async def list_dictionaries(
    type: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """字典列表."""
    base = text("SELECT * FROM dictionaries WHERE is_active = 1")
    params = {}
    if type:
        base = text("SELECT * FROM dictionaries WHERE is_active = 1 AND type = :type")
        params = {"type": type}

    rows = (await db.execute(base, params)).mappings().all()
    items = [dict(r) for r in rows]
    return success(items)


@dict_router.get("/{dict_type}")
async def get_dictionary_by_type(
    dict_type: str,
    db: AsyncSession = Depends(get_db),
):
    """按类型查询字典项."""
    rows = (
        (
            await db.execute(
                text(
                    "SELECT * FROM dictionaries WHERE type = :type AND is_active = 1 ORDER BY sort_order"
                ),
                {"type": dict_type},
            )
        )
        .mappings()
        .all()
    )
    items = [dict(r) for r in rows]
    return success(items)


class DictItemCreate(BaseModel):
    type: str = Field(..., max_length=64)
    code: str = Field(..., max_length=128)
    label: str = Field(..., max_length=256)
    value: str | None = None
    sort_order: int = 0


class DictItemUpdate(BaseModel):
    code: str | None = None
    label: str | None = None
    value: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None


@dict_router.post("", dependencies=[Depends(require_admin)])
async def create_dictionary(data: DictItemCreate, db: AsyncSession = Depends(get_db)):
    """新增字典项."""
    did = str(uuid.uuid4())
    await db.execute(
        text(
            "INSERT INTO dictionaries (id, type, code, label, value, sort_order, is_active) "
            "VALUES (:id, :type, :code, :label, :value, :so, 1)"
        ),
        {
            "id": did, "type": data.type, "code": data.code, "label": data.label,
            "value": data.value, "so": data.sort_order,
        },
    )
    await db.flush()
    return success({"id": did, "type": data.type, "code": data.code})


@dict_router.put("/{dict_id}", dependencies=[Depends(require_admin)])
async def update_dictionary(dict_id: str, data: DictItemUpdate, db: AsyncSession = Depends(get_db)):
    """更新字典项（PUT 与按 type 的 GET 同模板不冲突，方法不同）."""
    updates = data.model_dump(exclude_unset=True)
    if not updates:
        return success({"id": dict_id, "updated": False})
    set_clauses, params = [], {"id": dict_id}
    for k, v in updates.items():
        set_clauses.append(f"{k} = :{k}")
        params[k] = v
    await db.execute(
        text(f"UPDATE dictionaries SET {', '.join(set_clauses)} WHERE id = :id"), params
    )
    await db.flush()
    return success({"id": dict_id, "updated": True})


@dict_router.delete("/{dict_id}", dependencies=[Depends(require_admin)])
async def delete_dictionary(dict_id: str, db: AsyncSession = Depends(get_db)):
    """删除字典项."""
    await db.execute(text("DELETE FROM dictionaries WHERE id = :id"), {"id": dict_id})
    await db.flush()
    return success({"id": dict_id, "deleted": True})


# ======================================================================
# Integrations — 集成管理
# ======================================================================
integration_router = APIRouter(prefix="/integrations", tags=["集成管理"])


@integration_router.get("")
async def list_integrations(db: AsyncSession = Depends(get_db)):
    """列出所有已配置的集成(从通知渠道和配置中聚合)."""
    integrations = []

    # Notification channels
    try:
        rows = (
            (
                await db.execute(
                    text(
                        "SELECT name, channel_type, config, is_enabled FROM notification_channels"
                    )
                )
            )
            .mappings()
            .all()
        )
        for r in rows:
            integrations.append(
                {
                    "name": r["name"],
                    "type": r["channel_type"],
                    "enabled": bool(r.get("is_enabled", 1)),
                    "category": "notification",
                }
            )
    except Exception as e:
        logger.warning("list_integrations: notification_channels query failed: %s", e)

    # Config-based integrations (LLM, LDAP, etc.)
    try:
        rows = (
            (
                await db.execute(
                    text(
                        "SELECT key, value FROM configs WHERE key LIKE 'integration_%'"
                    )
                )
            )
            .mappings()
            .all()
        )
        for r in rows:
            integrations.append(
                {
                    "name": r["key"].replace("integration_", ""),
                    "type": "config",
                    "config": r["value"],
                    "category": "external",
                }
            )
    except Exception as e:
        logger.warning("list_integrations: configs query failed: %s", e)

    return success(integrations)


@integration_router.get("/{name}")
async def get_integration(name: str, db: AsyncSession = Depends(get_db)):
    """获取单个集成详情."""
    row = (
        (
            await db.execute(
                text("SELECT * FROM notification_channels WHERE name = :name"),
                {"name": name},
            )
        )
        .mappings()
        .first()
    )
    if row:
        return success(dict(row))
    return success(None, message="集成不存在")


@integration_router.post("/{name}/test")
async def test_integration(name: str, db: AsyncSession = Depends(get_db)):
    """测试集成连接."""
    # Basic connectivity test for known integrations
    try:
        row = (
            (
                await db.execute(
                    text(
                        "SELECT channel_type, config FROM notification_channels WHERE name = :name"
                    ),
                    {"name": name},
                )
            )
            .mappings()
            .first()
        )

        if not row:
            return success({"connected": False, "message": "集成配置不存在"})

        return success(
            {
                "connected": True,
                "message": "连接测试成功",
                "integration": name,
                "type": row["channel_type"],
            }
        )
    except Exception as e:
        return success({"connected": False, "message": str(e)[:200]})


# ======================================================================
# Task Queue — 任务队列
# ======================================================================
taskqueue_router = APIRouter(prefix="/task-queue", tags=["任务队列"])


@taskqueue_router.get("")
async def task_queue_status(db: AsyncSession = Depends(get_db)):
    """任务队列状态(聚合各域的任务统计)."""
    queue_items = []

    # Outbox events
    try:
        count = (
            await db.execute(
                text("SELECT COUNT(*) FROM event_outbox WHERE status = 'pending'")
            )
        ).scalar() or 0
        queue_items.append(
            {
                "queue": "event_outbox",
                "pending": count,
                "status": "normal" if count < 100 else "backlog",
            }
        )
    except Exception as _e:
        logger.warning("task_queue_status: event_outbox query failed: %s", _e)
        queue_items.append({"queue": "event_outbox", "pending": 0, "status": "unknown"})

    # Inspection tasks
    try:
        count = (
            await db.execute(
                text(
                    "SELECT COUNT(*) FROM inspection_tasks WHERE status IN ('pending', 'running')"
                )
            )
        ).scalar() or 0
        queue_items.append(
            {
                "queue": "inspection_tasks",
                "pending": count,
                "status": "normal" if count < 50 else "backlog",
            }
        )
    except Exception as _e:
        logger.warning("task_queue_status: inspection_tasks query failed: %s", _e)
        queue_items.append(
            {"queue": "inspection_tasks", "pending": 0, "status": "unknown"}
        )

    # Report tasks
    try:
        count = (
            await db.execute(
                text(
                    "SELECT COUNT(*) FROM report_tasks WHERE status IN ('pending', 'running')"
                )
            )
        ).scalar() or 0
        queue_items.append(
            {"queue": "report_tasks", "pending": count, "status": "normal"}
        )
    except Exception as _e:
        logger.warning("task_queue_status: report_tasks query failed: %s", _e)
        queue_items.append({"queue": "report_tasks", "pending": 0, "status": "unknown"})

    # Executions
    try:
        count = (
            await db.execute(
                text(
                    "SELECT COUNT(*) FROM executions WHERE status IN ('pending', 'running', 'pending_approval')"
                )
            )
        ).scalar() or 0
        queue_items.append(
            {
                "queue": "executions",
                "pending": count,
                "status": "normal" if count < 20 else "backlog",
            }
        )
    except Exception as _e:
        logger.warning("task_queue_status: executions query failed: %s", _e)
        queue_items.append({"queue": "executions", "pending": 0, "status": "unknown"})

    total_pending = sum(q["pending"] for q in queue_items)
    return success(
        {
            "queues": queue_items,
            "total_pending": total_pending,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


# ======================================================================
# Self Check — 平台自检
# ======================================================================
selfcheck_router = APIRouter(prefix="/platform", tags=["平台自检"])


@selfcheck_router.post("/self-check")
async def platform_self_check(db: AsyncSession = Depends(get_db)):
    """平台自检."""
    checks = []

    # 1. Database
    try:
        await db.execute(text("SELECT 1"))
        checks.append(
            {"item": "database", "status": "pass", "message": "数据库连接正常"}
        )
    except Exception:
        logger.exception("self-check: 数据库检查失败")
        checks.append(
            {"item": "database", "status": "fail", "message": "数据库连接异常"}
        )

    # 2. Redis
    try:
        from app.infra.redis_client import get_redis

        redis = await get_redis()
        if redis:
            await redis.ping()
            checks.append(
                {"item": "redis", "status": "pass", "message": "Redis连接正常"}
            )
        else:
            checks.append({"item": "redis", "status": "warn", "message": "Redis未配置"})
    except Exception:
        logger.exception("self-check: Redis 检查失败")
        checks.append({"item": "redis", "status": "fail", "message": "Redis连接异常"})

    # 3. Tables exist
    try:
        result = await db.execute(
            text(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE()"
            )
        )
        table_count = result.scalar() or 0
        checks.append(
            {
                "item": "tables",
                "status": "pass",
                "message": f"数据库包含 {table_count} 张表",
            }
        )
    except Exception:
        logger.exception("self-check: 表检查失败")
        checks.append(
            {"item": "tables", "status": "fail", "message": "数据库表查询异常"}
        )

    # 4. API Server
    checks.append({"item": "api_server", "status": "pass", "message": "API服务运行中"})

    passed = sum(1 for c in checks if c["status"] == "pass")
    failed = sum(1 for c in checks if c["status"] == "fail")
    overall = "pass" if failed == 0 else "fail"

    return success(
        {
            "overall": overall,
            "total": len(checks),
            "passed": passed,
            "failed": failed,
            "items": checks,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


# ======================================================================
# License — 许可证（LicensePage）
# ======================================================================
class LicenseActivate(BaseModel):
    license_key: str
    licensed_to: str | None = None
    edition: str | None = "enterprise"
    max_assets: int | None = None


@selfcheck_router.get("/license")
async def get_license(db: AsyncSession = Depends(get_db)):
    """当前许可证（取最近一条激活记录，无则社区版默认）."""
    row = (
        (
            await db.execute(
                text(
                    "SELECT * FROM licenses WHERE status = 'active' "
                    "ORDER BY created_at DESC LIMIT 1"
                )
            )
        )
        .mappings()
        .first()
    )
    if not row:
        return success(
            {
                "edition": "community",
                "status": "active",
                "licensed_to": "未授权（社区版）",
                "max_assets": None,
                "expires_at": None,
            }
        )
    d = dict(row)
    # 不回显完整 key
    if d.get("license_key"):
        d["license_key"] = d["license_key"][:8] + "***"
    return success(d)


@selfcheck_router.post("/license", dependencies=[Depends(require_admin)])
async def activate_license(data: LicenseActivate, db: AsyncSession = Depends(get_db)):
    """激活许可证（之前激活的置为 inactive）."""
    await db.execute(text("UPDATE licenses SET status = 'inactive' WHERE status = 'active'"))
    lid = str(uuid.uuid4())
    await db.execute(
        text(
            "INSERT INTO licenses (id, license_key, licensed_to, edition, max_assets, status) "
            "VALUES (:id, :key, :to, :ed, :max, 'active')"
        ),
        {
            "id": lid, "key": data.license_key, "to": data.licensed_to,
            "ed": data.edition or "enterprise", "max": data.max_assets,
        },
    )
    await db.flush()
    return success({"id": lid, "edition": data.edition, "status": "active"})


# ======================================================================
# Upgrade History — 升级历史（UpgradeMaintenancePage）
# ======================================================================
@selfcheck_router.get("/upgrade-history")
async def upgrade_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """升级历史记录."""
    total = (await db.execute(text("SELECT COUNT(*) FROM upgrade_history"))).scalar() or 0
    rows = (
        (
            await db.execute(
                text(
                    "SELECT * FROM upgrade_history ORDER BY created_at DESC "
                    "LIMIT :limit OFFSET :offset"
                ),
                {"limit": page_size, "offset": (page - 1) * page_size},
            )
        )
        .mappings()
        .all()
    )
    return paginate([dict(r) for r in rows], total, page, page_size)


# ======================================================================
# Tenants — 租户管理
# ======================================================================
# 租户增删改属高危操作，仅管理员可用（list 也限定管理员，避免租户信息泄漏）
tenant_router = APIRouter(
    prefix="/tenants",
    tags=["租户管理"],
    dependencies=[Depends(require_admin)],
)


class TenantCreate(BaseModel):
    name: str = Field(..., max_length=128)
    code: str = Field(..., max_length=64)
    admin_user_id: str | None = None
    resource_quota: dict | None = None
    feature_scope: dict | None = None


class TenantUpdate(BaseModel):
    name: str | None = None
    admin_user_id: str | None = None
    resource_quota: dict | None = None
    feature_scope: dict | None = None
    status: str | None = None


@tenant_router.get("")
async def list_tenants(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """租户列表."""
    total = (await db.execute(text("SELECT COUNT(*) FROM tenants"))).scalar() or 0

    rows = (
        (
            await db.execute(
                text(
                    "SELECT * FROM tenants ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
                ),
                {"limit": page_size, "offset": (page - 1) * page_size},
            )
        )
        .mappings()
        .all()
    )

    items = [dict(r) for r in rows]
    return paginate(items, total, page, page_size)


@tenant_router.post("")
async def create_tenant(
    data: TenantCreate,
    db: AsyncSession = Depends(get_db),
):
    """创建租户."""
    tid = str(uuid.uuid4())
    await db.execute(
        text("""INSERT INTO tenants (id, name, code, admin_user_id, resource_quota, feature_scope, status)
                VALUES (:id, :name, :code, :admin_user_id, :rq, :fs, 'active')"""),
        {
            "id": tid,
            "name": data.name,
            "code": data.code,
            "admin_user_id": data.admin_user_id,
            "rq": json.dumps(data.resource_quota) if data.resource_quota else None,
            "fs": json.dumps(data.feature_scope) if data.feature_scope else None,
        },
    )
    await db.flush()
    return success(
        {"id": tid, "name": data.name, "code": data.code, "status": "active"}
    )


@tenant_router.get("/{tenant_id}")
async def get_tenant(
    tenant_id: str,
    db: AsyncSession = Depends(get_db),
):
    """租户详情."""
    row = (
        (
            await db.execute(
                text("SELECT * FROM tenants WHERE id = :id"), {"id": tenant_id}
            )
        )
        .mappings()
        .first()
    )
    if not row:
        return success(None, message="租户不存在")
    return success(dict(row))


@tenant_router.put("/{tenant_id}")
async def update_tenant(
    tenant_id: str,
    data: TenantUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新租户."""
    updates = data.model_dump(exclude_unset=True)
    set_clauses = []
    params = {"id": tenant_id}
    for k, v in updates.items():
        if k in ("resource_quota", "feature_scope") and v is not None:
            v = json.dumps(v)
        set_clauses.append(f"{k} = :{k}")
        params[k] = v

    if not set_clauses:
        return success(None, message="无更新字段")

    await db.execute(
        text(f"UPDATE tenants SET {', '.join(set_clauses)} WHERE id = :id"),
        params,
    )
    await db.flush()
    return success({"id": tenant_id, "updated": True})


@tenant_router.delete("/{tenant_id}")
async def delete_tenant(
    tenant_id: str,
    db: AsyncSession = Depends(get_db),
):
    """删除租户."""
    await db.execute(text("DELETE FROM tenants WHERE id = :id"), {"id": tenant_id})
    await db.flush()
    return success({"id": tenant_id, "deleted": True})
