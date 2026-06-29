"""LLM 运行时模型配置.

让「模型服务」页注册的模型与全局配置真正生效：构造 LLMClient 时，
优先读取数据库 model_agents 中的默认/活跃模型与 system_settings 的全局配置，
回退到 env/yaml（LLMClient 默认）。
"""

from __future__ import annotations

import json
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.aiops.agent.llm_client import LLMClient

logger = logging.getLogger(__name__)


def _base_url_from_endpoint(endpoint: str) -> str:
    """模型注册里 endpoint 可能填到 .../chat/completions，统一规整为基础地址."""
    ep = (endpoint or "").rstrip("/")
    if ep.endswith("/chat/completions"):
        ep = ep[: -len("/chat/completions")]
    return ep


async def load_active_model(session: AsyncSession) -> dict | None:
    """读取默认/活跃模型；无则 None."""
    row = (
        await session.execute(
            text(
                "SELECT * FROM model_agents WHERE status = 'active' "
                "ORDER BY is_default DESC, created_at ASC LIMIT 1"
            )
        )
    ).mappings().first()
    if not row:
        return None

    api_key = ""
    if row.get("api_key_enc"):
        try:
            from app.common.crypto import decrypt_credential

            api_key = decrypt_credential(row["api_key_enc"])
        except Exception:  # noqa: BLE001
            logger.warning("model_agent api_key 解密失败 id=%s", row.get("id"))
    return {
        "id": row.get("id"),
        "name": row.get("name"),
        "base_url": _base_url_from_endpoint(row.get("endpoint", "")),
        "model_id": row.get("model_id"),
        "api_key": api_key,
        "max_tokens": row.get("max_tokens") or 4096,
        "temperature": row.get("temperature"),
        # NULL=自动(不发送)，1=开启，0=关闭；列可能在旧库不存在，用 get 容错
        "enable_thinking": row.get("enable_thinking"),
    }


async def _load_global_config(session: AsyncSession) -> dict:
    row = (
        await session.execute(
            text("SELECT svalue FROM system_settings WHERE skey = 'model_config'")
        )
    ).first()
    if row and row[0]:
        try:
            return json.loads(row[0])
        except (json.JSONDecodeError, ValueError):
            return {}
    return {}


async def build_llm_client(session: AsyncSession) -> LLMClient:
    """构造应用了运行时配置的 LLMClient（回退 env/yaml）."""
    client = LLMClient()
    try:
        active = await load_active_model(session)
        if active:
            if active["base_url"]:
                client.base_url = active["base_url"]
            if active["model_id"]:
                client.model = active["model_id"]
            client.api_key = active["api_key"] or "EMPTY"
            if active["max_tokens"]:
                client.max_tokens = int(active["max_tokens"])
            # 仅当显式配置(非 NULL)时才透传 enable_thinking；否则保持不发送（云端安全）
            et = active.get("enable_thinking")
            if et is not None:
                client.chat_template_kwargs = {"enable_thinking": bool(et)}
        cfg = await _load_global_config(session)
        if cfg.get("timeout"):
            client.timeout = int(cfg["timeout"])
        if cfg.get("max_tokens"):
            client.max_tokens = int(cfg["max_tokens"])
        # 注：default_model 存的是 model_agents.id，由保存配置时置 is_default 生效，
        # load_active_model 已据此选中正确模型，这里不再用 id 当作模型名覆盖。
    except Exception:  # noqa: BLE001
        logger.warning("加载运行时模型配置失败，回退 env/yaml", exc_info=True)
    return client
