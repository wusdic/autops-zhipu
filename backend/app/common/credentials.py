"""资产凭据解析.

根据 ``asset_id`` 查找绑定的凭据，解密后归一化为可直接用于 SSH / WinRM /
SNMP 登录的结构。约定密文 ``encrypted_data`` 解密后为 JSON 对象，例如::

    {"username": "root", "password": "***"}
    {"username": "root", "private_key": "-----BEGIN ..."}
    {"community": "public"}              # SNMP

为兼容历史/简单写法，若解密结果不是 JSON 对象，则按裸字符串处理：
SNMP 类凭据当作 community，其余当作 password。
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.crypto import decrypt_credential
from app.domains.config.models import Credential, CredentialBinding

logger = logging.getLogger(__name__)


@dataclass
class DeviceCredential:
    """归一化后的设备登录凭据."""

    cred_type: str = ""
    username: str | None = None
    password: str | None = None
    private_key: str | None = None
    community: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


# cred_type 与“访问方式”的粗映射，用于默认排序选取
SSH_TYPES = {"ssh_password", "ssh_key"}
WINDOWS_TYPES = {"windows_password", "winrm_password"}
SNMP_TYPES = {"snmp_community", "snmp"}


def _parse_secret(cred_type: str, plain: str) -> DeviceCredential:
    """把解密后的明文解析为 DeviceCredential."""
    data: dict[str, Any]
    try:
        parsed = json.loads(plain)
        data = parsed if isinstance(parsed, dict) else {}
    except (json.JSONDecodeError, ValueError):
        data = {}

    if not data:
        # 裸字符串：SNMP 当 community，其余当 password
        if cred_type in SNMP_TYPES:
            return DeviceCredential(cred_type=cred_type, community=plain, raw={})
        return DeviceCredential(cred_type=cred_type, password=plain, raw={})

    return DeviceCredential(
        cred_type=cred_type,
        username=data.get("username") or data.get("user"),
        password=data.get("password") or data.get("pass"),
        private_key=data.get("private_key") or data.get("key"),
        community=data.get("community"),
        raw={k: v for k, v in data.items() if k not in ("password", "private_key", "pass", "key")},
    )


async def resolve_asset_credential(
    session: AsyncSession,
    asset_id: str,
    prefer: list[str] | None = None,
) -> DeviceCredential | None:
    """解析某资产可用的登录凭据.

    Args:
        session: DB 会话
        asset_id: 资产 ID
        prefer: cred_type 优先序（如 ["ssh_key","ssh_password"]）；命中优先返回

    Returns:
        DeviceCredential；无绑定凭据时返回 None。解密失败的凭据会被跳过。
    """
    result = await session.execute(
        select(Credential)
        .join(CredentialBinding, CredentialBinding.credential_id == Credential.id)
        .where(
            CredentialBinding.asset_id == asset_id,
            Credential.is_deleted == False,  # noqa: E712
        )
    )
    creds = list(result.scalars().all())
    if not creds:
        return None

    if prefer:
        order = {t: i for i, t in enumerate(prefer)}
        creds.sort(key=lambda c: order.get(c.cred_type, len(prefer)))

    for cred in creds:
        try:
            plain = decrypt_credential(cred.encrypted_data)
        except Exception as exc:  # noqa: BLE001
            logger.warning("凭据解密失败 cred_id=%s: %s", cred.id, exc)
            continue
        return _parse_secret(cred.cred_type, plain)

    return None
