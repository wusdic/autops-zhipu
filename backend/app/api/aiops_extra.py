"""AIops 扩展 API — Prompt模板 & AI工具策略."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.common.response import paginate, success
from app.infra.database import get_db

router = APIRouter(tags=["AIops扩展"])


# ── Prompt 模板 ──────────────────────────────────────────────────


@router.get("/prompt-templates")
async def list_prompt_templates(
    search: str | None = None,
    usage: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """列出 Prompt 模板."""
    conditions = ["1=1"]
    params: dict = {}
    if search:
        conditions.append("name LIKE :search")
        params["search"] = "%" + search + "%"
    if usage:
        conditions.append("`usage` = :usage")
        params["usage"] = usage

    where = " AND ".join(conditions)
    count_sql = "SELECT COUNT(*) as cnt FROM aiops_prompt_templates WHERE " + where
    data_sql = (
        "SELECT * FROM aiops_prompt_templates WHERE "
        + where
        + " ORDER BY updated_at DESC LIMIT :limit OFFSET :offset"
    )

    try:
        cnt_result = await db.execute(text(count_sql), params)
        total = cnt_result.scalar() or 0

        params["limit"] = page_size
        params["offset"] = (page - 1) * page_size
        result = await db.execute(text(data_sql), params)
        items = [dict(row._mapping) for row in result.fetchall()]
    except Exception:
        # Table might not exist yet — return empty
        items = []
        total = 0

    return paginate(items, total, page, page_size)


@router.post("/prompt-templates")
async def create_prompt_template(
    body: dict,
    db: AsyncSession = Depends(get_db),
):
    """创建 Prompt 模板."""
    now = datetime.now(timezone.utc)
    item_id = str(uuid.uuid4())
    sql = text("""INSERT INTO aiops_prompt_templates
        (id, name, description, `usage`, content, variables, is_builtin, created_at, updated_at)
        VALUES (:id, :name, :description, :usage, :content, :variables, :is_builtin, :created_at, :updated_at)
    """)
    try:
        await db.execute(
            sql,
            {
                "id": item_id,
                "name": body.get("name", ""),
                "description": body.get("description", ""),
                "usage": body.get("usage", "general"),
                "content": body.get("content", ""),
                "variables": body.get("variables", ""),
                "is_builtin": body.get("is_builtin", False),
                "created_at": now,
                "updated_at": now,
            },
        )
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="创建失败")

    return success({"id": item_id, "name": body.get("name", "")})


@router.put("/prompt-templates/{template_id}")
async def update_prompt_template(
    template_id: str,
    body: dict,
    db: AsyncSession = Depends(get_db),
):
    """更新 Prompt 模板."""
    fields = []
    params: dict = {"id": template_id}
    for key in ["name", "description", "usage", "content", "variables"]:
        if key in body:
            sql_key = "`usage`" if key == "usage" else key
            fields.append(sql_key + " = :" + key)
            params[key] = body[key]
    fields.append("updated_at = :updated_at")
    params["updated_at"] = datetime.now(timezone.utc)

    if not fields:
        raise HTTPException(status_code=400, detail="无更新字段")

    sql = text(
        "UPDATE aiops_prompt_templates SET " + ", ".join(fields) + " WHERE id = :id"
    )
    try:
        await db.execute(sql, params)
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="更新失败")

    return success({"id": template_id})


@router.delete("/prompt-templates/{template_id}")
async def delete_prompt_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
):
    """删除 Prompt 模板."""
    try:
        await db.execute(
            text("DELETE FROM aiops_prompt_templates WHERE id = :id"),
            {"id": template_id},
        )
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="删除失败")

    return success({"id": template_id})


@router.post("/prompt-templates/{template_id}/test")
async def test_prompt_template(
    template_id: str,
    body: dict,
    db: AsyncSession = Depends(get_db),
):
    """测试 Prompt 模板."""
    result_row = await db.execute(
        text("SELECT * FROM aiops_prompt_templates WHERE id = :id"),
        {"id": template_id},
    )
    row = result_row.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="模板不存在")

    tpl = dict(row._mapping)
    content = tpl.get("content", "")
    variables = body.get("variables", {})
    for k, v in variables.items():
        content = content.replace("{{" + k + "}}", str(v))

    return success({"rendered": content, "template_name": tpl.get("name", "")})


# ── AI 工具策略 ──────────────────────────────────────────────────


@router.get("/tool-policies")
async def list_tool_policies(
    search: str | None = None,
    risk_level: str | None = None,
    approval_status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """列出 AI 工具策略."""
    conditions = ["1=1"]
    params: dict = {}
    if search:
        conditions.append("name LIKE :search")
        params["search"] = "%" + search + "%"
    if risk_level:
        conditions.append("risk_level = :risk_level")
        params["risk_level"] = risk_level
    if approval_status:
        conditions.append("approval_status = :approval_status")
        params["approval_status"] = approval_status

    where = " AND ".join(conditions)
    count_sql = "SELECT COUNT(*) as cnt FROM aiops_tool_policies WHERE " + where
    data_sql = (
        "SELECT * FROM aiops_tool_policies WHERE "
        + where
        + " ORDER BY updated_at DESC LIMIT :limit OFFSET :offset"
    )

    try:
        cnt_result = await db.execute(text(count_sql), params)
        total = cnt_result.scalar() or 0

        params["limit"] = page_size
        params["offset"] = (page - 1) * page_size
        result = await db.execute(text(data_sql), params)
        items = [dict(row._mapping) for row in result.fetchall()]
    except Exception:
        items = []
        total = 0

    return paginate(items, total, page, page_size)


@router.post("/tool-policies")
async def create_tool_policy(
    body: dict,
    db: AsyncSession = Depends(get_db),
):
    """创建 AI 工具策略."""
    now = datetime.now(timezone.utc)
    item_id = str(uuid.uuid4())
    sql = text("""INSERT INTO aiops_tool_policies
        (id, name, description, risk_level, approval_status, allowed_tools, denied_tools,
         requires_approval, max_auto_executions, created_at, updated_at)
        VALUES (:id, :name, :description, :risk_level, :approval_status, :allowed_tools, :denied_tools,
         :requires_approval, :max_auto_executions, :created_at, :updated_at)
    """)
    try:
        await db.execute(
            sql,
            {
                "id": item_id,
                "name": body.get("name", ""),
                "description": body.get("description", ""),
                "risk_level": body.get("risk_level", "medium"),
                "approval_status": body.get("approval_status", "pending"),
                "allowed_tools": body.get("allowed_tools", ""),
                "denied_tools": body.get("denied_tools", ""),
                "requires_approval": body.get("requires_approval", True),
                "max_auto_executions": body.get("max_auto_executions", 5),
                "created_at": now,
                "updated_at": now,
            },
        )
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="创建失败")

    return success({"id": item_id, "name": body.get("name", "")})


@router.put("/tool-policies/{policy_id}")
async def update_tool_policy(
    policy_id: str,
    body: dict,
    db: AsyncSession = Depends(get_db),
):
    """更新 AI 工具策略."""
    fields = []
    params: dict = {"id": policy_id}
    for key in [
        "name",
        "description",
        "risk_level",
        "approval_status",
        "allowed_tools",
        "denied_tools",
        "requires_approval",
        "max_auto_executions",
    ]:
        if key in body:
            fields.append(key + " = :" + key)
            params[key] = body[key]
    fields.append("updated_at = :updated_at")
    params["updated_at"] = datetime.now(timezone.utc)

    if not fields:
        raise HTTPException(status_code=400, detail="无更新字段")

    sql = text(
        "UPDATE aiops_tool_policies SET " + ", ".join(fields) + " WHERE id = :id"
    )
    try:
        await db.execute(sql, params)
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="更新失败")

    return success({"id": policy_id})


@router.delete("/tool-policies/{policy_id}")
async def delete_tool_policy(
    policy_id: str,
    db: AsyncSession = Depends(get_db),
):
    """删除 AI 工具策略."""
    try:
        await db.execute(
            text("DELETE FROM aiops_tool_policies WHERE id = :id"), {"id": policy_id}
        )
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="删除失败")

    return success({"id": policy_id})
