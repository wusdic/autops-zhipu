"""AIOps领域事件处理器."""

from __future__ import annotations

import logging
from collections import OrderedDict

from app.common.events import (
    DomainEvent,
    get_event_bus,
    AlertEvents,
    AIOpsEvents,
    AutomationEvents,
)

logger = logging.getLogger(__name__)

# 触发AI分析的告警严重度阈值
AI_ANALYSIS_SEVERITY_THRESHOLD = {"critical", "high"}

# ---------------------------------------------------------------------------
# Idempotency guard — 防止同一事件被同一处理器重复处理
# ---------------------------------------------------------------------------
# 用 OrderedDict 实现 LRU 淘汰：达上限时按插入顺序移除最旧条目，
# 而非全量 clear()（后者会在清空窗口内让重放事件被当作新事件重复处理）。
# 注意：多 worker 部署下进程内去重无效，需迁移到 Redis SETNX（后续架构演进）。
_processed_events: OrderedDict[str, None] = OrderedDict()
_MAX_PROCESSED = 50_000


def idempotent_handler(func):
    """装饰器: 防止同一事件被同一处理器重复处理."""

    async def wrapper(event):
        key = f"{getattr(event, 'event_id', '')}:{func.__name__}"
        if key in _processed_events:
            logger.debug("aiops: 跳过重复处理 key=%s", key)
            return
        # 先执行，成功后再登记幂等键：失败不登记，使 outbox 重试可重新执行。
        result = await func(event)
        if len(_processed_events) >= _MAX_PROCESSED:
            _processed_events.popitem(last=False)
        _processed_events[key] = None
        return result

    wrapper.__name__ = func.__name__
    wrapper.__qualname__ = func.__qualname__
    return wrapper


# ---------------------------------------------------------------------------
# 原有 AIOps 处理器
# ---------------------------------------------------------------------------


@idempotent_handler
async def on_alert_created_trigger_analysis(event: DomainEvent) -> None:
    """告警创建时触发AI分析(如severity=critical/high)."""
    payload = event.payload
    try:
        severity = payload.get("severity", "")
        alert_id = payload.get("alert_id", "")
        asset_ids = payload.get("asset_ids", [])

        if severity not in AI_ANALYSIS_SEVERITY_THRESHOLD:
            logger.debug("aiops: 告警severity=%s未达AI分析阈值, 跳过", severity)
            return

        from app.infra.database import async_session_factory
        from app.domains.aiops.service import AIOpsService
        from app.domains.aiops.schemas import AIAnalysisRequest

        # asset_ids 可能是 JSON 字符串或 list，统一规整为 list[str]
        if isinstance(asset_ids, str):
            import json as _json
            try:
                asset_ids = _json.loads(asset_ids)
            except (ValueError, TypeError):
                asset_ids = [asset_ids] if asset_ids else []
        if not isinstance(asset_ids, list):
            asset_ids = []

        analysis_id = None
        async with async_session_factory() as session:
            svc = AIOpsService(session)
            # 修复：request_analysis 接收单个 AIAnalysisRequest，而非 analysis_type/context 关键字。
            # 旧调用签名不匹配会 TypeError 并被下方 except 吞掉，导致高危告警自动分析链路一直静默失败。
            analysis = await svc.request_analysis(
                AIAnalysisRequest(
                    analysis_type="alert_correlation",
                    alert_id=alert_id or None,
                    asset_ids=asset_ids or None,
                )
            )
            analysis_id = str(getattr(analysis, "id", ""))
            await session.commit()

        if analysis_id:
            bus = get_event_bus()
            await bus.publish(
                DomainEvent(
                    event_type=AIOpsEvents.ANALYSIS_REQUESTED,
                    domain="aiops",
                    payload={
                        "analysis_id": analysis_id,
                        "analysis_type": "alert_correlation",
                        "alert_id": alert_id,
                        "severity": severity,
                    },
                    source="aiops_handler",
                    correlation_id=event.correlation_id or event.event_id,
                )
            )
        logger.info(
            "aiops: 告警触发AI分析 alert_id=%s severity=%s analysis_id=%s",
            alert_id,
            severity,
            analysis_id,
        )
    except Exception as e:
        logger.error("aiops: 告警触发AI分析失败: %s", e)


@idempotent_handler
async def on_analysis_completed_recommend(event: DomainEvent) -> None:
    """AI分析完成时记录结果."""
    payload = event.payload
    try:
        analysis_id = payload.get("analysis_id", "")
        result = payload.get("result", "")
        if not analysis_id:
            return
        logger.info(
            "aiops: AI分析完成 analysis_id=%s result_summary=%s",
            analysis_id,
            str(result)[:200] if result else "",
        )
        # AI分析结果可供知识中心推荐、策略引擎参考等
    except Exception as e:
        logger.error("aiops: AI分析完成处理失败: %s", e)


@idempotent_handler
async def on_analysis_failed_log(event: DomainEvent) -> None:
    """AI分析失败时记录降级."""
    payload = event.payload
    try:
        analysis_id = payload.get("analysis_id", "")
        error = payload.get("error", "")
        logger.warning("aiops: AI分析失败 analysis_id=%s error=%s", analysis_id, error)

        bus = get_event_bus()
        await bus.publish(
            DomainEvent(
                event_type=AIOpsEvents.ANALYSIS_DEGRADED,
                domain="aiops",
                payload={
                    "analysis_id": analysis_id,
                    "reason": f"analysis_failed: {error}",
                },
                source="aiops_handler",
                correlation_id=event.event_id,
            )
        )
    except Exception as e:
        logger.error("aiops: AI分析失败处理失败: %s", e)


# ---------------------------------------------------------------------------
# 执行运行器（唯一保留：EXECUTION_CREATED → 创建并运行执行记录）
# ---------------------------------------------------------------------------
# 注意：告警→策略匹配、策略审批→创建执行 两条链路统一由 policy 领域
# (policy/handlers.py) 负责，本模块此前重复订阅 ALERT_CREATED / POLICY_APPROVED
# 会导致同一告警双重匹配、同一审批双重创建执行。已移除重复 handler。


@idempotent_handler
async def on_execution_created_run(event) -> None:
    """EXECUTION_CREATED → 同步创建执行记录并入队（由 ExecutionWorker 真实运行）.

    关键修复（P0-03/P1-03）：不再用 `asyncio.create_task` 后台跑（进程退出即丢、
    异常不重试）。改为在本 handler 内同步创建执行记录 + 写 execution_queue 并提交；
    真正的长耗时执行交给 ExecutionWorker 领取运行（带租约/心跳/重试）。
    本 handler 失败会抛出异常，触发 outbox 重试，杜绝静默丢任务。
    """
    import json as _json

    from app.infra.database import async_session_factory
    from app.domains.automation.service import AutomationService
    from app.domains.automation.schemas import ExecutionCreate
    from app.domains.automation.models import ExecutionStatus
    from app.common.execution_queue import enqueue

    payload = event.payload
    asset_ids = payload.get("asset_ids", [])
    if isinstance(asset_ids, str):
        asset_ids = _json.loads(asset_ids)

    async with async_session_factory() as session:
        svc = AutomationService(session)
        exec_create = ExecutionCreate(
            execution_type=payload.get("execution_type", "script"),
            target_id=payload.get("target_id", ""),
            asset_ids=asset_ids,
            parameters=_json.dumps(payload.get("parameters", {})),
            trigger_source=payload.get("trigger_source", "policy"),
            trigger_source_id=payload.get("policy_id") or payload.get("alert_id"),
            is_dry_run=payload.get("is_dry_run", False),
        )
        execution = await svc.create_execution(exec_create)
        # 关联策略执行记录，打通 PolicyExecution↔Execution（审查 P0-02 全链）
        policy_execution_id = payload.get("policy_execution_id")
        if policy_execution_id:
            execution.policy_execution_id = policy_execution_id
            await session.flush()
            from app.domains.policy.service import PolicyService

            await PolicyService(session).mark_executing(
                policy_execution_id, str(execution.id)
            )
        # 需审批的不入队，等审批通过后再入队（见 automation API approve）
        if execution.status in (ExecutionStatus.PENDING, ExecutionStatus.APPROVED):
            await enqueue(session, str(execution.id))
        await session.commit()
        logger.info(
            "Execution %s created & enqueued (status=%s)",
            execution.id, execution.status,
        )


# ---------------------------------------------------------------------------
# 注册入口
# ---------------------------------------------------------------------------


def register_handlers() -> None:
    """注册AIOps领域的事件处理器."""
    bus = get_event_bus()

    # AI 分析链路
    bus.subscribe(AlertEvents.ALERT_CREATED, on_alert_created_trigger_analysis)
    bus.subscribe(AIOpsEvents.ANALYSIS_COMPLETED, on_analysis_completed_recommend)
    bus.subscribe(AIOpsEvents.ANALYSIS_FAILED, on_analysis_failed_log)

    # 执行运行器：策略链路最终产生 EXECUTION_CREATED 后由此创建并运行执行记录
    bus.subscribe(AutomationEvents.EXECUTION_CREATED, on_execution_created_run)

    logger.info("aiops领域事件处理器已注册 (含idempotency)")
