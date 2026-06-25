"""AIOps领域事件处理器."""

from __future__ import annotations

import asyncio
import logging
from collections import OrderedDict

from app.common.events import (
    DomainEvent,
    get_event_bus,
    AlertEvents,
    AIOpsEvents,
    PolicyEvents,
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

# 后台执行的长任务句柄集合，防止 task 被 GC 回收
_background_tasks: set[asyncio.Task] = set()


def idempotent_handler(func):
    """装饰器: 防止同一事件被同一处理器重复处理."""

    async def wrapper(event):
        key = f"{getattr(event, 'event_id', '')}:{func.__name__}"
        if key in _processed_events:
            logger.debug("aiops: 跳过重复处理 key=%s", key)
            return
        # LRU 淘汰：达上限时移除最旧的条目
        if len(_processed_events) >= _MAX_PROCESSED:
            _processed_events.popitem(last=False)
        _processed_events[key] = None
        return await func(event)

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

        analysis_id = None
        async with async_session_factory() as session:
            svc = AIOpsService(session)
            analysis = await svc.request_analysis(
                analysis_type="alert_correlation",
                context={
                    "alert_id": alert_id,
                    "severity": severity,
                    "asset_ids": asset_ids,
                    "context": payload.get("context", {}),
                    "source_event_id": event.event_id,
                },
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
# 从 common/event_handlers.py 迁移的处理器
# ---------------------------------------------------------------------------


@idempotent_handler
async def on_alert_created_match_policies(event) -> None:
    """告警创建 → 触发策略匹配."""
    payload = event.payload
    matched_policies = await _match_policies(payload)
    bus = get_event_bus()
    for policy_data in matched_policies:
        await bus.publish(
            DomainEvent(
                event_type=PolicyEvents.POLICY_TRIGGERED,
                domain="policy",
                payload=policy_data,
                source="policy_engine",
                correlation_id=event.correlation_id or event.event_id,
            )
        )


@idempotent_handler
async def on_policy_approved_create_execution(event) -> None:
    """策略审批通过 → 创建执行."""
    payload = event.payload
    bus = get_event_bus()
    # 安全解析 action_chain
    action_chain = payload.get("action_chain", [])
    first_action = {}
    if isinstance(action_chain, list) and len(action_chain) > 0:
        first = action_chain[0]
        if isinstance(first, list) and len(first) > 0:
            first_action = first[0] if isinstance(first[0], dict) else {}
        elif isinstance(first, dict):
            first_action = first
    await bus.publish(
        DomainEvent(
            event_type=AutomationEvents.EXECUTION_CREATED,
            domain="automation",
            payload={
                "execution_type": first_action.get("type", "script"),
                "target_id": first_action.get("target_id", ""),
                "asset_ids": payload.get("matched_assets", []),
                "trigger_source": "policy",
                "policy_id": payload.get("policy_id"),
                "alert_id": payload.get("alert_id"),
                "is_dry_run": False,
            },
            source="handler",
            correlation_id=event.event_id,
        )
    )


@idempotent_handler
async def on_execution_created_run(event) -> None:
    """EXECUTION_CREATED事件 → 后台创建执行记录并运行.

    run_execution 可能起子进程并阻塞最长 300 秒，若在事件总线串行派发中
    同步执行会卡死整个总线（含高优先级告警）。因此改为后台 task 执行，
    handler 立即返回不阻塞总线。
    """
    payload = event.payload
    task = asyncio.create_task(_run_execution_async(payload, event.event_id))
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)


async def _run_execution_async(payload: dict, correlation_id: str) -> None:
    """后台执行：创建执行记录并运行，完成后发布完成/失败事件."""
    try:
        from app.infra.database import async_session_factory
        from app.domains.automation.service import AutomationService
        from app.domains.automation.schemas import ExecutionCreate

        async with async_session_factory() as session:
            svc = AutomationService(session)
            import json as _json

            asset_ids = payload.get("asset_ids", [])
            if isinstance(asset_ids, str):
                asset_ids = _json.loads(asset_ids)

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
            await session.commit()

            # 创建成功后立即运行
            if execution.status in ("pending", "approved"):
                execution = await svc.run_execution(str(execution.id))
                await session.commit()

            logger.info(
                "Execution %s created and run: status=%s",
                execution.id,
                execution.status,
            )

            # 运行完成后发布完成/失败事件
            bus = get_event_bus()
            if execution.status == "completed":
                await bus.publish(
                    DomainEvent(
                        event_type=AutomationEvents.EXECUTION_COMPLETED,
                        domain="automation",
                        payload={
                            "execution_id": str(execution.id),
                            "alert_id": payload.get("alert_id"),
                            "policy_id": payload.get("policy_id"),
                            "result": execution.result,
                            "status": "completed",
                        },
                        source="automation",
                        correlation_id=correlation_id,
                    )
                )
            elif execution.status in ("failed", "blocked", "timeout"):
                await bus.publish(
                    DomainEvent(
                        event_type=AutomationEvents.EXECUTION_FAILED,
                        domain="automation",
                        payload={
                            "execution_id": str(execution.id),
                            "alert_id": payload.get("alert_id"),
                            "policy_id": payload.get("policy_id"),
                            "error_message": execution.error_message,
                            "status": execution.status,
                        },
                        source="automation",
                        correlation_id=correlation_id,
                    )
                )
    except Exception as e:
        logger.error("创建/运行执行失败: %s", e, exc_info=True)


# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------


async def _match_policies(alert_payload: dict) -> list[dict]:
    """匹配策略，返回匹配到的策略数据列表."""
    import json as _json

    try:
        from app.infra.database import async_session_factory
        from app.domains.policy.service import PolicyService

        async with async_session_factory() as session:
            svc = PolicyService(session)
            policies, _ = await svc.list_policies(status="active")
            results = []
            severity = alert_payload.get("severity", "")
            for policy in policies:
                trigger_type = policy.trigger_type
                matched = False
                # 解析 trigger_condition (可能是 JSON string 或 dict)
                tc = policy.trigger_condition or {}
                if isinstance(tc, str):
                    try:
                        tc = _json.loads(tc)
                    except Exception:
                        tc = {}
                # 解析 action_chain (可能是 JSON string 或 list)
                ac = policy.action_chain or []
                if isinstance(ac, str):
                    try:
                        ac = _json.loads(ac)
                    except Exception:
                        ac = []

                if trigger_type == "alert_severity" and severity:
                    target_sev = tc.get("severity", "")
                    if target_sev and severity == target_sev:
                        matched = True
                elif trigger_type == "event_type":
                    target_type = tc.get("event_type", "")
                    if target_type and alert_payload.get("event_type") == target_type:
                        matched = True
                elif trigger_type == "any_alert":
                    matched = True
                if matched:
                    results.append(
                        {
                            "policy_id": str(policy.id),
                            "policy_name": policy.name,
                            "action_chain": ac,
                            "requires_approval": policy.requires_approval,
                            "risk_level": policy.risk_level,
                            "matched_assets": alert_payload.get("asset_ids", []),
                            "alert_id": alert_payload.get("alert_id")
                            or alert_payload.get("rule_id"),
                        }
                    )
            return results
    except Exception as e:
        logger.error("匹配策略失败: %s", e)
        return []


# ---------------------------------------------------------------------------
# 注册入口
# ---------------------------------------------------------------------------


def register_handlers() -> None:
    """注册AIOps领域的事件处理器."""
    bus = get_event_bus()

    # 原有handlers
    bus.subscribe(AlertEvents.ALERT_CREATED, on_alert_created_trigger_analysis)
    bus.subscribe(AIOpsEvents.ANALYSIS_COMPLETED, on_analysis_completed_recommend)
    bus.subscribe(AIOpsEvents.ANALYSIS_FAILED, on_analysis_failed_log)

    # 从 event_handlers 迁移
    bus.subscribe(AlertEvents.ALERT_CREATED, on_alert_created_match_policies)
    bus.subscribe(PolicyEvents.POLICY_APPROVED, on_policy_approved_create_execution)
    bus.subscribe(AutomationEvents.EXECUTION_CREATED, on_execution_created_run)

    logger.info("aiops领域事件处理器已注册 (含idempotency)")
