"""巡检执行引擎.

把巡检任务真正跑起来：按模板 ``check_items`` 对目标资产逐项检查，
写入 ``InspectionResult``，汇总 ``InspectionReport``，并更新任务状态。

目标资产来源：任务关联计划的 ``target_assets``；无计划时取全部未删除资产。
设备指标由 ``app.workers.device_inspect.collect_device_info`` 通过凭据登录采集。
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select

from app.domains.inspection.models import (
    InspectionPlan,
    InspectionReport,
    InspectionResult,
    InspectionTask,
    InspectionTemplate,
)

logger = logging.getLogger(__name__)

# 后台任务句柄，防止被 GC
_running_tasks: set[asyncio.Task] = set()

# 默认巡检项（模板未定义 check_items 时使用），按 check_type 分类。
# 可用 metric 见 device_inspect 归一化输出；op 支持 > >= < <= == != is_true is_false。
_DEFAULT_CHECK_ITEMS: list[dict[str, Any]] = [
    # 基线
    {"key": "reachable", "name": "可达性", "metric": "reachable", "op": "is_false", "severity": "fail", "check_type": "baseline"},
    # 资源
    {"key": "cpu_load", "name": "CPU单核负载", "metric": "load_per_core", "op": ">", "threshold": 4, "warn": 2, "severity": "fail", "check_type": "resource"},
    {"key": "memory", "name": "内存使用率", "metric": "mem_used_percent", "op": ">", "threshold": 90, "warn": 80, "severity": "warning", "check_type": "resource"},
    {"key": "swap", "name": "Swap使用率", "metric": "swap_used_percent", "op": ">", "threshold": 80, "warn": 50, "severity": "warning", "check_type": "resource"},
    {"key": "disk", "name": "磁盘使用率", "metric": "disk_used_percent_max", "op": ">", "threshold": 90, "warn": 80, "severity": "fail", "check_type": "resource"},
    {"key": "inode", "name": "inode使用率", "metric": "inode_used_percent_max", "op": ">", "threshold": 90, "warn": 80, "severity": "fail", "check_type": "resource"},
    {"key": "zombie", "name": "僵尸进程数", "metric": "zombie_count", "op": ">", "threshold": 10, "warn": 3, "severity": "warning", "check_type": "resource"},
    # 安全基线
    {"key": "ntp", "name": "时间同步(NTP)", "metric": "ntp_synchronized", "op": "is_false", "severity": "warning", "check_type": "security"},
    {"key": "ssh_root", "name": "SSH允许root登录", "metric": "ssh_permit_root", "op": "is_true", "severity": "warning", "check_type": "security"},
]


def _breach(value: float, op: str, threshold: float) -> bool:
    if op == ">":
        return value > threshold
    if op == ">=":
        return value >= threshold
    if op == "<":
        return value < threshold
    if op == "<=":
        return value <= threshold
    if op == "==":
        return value == threshold
    if op == "!=":
        return value != threshold
    return False


def evaluate_check_item(item: dict[str, Any], info: dict[str, Any]) -> tuple[str, dict]:
    """根据单个巡检项与设备指标返回 (status, detail).

    status ∈ {pass, warning, fail}。
    """
    metric = item.get("metric", "")
    severity = item.get("severity", "warning")
    name = item.get("name", item.get("key", metric))
    op = item.get("op", ">")
    value = info.get(metric)
    detail: dict[str, Any] = {"name": name, "metric": metric, "value": value}

    # 布尔类巡检项（is_true / is_false）
    if op in ("is_true", "is_false"):
        # 未采集到（None）且非可达性项 → 视为不适用，不计失败，避免噪声
        if value is None and metric != "reachable":
            detail["message"] = "指标未采集（方式不支持）"
            return "pass", detail
        bval = bool(value)
        breach = bval if op == "is_true" else (not bval)
        if metric == "reachable" and not bval:
            detail["message"] = info.get("error") or "设备不可达/采集失败"
        if breach:
            detail.setdefault("message", f"{name} 命中条件({op})")
            return severity, detail
        return "pass", detail

    # 数值类
    if not info.get("reachable") and metric != "reachable":
        detail["message"] = "设备不可达，未采集"
        return "warning", detail
    if value is None:
        detail["message"] = "指标不可用（采集失败或方式不支持）"
        return "warning", detail

    threshold = item.get("threshold")
    warn = item.get("warn")
    try:
        fvalue = float(value)
    except (ValueError, TypeError):
        detail["message"] = "指标非数值"
        return "warning", detail

    if threshold is not None and _breach(fvalue, op, float(threshold)):
        detail["threshold"] = threshold
        detail["message"] = f"{name}={fvalue} 触发阈值 {op}{threshold}"
        return severity, detail
    if warn is not None and _breach(fvalue, op, float(warn)):
        detail["threshold"] = warn
        detail["message"] = f"{name}={fvalue} 触发预警 {op}{warn}"
        return "warning", detail
    return "pass", detail


async def _resolve_targets(session, task: InspectionTask) -> list[str]:
    """确定巡检目标资产 ID 列表."""
    if task.plan_id:
        plan = await session.get(InspectionPlan, task.plan_id)
        if plan and plan.target_assets:
            return [str(a) for a in plan.target_assets]
    # 无计划或计划未指定：取全部未删除资产
    from app.domains.asset.models import Asset

    result = await session.execute(
        select(Asset.id).where(Asset.is_deleted == False)  # noqa: E712
    )
    return [str(r) for r in result.scalars().all()]


async def run_inspection_task(task_id: str) -> None:
    """执行一次巡检任务（后台运行，使用独立 session）."""
    from app.common.credentials import resolve_asset_credential
    from app.domains.asset.models import Asset
    from app.infra.database import async_session_factory
    from app.workers.device_inspect import collect_device_info

    async with async_session_factory() as session:
        task = await session.get(InspectionTask, task_id)
        if not task:
            logger.warning("巡检任务不存在: %s", task_id)
            return
        try:
            task.status = "running"
            task.started_at = datetime.now(timezone.utc)
            await session.flush()

            template = await session.get(InspectionTemplate, task.template_id)
            check_items = (template.check_items if template else None) or _DEFAULT_CHECK_ITEMS

            target_ids = await _resolve_targets(session, task)
            logger.info("巡检任务 %s 开始：%d 个目标资产", task_id, len(target_ids))

            counts = {"pass": 0, "warning": 0, "fail": 0}
            per_asset: list[dict[str, Any]] = []

            for asset_id in target_ids:
                asset = await session.get(Asset, asset_id)
                if not asset or asset.is_deleted:
                    continue
                asset_dict = {
                    "ip": asset.ip,
                    "port": asset.port,
                    "asset_type": asset.asset_type,
                    "os_type": asset.os_type,
                }
                cred = await resolve_asset_credential(
                    session, asset_id, prefer=["ssh_key", "ssh_password", "windows_password", "snmp_community"]
                )
                info = await collect_device_info(asset_dict, cred)

                asset_summary = {
                    "asset_id": asset_id,
                    "hostname": asset.hostname or info.get("hostname"),
                    "ip": asset.ip,
                    "method": info.get("method"),
                    "reachable": info.get("reachable"),
                    "metrics": {
                        "cpu_count": info.get("cpu_count"),
                        "load_1m": info.get("load_1m"),
                        "mem_used_percent": info.get("mem_used_percent"),
                        "disk_used_percent_max": info.get("disk_used_percent_max"),
                        "uptime_seconds": info.get("uptime_seconds"),
                    },
                    "items": [],
                }

                for item in check_items:
                    status, detail = evaluate_check_item(item, info)
                    counts[status] = counts.get(status, 0) + 1
                    check_type = item.get("check_type", "baseline")
                    session.add(
                        InspectionResult(
                            task_id=task_id,
                            asset_id=asset_id,
                            check_item=item.get("name", item.get("key", "check")),
                            check_type=check_type,
                            status=status,
                            detail=detail,
                        )
                    )
                    asset_summary["items"].append(
                        {"status": status, "check_type": check_type, **detail}
                    )

                per_asset.append(asset_summary)

            summary = {
                "targets": len(target_ids),
                "checked_assets": len(per_asset),
                "results": counts,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }
            task.summary = summary
            task.status = "completed"
            task.completed_at = datetime.now(timezone.utc)

            session.add(
                InspectionReport(
                    task_id=task_id,
                    report_data={"summary": summary, "assets": per_asset},
                )
            )
            await session.commit()
            logger.info("巡检任务 %s 完成：%s", task_id, counts)
        except Exception as exc:  # noqa: BLE001
            logger.exception("巡检任务执行失败 task=%s", task_id)
            await session.rollback()
            try:
                task = await session.get(InspectionTask, task_id)
                if task:
                    task.status = "failed"
                    task.completed_at = datetime.now(timezone.utc)
                    task.summary = {"error": str(exc)[:500]}
                    await session.commit()
            except Exception:  # noqa: BLE001
                logger.exception("写入巡检失败状态再次异常 task=%s", task_id)


def launch_inspection_task(task_id: str) -> None:
    """以后台 asyncio 任务方式启动巡检执行（fire-and-forget，保句柄防 GC）."""
    t = asyncio.create_task(run_inspection_task(task_id))
    _running_tasks.add(t)
    t.add_done_callback(_running_tasks.discard)
