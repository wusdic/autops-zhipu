"""异常检测 Service."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import NotFoundError, ValidationError
from app.common.repository import BaseRepository

logger = logging.getLogger(__name__)
from app.domains.anomaly.models import Anomaly

_SEVERITY_LEVELS = ["low", "medium", "high", "critical"]


class AnomalyService:
    """异常检测业务逻辑."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo: BaseRepository[Anomaly] = BaseRepository(session, Anomaly)

    # ------------------------------------------------------------------
    # CRUD helpers
    # ------------------------------------------------------------------
    async def _get_or_raise(self, anomaly_id: str) -> Anomaly:
        anomaly = await self.repo.get_by_id(anomaly_id)
        if not anomaly:
            raise NotFoundError(f"异常 {anomaly_id} 不存在")
        return anomaly

    @staticmethod
    def _normalize_meta(kwargs: dict) -> dict:
        """Accept either `metadata` or `meta` from callers; map to model.meta."""
        if "metadata" in kwargs:
            kwargs["meta"] = kwargs.pop("metadata")
        return kwargs

    # ------------------------------------------------------------------
    # List / Get
    # ------------------------------------------------------------------
    async def list_anomalies(
        self,
        status: str | None = None,
        severity: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Anomaly], int]:
        stmt = select(Anomaly)
        count_stmt = select(func.count()).select_from(Anomaly)

        if status:
            stmt = stmt.where(Anomaly.status == status)
            count_stmt = count_stmt.where(Anomaly.status == status)
        if severity:
            stmt = stmt.where(Anomaly.severity == severity)
            count_stmt = count_stmt.where(Anomaly.severity == severity)

        total = (await self.session.execute(count_stmt)).scalar() or 0
        offset = (page - 1) * page_size
        stmt = stmt.order_by(Anomaly.detected_at.desc()).offset(offset).limit(page_size)
        result = await self.session.execute(stmt)
        items = list(result.scalars().all())
        return items, total

    async def get_anomaly(self, anomaly_id: str) -> Anomaly:
        return await self._get_or_raise(anomaly_id)

    # ------------------------------------------------------------------
    # Create / Update / Delete
    # ------------------------------------------------------------------
    async def create_anomaly(self, **kwargs: Any) -> Anomaly:
        kwargs = self._normalize_meta(kwargs)
        if "detected_at" not in kwargs or kwargs["detected_at"] is None:
            kwargs["detected_at"] = datetime.now(timezone.utc)
        anomaly = await self.repo.create(**kwargs)
        await self.session.flush()
        await self.session.refresh(anomaly)
        return anomaly

    async def update_anomaly(self, anomaly_id: str, **kwargs: Any) -> Anomaly:
        kwargs = self._normalize_meta(kwargs)
        anomaly = await self._get_or_raise(anomaly_id)
        for key, value in kwargs.items():
            if value is not None and hasattr(anomaly, key):
                setattr(anomaly, key, value)
        await self.session.flush()
        await self.session.refresh(anomaly)
        return anomaly

    async def delete_anomaly(self, anomaly_id: str) -> None:
        anomaly = await self._get_or_raise(anomaly_id)
        await self.session.delete(anomaly)
        await self.session.flush()

    # ------------------------------------------------------------------
    # Lifecycle operations
    # ------------------------------------------------------------------
    async def acknowledge(self, anomaly_id: str, user_id: str | None = None) -> Anomaly:
        anomaly = await self._get_or_raise(anomaly_id)
        if anomaly.status == "closed":
            raise ValidationError("已关闭的异常无法认领")
        anomaly.status = "acknowledged"
        if user_id and not anomaly.assigned_to:
            anomaly.assigned_to = user_id
        await self.session.flush()
        await self.session.refresh(anomaly)
        return anomaly

    async def assign(self, anomaly_id: str, assignee_id: str) -> Anomaly:
        anomaly = await self._get_or_raise(anomaly_id)
        anomaly.assigned_to = assignee_id
        if anomaly.status == "open":
            anomaly.status = "acknowledged"
        await self.session.flush()
        await self.session.refresh(anomaly)
        return anomaly

    async def close(self, anomaly_id: str, user_id: str | None = None) -> Anomaly:
        anomaly = await self._get_or_raise(anomaly_id)
        anomaly.status = "closed"
        anomaly.resolved_at = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.refresh(anomaly)
        return anomaly

    async def escalate(
        self,
        anomaly_id: str,
        target_severity: str | None = None,
        reason: str | None = None,
    ) -> Anomaly:
        anomaly = await self._get_or_raise(anomaly_id)
        current_idx = (
            _SEVERITY_LEVELS.index(anomaly.severity)
            if anomaly.severity in _SEVERITY_LEVELS
            else 0
        )
        if target_severity:
            if target_severity not in _SEVERITY_LEVELS:
                raise ValidationError(f"无效的严重级别: {target_severity}")
            anomaly.severity = target_severity
        else:
            # auto-escalate to next level；已在最高级则跳过（避免无意义 append）
            next_idx = min(current_idx + 1, len(_SEVERITY_LEVELS) - 1)
            if next_idx == current_idx:
                # 已是最高级，记录日志后直接返回，不再 append escalation 记录
                logger.debug(
                    "异常 %s 已在最高级 %s，跳过升级", anomaly_id, anomaly.severity
                )
                return anomaly
            anomaly.severity = _SEVERITY_LEVELS[next_idx]

        # Track escalation reason in metadata
        # meta 可能是非 dict 类型（历史数据），需类型校验避免 dict(str) 抛错
        raw_meta = anomaly.meta
        meta = dict(raw_meta) if isinstance(raw_meta, dict) else {}
        escalations = meta.get("escalations", [])
        escalations.append(
            {
                "escalated_at": datetime.now(timezone.utc).isoformat(),
                "target_severity": anomaly.severity,
                "reason": reason,
            }
        )
        meta["escalations"] = escalations
        anomaly.meta = meta

        await self.session.flush()
        await self.session.refresh(anomaly)
        return anomaly

    async def convert_to_ticket(
        self,
        anomaly_id: str,
        title: str | None = None,
        description: str | None = None,
        priority: str | None = None,
    ) -> dict:
        """将异常转为工单。返回创建信息（不实际写工单表以避免循环依赖）。"""
        anomaly = await self._get_or_raise(anomaly_id)
        ticket_payload = {
            "source_type": "anomaly",
            "source_id": str(anomaly.id),
            "title": title or anomaly.title,
            "description": description or anomaly.description or anomaly.title,
            "priority": priority or _map_severity_to_priority(anomaly.severity),
            "asset_id": anomaly.asset_id,
            "assigned_to": anomaly.assigned_to,
        }
        # Attempt to call ticket service if available; otherwise return payload.
        # 注意：ImportError 表示工单服务未启用（正常降级），其它异常（DB 错误、
        # 字段非法等）是真实故障，必须区分处理，否则会静默吞掉问题。
        try:
            from app.domains.ticket.service import TicketService
        except ImportError:
            return {
                "anomaly_id": str(anomaly.id),
                "ticket_payload": ticket_payload,
                "created": False,
                "message": "Ticket service unavailable; payload returned for manual creation.",
            }

        try:
            ticket_svc = TicketService(self.session)
            create_fn = getattr(ticket_svc, "create_ticket", None)
            if create_fn is not None:
                ticket = await create_fn(**ticket_payload)
                # Mark anomaly as resolved
                anomaly.status = "closed"
                anomaly.resolved_at = datetime.now(timezone.utc)
                await self.session.flush()
                return {
                    "anomaly_id": str(anomaly.id),
                    "ticket_id": str(getattr(ticket, "id", "")),
                    "ticket": _safe_model_dict(ticket),
                    "created": True,
                }
        except Exception:
            # 工单服务存在但创建失败属真实故障，记录日志并抛出让调用方感知
            logger.exception("创建工单失败，异常 %s 转工单中断", anomaly.id)
            raise

        return {
            "anomaly_id": str(anomaly.id),
            "ticket_payload": ticket_payload,
            "created": False,
            "message": "Ticket service unavailable; payload returned for manual creation.",
        }

    # ------------------------------------------------------------------
    # Stats / Impact
    # ------------------------------------------------------------------
    async def stats(self) -> dict:
        """按 status / severity 维度统计."""
        total = (
            await self.session.execute(select(func.count()).select_from(Anomaly))
        ).scalar() or 0

        by_status: dict[str, int] = {}
        status_rows = await self.session.execute(
            select(Anomaly.status, func.count()).group_by(Anomaly.status)
        )
        for s, c in status_rows.all():
            by_status[s] = c

        by_severity: dict[str, int] = {}
        sev_rows = await self.session.execute(
            select(Anomaly.severity, func.count()).group_by(Anomaly.severity)
        )
        for s, c in sev_rows.all():
            by_severity[s] = c

        return {
            "total": total,
            "by_status": by_status,
            "by_severity": by_severity,
        }

    async def impact_analysis(self, anomaly_id: str) -> dict:
        """异常影响分析."""
        anomaly = await self._get_or_raise(anomaly_id)

        # Related anomalies on the same asset
        related: list[dict] = []
        if anomaly.asset_id:
            rel_rows = await self.session.execute(
                select(Anomaly)
                .where(Anomaly.asset_id == anomaly.asset_id)
                .where(Anomaly.id != anomaly.id)
                .order_by(Anomaly.detected_at.desc())
                .limit(20)
            )
            for r in rel_rows.scalars().all():
                related.append(
                    {
                        "id": str(r.id),
                        "title": r.title,
                        "severity": r.severity,
                        "status": r.status,
                        "detected_at": r.detected_at.isoformat()
                        if r.detected_at
                        else None,
                    }
                )

        severity_weight = {
            "low": 1,
            "medium": 2,
            "high": 3,
            "critical": 4,
        }.get(anomaly.severity, 1)

        # Simple impact scoring
        score = severity_weight * 25
        if anomaly.assigned_to is None:
            score += 10
        if anomaly.status in ("open",):
            score += 15

        score = min(score, 100)

        return {
            "anomaly_id": str(anomaly.id),
            "asset_id": anomaly.asset_id,
            "severity": anomaly.severity,
            "status": anomaly.status,
            "impact_score": score,
            "impact_level": _score_to_level(score),
            "related_anomalies": related,
            "recommendations": _recommendations(anomaly, score),
        }


# ----------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------
def _map_severity_to_priority(severity: str) -> str:
    return {
        "low": "low",
        "medium": "medium",
        "high": "high",
        "critical": "urgent",
    }.get(severity, "medium")


def _score_to_level(score: int) -> str:
    if score >= 80:
        return "critical"
    if score >= 60:
        return "high"
    if score >= 30:
        return "medium"
    return "low"


def _recommendations(anomaly: Anomaly, score: int) -> list[str]:
    recs: list[str] = []
    if anomaly.status == "open" and not anomaly.assigned_to:
        recs.append("立即指派责任人处理")
    if anomaly.severity in ("high", "critical"):
        recs.append("建议启动应急响应流程")
    if score >= 70:
        recs.append("建议通知相关业务方并准备升级工单")
    if anomaly.asset_id:
        recs.append(f"检查关联资产 {anomaly.asset_id} 的相关异常")
    if not recs:
        recs.append("持续观察异常趋势")
    return recs


def _safe_model_dict(obj: Any) -> dict:
    """Best-effort conversion of a SQLAlchemy model to dict."""
    try:
        from app.common.crud_service import model_to_dict

        return model_to_dict(obj)
    except Exception:
        return {"id": str(getattr(obj, "id", ""))}
