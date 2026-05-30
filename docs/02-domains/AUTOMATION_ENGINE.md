# 自动化执行中心 (Automation Engine)

> 文档状态：current
> 是否为事实源：yes
> 领域目录：`backend/app/domains/automation/`

---

## 1. 职责

安全、可控、可审计地执行自动化动作。所有自动化执行必须经过此中心。

**关键约束：AI 不能绕过执行中心。策略中心通过执行中心调用。**

## 2. 执行状态机

```text
created
  ↓ validate
validated
  ↓ risk_assess
risk_assessed
  ↓ dry_run (可选)
dry_run_completed
  ↓ check_approval
waiting_approval ←→ approved / rejected
  ↓
queued
  ↓
running
  ↓ step by step
verifying
  ↓
success / failed / partial_success
  ↓ (if failed and has rollback)
rollback_running
  ↓
rollback_success / rollback_failed
  ↓
closed
```

## 3. 执行对象

| 类型 | 说明 | 示例 |
|---|---|---|
| Shell 脚本 | Bash 脚本 | 清理临时文件、检查磁盘 |
| PowerShell 脚本 | Windows 脚本 | 重启服务、查询状态 |
| Python 脚本 | Python 脚本 | 复杂逻辑、数据分析 |
| SQL 检查 | 数据库 SQL | 查询连接数、表空间 |
| REST API 调用 | HTTP 请求 | 调用外部接口 |
| Playbook | 多步骤编排 | 组合多个脚本顺序执行 |

## 4. Playbook 结构

```json
{
  "id": "playbook-001",
  "name": "Linux 磁盘清理",
  "steps": [
    {
      "index": 1,
      "name": "检查磁盘使用率",
      "script_id": "script-check-disk",
      "parameters": {},
      "on_failure": "abort"
    },
    {
      "index": 2,
      "name": "清理临时文件",
      "script_id": "script-clean-tmp",
      "parameters": {"dirs": ["/tmp", "/var/tmp"]},
      "on_failure": "continue"
    },
    {
      "index": 3,
      "name": "压缩旧日志",
      "script_id": "script-compress-logs",
      "parameters": {"days": 7},
      "on_failure": "abort"
    },
    {
      "index": 4,
      "name": "验证磁盘使用率",
      "script_id": "script-check-disk",
      "parameters": {},
      "on_failure": "abort",
      "is_verification": true
    }
  ],
  "parameters": [],
  "risk_level": "low",
  "requires_approval": false
}
```

## 5. 安全约束

### 5.1 高危命令黑名单

在脚本执行前检查内容，匹配黑名单则阻断：
- `rm -rf /`
- `dd if=* of=/dev/*`
- `mkfs`
- `shutdown`, `reboot`, `halt`
- `DROP DATABASE`, `DROP TABLE`
- `DELETE FROM` (无 WHERE)
- `UPDATE` (无 WHERE)

黑名单可配置，支持正则。

### 5.2 自动执行白名单

低风险动作可自动执行：
- 查询类操作
- 清理指定目录临时文件
- 压缩日志
- 健康检查

### 5.3 并发锁

- 同一资产同一类型操作加锁
- 锁通过 Redis 分布式锁实现
- 锁超时自动释放

### 5.4 影响面控制

- 单次执行最大目标资产数（默认 50）
- 超出需分批执行
- 支持灰度：1台 → 10% → 50% → 100%

### 5.5 dry-run

- 不实际执行，只展示将要执行的操作
- 展示影响范围
- 展示脚本内容
- 记录 dry-run 结果

### 5.6 审批

- 高风险动作需要审批
- 审批通过后才能执行
- 审批记录关联 execution_id
- 超时未审批自动取消

### 5.7 回滚

- 执行前可选创建回滚点（配置快照）
- 失败时自动或手动触发回滚
- 回滚动作定义在策略或 Playbook 中
- 回滚结果记录

## 6. 实时日志

- 执行日志通过 WebSocket 实时推送
- 按 execution_id 和 step_id 组织
- stdout/stderr 分流
- 支持日志偏移量（断线续传）

## 7. 数据模型

见 `DATA_ARCHITECTURE.md` 3.10 节：
- scripts
- playbooks
- automation_executions
- automation_execution_steps

## 8. API 设计

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | /api/v1/scripts | 脚本列表 |
| POST | /api/v1/scripts | 创建脚本 |
| GET | /api/v1/scripts/{id} | 脚本详情 |
| PUT | /api/v1/scripts/{id} | 更新脚本 |
| GET | /api/v1/playbooks | Playbook 列表 |
| POST | /api/v1/playbooks | 创建 Playbook |
| GET | /api/v1/playbooks/{id} | Playbook 详情 |
| PUT | /api/v1/playbooks/{id} | 更新 Playbook |
| POST | /api/v1/executions | 创建执行 |
| GET | /api/v1/executions | 执行列表 |
| GET | /api/v1/executions/{id} | 执行详情 |
| POST | /api/v1/executions/{id}/dry-run | dry-run |
| POST | /api/v1/executions/{id}/approve | 审批通过 |
| POST | /api/v1/executions/{id}/reject | 审批拒绝 |
| POST | /api/v1/executions/{id}/cancel | 取消执行 |
| POST | /api/v1/executions/{id}/rollback | 触发回滚 |
| GET | /api/v1/executions/{id}/logs | 执行日志 |
| WS | /ws/executions/{id}/logs | 实时日志流 |

## 9. 领域事件

| 事件 | 说明 |
|---|---|
| ExecutionCreated | 执行创建 |
| ExecutionStarted | 执行开始 |
| ExecutionStepStarted | 步骤开始 |
| ExecutionStepCompleted | 步骤完成 |
| ExecutionCompleted | 执行完成 |
| ExecutionFailed | 执行失败 |
| ExecutionRolledBack | 执行回滚 |
| ExecutionCancelled | 执行取消 |

## 10. 与其他领域交互

| 领域 | 交互方式 | 说明 |
|---|---|---|
| policy | 策略触发执行 | service 调用 |
| asset | 执行目标为资产 | service 调用 |
| config | 执行使用配置版本 | service 调用 |
| credential | 执行使用凭证 | service 调用 |
| log | 执行日志记录 | 事件发布 |
| alert | 执行结果关联告警 | service 调用 |
| ticket | 执行失败转工单 | service 调用 |
