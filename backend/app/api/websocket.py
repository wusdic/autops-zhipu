"""WebSocket 实时推送端点.

路径: /api/v1/ws
认证: 通过 query param ?token=<jwt>
支持频道:
  - alerts: 告警实时推送
  - executions: 执行状态/日志推送
  - events: 事件流
  - notifications: 通知推送
  - system: 系统状态
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from app.common.auth import decode_token
from app.common.events import (
    AlertEvents,
    AutomationEvents,
    DomainEvent,
    EventEvents,
    NotificationEvents,
    TicketEvents,
    get_event_bus,
)

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """WebSocket 连接管理器."""

    def __init__(self):
        self._connections: dict[str, WebSocket] = {}  # client_id -> ws
        self._subscriptions: dict[str, set[str]] = {}  # client_id -> set of channels
        self._user_connections: dict[str, set[str]] = {}  # user_id -> set of client_ids
        self._lock = asyncio.Lock()

    async def connect(
        self, client_id: str, websocket: WebSocket, user_id: str = ""
    ) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections[client_id] = websocket
            self._subscriptions[client_id] = set()
            if user_id:
                if user_id not in self._user_connections:
                    self._user_connections[user_id] = set()
                self._user_connections[user_id].add(client_id)
        logger.info("WS客户端连接: %s (user=%s)", client_id[:8], user_id)

    async def disconnect(self, client_id: str, user_id: str = "") -> None:
        async with self._lock:
            self._connections.pop(client_id, None)
            self._subscriptions.pop(client_id, None)
            if user_id and user_id in self._user_connections:
                self._user_connections[user_id].discard(client_id)
                if not self._user_connections[user_id]:
                    del self._user_connections[user_id]
        logger.info("WS客户端断开: %s", client_id[:8])

    async def subscribe(self, client_id: str, channels: list[str]) -> None:
        async with self._lock:
            if client_id in self._subscriptions:
                self._subscriptions[client_id].update(channels)

    async def unsubscribe(self, client_id: str, channels: list[str]) -> None:
        async with self._lock:
            if client_id in self._subscriptions:
                self._subscriptions[client_id].difference_update(channels)

    async def broadcast(self, channel: str, message: dict[str, Any]) -> None:
        """向订阅了指定频道的所有客户端广播消息.

        只有明确订阅了该频道的客户端才会收到；未订阅的客户端不接收
        （避免新连接意外收到全平台数据）。
        """
        async with self._lock:
            disconnected = []
            targets = [
                (client_id, ws)
                for client_id, ws in self._connections.items()
                if channel in self._subscriptions.get(client_id, set())
            ]
        # 锁外并发发送，避免单个慢客户端阻塞全局广播
        for client_id, ws in targets:
            try:
                if ws.client_state == WebSocketState.CONNECTED:
                    await ws.send_json(message)
            except Exception:
                disconnected.append(client_id)
        if disconnected:
            async with self._lock:
                for cid in disconnected:
                    self._connections.pop(cid, None)
                    self._subscriptions.pop(cid, None)

    async def send_to_user(self, user_id: str, message: dict[str, Any]) -> None:
        """向指定用户的所有连接发送消息."""
        async with self._lock:
            client_ids = list(self._user_connections.get(user_id, set()))
        for cid in client_ids:
            ws = self._connections.get(cid)
            if ws and ws.client_state == WebSocketState.CONNECTED:
                try:
                    await ws.send_json(message)
                except Exception:
                    pass

    @property
    def active_count(self) -> int:
        return len(self._connections)


# 全局连接管理器
manager = ConnectionManager()

# realtime 桥接后台任务句柄（lifespan shutdown 时停止，避免悬挂/重复桥接）
_realtime_task: asyncio.Task | None = None


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(default=""),
):
    """WebSocket 主端点."""
    import uuid

    client_id = str(uuid.uuid4())
    user_id = ""

    # 验证 token（无 token 一律拒绝，禁止匿名连接）
    if not token:
        await websocket.close(code=4001, reason="缺少认证 Token")
        return
    try:
        payload = decode_token(token)
        user_id = payload.get("sub", "")
        if not user_id:
            await websocket.close(code=4001, reason="Token 中缺少用户标识")
            return
    except Exception:
        await websocket.close(code=4001, reason="认证失败")
        return

    await manager.connect(client_id, websocket, user_id)

    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                msg_type = msg.get("type", "")
                payload = msg.get("payload", {})

                if msg_type == "subscribe":
                    channels = payload.get("channels", [])
                    await manager.subscribe(client_id, channels)
                    await websocket.send_json(
                        {
                            "type": "subscribed",
                            "payload": {"channels": channels},
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    )

                elif msg_type == "unsubscribe":
                    channels = payload.get("channels", [])
                    await manager.unsubscribe(client_id, channels)
                    await websocket.send_json(
                        {
                            "type": "unsubscribed",
                            "payload": {"channels": channels},
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    )

                elif msg_type in ("ping", "_ping"):
                    await websocket.send_json(
                        {
                            "type": "_pong",
                            "payload": {},
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    )

            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        await manager.disconnect(client_id, user_id)
    except Exception:
        logger.exception("WebSocket异常: client=%s", client_id[:8])
        await manager.disconnect(client_id, user_id)


# ============================================================
# 事件总线 → WebSocket 推送桥接
# ============================================================


async def _on_alert_event(event: DomainEvent) -> None:
    """告警事件 → WebSocket 推送."""
    await manager.broadcast(
        "alerts",
        {
            "type": "alert:new",
            "payload": event.payload,
            "timestamp": event.timestamp,
        },
    )


async def _on_execution_event(event: DomainEvent) -> None:
    """执行事件 → WebSocket 推送."""
    channel_map = {
        AutomationEvents.EXECUTION_STARTED: "execution:started",
        AutomationEvents.EXECUTION_COMPLETED: "execution:completed",
        AutomationEvents.EXECUTION_FAILED: "execution:failed",
        AutomationEvents.EXECUTION_STEP_COMPLETED: "execution:progress",
        AutomationEvents.EXECUTION_STEP_FAILED: "execution:progress",
        AutomationEvents.EXECUTION_LOG: "execution:log",
        AutomationEvents.DRY_RUN_COMPLETED: "execution:completed",
    }
    msg_type = channel_map.get(event.event_type, "execution:update")
    await manager.broadcast(
        "executions",
        {
            "type": msg_type,
            "payload": event.payload,
            "timestamp": event.timestamp,
        },
    )


async def _on_event_event(event: DomainEvent) -> None:
    """事件流 → WebSocket 推送."""
    await manager.broadcast(
        "events",
        {
            "type": "event:new",
            "payload": event.payload,
            "timestamp": event.timestamp,
        },
    )


async def _on_notification_event(event: DomainEvent) -> None:
    """通知事件 → WebSocket 推送到特定用户."""
    user_id = event.payload.get("user_id", "")
    if user_id:
        await manager.send_to_user(
            user_id,
            {
                "type": "notification",
                "payload": event.payload,
                "timestamp": event.timestamp,
            },
        )
    else:
        await manager.broadcast(
            "notifications",
            {
                "type": "notification",
                "payload": event.payload,
                "timestamp": event.timestamp,
            },
        )


async def _on_ticket_event(event: DomainEvent) -> None:
    """工单事件 → WebSocket 推送."""
    await manager.broadcast(
        "notifications",
        {
            "type": "ticket:updated",
            "payload": event.payload,
            "timestamp": event.timestamp,
        },
    )


def register_ws_event_bridges() -> None:
    """注册实时事件 → WebSocket 推送桥接。

    生产模式（outbox enabled）: 启动 Redis subscriber，接收 Worker 进程发布的事件。
    开发模式（outbox disabled）: 直接注册进程内 EventBus handler。
    """
    bus = get_event_bus()

    if bus.outbox_enabled:
        # 生产模式: 通过 Redis Pub/Sub 接收 Worker 的事件
        from app.common.realtime import start_api_realtime_subscriber

        async def _on_realtime_message(data: dict) -> None:
            """Redis realtime 消息 → WebSocket 广播."""
            event_type = data.get("type", "")
            payload = data.get("payload", {})

            # 根据事件类型路由到对应频道
            if event_type.startswith("alert."):
                await manager.broadcast("alerts", data)
            elif event_type.startswith("automation.") or event_type.startswith(
                "execution."
            ):
                await manager.broadcast("executions", data)
            elif event_type.startswith("event.") or event_type.startswith("state."):
                await manager.broadcast("events", data)
            elif event_type.startswith("notification."):
                user_id = payload.get("user_id", "")
                if user_id:
                    await manager.send_to_user(user_id, data)
                else:
                    await manager.broadcast("notifications", data)
            elif event_type.startswith("ticket."):
                await manager.broadcast("notifications", data)
            else:
                # 未知事件类型仅记录日志，不广播（避免泄漏给无关客户端）
                logger.debug("未识别的 realtime 事件类型，已忽略: %s", event_type)

        # 需要在运行中的 event loop 内启动 subscriber，并保存句柄供 shutdown 停止
        global _realtime_task
        loop = asyncio.get_running_loop()
        _realtime_task = loop.create_task(
            start_api_realtime_subscriber(_on_realtime_message),
            name="realtime-ws-bridge",
        )
        logger.info("WebSocket realtime bridge: Redis subscriber mode (cross-process)")
    else:
        # 开发模式: 直接注册进程内 handler
        bus.subscribe(AlertEvents.ALERT_CREATED, _on_alert_event)
        bus.subscribe(AlertEvents.ALERT_ESCALATED, _on_alert_event)
        bus.subscribe(AlertEvents.ALERT_RESOLVED, _on_alert_event)
        bus.subscribe(AutomationEvents.EXECUTION_STARTED, _on_execution_event)
        bus.subscribe(AutomationEvents.EXECUTION_COMPLETED, _on_execution_event)
        bus.subscribe(AutomationEvents.EXECUTION_FAILED, _on_execution_event)
        bus.subscribe(AutomationEvents.EXECUTION_STEP_COMPLETED, _on_execution_event)
        bus.subscribe(AutomationEvents.EXECUTION_STEP_FAILED, _on_execution_event)
        bus.subscribe(EventEvents.EVENT_CREATED, _on_event_event)
        bus.subscribe(NotificationEvents.NOTIFICATION_SENT, _on_notification_event)
        bus.subscribe(TicketEvents.TICKET_CREATED, _on_ticket_event)
        bus.subscribe(TicketEvents.TICKET_UPDATED, _on_ticket_event)
        logger.info("WebSocket event bridges: in-process mode (dev only)")


async def stop_ws_event_bridges() -> None:
    """停止 realtime 桥接后台任务（lifespan shutdown 调用）."""
    global _realtime_task
    if _realtime_task is not None:
        _realtime_task.cancel()
        try:
            await _realtime_task
        except (asyncio.CancelledError, Exception):  # noqa: BLE001
            pass
        _realtime_task = None
        logger.info("WebSocket realtime bridge stopped")
