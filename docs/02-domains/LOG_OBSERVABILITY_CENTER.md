# 日志与可观测中心 (Log & Observability Center)

> 文档状态：current
> 是否为事实源：yes
> 领域目录：`backend/app/domains/log/`

---

## 1. 职责

成为故障分析、执行审计、AI 诊断和自动化闭环的证据中心。

## 2. 日志类型

| 类型 | 来源 | 说明 |
|---|---|---|
| 执行日志 | 自动化执行 | stdout/stderr 流，按 execution_id 组织 |
| 采集日志 | 采集任务 | 采集器输出，按 collection_result_id 组织 |
| 审计日志 | 全平台 | 操作记录，不可篡改 |
| 平台日志 | 后端服务 | 应用运行日志 |
| AI 工具调用日志 | AIops | AI 工具调用记录 |

## 3. 执行日志模型

```text
execution_id
  ├── trigger_source (policy/manual/aiops/alert)
  ├── policy_id
  ├── playbook_id
  ├── script_version
  ├── target_assets []
  ├── parameters
  ├── approval_id
  ├── steps []
  │   ├── step_index
  │   ├── script_id
  │   ├── target_asset_id
  │   ├── status
  │   ├── stdout stream []
  │   ├── stderr stream []
  │   ├── exit_code
  │   └── duration
  ├── final_status
  └── audit_record
```

## 4. 日志存储策略

### 第一阶段（简化）

```text
执行日志索引 → execution_logs 表（关系库）
执行日志内容 → execution_logs.log_content（TEXT，限制大小）
超长日志 → 文件/对象存储，log_content 引用 storage_ref
```

### 后续阶段

```text
日志索引 → 关系库
日志内容 → Loki/OpenSearch
执行实时流 → WebSocket
```

## 5. WebSocket 实时日志

### 推送格式

```json
{
  "type": "execution.log",
  "execution_id": "exec-001",
  "step_id": "step-001",
  "stream_type": "stdout",
  "content": "日志内容...",
  "offset": 1234,
  "timestamp": "2026-01-01T00:00:00Z"
}
```

### 订阅机制

- 用户通过 WebSocket 订阅特定 execution_id
- 后端通过 Redis Pub/Sub 接收日志并推送
- 支持断线重连后从 offset 继续

## 6. 日志检索

### 查询维度

- 按 execution_id
- 按 asset_id
- 按 trace_id
- 按 alert_id
- 按时间范围
- 按关键字（日志内容搜索）
- 按日志级别

### 脱敏规则

- 日志中的密码字段自动脱敏
- IP 地址根据权限脱敏
- 日志内容中的凭证模式匹配脱敏

## 7. OpenTelemetry 集成

### Trace

- 每个请求有 trace_id
- 跨服务调用携带 trace context
- 采集任务和执行任务继承 trace_id
- 支持按 trace_id 查询完整调用链

### Metrics

- 平台自身指标暴露（Prometheus 格式）
- API 响应时间、错误率
- 采集任务成功率
- 执行任务成功率
- 队列长度
- 数据库连接池

## 8. 平台自监控

### 自检 API

| 端点 | 检查内容 |
|---|---|
| /health | 服务存活 |
| /ready | 数据库 + Redis + 各组件就绪 |
| /api/v1/platform/status | 全组件状态概览 |

### 组件健康检查

| 组件 | 检查方式 |
|---|---|
| MySQL | 连接 + 简单查询 |
| Redis | PING |
| VictoriaMetrics | HTTP health |
| MinIO | HTTP health |
| Qdrant | HTTP health |
| vLLM | HTTP health |

## 9. 数据模型

见 `DATA_ARCHITECTURE.md` 3.11 节：
- execution_logs

## 10. API 设计

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | /api/v1/execution-logs | 执行日志搜索 |
| GET | /api/v1/execution-logs/stream | WebSocket 日志流 |
| GET | /api/v1/audit-logs | 审计日志查询 |
| GET | /api/v1/audit-logs/export | 审计日志导出 |
| GET | /api/v1/platform/status | 平台组件状态 |
| GET | /metrics | Prometheus 指标 |

## 11. 领域事件

| 事件 | 说明 |
|---|---|
| LogEntryCreated | 日志条目创建 |
| AuditLogCreated | 审计日志创建 |
| PlatformComponentUnhealthy | 平台组件不健康 |

## 12. 与其他领域交互

| 领域 | 交互方式 | 说明 |
|---|---|---|
| automation | 执行日志来源 | 事件订阅 |
| collector | 采集日志来源 | 事件订阅 |
| alert | 告警关联日志 | service 调用 |
| aiops | AI 读取日志上下文 | service 调用 |
| governance | 审计日志查询 | service 调用 |
