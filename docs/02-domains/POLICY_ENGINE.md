# 策略中心 (Policy Engine)

> 文档状态：current
> 是否为事实源：yes
> 领域目录：`backend/app/domains/policy/`

---

## 1. 职责

定义、管理、匹配和验证自动化处置策略。策略中心是告警到动作的决策层。

**关键约束：策略不直接执行动作，只调用自动化执行中心。**

## 2. 策略结构

```json
{
  "id": "policy-001",
  "name": "Linux 磁盘空间异常清理",
  "trigger_type": "alert",
  "trigger_conditions": {
    "alert_title_pattern": "磁盘空间异常",
    "asset_types": ["linux_server"],
    "severity": ["warning", "critical"]
  },
  "asset_scope": {
    "type": "dynamic",
    "filter": {"asset_type": ["linux_server"], "environment": ["production"]}
  },
  "risk_level": "low",
  "requires_approval": false,
  "max_impact_scope": 10,
  "action_chain": [
    {"type": "playbook", "id": "playbook-disk-cleanup", "parameters": {}},
    {"type": "verify", "conditions": [{"field": "disk_usage_pct", "op": "lt", "value": 80}]}
  ],
  "verification_conditions": [
    {"field": "disk_usage_pct", "op": "lt", "value": 80}
  ],
  "failure_handling": {
    "action": "create_ticket",
    "ticket_type": "incident",
    "priority": "high"
  },
  "rollback_actions": [],
  "exclusion_conditions": {
    "asset_tags": ["no-auto-cleanup"]
  }
}
```

## 3. 策略匹配流程

```text
事件/告警触发
  ↓
加载所有 active 策略
  ↓
过滤：trigger_type 匹配？
  ↓
过滤：trigger_conditions 匹配？
  ↓
过滤：asset_scope 匹配？
  ↓
过滤：exclusion_conditions 排除？
  ↓
冲突检测（多个策略命中同一资产）
  ↓
选择最优策略（优先级排序）
  ↓
风险评估
  ↓
需要审批？
  ↓ 是 → 创建审批请求
  ↓ 否 → 调用自动化执行中心
```

## 4. 策略生命周期

```text
draft → testing → active → inactive → archived
```

- **draft：** 编辑中
- **testing：** 仅模拟执行，不实际执行
- **active：** 可被触发
- **inactive：** 临时停用
- **archived：** 归档

## 5. 策略模拟（dry-run）

策略激活前可模拟执行：
- 输入模拟事件
- 匹配策略
- 展示将执行的动作链
- 展示影响范围
- 展示风险评估
- 不实际执行

## 6. 冲突检测

当多个策略命中同一事件/资产时：

| 冲突类型 | 处理方式 |
|---|---|
| 同一触发源不同策略 | 按策略优先级选择 |
| 同一资产不同动作 | 按风险等级排序，低风险优先 |
| 矛盾动作 | 不自动执行，转人工 |

## 7. 命中解释

策略命中后必须输出解释：
- 哪个策略被命中
- 为什么命中（条件匹配详情）
- 将执行什么动作
- 影响范围
- 风险等级
- 是否需要审批

## 8. 数据模型

见 `DATA_ARCHITECTURE.md` 3.9 节：
- policies
- policy_versions

## 9. API 设计

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | /api/v1/policies | 策略列表 |
| POST | /api/v1/policies | 创建策略 |
| GET | /api/v1/policies/{id} | 策略详情 |
| PUT | /api/v1/policies/{id} | 更新策略 |
| DELETE | /api/v1/policies/{id} | 删除策略 |
| GET | /api/v1/policies/{id}/versions | 版本列表 |
| POST | /api/v1/policies/{id}/publish | 发布策略 |
| POST | /api/v1/policies/{id}/simulate | 模拟执行 |
| GET | /api/v1/policies/{id}/history | 执行历史 |
| POST | /api/v1/policies/conflict-check | 冲突检测 |

## 10. 领域事件

| 事件 | 说明 |
|---|---|
| PolicyCreated | 策略创建 |
| PolicyUpdated | 策略更新 |
| PolicyPublished | 策略发布 |
| PolicyMatched | 策略命中 |
| PolicySimulated | 策略模拟完成 |

## 11. 与其他领域交互

| 领域 | 交互方式 | 说明 |
|---|---|---|
| event/alert | 接收事件/告警触发 | 事件订阅 |
| asset | 策略适用范围基于资产 | service 调用 |
| automation | 策略调用自动化执行 | service 调用 |
| knowledge | 策略关联知识库 | service 调用 |
| governance | 审批流程 | service 调用 |
