"""巡检域 API Router."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import paginate, success
from app.domains.inspection.schemas import (
    InspectionPlanCreate, InspectionPlanUpdate, InspectionTaskCreate,
    InspectionTemplateCreate, InspectionTemplateUpdate,
)
from app.domains.inspection.service import InspectionService
from app.infra.database import get_db

router = APIRouter(prefix="/inspection", tags=["巡检"])


def _get_service(db: AsyncSession = Depends(get_db)) -> InspectionService:
    return InspectionService(db)


# --- Helpers ---
def _template_to_dict(t) -> dict:
    return {
        "id": t.id,
        "name": t.name,
        "description": t.description,
        "check_items": t.check_items,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "updated_at": t.updated_at.isoformat() if t.updated_at else None,
    }


def _plan_to_dict(p) -> dict:
    return {
        "id": p.id,
        "name": p.name,
        "template_id": p.template_id,
        "cron_expression": p.cron_expression,
        "target_assets": p.target_assets,
        "enabled": p.enabled,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }


def _task_to_dict(t) -> dict:
    return {
        "id": t.id,
        "plan_id": t.plan_id,
        "template_id": t.template_id,
        "status": t.status,
        "started_at": t.started_at.isoformat() if t.started_at else None,
        "completed_at": t.completed_at.isoformat() if t.completed_at else None,
        "summary": t.summary,
        "created_at": t.created_at.isoformat() if t.created_at else None,
    }


def _result_to_dict(r) -> dict:
    return {
        "id": r.id,
        "task_id": r.task_id,
        "asset_id": r.asset_id,
        "check_item": r.check_item,
        "check_type": getattr(r, "check_type", "baseline"),
        "status": r.status,
        "detail": r.detail,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


def _report_to_dict(r) -> dict:
    return {
        "id": r.id,
        "task_id": r.task_id,
        "report_data": r.report_data,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


# --- Templates ---
@router.get("/templates")
async def list_templates(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    svc: InspectionService = Depends(_get_service),
):
    items, total = await svc.list_templates(
        page=page, page_size=page_size, search=search,
    )
    return paginate([_template_to_dict(t) for t in items], total, page, page_size)


@router.post("/templates")
async def create_template(
    data: InspectionTemplateCreate,
    svc: InspectionService = Depends(_get_service),
):
    template = await svc.create_template(data)
    return success(_template_to_dict(template))


@router.get("/templates/{template_id}")
async def get_template(template_id: str, svc: InspectionService = Depends(_get_service)):
    template = await svc.get_template(template_id)
    return success(_template_to_dict(template))


@router.put("/templates/{template_id}")
async def update_template(
    template_id: str,
    data: InspectionTemplateUpdate,
    svc: InspectionService = Depends(_get_service),
):
    template = await svc.update_template(template_id, data)
    return success(_template_to_dict(template))


@router.delete("/templates/{template_id}")
async def delete_template(template_id: str, svc: InspectionService = Depends(_get_service)):
    await svc.delete_template(template_id)
    return success(message="删除成功")


# --- Plans ---
@router.get("/plans")
async def list_plans(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    svc: InspectionService = Depends(_get_service),
):
    items, total = await svc.list_plans(page=page, page_size=page_size)
    return paginate([_plan_to_dict(p) for p in items], total, page, page_size)


@router.post("/plans")
async def create_plan(
    data: InspectionPlanCreate,
    svc: InspectionService = Depends(_get_service),
):
    plan = await svc.create_plan(data)
    return success(_plan_to_dict(plan))


@router.get("/plans/{plan_id}")
async def get_plan(plan_id: str, svc: InspectionService = Depends(_get_service)):
    plan = await svc.get_plan(plan_id)
    return success(_plan_to_dict(plan))


@router.put("/plans/{plan_id}")
async def update_plan(
    plan_id: str,
    data: InspectionPlanUpdate,
    svc: InspectionService = Depends(_get_service),
):
    plan = await svc.update_plan(plan_id, data)
    return success(_plan_to_dict(plan))


@router.delete("/plans/{plan_id}")
async def delete_plan(plan_id: str, svc: InspectionService = Depends(_get_service)):
    await svc.delete_plan(plan_id)
    return success(message="删除成功")


# --- Tasks ---
@router.get("/tasks")
async def list_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    plan_id: str | None = None,
    svc: InspectionService = Depends(_get_service),
):
    items, total = await svc.list_tasks(
        page=page, page_size=page_size, status=status, plan_id=plan_id,
    )
    return paginate([_task_to_dict(t) for t in items], total, page, page_size)


@router.post("/tasks")
async def trigger_task(
    data: InspectionTaskCreate,
    svc: InspectionService = Depends(_get_service),
):
    task = await svc.trigger_task(data)
    # 确保任务落库后再启动后台执行（执行器使用独立 session 读取该任务）
    await svc.session.commit()
    from app.domains.inspection.executor import launch_inspection_task

    launch_inspection_task(str(task.id))
    return success(_task_to_dict(task))


@router.get("/tasks/{task_id}")
async def get_task(task_id: str, svc: InspectionService = Depends(_get_service)):
    task = await svc.get_task(task_id)
    return success(_task_to_dict(task))


# --- Results ---
@router.get("/results")
async def list_results(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    task_id: str | None = None,
    asset_id: str | None = None,
    status: str | None = None,
    svc: InspectionService = Depends(_get_service),
):
    items, total = await svc.list_results(
        page=page, page_size=page_size,
        task_id=task_id, asset_id=asset_id, status=status,
    )
    return paginate([_result_to_dict(r) for r in items], total, page, page_size)


@router.get("/results/{result_id}")
async def get_result(result_id: str, svc: InspectionService = Depends(_get_service)):
    result = await svc.get_result(result_id)
    return success(_result_to_dict(result))


# --- Reports ---
@router.get("/reports")
async def list_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    task_id: str | None = None,
    svc: InspectionService = Depends(_get_service),
):
    items, total = await svc.list_reports(
        page=page, page_size=page_size, task_id=task_id,
    )
    return paginate([_report_to_dict(r) for r in items], total, page, page_size)


@router.get("/reports/{report_id}")
async def get_report(report_id: str, svc: InspectionService = Depends(_get_service)):
    report = await svc.get_report(report_id)
    return success(_report_to_dict(report))


# --- 巡检规则 ---
def _rule_to_dict(r) -> dict:
    return {
        "id": r.id,
        "name": r.name,
        "category": r.category,
        "check_target": r.check_target,
        "condition": r.condition,
        "severity": r.severity,
        "asset_types": r.asset_types or [],
        "asset_count": len(r.asset_types or []),
        "remediation": r.remediation,
        "description": r.description,
        "enabled": r.enabled,
        "last_triggered": r.last_triggered_at.isoformat() if r.last_triggered_at else None,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


class InspectionRuleCreate(BaseModel):
    name: str
    category: str
    check_target: str | None = None
    condition: str | None = None
    severity: str = "medium"
    asset_types: list[str] | None = None
    remediation: str | None = None
    description: str | None = None
    enabled: bool = True


class InspectionRuleUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    check_target: str | None = None
    condition: str | None = None
    severity: str | None = None
    asset_types: list[str] | None = None
    remediation: str | None = None
    description: str | None = None
    enabled: bool | None = None


@router.get("/rules")
async def list_rules(
    category: str | None = None,
    keyword: str | None = None,
    severity: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    svc: InspectionService = Depends(_get_service),
):
    items, total = await svc.list_rules(
        category=category, keyword=keyword, severity=severity,
        page=page, page_size=page_size,
    )
    return paginate([_rule_to_dict(r) for r in items], total, page, page_size)


@router.post("/rules")
async def create_rule(data: InspectionRuleCreate, svc: InspectionService = Depends(_get_service)):
    rule = await svc.create_rule(data.model_dump(exclude_none=True))
    return success(_rule_to_dict(rule))


@router.get("/rules/{rule_id}")
async def get_rule(rule_id: str, svc: InspectionService = Depends(_get_service)):
    rule = await svc.get_rule(rule_id)
    return success(_rule_to_dict(rule))


@router.put("/rules/{rule_id}")
async def update_rule(rule_id: str, data: InspectionRuleUpdate, svc: InspectionService = Depends(_get_service)):
    rule = await svc.update_rule(rule_id, data.model_dump(exclude_unset=True))
    return success(_rule_to_dict(rule))


@router.delete("/rules/{rule_id}")
async def delete_rule(rule_id: str, svc: InspectionService = Depends(_get_service)):
    await svc.delete_rule(rule_id)
    return success(message="巡检规则已删除")


@router.post("/rules/{rule_id}/toggle")
async def toggle_rule(rule_id: str, svc: InspectionService = Depends(_get_service)):
    rule = await svc.toggle_rule(rule_id)
    return success(_rule_to_dict(rule))


# --- Stats ---
@router.get("/stats")
async def get_stats(svc: InspectionService = Depends(_get_service)):
    stats = await svc.get_stats()
    return success(stats)
