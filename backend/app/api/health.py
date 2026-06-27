"""健康检查路由."""

from __future__ import annotations

import logging

from fastapi import APIRouter
from sqlalchemy import text

from app.infra.database import get_session_factory
from app.infra.redis_client import get_redis

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


async def _check_db() -> bool:
    """检查数据库连通性，正确关闭会话避免连接泄漏."""
    session_factory = get_session_factory()
    try:
        async with session_factory() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception:
        logger.exception("健康检查：数据库连接失败")
        return False


@router.get("/health")
async def health():
    """存活检查."""
    return {"status": "alive"}


@router.get("/ready")
async def ready():
    """就绪检查：DB + Redis。

    对外只返回 ok/error 状态，不回显异常详情（避免泄漏内部拓扑）。
    """
    checks: dict[str, str] = {}

    checks["database"] = "ok" if await _check_db() else "error"

    try:
        redis = await get_redis()
        await redis.ping()
        checks["redis"] = "ok"
    except Exception:
        logger.exception("健康检查：Redis 连接失败")
        checks["redis"] = "error"

    all_ok = all(v == "ok" for v in checks.values())
    return {"status": "ready" if all_ok else "degraded", "checks": checks}


# Platform status (mounted under /api/v1/platform)
platform_router = APIRouter(prefix="/platform", tags=["平台管理"])


@platform_router.get("/status")
async def platform_status():
    """平台组件状态。

    对外只返回 ok/error 状态，不回显异常详情（避免泄漏内部拓扑）。
    """
    from app.common.response import success

    checks: dict[str, dict] = {}

    checks["database"] = {"status": "ok" if await _check_db() else "error"}

    try:
        redis = await get_redis()
        await redis.ping()
        checks["redis"] = {"status": "ok"}
    except Exception:
        logger.exception("平台状态检查：Redis 连接失败")
        checks["redis"] = {"status": "error"}

    all_ok = all(v.get("status") == "ok" for v in checks.values())
    return success(
        {
            "status": "healthy" if all_ok else "degraded",
            "components": checks,
            "version": "1.0.0",
        }
    )


# ======================================================================
# GET /platform/diagnostics — 生产级综合诊断（多检查项 + 三级告警）
# ======================================================================
# 严重级别：ok < warning < critical
_SEVERITY_ORDER = {"ok": 0, "warning": 1, "critical": 2}


def _worst(checks: list[dict]) -> str:
    """取所有检查项中最严重的级别作为整体状态。"""
    worst = "ok"
    for c in checks:
        if _SEVERITY_ORDER.get(c["status"], 0) > _SEVERITY_ORDER[worst]:
            worst = c["status"]
    return worst


async def _scalar(session, sql: str, **params) -> int:
    """执行 COUNT 类查询，失败返回 -1（由调用方按需处理）。"""
    try:
        res = await session.execute(text(sql), params or None)
        return int(res.scalar() or 0)
    except Exception:
        return -1


@platform_router.get("/diagnostics")
async def platform_diagnostics():
    """生产级综合诊断：DB / Redis / outbox 积压·死信·卡住 / worker 存活 / 磁盘 / 数据完整性。

    每项返回 {name, status(ok|warning|critical), message, value?}；
    整体 status 取最严重项。供运维主动告警与首页指挥台展示。
    """
    from app.common.response import success

    checks: list[dict] = []

    # 1. 数据库
    db_ok = await _check_db()
    checks.append({
        "name": "database",
        "status": "ok" if db_ok else "critical",
        "message": "连接正常" if db_ok else "数据库连接失败",
    })

    # 2. Redis
    redis = None
    try:
        redis = await get_redis()
        await redis.ping()
        checks.append({"name": "redis", "status": "ok", "message": "连接正常"})
    except Exception:
        redis = None
        checks.append({"name": "redis", "status": "warning", "message": "Redis 连接失败（实时推送/心跳降级）"})

    # 3-9. 依赖 DB 的检查项
    session_factory = get_session_factory()
    try:
        async with session_factory() as session:
            # 3. outbox 待处理积压
            pending = await _scalar(session, "SELECT COUNT(*) FROM event_outbox WHERE status='pending'")
            if pending < 0:
                checks.append({"name": "outbox_backlog", "status": "warning", "message": "event_outbox 不可查询"})
            else:
                st = "ok" if pending < 100 else ("warning" if pending < 1000 else "critical")
                checks.append({"name": "outbox_backlog", "status": st, "message": f"待处理事件 {pending}", "value": pending})

            # 4. outbox 死信
            dead = await _scalar(session, "SELECT COUNT(*) FROM event_outbox WHERE status='dead'")
            if dead > 0:
                checks.append({"name": "outbox_deadletter", "status": "warning", "message": f"死信事件 {dead}（需人工排查）", "value": dead})
            elif dead == 0:
                checks.append({"name": "outbox_deadletter", "status": "ok", "message": "无死信", "value": 0})
            else:
                checks.append({"name": "outbox_deadletter", "status": "warning", "message": "event_outbox 不可查询"})

            # 5. outbox 卡住（processing 但租约过期）
            stuck = await _scalar(
                session,
                "SELECT COUNT(*) FROM event_outbox WHERE status='processing' AND locked_until < NOW()",
            )
            checks.append({
                "name": "outbox_stuck",
                "status": "ok" if stuck <= 0 else "warning",
                "message": "无卡住事件" if stuck <= 0 else f"租约过期未释放 {stuck}（worker 可能异常）",
                "value": max(stuck, 0),
            })

            # 6. 巡检积压
            insp = await _scalar(session, "SELECT COUNT(*) FROM inspection_tasks WHERE status IN ('pending','running')")
            if insp >= 0:
                st = "ok" if insp < 50 else "warning"
                checks.append({"name": "inspection_backlog", "status": st, "message": f"巡检待处理 {insp}", "value": insp})

            # 7. 执行积压
            exe = await _scalar(session, "SELECT COUNT(*) FROM executions WHERE status IN ('pending','running','awaiting_approval')")
            if exe >= 0:
                st = "ok" if exe < 20 else "warning"
                checks.append({"name": "execution_backlog", "status": st, "message": f"执行待处理 {exe}", "value": exe})

            # 8. 数据完整性：管理员账户
            admin_cnt = await _scalar(session, "SELECT COUNT(*) FROM users WHERE role='admin' OR is_superuser=1")
            checks.append({
                "name": "admin_user",
                "status": "ok" if admin_cnt > 0 else "critical",
                "message": "管理员存在" if admin_cnt > 0 else "无管理员账户（系统不可管理）",
                "value": max(admin_cnt, 0),
            })

            # 9. 数据完整性：角色
            role_cnt = await _scalar(session, "SELECT COUNT(*) FROM roles")
            checks.append({
                "name": "roles",
                "status": "ok" if role_cnt > 0 else "warning",
                "message": f"角色 {role_cnt} 个" if role_cnt > 0 else "未初始化角色",
                "value": max(role_cnt, 0),
            })

            # 10. 迁移版本
            ver = None
            try:
                ver = (await session.execute(text("SELECT version_num FROM alembic_version"))).scalar()
            except Exception:
                ver = None
            checks.append({
                "name": "db_migration",
                "status": "ok" if ver else "warning",
                "message": f"alembic head: {ver}" if ver else "无法读取迁移版本",
            })
    except Exception:
        logger.exception("diagnostics: DB 检查批次失败")
        checks.append({"name": "db_batch", "status": "critical", "message": "数据库诊断批次失败"})

    # 11. Worker 存活（读 Redis 心跳）
    if redis is not None:
        try:
            keys = await redis.keys("autops:worker:heartbeat:*")
            checks.append({
                "name": "worker_liveness",
                "status": "ok" if keys else "critical",
                "message": f"在线 worker {len(keys)} 个" if keys else "无存活 worker（outbox/采集/执行将停滞）",
                "value": len(keys),
            })
        except Exception:
            checks.append({"name": "worker_liveness", "status": "warning", "message": "无法读取 worker 心跳"})
    else:
        checks.append({"name": "worker_liveness", "status": "warning", "message": "Redis 不可用，无法判断 worker 存活"})

    # 12. 磁盘
    try:
        import shutil

        usage = shutil.disk_usage("/")
        pct = round(usage.used / usage.total * 100, 1)
        st = "ok" if pct < 85 else ("warning" if pct < 95 else "critical")
        checks.append({"name": "disk_usage", "status": st, "message": f"根分区已用 {pct}%", "value": pct})
    except Exception:
        checks.append({"name": "disk_usage", "status": "warning", "message": "无法读取磁盘用量"})

    # 13. API 自身
    checks.append({"name": "api_server", "status": "ok", "message": "运行中"})

    overall = _worst(checks)
    summary = {
        "ok": sum(1 for c in checks if c["status"] == "ok"),
        "warning": sum(1 for c in checks if c["status"] == "warning"),
        "critical": sum(1 for c in checks if c["status"] == "critical"),
    }
    return success({
        "status": overall,
        "summary": summary,
        "checks": checks,
        "version": "1.0.0",
    })
