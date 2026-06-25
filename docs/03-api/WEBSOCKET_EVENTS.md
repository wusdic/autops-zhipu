# AUTOPS WebSocket 事件

> 文档状态：current
> 建议路径：`docs/03-api/WEBSOCKET_EVENTS.md`

---

## 1. 连接

```
ws://{host}/api/v1/ws?token={jwt_token}
```

**强制鉴权**：连接时必须通过 query 参数 `token` 传递有效 JWT。
- 无 token、token 无效或 token 中缺少 `sub`：服务端以 close code `4001` 立即关闭连接，禁止匿名连接。

---

## 2. 频道与订阅

客户端**必须先订阅频道才能收到对应推送**；未订阅任何频道时不会收到任何业务消息。

### 可用频道

| 频道 | 内容 |
|------|------|
| `alerts` | 告警创建/升级/恢复 |
| `executions` | 执行启动/完成/失败/步骤进度/日志 |
| `events` | 事件流 |
| `notifications` | 通知、工单更新 |

### 订阅消息格式

```json
{"type": "subscribe", "payload": {"channels": ["alerts", "executions"]}}
```

服务端确认：

```json
{"type": "subscribed", "payload": {"channels": ["alerts", "executions"]}, "timestamp": "..."}
```

---

## 3. 事件类型

所有推送消息统一结构：`{"type": "<type>", "payload": {...}, "timestamp": "<iso8601>"}`。

### 3.1 告警（alerts 频道）

```json
{"type": "alert:new", "payload": {"alert_id": "xxx", "severity": "warning", ...}}
{"type": "alert:new", "payload": {...}}   // 升级/恢复也走 alert:new（按事件类型区分）
```

### 3.2 执行（executions 频道）

```json
{"type": "execution:started", "payload": {"execution_id": "xxx", ...}}
{"type": "execution:completed", "payload": {"execution_id": "xxx", ...}}
{"type": "execution:failed", "payload": {"execution_id": "xxx", "error_message": "...", ...}}
{"type": "execution:progress", "payload": {"execution_id": "xxx", ...}}   // 步骤完成/失败
{"type": "execution:log", "payload": {"execution_id": "xxx", ...}}
```

### 3.3 事件流（events 频道）

```json
{"type": "event:new", "payload": {...}}
```

### 3.4 通知（notifications 频道 / 定向推送）

- 含 `user_id` 的通知定向推送给该用户的所有连接（`send_to_user`）
- 无 `user_id` 的通知广播到 `notifications` 频道

```json
{"type": "notification", "payload": {"user_id": "...", ...}}
{"type": "ticket:updated", "payload": {...}}
```

---

## 4. 心跳

客户端发送 ping，服务端回复 pong（服务端不主动发心跳）：

```json
// 客户端发
{"type": "ping"}
// 或
{"type": "_ping"}

// 服务端回
{"type": "_pong", "payload": {}, "timestamp": "..."}
```
