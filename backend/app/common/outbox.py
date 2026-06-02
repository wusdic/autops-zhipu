"""AUTOPS Outbox Consumer.

从 event_outbox 表中消费待处理事件并分发给 handler。
仅运行在 Worker 进程中，API 进程不启动此消费者。
"""
from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import text

from app.common.events import DomainEvent, EventPriority, get_event_bus

logger = logging.getLogger(__name__)


class OutboxConsumer:
    """Outbox 表消费者 — 从 DB 拉取 pending 事件并调用 handler.

    用法:
        consumer = OutboxConsumer(worker_id="worker-1")
        await consumer.run_forever(interval=1.0)
    """

    def __init__(
        self,
        worker_id: str | None = None,
        batch_size: int = 50,
        lock_seconds: int = 120,
    ):
        self.worker_id = worker_id or f"worker-{uuid.uuid4().hex[:8]}"
        self.batch_size = batch_size
        self.lock_seconds = lock_seconds
        self._running = False

    async def consume_once(self) -> int:
        """执行一次 outbox 消费: claim → dispatch → mark done/failed.

        Returns:
            本批次处理成功的事件数量
        """
        from app.infra.database import get_session_factory

        session_factory = get_session_factory()
        processed = 0

        async with session_factory() as session:
            # 0. Recover expired processing leases
            await session.execute(
                text("""
                    UPDATE event_outbox
                    SET status = 'pending',
                        locked_by = NULL,
                        locked_until = NULL
                    WHERE status = 'processing'
                      AND locked_until < NOW()
                """),
            )
            await session.commit()

            # 1. Claim pending events with row lock
            result = await session.execute(
                text("""
                    SELECT id, event_id, event_type, domain, payload, priority,
                           source, correlation_id, retry_count, max_retries
                    FROM event_outbox
                    WHERE status = 'pending'
                      AND (next_retry_at IS NULL OR next_retry_at <= NOW())
                    ORDER BY priority DESC, created_at ASC
                    LIMIT :batch_size
                    FOR UPDATE SKIP LOCKED
                """),
                {"batch_size": self.batch_size},
            )
            rows = result.fetchall()

            if not rows:
                return 0

            lock_until = datetime.now(timezone.utc) + timedelta(seconds=self.lock_seconds)

            # Mark claimed rows as processing — use expanding bindparam for IN clause
            row_ids = [row.id for row in rows]
            from sqlalchemy import bindparam
            await session.execute(
                text("""
                    UPDATE event_outbox
                    SET status = 'processing',
                        locked_by = :worker_id,
                        locked_until = :lock_until
                    WHERE id IN :ids
                """).bindparams(
                    bindparam("worker_id", value=self.worker_id),
                    bindparam("lock_until", value=lock_until),
                    bindparam("ids", expanding=True),
                ),
                {"ids": row_ids},
            )
            await session.commit()

            # 2. Process each claimed event
            bus = get_event_bus()
            for row in rows:
                try:
                    # Build DomainEvent from row
                    payload = row.payload
                    if isinstance(payload, str):
                        payload = json.loads(payload)
                    elif payload is None:
                        payload = {}

                    try:
                        priority = EventPriority(row.priority)
                    except ValueError:
                        priority = EventPriority.NORMAL

                    event = DomainEvent(
                        event_id=row.event_id,
                        event_type=row.event_type,
                        domain=row.domain,
                        payload=payload,
                        priority=priority,
                        source=row.source or "",
                        correlation_id=row.correlation_id or "",
                    )

                    # Dispatch to handlers only (NOT bus.publish)
                    await bus.dispatch_to_handlers(event)

                    # Publish to Redis for cross-process WS bridge
                    from app.common.realtime import publish_realtime
                    await publish_realtime(event.event_type, event.payload)

                    # 3a. Success → mark done
                    await session.execute(
                        text("""
                            UPDATE event_outbox
                            SET status = 'done',
                                processed_at = NOW(),
                                locked_by = NULL,
                                locked_until = NULL
                            WHERE id = :id
                        """),
                        {"id": row.id},
                    )
                    await session.commit()
                    processed += 1

                except Exception as exc:
                    logger.exception(
                        "OutboxConsumer: handler failed for event_id=%s type=%s",
                        row.event_id, row.event_type,
                    )
                    await session.rollback()

                    # 3b. Failure → retry or dead-letter
                    new_retry = (row.retry_count or 0) + 1
                    max_retries = row.max_retries if row.max_retries is not None else 5

                    if new_retry < max_retries:
                        delay_seconds = (2 ** new_retry) * 5
                        next_retry = datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)
                        await session.execute(
                            text("""
                                UPDATE event_outbox
                                SET status = 'pending',
                                    retry_count = :retry_count,
                                    next_retry_at = :next_retry,
                                    last_error = :last_error,
                                    locked_by = NULL,
                                    locked_until = NULL
                                WHERE id = :id
                            """),
                            {
                                "id": row.id,
                                "retry_count": new_retry,
                                "next_retry": next_retry,
                                "last_error": str(exc)[:4000],
                            },
                        )
                        logger.info(
                            "OutboxConsumer: event %s retry %d/%d, next at %s",
                            row.event_id, new_retry, max_retries, next_retry.isoformat(),
                        )
                    else:
                        await session.execute(
                            text("""
                                UPDATE event_outbox
                                SET status = 'dead',
                                    retry_count = :retry_count,
                                    last_error = :last_error,
                                    locked_by = NULL,
                                    locked_until = NULL,
                                    processed_at = NOW()
                                WHERE id = :id
                            """),
                            {
                                "id": row.id,
                                "retry_count": new_retry,
                                "last_error": str(exc)[:4000],
                            },
                        )
                        logger.warning(
                            "OutboxConsumer: event %s dead-lettered after %d retries",
                            row.event_id, new_retry,
                        )
                    await session.commit()

        return processed

    async def run_forever(self, interval: float = 1.0) -> None:
        """持续消费 outbox 事件，直到 _running 被设为 False."""
        self._running = True
        logger.info(
            "OutboxConsumer [%s] started (batch=%d, interval=%.1fs)",
            self.worker_id, self.batch_size, interval,
        )
        while self._running:
            try:
                processed = await self.consume_once()
                if processed == 0:
                    # No events — sleep a bit longer
                    await asyncio.sleep(interval)
                else:
                    # Processed events — brief pause before next batch
                    await asyncio.sleep(0.1)
            except asyncio.CancelledError:
                logger.info("OutboxConsumer [%s] cancelled", self.worker_id)
                break
            except Exception:
                logger.exception("OutboxConsumer [%s] consume_once error", self.worker_id)
                await asyncio.sleep(interval)

        logger.info("OutboxConsumer [%s] stopped", self.worker_id)

    def stop(self) -> None:
        """请求停止消费循环."""
        self._running = False
