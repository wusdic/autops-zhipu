# AUTOPS WebSocket 事件

> 文档状态：current
> 建议路径：`docs/03-api/WEBSOCKET_EVENTS.md`

---

## 1. 连接

```
ws://{host}/ws/events?token={jwt_token}
```

认证：连接时通过 query 参数传递 JWT Token。

---

## 2. 事件类型

### 2.1 状态事件

```json
{"type": "state.change", "data": {"asset_id": "xxx", "state_type": "disk", "old_status": "normal", "new_status": "warning", "value": {"usage_pct": 92}}}
```

### 2.2 告警事件

```json
{"type": "alert.new", "data": {"id": "xxx", "title": "磁盘空间异常", "severity": "warning", "asset_ids": ["asset-001"]}}
{"type": "alert.update", "data": {"id": "xxx", "status": "acknowledged", "updated_by": "user-001"}}
{"type": "alert.resolved", "data": {"id": "xxx", "resolved_by": "user-001"}}
```

### 2.3 执行事件

```json
{"type": "execution.log", "data": {"execution_id": "xxx", "step_id": "yyy", "stream_type": "stdout", "content": "...", "offset": 1234}}
{"type": "execution.status", "data": {"execution_id": "xxx", "status": "running", "current_step": 2}}
{"type": "execution.completed", "data": {"execution_id": "xxx", "status": "success", "duration_ms": 5000}}
```

### 2.4 AI 事件

```json
{"type": "aiops.analysis", "data": {"id": "xxx", "status": "completed", "summary": "..."}}
```

### 2.5 通知事件

```json
{"type": "notification", "data": {"level": "info", "title": "操作成功", "message": "采集任务已完成"}}
```

### 2.6 平台事件

```json
{"type": "platform.health", "data": {"component": "mysql", "status": "unhealthy", "message": "连接超时"}}
```

---

## 3. 订阅过滤

连接后可发送订阅过滤消息：

```json
{"action": "subscribe", "channels": ["alerts", "executions"]}
{"action": "unsubscribe", "channels": ["state.change"]}
```

---

## 4. 心跳

- 服务端每 30 秒发送 ping
- 客户端必须回复 pong
- 60 秒无响应断开连接
