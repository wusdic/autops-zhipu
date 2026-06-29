"""模型服务管理 API（前端 ModelServicePage 的后端）.

挂载于 /aiops 前缀下：
- /aiops/agents            模型注册 CRUD
- /aiops/agents/{id}/test  连接测试
- /aiops/model-config      全局模型配置（默认模型/超时/max_tokens/温度）
api_key 加密存储；运行时由 model_runtime 读取生效。
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.auth_dependency import require_admin
from app.common.response import success
from app.infra.database import get_db

logger = logging.getLogger(__name__)

# 管理类操作要求管理员
agents_router = APIRouter(prefix="/agents", tags=["模型服务"], dependencies=[Depends(require_admin)])
config_router = APIRouter(tags=["模型服务"], dependencies=[Depends(require_admin)])


class ModelAgentCreate(BaseModel):
    name: str
    provider: str = "openai"
    model_id: str
    endpoint: str
    api_key: str | None = None
    max_tokens: int = 4096
    temperature: float = 0.3
    description: str | None = None
    is_default: bool = False


class ModelAgentUpdate(BaseModel):
    name: str | None = None
    provider: str | None = None
    model_id: str | None = None
    endpoint: str | None = None
    api_key: str | None = None
    max_tokens: int | None = None
    temperature: float | None = None
    description: str | None = None
    is_default: bool | None = None
    status: str | None = None


def _public(row: dict) -> dict:
    """脱敏输出（不返回密文）."""
    d = dict(row)
    d.pop("api_key_enc", None)
    d["has_api_key"] = bool(row.get("api_key_enc"))
    return d


@agents_router.get("")
async def list_model_agents(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        text("SELECT * FROM model_agents ORDER BY is_default DESC, created_at DESC")
    )).mappings().all()
    return success([_public(r) for r in rows])


@agents_router.post("")
async def create_model_agent(data: ModelAgentCreate, db: AsyncSession = Depends(get_db)):
    from app.common.crypto import encrypt_credential

    mid = str(uuid.uuid4())
    enc = encrypt_credential(data.api_key) if data.api_key else None
    if data.is_default:
        await db.execute(text("UPDATE model_agents SET is_default = 0"))
    await db.execute(
        text(
            "INSERT INTO model_agents (id, name, provider, model_id, endpoint, api_key_enc, "
            "max_tokens, temperature, description, is_default, status) VALUES "
            "(:id, :name, :provider, :model_id, :endpoint, :enc, :mt, :temp, :desc, :def, 'active')"
        ),
        {
            "id": mid, "name": data.name, "provider": data.provider,
            "model_id": data.model_id, "endpoint": data.endpoint, "enc": enc,
            "mt": data.max_tokens, "temp": data.temperature, "desc": data.description,
            "def": data.is_default,
        },
    )
    await db.commit()
    return success({"id": mid, "name": data.name, "status": "active"})


@agents_router.put("/{agent_id}")
async def update_model_agent(agent_id: str, data: ModelAgentUpdate, db: AsyncSession = Depends(get_db)):
    from app.common.crypto import encrypt_credential

    updates = data.model_dump(exclude_unset=True, exclude_none=True)
    if not updates:
        return success({"id": agent_id, "updated": False})
    if updates.get("is_default"):
        await db.execute(text("UPDATE model_agents SET is_default = 0"))
    set_clauses, params = [], {"id": agent_id}
    for k, v in updates.items():
        if k == "api_key":
            set_clauses.append("api_key_enc = :api_key_enc")
            params["api_key_enc"] = encrypt_credential(v) if v else None
            continue
        set_clauses.append(f"{k} = :{k}")
        params[k] = v
    await db.execute(
        text(f"UPDATE model_agents SET {', '.join(set_clauses)} WHERE id = :id"), params
    )
    await db.commit()
    return success({"id": agent_id, "updated": True})


@agents_router.delete("/{agent_id}")
async def delete_model_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    await db.execute(text("DELETE FROM model_agents WHERE id = :id"), {"id": agent_id})
    await db.commit()
    return success({"id": agent_id, "deleted": True})


@agents_router.post("/{agent_id}/test")
async def test_model_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    """真实连接测试：用该模型发起一次最小对话。"""
    from app.domains.aiops.agent.llm_client import LLMClient
    from app.domains.aiops.model_runtime import _base_url_from_endpoint

    row = (await db.execute(
        text("SELECT * FROM model_agents WHERE id = :id"), {"id": agent_id}
    )).mappings().first()
    if not row:
        return success({"success": False, "error": "模型不存在"})

    api_key = ""
    if row.get("api_key_enc"):
        try:
            from app.common.crypto import decrypt_credential
            api_key = decrypt_credential(row["api_key_enc"])
        except Exception:  # noqa: BLE001
            pass

    client = LLMClient()
    client.base_url = _base_url_from_endpoint(row.get("endpoint", "")) or client.base_url
    client.model = row.get("model_id") or client.model
    client.api_key = api_key or "EMPTY"
    # 本地大模型（尤其带"思考"的推理模型 / 普通硬件）连一句 ping 也可能数十秒，
    # 10s 会把正常推理误判为超时失败（云端 API 毫秒级则通过）。放宽到 60s，
    # 并把 ping 的 max_tokens 压到极小，让其尽快返回。
    client.timeout = 60
    client.max_tokens = 16

    start = time.monotonic()
    try:
        reply = await client._do_chat([{"role": "user", "content": "ping"}])
        latency = int((time.monotonic() - start) * 1000)
        return success({
            "success": True, "name": row.get("name"), "latency": latency,
            "response": (reply or "")[:200],
        })
    except httpx.TimeoutException:
        latency = int((time.monotonic() - start) * 1000)
        return success({
            "success": False, "name": row.get("name"), "latency": latency,
            "error": "连接超时（60s）：本地模型可能正在加载或推理过慢，请确认服务已就绪后重试；"
                     "或确认端点为 OpenAI 兼容地址（.../v1）。",
        })
    except Exception as exc:  # noqa: BLE001
        latency = int((time.monotonic() - start) * 1000)
        return success({
            "success": False, "name": row.get("name"), "latency": latency,
            "error": str(exc)[:300] or "连接失败：请检查端点、端口与网络可达性。",
        })


@config_router.get("/model-config")
async def get_model_config(db: AsyncSession = Depends(get_db)):
    row = (await db.execute(
        text("SELECT svalue FROM system_settings WHERE skey = 'model_config'")
    )).first()
    if row and row[0]:
        try:
            return success(json.loads(row[0]))
        except (json.JSONDecodeError, ValueError):
            pass
    return success({"default_model": "", "timeout": 60, "max_tokens": 4096, "temperature": 0.3})


@config_router.post("/model-config")
async def save_model_config(data: dict, db: AsyncSession = Depends(get_db)):
    value = json.dumps(data, ensure_ascii=False)
    ts = datetime.now(timezone.utc)
    # 方言安全的 upsert：先 UPDATE，无命中再 INSERT
    res = await db.execute(
        text("UPDATE system_settings SET svalue = :v, updated_at = :ts WHERE skey = 'model_config'"),
        {"v": value, "ts": ts},
    )
    if (res.rowcount or 0) == 0:
        await db.execute(
            text("INSERT INTO system_settings (skey, svalue, updated_at) VALUES ('model_config', :v, :ts)"),
            {"v": value, "ts": ts},
        )

    # 让「默认模型」真正生效：运行时 load_active_model 按 is_default 选模型，
    # 因此把所选模型置为默认（其余清零），否则切换默认模型不会改变实际调用的模型。
    default_id = data.get("default_model")
    if default_id:
        exists = (
            await db.execute(
                text("SELECT 1 FROM model_agents WHERE id = :id"), {"id": default_id}
            )
        ).first()
        if exists:
            await db.execute(text("UPDATE model_agents SET is_default = 0"))
            await db.execute(
                text("UPDATE model_agents SET is_default = 1, status = 'active' WHERE id = :id"),
                {"id": default_id},
            )

    await db.commit()
    return success({"saved": True})
