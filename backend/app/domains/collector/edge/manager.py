"""Edge Collector 管理器."""
from __future__ import annotations
import logging
from datetime import datetime, timedelta
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.domains.collector.edge.protocol import (
    HeartbeatPayload, TaskPayload, ResultPayload, RegisterPayload
)

logger = logging.getLogger(__name__)

# 心跳超时阈值
HEARTBEAT_TIMEOUT_SECONDS = 120

class EdgeCollectorManager:
    """远程采集器管理器."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def register(self, payload: RegisterPayload) -> dict:
        """注册新的远程采集器."""
        from uuid import uuid4
        from app.domains.collector.models import Collector

        collector_id = payload.collector_id or str(uuid4())
        collector = Collector(
            id=collector_id,
            name=payload.name,
            collector_type=payload.collector_type,
            description=f"Edge collector on {payload.hostname}",
            is_builtin=False,
        )
        # 检查是否已存在
        existing = await self.session.get(Collector, collector_id)
        if existing:
            return {"collector_id": collector_id, "status": "already_registered"}

        self.session.add(collector)
        await self.session.flush()
        return {"collector_id": collector_id, "status": "registered"}

    async def heartbeat(self, payload: HeartbeatPayload) -> dict:
        """处理心跳."""
        try:
            from app.infra.redis_client import get_redis
            redis = await get_redis()
            key = f"collector:heartbeat:{payload.collector_id}"
            data = {
                "status": payload.status,
                "cpu": str(payload.cpu_usage or 0),
                "memory": str(payload.memory_usage or 0),
                "tasks": str(payload.active_tasks),
                "ts": payload.timestamp or datetime.utcnow().isoformat(),
            }
            await redis.hset(key, mapping=data)  # type: ignore
            await redis.expire(key, HEARTBEAT_TIMEOUT_SECONDS)  # type: ignore
        except Exception as e:
            logger.warning(f"Heartbeat redis write failed: {e}")

        return {"collector_id": payload.collector_id, "accepted": True}

    async def get_pending_tasks(self, collector_id: str) -> list[dict]:
        """获取待执行任务."""
        from app.domains.collector.models import CollectionJob
        q = select(CollectionJob).where(
            CollectionJob.collector_id == collector_id,
            CollectionJob.status == "pending"
        ).limit(10)
        result = await self.session.execute(q)
        jobs = result.scalars().all()
        return [
            {
                "task_id": str(j.id),
                "collector_type": "ssh",
                "config": {"asset_id": str(j.asset_id), "timeout": j.timeout or 300},
            }
            for j in jobs
        ]

    async def submit_result(self, payload: ResultPayload) -> dict:
        """接收任务结果."""
        from app.domains.collector.models import CollectionJob, CollectionResult
        from uuid import uuid4

        # 更新Job状态
        job = await self.session.get(CollectionJob, payload.task_id)
        if job:
            job.status = payload.status
            job.last_run_at = datetime.utcnow()

        # 保存结果
        result = CollectionResult(
            id=str(uuid4()),
            job_id=payload.task_id,
            asset_id=str(job.asset_id) if job else None,
            status=payload.status,
            result_data=payload.data,
            error_message=payload.error_message,
            duration_ms=payload.duration_ms,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )
        self.session.add(result)
        await self.session.flush()

        return {"accepted": True, "task_id": payload.task_id}

    async def get_collector_status(self, collector_id: str) -> dict:
        """获取采集器状态（含心跳信息）."""
        status = {"collector_id": collector_id, "alive": False}
        try:
            from app.infra.redis_client import get_redis
            redis = await get_redis()
            key = f"collector:heartbeat:{collector_id}"
            data = await redis.hgetall(key)  # type: ignore
            if data:
                status["alive"] = True
                status["heartbeat"] = {k.decode() if isinstance(k, bytes) else k: v.decode() if isinstance(v, bytes) else v for k, v in data.items()}
        except Exception:
            pass
        return status
