"""巡检定时调度器.

每分钟检查启用的巡检计划，按 cron 表达式匹配当前时间则自动创建巡检任务并执行。
内置极简 cron 匹配（5 字段：分 时 日 月 周），不引入第三方依赖。
周字段采用 cron 习惯：0=周日 … 6=周六（兼容 7=周日）。
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select

logger = logging.getLogger(__name__)


def _field_match(expr: str, value: int, lo: int) -> bool:
    for part in expr.split(","):
        part = part.strip()
        if part == "*":
            return True
        if part.startswith("*/"):
            try:
                step = int(part[2:])
            except ValueError:
                continue
            if step > 0 and (value - lo) % step == 0:
                return True
            continue
        if "-" in part:
            try:
                a, b = part.split("-", 1)
                if int(a) <= value <= int(b):
                    return True
            except ValueError:
                pass
            continue
        if part.isdigit() and int(part) == value:
            return True
    return False


def cron_matches(expr: str, dt: datetime) -> bool:
    """判断 cron 表达式是否匹配给定时间（分钟粒度）."""
    fields = (expr or "").split()
    if len(fields) != 5:
        return False
    minute, hour, dom, month, dow = fields
    cron_dow = (dt.weekday() + 1) % 7  # Mon=0..Sun=6 → cron 0=Sun..6=Sat
    return (
        _field_match(minute, dt.minute, 0)
        and _field_match(hour, dt.hour, 0)
        and _field_match(dom, dt.day, 1)
        and _field_match(month, dt.month, 1)
        and (_field_match(dow, cron_dow, 0) or _field_match(dow, 7 if cron_dow == 0 else cron_dow, 0))
    )


class InspectionScheduler:
    """按 cron 触发启用的巡检计划."""

    def __init__(self):
        self._running = False
        self._task: asyncio.Task | None = None
        # 防止同一分钟内重复触发：plan_id -> "YYYYMMDDHHMM"
        self._last_fired: dict[str, str] = {}

    async def start(self, interval: int = 60) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop(interval))
        logger.info("InspectionScheduler started, interval=%ds", interval)

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _loop(self, interval: int) -> None:
        while self._running:
            try:
                await self._tick()
            except Exception:  # noqa: BLE001
                logger.exception("InspectionScheduler tick error")
            await asyncio.sleep(interval)

    async def _tick(self) -> None:
        from app.domains.inspection.executor import run_inspection_task
        from app.domains.inspection.models import InspectionPlan, InspectionTask
        from app.infra.database import async_session_factory

        now = datetime.now(timezone.utc)
        minute_key = now.strftime("%Y%m%d%H%M")

        async with async_session_factory() as session:
            result = await session.execute(
                select(InspectionPlan).where(InspectionPlan.enabled == True)  # noqa: E712
            )
            plans = list(result.scalars().all())

        for plan in plans:
            if not cron_matches(plan.cron_expression, now):
                continue
            if self._last_fired.get(str(plan.id)) == minute_key:
                continue
            self._last_fired[str(plan.id)] = minute_key

            # 创建任务并执行
            try:
                async with async_session_factory() as session:
                    task = InspectionTask(
                        plan_id=str(plan.id),
                        template_id=str(plan.template_id),
                        status="pending",
                    )
                    session.add(task)
                    await session.commit()
                    task_id = str(task.id)
                logger.info("InspectionScheduler 触发计划 %s → 任务 %s", plan.id, task_id)
                await run_inspection_task(task_id)
            except Exception:  # noqa: BLE001
                logger.exception("InspectionScheduler 执行计划失败 plan=%s", plan.id)


_scheduler_instance: InspectionScheduler | None = None


def get_inspection_scheduler() -> InspectionScheduler:
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = InspectionScheduler()
    return _scheduler_instance
