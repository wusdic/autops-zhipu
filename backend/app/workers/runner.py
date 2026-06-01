"""AUTOPS Worker Runner.

独立进程运行采集调度器和事件消费者。
生产环境应使用此入口，而非API进程内启动。

用法:
    python -m app.workers.runner
"""

from __future__ import annotations

import asyncio
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
        logger.info("WorkerRunner: outbox enabled, all handlers registered")

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
        logger.info("WorkerRunner stopped")

    async def _heartbeat_loop(self) -> None:
        """每 60s 打印一次心跳日志."""
        while not self.stop_event.is_set():
            logger.info("WorkerRunner heartbeat: %d tasks running", len(self._tasks))
            try:
                await asyncio.wait_for(
                    asyncio.create_task(self.stop_event.wait()),
                    timeout=60.0,
                )
            except asyncio.TimeoutError:
                pass

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
