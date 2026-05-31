"""通知渠道配置 API."""
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.integrations.registry import NotificationRegistry
from app.integrations.base import NotificationPayload
from app.common.response import success

router = APIRouter(prefix="/notification-channels", tags=["通知渠道"])

class ChannelConfig(BaseModel):
    name: str
    enabled: bool = True
    config: dict = {}

class TestMessage(BaseModel):
    message: str = "测试通知"

@router.get("")
async def list_channels():
    """列出所有通知渠道及状态."""
    reg = NotificationRegistry.get_instance()
    channels = []
    for name in reg.list_channels():
        ch = reg.get(name)
        channels.append({
            "name": name,
            "enabled": ch.enabled if ch else False,
            "description": getattr(ch, 'description', ''),
        })
    # 也包含内置但未注册的
    for builtin in ["webhook", "dingtalk", "email"]:
        if not any(c["name"] == builtin for c in channels):
            channels.append({"name": builtin, "enabled": False, "description": f"{builtin}通知渠道"})
    return success(channels)

@router.patch("/{channel_name}")
async def update_channel(channel_name: str, body: ChannelConfig):
    """更新渠道配置."""
    reg = NotificationRegistry.get_instance()
    ch = reg.get(channel_name)
    if ch:
        # 对于有 _enabled 属性的渠道，更新其状态
        if hasattr(ch, '_enabled'):
            ch._enabled = body.enabled
        if body.config:
            if hasattr(ch, 'config'):
                ch.config = body.config
            elif hasattr(ch, '_url') and 'url' in body.config:
                ch._url = body.config['url']
            elif hasattr(ch, '_secret') and 'secret' in body.config:
                ch._secret = body.config['secret']
    return success({"name": channel_name, "enabled": body.enabled})

@router.post("/{channel_name}/test")
async def test_channel(channel_name: str, body: TestMessage):
    """测试渠道连通性."""
    reg = NotificationRegistry.get_instance()
    ch = reg.get(channel_name)
    if not ch:
        raise HTTPException(404, f"渠道 {channel_name} 未注册")
    payload = NotificationPayload(
        title=body.message,
        message=body.message,
        severity="info",
    )
    ok = await ch.send(payload)
    return success({"sent": ok})
