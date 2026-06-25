"""报告生成器.

把报告任务真正生成出来：汇总资产 / 告警 / 最近巡检数据，渲染为自包含 HTML，
落盘到报告目录，写入 ``ReportArchive`` 并更新 ``ReportTask`` 状态与下载路径。

报告目录优先取环境变量 ``AUTOPS_REPORTS_DIR``，否则用 ``<cwd>/data/reports``。
"""

from __future__ import annotations

import asyncio
import html
import logging
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import func, select

from app.domains.report.models import ReportArchive, ReportTask, ReportTemplate

logger = logging.getLogger(__name__)

_running_tasks: set[asyncio.Task] = set()


def _reports_dir() -> Path:
    candidate = os.getenv("AUTOPS_REPORTS_DIR") or str(Path.cwd() / "data" / "reports")
    try:
        Path(candidate).mkdir(parents=True, exist_ok=True)
        return Path(candidate)
    except Exception:  # noqa: BLE001
        fallback = Path(tempfile.gettempdir()) / "autops_reports"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


async def _gather_data(session) -> dict[str, Any]:
    """汇总报告所需数据."""
    from app.domains.alert.models import Alert
    from app.domains.asset.models import Asset
    from app.domains.inspection.models import InspectionTask

    data: dict[str, Any] = {}

    # 资产统计
    total_assets = (
        await session.execute(
            select(func.count()).select_from(Asset).where(Asset.is_deleted == False)  # noqa: E712
        )
    ).scalar() or 0
    by_status = dict(
        (
            await session.execute(
                select(Asset.status, func.count(Asset.id))
                .where(Asset.is_deleted == False)  # noqa: E712
                .group_by(Asset.status)
            )
        ).all()
    )
    by_type = dict(
        (
            await session.execute(
                select(Asset.asset_type, func.count(Asset.id))
                .where(Asset.is_deleted == False)  # noqa: E712
                .group_by(Asset.asset_type)
            )
        ).all()
    )
    data["assets"] = {"total": total_assets, "by_status": by_status, "by_type": by_type}

    # 告警统计
    alert_by_sev = dict(
        (
            await session.execute(
                select(Alert.severity, func.count(Alert.id)).group_by(Alert.severity)
            )
        ).all()
    )
    firing = (
        await session.execute(
            select(func.count()).select_from(Alert).where(Alert.status == "firing")
        )
    ).scalar() or 0
    data["alerts"] = {"by_severity": alert_by_sev, "firing": firing}

    # 最近一次完成的巡检任务
    last_task = (
        await session.execute(
            select(InspectionTask)
            .where(InspectionTask.status == "completed")
            .order_by(InspectionTask.completed_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    data["last_inspection"] = last_task.summary if last_task else None

    return data


def _render_html(template_name: str, data: dict[str, Any]) -> str:
    """渲染自包含 HTML 报告（不引入模板引擎依赖）."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    a = data.get("assets", {})
    al = data.get("alerts", {})
    insp = data.get("last_inspection")

    def _rows(d: dict) -> str:
        return "".join(
            f"<tr><td>{html.escape(str(k))}</td><td>{html.escape(str(v))}</td></tr>"
            for k, v in (d or {}).items()
        ) or "<tr><td colspan=2>无数据</td></tr>"

    insp_html = "<p>暂无已完成巡检</p>"
    if insp:
        results = insp.get("results", {})
        insp_html = (
            f"<p>目标资产 {insp.get('targets', 0)}，已检 {insp.get('checked_assets', 0)}；"
            f"通过 {results.get('pass', 0)} / 预警 {results.get('warning', 0)} / 失败 {results.get('fail', 0)}</p>"
        )

    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>{html.escape(template_name)} - AUTOPS 运维报告</title>
<style>
body{{font-family:-apple-system,Segoe UI,Microsoft YaHei,sans-serif;margin:32px;color:#1d2129}}
h1{{font-size:22px}} h2{{font-size:16px;margin-top:24px;border-left:4px solid #165dff;padding-left:8px}}
table{{border-collapse:collapse;width:360px;margin-top:8px}}
td,th{{border:1px solid #e5e6eb;padding:6px 12px;font-size:14px}}
.meta{{color:#86909c;font-size:13px}}
</style></head>
<body>
<h1>{html.escape(template_name)}</h1>
<p class="meta">生成时间：{now}</p>
<h2>资产概览</h2>
<p>资产总数：<b>{a.get('total', 0)}</b></p>
<table><tr><th>状态</th><th>数量</th></tr>{_rows(a.get('by_status', {}))}</table>
<table><tr><th>类型</th><th>数量</th></tr>{_rows(a.get('by_type', {}))}</table>
<h2>告警概览</h2>
<p>活跃告警（firing）：<b>{al.get('firing', 0)}</b></p>
<table><tr><th>严重度</th><th>数量</th></tr>{_rows(al.get('by_severity', {}))}</table>
<h2>最近巡检</h2>
{insp_html}
</body></html>
"""


async def build_report(task_id: str) -> None:
    """生成报告任务对应的报告文件（后台运行，独立 session）."""
    from app.infra.database import async_session_factory

    async with async_session_factory() as session:
        task = await session.get(ReportTask, task_id)
        if not task:
            logger.warning("报告任务不存在: %s", task_id)
            return
        try:
            task.status = "running"
            task.started_at = datetime.now(timezone.utc)
            await session.flush()

            template = await session.get(ReportTemplate, task.template_id)
            template_name = template.name if template else "运维报告"

            data = await _gather_data(session)
            html_content = _render_html(template_name, data)

            filename = f"report_{task_id}.html"
            path = _reports_dir() / filename
            path.write_text(html_content, encoding="utf-8")
            size = path.stat().st_size

            task.status = "completed"
            task.completed_at = datetime.now(timezone.utc)
            task.result_path = str(path)
            session.add(
                ReportArchive(
                    task_id=task_id,
                    filename=filename,
                    file_size=size,
                    storage_path=str(path),
                )
            )
            await session.commit()
            logger.info("报告生成完成 task=%s path=%s size=%d", task_id, path, size)
        except Exception:  # noqa: BLE001
            logger.exception("报告生成失败 task=%s", task_id)
            await session.rollback()
            try:
                task = await session.get(ReportTask, task_id)
                if task:
                    task.status = "failed"
                    task.completed_at = datetime.now(timezone.utc)
                    await session.commit()
            except Exception:  # noqa: BLE001
                logger.exception("写入报告失败状态再次异常 task=%s", task_id)


def launch_report_build(task_id: str) -> None:
    """以后台 asyncio 任务方式启动报告生成."""
    t = asyncio.create_task(build_report(task_id))
    _running_tasks.add(t)
    t.add_done_callback(_running_tasks.discard)
