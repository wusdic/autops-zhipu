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
    """后台任务运行器."""

    def __init__(self):
        self.config = get_config()
        self.stop_event = asyncio.Event()
        self._tasks: list[asyncio.Task] = []

    async def start(self) -> None:
        init_db_engine()
        register_all_handlers()

        from app.workers.scheduler import get_scheduler
        scheduler = get_scheduler()
        self._tasks.append(asyncio.create_task(
            scheduler.start(interval=300),
            name="collection-scheduler",
        ))

        logger.info("WorkerRunner started with %d tasks", len(self._tasks))
        await self.stop_event.wait()
        await scheduler.stop()
        logger.info("WorkerRunner stopped")

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
