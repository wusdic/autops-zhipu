"""采集调度器 - 定时+事件驱动采集."""
from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from app.workers.builtin_collectors import run_collection, COLLECTOR_REGISTRY

logger = logging.getLogger(__name__)

# 全局调度器实例
_scheduler_instance: "CollectionScheduler | None" = None

# 内置采集器名 → collector_type 映射
BUILTIN_NAME_TO_TYPE = {
    "ping-collector": "ping",
    "tcp-port-collector": "tcp_port",
    "http-collector": "http",
    "cert-collector": "certificate",
    "db-collector": "database",
}

# 资产类型 → 适用的采集器类型
ASSET_TYPE_COLLECTOR_MAP: dict[str, list[str]] = {
    "linux_server": ["ping", "tcp_port", "http"],
    "windows_server": ["ping", "tcp_port"],
    "network_device": ["ping", "tcp_port"],
    "database": ["ping", "tcp_port", "database"],
    "web_service": ["ping", "tcp_port", "http", "certificate"],
    "container": ["ping", "tcp_port"],
}

# 所有资产类型默认至少跑 Ping
DEFAULT_COLLECTORS = ["ping"]


def _get_applicable_collectors(
    asset_type: str, ip: str
) -> dict[str, object]:
    """根据资产类型返回适用的采集器子集."""
    types = ASSET_TYPE_COLLECTOR_MAP.get(asset_type, DEFAULT_COLLECTORS)
    applicable = {}
    for ctype in types:
        if ctype in COLLECTOR_REGISTRY:
            applicable[ctype] = COLLECTOR_REGISTRY[ctype]
    # 如果 IP 含端口则也做 tcp_port
    if "tcp_port" not in applicable and ":" in ip:
        if "tcp_port" in COLLECTOR_REGISTRY:
            applicable["tcp_port"] = COLLECTOR_REGISTRY["tcp_port"]
    return applicable


async def run_collection_for_asset(
    asset,
    session,
    trigger: str = "schedule",
    collector_types: list[str] | None = None,
) -> "CollectionJob | None":
    """统一采集入口 — 为单个资产执行完整的采集流程.

    Args:
        asset: Asset ORM 对象（必须已绑定到 *session*）
        session: AsyncSession（调用方负责 commit/rollback）
        trigger: 触发来源标识，如 "schedule" / "asset_created" / "manual"
        collector_types: 可选，指定只跑哪些采集器类型；None = 自动选择

    Returns:
        最后一个创建/更新的 CollectionJob（可能有多个），失败时返回 None
    """
    from app.domains.collector.models import CollectionJob, CollectionResult
    from app.domains.collector.service import CollectorService
    from app.common.events import DomainEvent, get_event_bus, StateEvents

    ip = asset.ip
    if not ip or ip == "0.0.0.0":
        logger.debug("run_collection_for_asset: skip asset=%s (no valid IP)", getattr(asset, "id", "?"))
        return None

    # 确保内置采集器已注册 & 建立 type→id 映射
    svc = CollectorService(session)
    all_collectors = await svc.get_or_create_builtin_collectors()
    await session.flush()

    type_to_id: dict[str, str] = {}
    for col in all_collectors:
        mapped_type = BUILTIN_NAME_TO_TYPE.get(col.name, col.collector_type)
        type_to_id[mapped_type] = str(col.id)

    # 确定要运行的采集器
    asset_type = getattr(asset, "asset_type", "unknown") or "unknown"
    if collector_types is not None:
        # 调用方指定了采集器类型，只跑这些
        applicable = {ct: COLLECTOR_REGISTRY[ct] for ct in collector_types if ct in COLLECTOR_REGISTRY}
    else:
        applicable = _get_applicable_collectors(asset_type, ip)

    logger.info(
        "run_collection_for_asset: asset=%s ip=%s trigger=%s collectors=%s",
        getattr(asset, "hostname", "?"), ip, trigger, list(applicable.keys()),
    )

    last_job = None

    for ctype, collector in applicable.items():
        try:
            result_data = await run_collection(ctype, ip)
            status = result_data.get("status", "error")
        except Exception as e:
            logger.warning("Collection %s error for %s: %s", ctype, ip, e)
            result_data = {"error": str(e), "collector": ctype, "ip": ip, "status": "error"}
            status = "error"

        # --- 写入 DB: Job + Result ---
        try:
            real_collector_id = type_to_id.get(ctype)
            if not real_collector_id:
                logger.warning("No DB collector for type=%s, skip", ctype)
                continue

            # 查找或创建 Job
            existing = await session.execute(
                select(CollectionJob).where(
                    CollectionJob.asset_id == str(asset.id),
                    CollectionJob.collector_id == real_collector_id,
                    CollectionJob.status == "running",
                ).limit(1)
            )
            job_obj = existing.scalar_one_or_none()
            if not job_obj:
                job_obj = CollectionJob(
                    name=f"{trigger}_{ctype}_{(asset.hostname or 'unknown')[:20]}",
                    collector_id=real_collector_id,
                    asset_id=str(asset.id),
                    status="running",
                )
                session.add(job_obj)
                await session.flush()

            # 写采集结果
            cr = CollectionResult(
                job_id=str(job_obj.id),
                asset_id=str(asset.id),
                status="success" if status == "success" else "failed",
                result_data=json.dumps(result_data, ensure_ascii=False, default=str),
                error_message=result_data.get("error"),
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
                duration_ms=int(result_data.get("latency_ms", 0) or 0),
            )
            session.add(cr)

            # 更新 job 状态
            job_obj.status = "completed" if status == "success" else "failed"
            job_obj.last_run_at = datetime.now(timezone.utc)
            last_job = job_obj

        except Exception as db_err:
            logger.warning("DB write error for %s/%s: %s", ip, ctype, db_err)
            # 不再 return，继续尝试其他采集器
            continue

        # --- Ping 状态变更检测 → 发事件 ---
        if ctype == "ping":
            was_online = getattr(asset, "status", "") == "online"
            is_alive = result_data.get("alive", False)
            new_status = "online" if is_alive else "offline"

            logger.info(
                "Ping check: asset=%s was_online=%s is_alive=%s",
                asset.hostname, was_online, is_alive,
            )

            if was_online != is_alive:
                old_status = asset.status
                asset.status = new_status
                await session.flush()

                # 在同一事务中写 outbox（不单独 commit）
                bus = get_event_bus()
                logger.info("Publishing STATE_CHANGED: %s → %s (trigger=%s)", old_status, new_status, trigger)
                await bus.publish(DomainEvent(
                    domain="state",
                    event_type=StateEvents.STATE_CHANGED,
                    payload={
                        "asset_id": str(asset.id),
                        "asset_name": asset.hostname,
                        "ip": ip,
                        "old_status": old_status,
                        "new_status": new_status,
                        "source": "collector.ping",
                        "metrics": result_data,
                    },
                ))
                logger.info(
                    "State change published: asset=%s %s → %s",
                    asset.hostname, old_status, new_status,
                )

    await session.flush()
    return last_job


class CollectionScheduler:
    """采集调度器 — 定期遍历资产执行采集."""

    def __init__(self):
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self, interval: int = 300):
        """启动定期采集 (默认5分钟)."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop(interval))
        logger.info("CollectionScheduler started, interval=%ds", interval)

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("CollectionScheduler stopped")

    async def _loop(self, interval: int):
        while self._running:
            try:
                await self._run_all_assets()
            except Exception as e:
                logger.error("CollectionScheduler loop error: %s", e, exc_info=True)
            await asyncio.sleep(interval)

    async def _run_all_assets(self):
        """遍历所有在线资产，执行匹配的采集."""
        from app.infra.database import async_session_factory
        from app.domains.asset.models import Asset

        async with async_session_factory() as session:
            # 获取所有未删除资产
            result = await session.execute(
                select(Asset).where(Asset.is_deleted == False)
            )
            assets = list(result.scalars().all())
            if not assets:
                return

            logger.info("CollectionScheduler: scanning %d assets", len(assets))

            for asset in assets:
                if not self._running:
                    break
                try:
                    await run_collection_for_asset(
                        asset, session, trigger="schedule"
                    )
                except Exception as e:
                    logger.warning("Collection error: asset=%s, error=%s", asset.ip, e, exc_info=True)

            await session.commit()
            logger.info("CollectionScheduler: batch completed for %d assets", len(assets))


async def on_asset_created_run_collection(event) -> None:
    """资产创建/纳管时立即执行采集 — 复用统一采集入口."""
    from app.common.events import DomainEvent
    from app.infra.database import async_session_factory
    from app.domains.asset.models import Asset

    payload = event.payload
    asset_id = payload.get("asset_id")
    ip = payload.get("ip")
    if not asset_id or not ip:
        return

    logger.info("Triggering immediate collection for asset=%s ip=%s", asset_id, ip)

    try:
        async with async_session_factory() as session:
            result = await session.execute(
                select(Asset).where(Asset.id == asset_id)
            )
            asset = result.scalar_one_or_none()
            if not asset:
                return

            await run_collection_for_asset(
                asset, session, trigger="asset_created"
            )
            await session.commit()

    except Exception as e:
        logger.error("Immediate collection failed: %s", e, exc_info=True)


def get_scheduler() -> CollectionScheduler:
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = CollectionScheduler()
    return _scheduler_instance
