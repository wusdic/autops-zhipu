"""AUTOPS Worker Runner.

独立进程运行采集调度器和事件消费者。
生产环境应使用此入口，而非API进程内启动。

用法:
    python -m app.workers.runner
"""

from __future__ import annotations

import asyncio
import json
import logging
import signal
import uuid

from app.infra.config import get_config
from app.infra.database import init_db_engine, close_db_engine
from app.infra.redis_client import close_redis
from app.common.event_handlers import register_all_handlers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


class WorkerRunner:
    """后台任务运行器 — 运行 outbox consumer + scheduler + heartbeat."""

    def __init__(self):
        self.config = get_config()
        self.stop_event = asyncio.Event()
        self._tasks: list[asyncio.Task] = []

    async def start(self) -> None:
        init_db_engine()

        # 1. 启用 outbox 模式并注册 handler
        from app.common.events import get_event_bus
        bus = get_event_bus()
        bus.enable_outbox()
        register_all_handlers()

        # 注册 asset_created → 立即采集（只在 worker 中）
        from app.common.events import AssetEvents
        from app.workers.scheduler import on_asset_created_run_collection
        bus.subscribe(AssetEvents.ASSET_CREATED, on_asset_created_run_collection)

        # 注册发现扫描请求 → 在 Worker 进程执行扫描（移出 API 进程，P1-07）
        from app.domains.asset.discovery_service import on_discovery_scan_requested
        bus.subscribe(
            AssetEvents.DISCOVERY_SCAN_REQUESTED, on_discovery_scan_requested
        )

        # 注册手动全量采集请求 → Worker 进程执行（API 进程无 CAP_NET_RAW，R13）
        from app.common.events import CollectorEvents
        from app.workers.scheduler import on_full_scan_requested
        bus.subscribe(CollectorEvents.FULL_SCAN_REQUESTED, on_full_scan_requested)
        logger.info("WorkerRunner: outbox enabled, handlers registered, asset_created→collection & discovery_scan→worker linked")

        # 启动恢复：重新派发 Worker 离线期间卡住的发现任务（pending/running）
        try:
            from app.infra.database import async_session_factory
            from app.domains.asset.discovery_service import DiscoveryService

            async with async_session_factory() as _s:
                n = await DiscoveryService(_s).requeue_stuck_tasks()
                await _s.commit()
            if n:
                logger.info("WorkerRunner: 已恢复 %d 个未完成发现任务", n)
        except Exception:
            logger.exception("WorkerRunner: 发现任务启动恢复失败（忽略，不阻塞启动）")

        # 2. 启动 OutboxConsumer
        from app.common.outbox import OutboxConsumer
        worker_id = f"worker-{uuid.uuid4().hex[:8]}"
        outbox_consumer = OutboxConsumer(
            worker_id=worker_id,
            batch_size=50,
            lock_seconds=120,
        )
        self._tasks.append(asyncio.create_task(
            outbox_consumer.run_forever(interval=1.0),
            name="outbox-consumer",
        ))

        # 3. 启动 Scheduler
        from app.workers.scheduler import get_scheduler
        scheduler = get_scheduler()
        self._tasks.append(asyncio.create_task(
            scheduler.start(interval=300),
            name="collection-scheduler",
        ))

        # 3.5 启动巡检定时调度器（按 cron 触发巡检计划）
        from app.workers.inspection_scheduler import get_inspection_scheduler
        inspection_scheduler = get_inspection_scheduler()
        self._tasks.append(asyncio.create_task(
            inspection_scheduler.start(interval=60),
            name="inspection-scheduler",
        ))

        # 3.6 启动执行队列 Worker（领取 execution_queue 并真实执行）
        from app.workers.execution_worker import ExecutionWorker
        execution_worker = ExecutionWorker(lease_seconds=300, poll_interval=2.0)
        self._tasks.append(asyncio.create_task(
            execution_worker.run_forever(),
            name="execution-worker",
        ))

        # 4. 启动 heartbeat loop
        self._tasks.append(asyncio.create_task(
            self._heartbeat_loop(),
            name="heartbeat",
        ))

        logger.info("WorkerRunner started with %d tasks: %s",
                     len(self._tasks), [t.get_name() for t in self._tasks])
        await self.stop_event.wait()

        # Shutdown: stop consumer and scheduler
        outbox_consumer.stop()
        await scheduler.stop()
        await inspection_scheduler.stop()
        execution_worker.stop()
        logger.info("WorkerRunner stopped")

    async def _heartbeat_loop(self) -> None:
        """每 60s 打印一次心跳日志，并写 Redis 存活信号（供 /platform/diagnostics 检测 worker 是否在跑）。"""
        worker_id = f"runner-{uuid.uuid4().hex[:8]}"
        while not self.stop_event.is_set():
            logger.info("WorkerRunner heartbeat: %d tasks running", len(self._tasks))
            await self._write_heartbeat(worker_id)
            try:
                await asyncio.wait_for(
                    asyncio.create_task(self.stop_event.wait()),
                    timeout=60.0,
                )
            except asyncio.TimeoutError:
                pass

    async def _write_heartbeat(self, worker_id: str) -> None:
        """写 Redis 存活信号（TTL 180s）；Redis 不可用时只记日志不影响运行。"""
        from datetime import datetime, timezone

        try:
            from app.infra.redis_client import get_redis

            redis = await get_redis()
            if redis is not None:
                payload = json.dumps({
                    "worker_id": worker_id,
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "tasks": len(self._tasks),
                })
                await redis.set(f"autops:worker:heartbeat:{worker_id}", payload, ex=180)
        except Exception:
            logger.debug("WorkerRunner: 写心跳到 Redis 失败（忽略）", exc_info=True)

    async def shutdown(self) -> None:
        logger.info("WorkerRunner shutting down...")
        self.stop_event.set()


async def main() -> None:
    runner = WorkerRunner()
    loop = asyncio.get_running_loop()

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(runner.shutdown()))

    try:
        await runner.start()
    finally:
        await close_redis()
        await close_db_engine()


if __name__ == "__main__":
    asyncio.run(main())
