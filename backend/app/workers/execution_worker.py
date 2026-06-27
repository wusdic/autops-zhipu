"""执行队列 Worker — 领取 execution_queue 任务并真实执行.

取代此前 outbox handler 内的 `asyncio.create_task` 后台执行：
- 持久化领取（lease）+ 心跳续租，崩溃后租约过期自动回收重投；
- 运行结束发布 EXECUTION_COMPLETED / EXECUTION_FAILED（走 outbox）；
- 失败按指数退避重试，超过上限进 failed。
仅在 Worker 进程中运行（由 WorkerRunner 启动）。
"""

from __future__ import annotations

import asyncio
import logging
import uuid

from app.common import execution_queue as q

logger = logging.getLogger(__name__)


class ExecutionWorker:
    """从 execution_queue 领取并执行自动化任务."""

    def __init__(
        self,
        worker_id: str | None = None,
        lease_seconds: int = 300,
        poll_interval: float = 2.0,
    ):
        self.worker_id = worker_id or f"exec-{uuid.uuid4().hex[:8]}"
        self.lease_seconds = lease_seconds
        self.poll_interval = poll_interval
        self._running = False

    async def run_forever(self) -> None:
        self._running = True
        logger.info(
            "ExecutionWorker [%s] started (lease=%ds, poll=%.1fs)",
            self.worker_id, self.lease_seconds, self.poll_interval,
        )
        while self._running:
            try:
                leased = await self._lease()
                if not leased:
                    await asyncio.sleep(self.poll_interval)
                    continue
                await self._run(leased)
            except asyncio.CancelledError:
                logger.info("ExecutionWorker [%s] cancelled", self.worker_id)
                break
            except Exception:
                logger.exception("ExecutionWorker [%s] loop error", self.worker_id)
                await asyncio.sleep(self.poll_interval)
        logger.info("ExecutionWorker [%s] stopped", self.worker_id)

    def stop(self) -> None:
        self._running = False

    async def _lease(self) -> dict | None:
        from app.infra.database import async_session_factory

        async with async_session_factory() as session:
            return await q.lease_one(session, self.worker_id, self.lease_seconds)

    async def _run(self, leased: dict) -> None:
        queue_id = leased["queue_id"]
        execution_id = leased["execution_id"]
        hb = asyncio.create_task(self._heartbeat(queue_id))
        try:
            execution = await self._execute(execution_id)
            from app.infra.database import async_session_factory

            async with async_session_factory() as session:
                await q.complete(session, queue_id)
            await self._publish_result(execution, leased)
            logger.info(
                "ExecutionWorker: 执行完成 execution_id=%s status=%s",
                execution_id, getattr(execution, "status", "?"),
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("ExecutionWorker: 执行失败 execution_id=%s", execution_id)
            from app.infra.database import async_session_factory

            async with async_session_factory() as session:
                await q.fail(
                    session, queue_id, str(exc),
                    leased["attempts"], leased["max_attempts"],
                )
        finally:
            hb.cancel()

    async def _execute(self, execution_id: str):
        from app.domains.automation.service import AutomationService
        from app.infra.database import async_session_factory

        async with async_session_factory() as session:
            svc = AutomationService(session)
            # 重投时把崩溃残留的中间态回退，使 run_execution 状态守卫放行
            await svc.reset_for_retry(execution_id)
            await session.commit()
            execution = await svc.run_execution(execution_id)
            await session.commit()
            return execution

    async def _publish_result(self, execution, leased: dict) -> None:
        from app.common.events import (
            AutomationEvents,
            DomainEvent,
            get_event_bus,
        )

        status = getattr(execution, "status", "")
        bus = get_event_bus()
        if status == "completed":
            await bus.publish(
                DomainEvent(
                    event_type=AutomationEvents.EXECUTION_COMPLETED,
                    domain="automation",
                    payload={
                        "execution_id": str(execution.id),
                        "status": "completed",
                        "result": execution.result,
                    },
                    source="execution_worker",
                )
            )
        elif status in ("failed", "rollback_failed", "dry_run_failed"):
            await bus.publish(
                DomainEvent(
                    event_type=AutomationEvents.EXECUTION_FAILED,
                    domain="automation",
                    payload={
                        "execution_id": str(execution.id),
                        "status": status,
                        "error_message": execution.error_message,
                    },
                    source="execution_worker",
                )
            )

    async def _heartbeat(self, queue_id: str) -> None:
        interval = max(self.lease_seconds / 3, 5)
        try:
            while True:
                await asyncio.sleep(interval)
                from app.infra.database import async_session_factory

                async with async_session_factory() as session:
                    await q.heartbeat(
                        session, queue_id, self.worker_id, self.lease_seconds
                    )
        except asyncio.CancelledError:
            return
        except Exception:
            logger.debug("ExecutionWorker heartbeat 失败 queue_id=%s", queue_id,
                         exc_info=True)
