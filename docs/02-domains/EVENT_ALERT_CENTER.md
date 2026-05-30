# 事件与告警中心 (Event & Alert Center)

> 文档状态：current
> 是否为事实源：yes
> 领域目录：`backend/app/domains/event/` + `backend/app/domains/alert/`

---

## 1. 职责

- **事件中心：** 接收原始信号，标准化、去重、关联、分类、路由
- **告警中心：** 基于事件和规则生成告警，管理告警生命周期

## 2. 事件处理流水线

```text
raw signal (采集结果/状态变更/日志/配置变更)
  ↓
normalized event (标准化事件)
  ↓
deduplication (去重，基于 dedup_key)
  ↓
correlation (关联，基于 asset + time window)
  ↓
classification (分类)
  ↓
routing (路由 → alert / policy / ticket / audit)
```

## 3. 事件来源

| 来源 | 说明 | 事件类型示例 |
|---|---|---|
| collector | 采集结果异常 | collection_failed, metric_anomaly |
| state | 状态变更 | state_changed_to_warning, state_changed_to_critical |
| log | 日志关键字命中 | log_error_pattern, log_keyword_matched |
| config | 配置漂移 | config_drift_detected |
| automation | 执行结果 | execution_failed, execution_success |
| platform | 平台组件异常 | collector_offline, model_unavailable |
| aiops | AI 分析结果 | ai_analysis_complete |

## 4. 告警生命周期

```text
firing → acknowledged → investigating → resolved → closed
  ↓                    ↓
  suppressed           escalated → ticket_created
  ↓
silenced (静默期)
```

### 4.1 告警收敛

| 策略 | 说明 |
|---|---|
| 去重 | 相同 fingerprint 的告警合并 |
| 压缩 | 同一资产多个相关告警压缩 |
| 抑制 | 高级别告警抑制低级别 |
| 静默 | 维护窗口内不生成告警 |
| 延迟 | 短时间恢复的不生成告警 |

### 4.2 告警升级

```text
firing 5min 未确认 → 升级到组长
firing 15min 未确认 → 升级到经理
firing 30min 未确认 → 升级到总监
```

升级规则可配置。

### 4.3 告警上下文

告警自动关联并展示：
- 关联资产信息和关系
- 相关指标趋势图
- 相关日志片段
- 相关配置变更
- 相关执行记录
- 相关 AI 分析
- 相似知识案例

## 5. 告警规则

### 5.1 规则结构

```json
{
  "name": "磁盘使用率告警",
  "event_types": ["metric_anomaly"],
  "conditions": [
    {"field": "metric_name", "op": "eq", "value": "disk_usage_pct"},
    {"field": "metric_value", "op": "gt", "value": 90}
  ],
  "severity_mapping": [
    {"conditions": [{"field": "metric_value", "op": "gt", "value": 95}], "severity": "critical"},
    {"conditions": [{"field": "metric_value", "op": "gt", "value": 90}], "severity": "warning"}
  ],
  "asset_filter": {"asset_type": ["linux_server"]},
  "cooldown_minutes": 5,
  "suppression_rules": [],
  "escalation_rules": [
    {"after_minutes": 5, "action": "notify", "target": "group:oncall"}
  ]
}
```

## 6. 数据模型

见 `DATA_ARCHITECTURE.md` 3.7-3.8 节：
- events
- alerts
- alert_rules

## 7. API 设计

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | /api/v1/events | 事件列表 |
| GET | /api/v1/events/{id} | 事件详情 |
| GET | /api/v1/alerts | 告警列表 |
| GET | /api/v1/alerts/{id} | 告警详情 |
| POST | /api/v1/alerts/{id}/acknowledge | 确认告警 |
| POST | /api/v1/alerts/{id}/resolve | 解决告警 |
| POST | /api/v1/alerts/{id}/suppress | 抑制告警 |
| POST | /api/v1/alerts/{id}/escalate | 升级告警 |
| POST | /api/v1/alerts/{id}/create-ticket | 转工单 |
| GET | /api/v1/alert-rules | 告警规则列表 |
| POST | /api/v1/alert-rules | 创建告警规则 |
| PUT | /api/v1/alert-rules/{id} | 更新规则 |
| GET | /api/v1/alerts/stats | 告警统计 |

## 8. 领域事件

| 事件 | 说明 |
|---|---|
| EventReceived | 事件接收 |
| EventNormalized | 事件标准化完成 |
| AlertTriggered | 告警触发 |
| AlertAcknowledged | 告警确认 |
| AlertResolved | 告警解决 |
| AlertEscalated | 告警升级 |
| AlertSuppressed | 告警抑制 |

## 9. 与其他领域交互

| 领域 | 交互方式 | 说明 |
|---|---|---|
| collector/state | 接收采集和状态变更事件 | 事件订阅 |
| asset | 告警关联资产 | service 调用 |
| policy | 事件触发策略匹配 | 事件发布 |
| automation | 告警触发自动化 | 事件订阅 |
| ticket | 告警转工单 | service 调用 |
| aiops | 告警触发 AI 分析 | 事件订阅 |
| knowledge | 告警关联知识 | service 调用 |
