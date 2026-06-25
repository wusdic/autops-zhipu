# AUTOPS API 契约文档

> 文档路径：`docs/03-api/API_CONTRACT.md`
> 状态：current | 事实源：yes
> 反向同步时间：2026-05-31（从实际运行后端提取）
> 
> **本文件是 API 端点的唯一事实源。前端 routes.ts 和后端 router.py 必须与此文档一致。**

---

## 1. 通用约定

### 1.1 基础信息

| 项目 | 值 |
|---|---|
| API 前缀 | `/api/v1` |
| 协议 | HTTP/HTTPS |
| 认证 | Bearer Token (JWT) |
| Content-Type | `application/json` |

**认证机制**：全局由 HTTP 中间件 `AuthMiddleware` 强制。公开端点白名单：`/auth/login`、`/auth/refresh`、`/auth/logout`、`/health`、`/ready`、`/docs`、`/redoc`、`/openapi.json`；其余 `/api/v1/*` 均需有效 Bearer Token。

**权限**：除登录态外，部分高危端点（用户/角色 CRUD、资产增删、脚本/Playbook 增删、执行审批/回滚、审计日志、备份恢复、租户管理等）通过 `require_admin` 依赖额外要求 `super_admin` 或 `admin` 角色，否则返回 403。下表"权限"列标注 `admin` 的即属此类。

### 1.2 统一响应结构

```json
{
  "code": 0,
  "message": "success",
  "data": { ... },
  "trace_id": "uuid"
}
```

### 1.3 分页参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `page` | int | 1 | 页码 |
| `page_size` | int | 20 | 每页数量（最大100） |

分页响应：
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5
}
```

### 1.4 错误码

| 范围 | 含义 |
|---|---|
| 0 | 成功 |
| 1000-1999 | 通用错误（参数、认证、权限） |
| 2000-2999 | 资产中心 |
| 3000-3999 | 事件与告警 |
| 4000-4999 | 自动化引擎 |
| 5000-5999 | 知识与AI |
| 6000-6999 | 工单与协同 |
| 7000-7999 | 平台治理 |

---

## 2. 系统端点

| 方法 | 路径 | 说明 | 认证 |
|---|---|---|---|
| GET | `/health` | 健康检查 | 否 |
| GET | `/ready` | 就绪检查 | 否 |

---

## 3. 认证模块 (auth)

| 方法 | 路径 | 说明 | 认证 |
|---|---|---|---|
| POST | `/api/v1/auth/login` | 用户登录 | 否 |
| POST | `/api/v1/auth/logout` | 用户登出 | 否（白名单） |
| POST | `/api/v1/auth/refresh` | 刷新 Token | 否（白名单） |
| GET | `/api/v1/auth/me` | 获取当前用户（含 roles 数组） | 是 |
| PUT | `/api/v1/auth/password` | 修改密码 | 是 |

`/auth/me` 响应的 `data` 字段（`UserResponse`）：

```json
{
  "id": "...", "username": "admin", "display_name": "管理员",
  "email": null, "status": "active",
  "roles": [{"id": "...", "name": "super_admin", "display_name": "超级管理员", "permissions": ["*:*"], ...}],
  "last_login_at": "...", "created_at": "..."
}
```

---

## 4. 资产中心 (assets / asset-groups / discovery)

| 方法 | 路径 | 说明 | 权限 |
|---|---|---|---|
| GET | `/api/v1/assets` | 资产列表（分页、筛选） | 登录 |
| POST | `/api/v1/assets` | 创建资产 | admin |
| GET | `/api/v1/assets/{asset_id}` | 资产详情 | 登录 |
| PUT | `/api/v1/assets/{asset_id}` | 更新资产 | 登录 |
| DELETE | `/api/v1/assets/{asset_id}` | 删除资产 | admin |
| POST | `/api/v1/assets/import` | 批量导入资产（返回 imported/skipped/errors） | admin |
| GET | `/api/v1/assets/{asset_id}/relations` | 资产关系图 | 登录 |
| POST | `/api/v1/assets/{asset_id}/relations` | 创建资产关系 | 登录 |
| DELETE | `/api/v1/assets/{asset_id}/relations/{relation_id}` | 删除关系 | 登录 |
| GET | `/api/v1/assets/{asset_id}/timeline` | 资产时间线 | 登录 |
| GET | `/api/v1/assets/{asset_id}/credentials` | 资产绑定凭证 | 登录 |
| DELETE | `/api/v1/assets/{asset_id}/credentials/{cred_id}` | 解绑凭证 | admin |
| GET | `/api/v1/assets/{asset_id}/policies` | 资产绑定策略 | 登录 |
| DELETE | `/api/v1/assets/{asset_id}/policies/{policy_id}` | 解绑策略 | 登录 |
| GET | `/api/v1/assets/{asset_id}/collection-configs` | 采集配置 | 登录 |
| POST | `/api/v1/assets/{asset_id}/collection-trigger` | 触发采集 | 登录 |
| GET | `/api/v1/asset-groups` | 资产分组列表 | 登录 |
| POST | `/api/v1/asset-groups` | 创建分组 | 登录 |
| GET | `/api/v1/asset-groups/{group_id}` | 分组详情 | 登录 |
| POST | `/api/v1/asset-groups/{group_id}/members` | 添加组成员 | 登录 |
| DELETE | `/api/v1/asset-groups/{group_id}/members/{asset_id}` | 移除组成员 | 登录 |
| GET | `/api/v1/discovery/tasks` | 发现任务列表 | 登录 |
| POST | `/api/v1/discovery/tasks` | 创建发现任务（见下方字段说明） | 登录 |
| GET | `/api/v1/discovery/tasks/{task_id}` | 发现任务详情 | 登录 |
| POST | `/api/v1/discovery/tasks/{task_id}/start` | 启动发现任务扫描 | 登录 |
| GET | `/api/v1/discovery/results` | 发现结果（可按 task_id 过滤） | 登录 |
| POST | `/api/v1/discovery/onboard` | 纳管发现结果（result_ids 为空则纳管全部 discovered） | 登录 |
| POST | `/api/v1/discovery/import` | 手动导入单个资产 | 登录 |

**`POST /discovery/tasks` 请求体**（`DiscoveryTaskCreate`）：

| 字段 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `name` | string | 必填 | 任务名称 |
| `ip_mode` | string | `cidr` | `cidr` 或 `range` |
| `cidr` | string | - | CIDR，如 `10.0.0.0/24`（cidr 模式） |
| `ip_start`/`ip_end` | string | - | 起止 IP（range 模式） |
| `protocols` | string[] | `["icmp"]` | 探测协议 |
| `ports` | string | - | 端口，如 `22,80,443` |
| `credential_id` | string | - | 绑定凭证 |
| `timeout` | int | 30 | 超时秒数 |
| `auto_onboard` | bool | `true` | **自动发现并纳管**：为 true 时建任务即自动启动扫描，扫描完成自动纳管全部存活 IP（幂等，重复 IP 不会重复建资产） |

---

## 5. 凭证中心 (credentials)

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/v1/credentials` | 凭证列表 |
| POST | `/api/v1/credentials` | 创建凭证 |
| GET | `/api/v1/credentials/{cred_id}` | 凭证详情 |
| POST | `/api/v1/credentials/{cred_id}/bind` | 绑定到资产 |

---

## 6. 配置中心 (configs)

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/v1/configs/definitions` | 配置定义列表 |
| POST | `/api/v1/configs/definitions` | 创建配置定义 |
| GET | `/api/v1/configs/definitions/{def_id}` | 配置定义详情 |
| GET | `/api/v1/configs/definitions/{def_id}/versions` | 配置版本列表 |
| POST | `/api/v1/configs/definitions/{def_id}/versions` | 创建配置版本 |
| POST | `/api/v1/configs/versions/{version_id}/publish` | 发布配置版本 |
| GET | `/api/v1/configs/inheritance` | 配置继承链 |

---

## 7. 采集与状态 (collectors / collection-jobs / states)

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/v1/collectors` | 采集器列表 |
| POST | `/api/v1/collectors` | 注册采集器 |
| GET | `/api/v1/collection-jobs` | 采集任务列表 |
| POST | `/api/v1/collection-jobs` | 创建采集任务 |
| GET | `/api/v1/collection-jobs/{job_id}/results` | 采集结果 |
| POST | `/api/v1/states/snapshots` | 上报状态快照 |
| GET | `/api/v1/states/latest/{asset_id}` | 资产最新状态 |
| GET | `/api/v1/states/changes` | 状态变更列表 |
| GET | `/api/v1/states/changes/{asset_id}` | 资产状态变更历史 |

---

## 8. 事件与告警 (events / alert-rules / alerts)

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/v1/events` | 事件列表 |
| POST | `/api/v1/events` | 创建事件 |
| GET | `/api/v1/events/{event_id}` | 事件详情 |
| GET | `/api/v1/alerts` | 告警列表 |
| POST | `/api/v1/alerts` | 创建告警 |
| GET | `/api/v1/alerts/{alert_id}` | 告警详情 |
| POST | `/api/v1/alerts/{alert_id}/acknowledge` | 确认告警 |
| POST | `/api/v1/alerts/{alert_id}/resolve` | 解决告警 |
| POST | `/api/v1/alerts/{alert_id}/escalate` | 升级告警 |
| GET | `/api/v1/alerts/stats/overview` | 告警统计 |
| GET | `/api/v1/alert-rules` | 告警规则列表 |
| POST | `/api/v1/alert-rules` | 创建告警规则 |
| PUT | `/api/v1/alert-rules/{rule_id}` | 更新规则 |
| PATCH | `/api/v1/alert-rules/{rule_id}` | 部分更新规则 |
| POST | `/api/v1/alert-rules/{rule_id}/test` | 测试规则 |

---

## 9. 自动化引擎 (scripts / playbooks / policies / executions)

| 方法 | 路径 | 说明 | 权限 |
|---|---|---|---|
| GET | `/api/v1/scripts` | 脚本列表 | 登录 |
| POST | `/api/v1/scripts` | 创建脚本 | admin |
| PUT | `/api/v1/scripts/{script_id}` | 更新脚本 | 登录 |
| DELETE | `/api/v1/scripts/{script_id}` | 删除脚本 | admin |
| GET | `/api/v1/playbooks` | Playbook 列表 | 登录 |
| POST | `/api/v1/playbooks` | 创建 Playbook | admin |
| GET | `/api/v1/playbooks/{playbook_id}` | Playbook 详情 | 登录 |
| PUT | `/api/v1/playbooks/{playbook_id}` | 更新 Playbook | 登录 |
| DELETE | `/api/v1/playbooks/{playbook_id}` | 删除 Playbook | admin |
| GET | `/api/v1/policies` | 策略列表 | 登录 |
| POST | `/api/v1/policies` | 创建策略 | 登录 |
| GET | `/api/v1/policies/{policy_id}` | 策略详情 | 登录 |
| PUT | `/api/v1/policies/{policy_id}` | 更新策略 | 登录 |
| DELETE | `/api/v1/policies/{policy_id}` | 删除策略 | 登录 |
| POST | `/api/v1/policies/{policy_id}/simulate` | 模拟策略 | 登录 |
| GET | `/api/v1/executions` | 执行列表 | 登录 |
| POST | `/api/v1/executions` | 创建执行 | 登录 |
| GET | `/api/v1/executions/{exec_id}` | 执行详情 | 登录 |
| POST | `/api/v1/executions/{exec_id}/approve` | 审批执行 | admin |
| POST | `/api/v1/executions/{exec_id}/cancel` | 取消执行 | admin |
| POST | `/api/v1/executions/{exec_id}/rollback` | 回滚执行 | admin |
| GET | `/api/v1/executions/{exec_id}/verification` | 验证结果 | 登录 |

---

## 10. 日志 (logs)

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/v1/logs/execution/{execution_id}` | 执行日志 |
| POST | `/api/v1/logs/execution/{execution_id}` | 追加日志 |
| GET | `/api/v1/logs/execution/{exec_id}/step/{step_id}` | 步骤日志 |

---

## 11. 工单 (tickets)

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/v1/tickets` | 工单列表 |
| POST | `/api/v1/tickets` | 创建工单 |
| GET | `/api/v1/tickets/{ticket_id}` | 工单详情 |
| PUT | `/api/v1/tickets/{ticket_id}` | 更新工单 |
| GET | `/api/v1/tickets/{ticket_id}/comments` | 工单评论 |
| POST | `/api/v1/tickets/{ticket_id}/comments` | 添加评论 |
| GET | `/api/v1/tickets/{ticket_id}/attachments` | 工单附件 |
| POST | `/api/v1/tickets/{ticket_id}/attachments` | 上传附件 |

---

## 12. 知识与AI (knowledge / aiops)

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/v1/knowledge` | 知识库列表 |
| POST | `/api/v1/knowledge` | 创建知识 |
| GET | `/api/v1/knowledge/{article_id}` | 知识详情 |
| PUT | `/api/v1/knowledge/{article_id}` | 更新知识 |
| POST | `/api/v1/knowledge/{article_id}/publish` | 发布知识 |
| POST | `/api/v1/knowledge/{article_id}/feedback` | 知识反馈 |
| POST | `/api/v1/knowledge/{article_id}/view` | 记录浏览 |
| GET | `/api/v1/knowledge/{article_id}/related` | 相关知识 |
| GET | `/api/v1/knowledge/{article_id}/versions` | 版本历史 |
| POST | `/api/v1/knowledge/{article_id}/convert-runbook` | 转为 Runbook |
| GET | `/api/v1/knowledge/stats` | 知识统计 |
| GET | `/api/v1/knowledge/export` | 导出知识 |
| POST | `/api/v1/knowledge/import/validate` | 验证导入数据 |
| POST | `/api/v1/knowledge/import/batch` | 批量导入 |
| GET | `/api/v1/aiops/health` | AI 服务健康 |
| POST | `/api/v1/aiops/diagnose` | AI 诊断 |
| GET | `/api/v1/aiops/analyses` | AI 分析列表 |
| POST | `/api/v1/aiops/analyses` | 创建分析 |
| GET | `/api/v1/aiops/analyses/{analysis_id}` | 分析详情 |
| POST | `/api/v1/aiops/analyses/{analysis_id}/feedback` | 分析反馈 |

---

## 13. 通知 (notifications)

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/v1/notifications` | 通知列表 |
| PATCH | `/api/v1/notifications/{notification_id}/read` | 标记已读 |
| POST | `/api/v1/notifications/read-all` | 全部已读 |

---

## 14. 平台治理 (users / roles / api-keys / audit-logs / backups / platform)

| 方法 | 路径 | 说明 | 权限 |
|---|---|---|---|
| GET | `/api/v1/users` | 用户列表 | 登录 |
| POST | `/api/v1/users` | 创建用户 | admin |
| GET | `/api/v1/users/{user_id}` | 用户详情 | 登录 |
| PUT | `/api/v1/users/{user_id}` | 更新用户 | 登录 |
| DELETE | `/api/v1/users/{user_id}` | 删除用户 | admin |
| GET | `/api/v1/roles` | 角色列表 | 登录 |
| POST | `/api/v1/roles` | 创建角色 | admin |
| GET | `/api/v1/api-keys` | API Key 列表 | 登录 |
| POST | `/api/v1/api-keys` | 创建 API Key | 登录 |
| PATCH | `/api/v1/api-keys/{key_id}` | 更新 API Key | 登录 |
| DELETE | `/api/v1/api-keys/{key_id}` | 删除 API Key | 登录 |
| GET | `/api/v1/audit-logs` | 审计日志（含全平台操作明细） | admin |
| GET | `/api/v1/platform/status` | 平台状态 | 登录 |
| POST | `/api/v1/platform/self-check` | 完整自检 | 登录 |
| GET | `/api/v1/backups` | 备份列表 | admin |
| POST | `/api/v1/backups` | 创建备份 | admin |
| GET | `/api/v1/backups/{backup_id}` | 备份详情 | admin |
| GET | `/api/v1/backups/{backup_id}/download` | 下载备份 | admin |
| POST | `/api/v1/backups/{backup_id}/restore` | 恢复备份 | admin |
| 租户管理（`/api/v1/tenants/*`） | 增删改查 | admin（router 级 require_admin） |

---

## 15. WebSocket

| 路径 | 说明 |
|---|---|
| `/api/v1/ws` | WebSocket 实时推送（告警、执行、通知等） |

---

## 附录：端点统计

| 模块 | 端点数 |
|---|---|
| 系统 (health/ready) | 2 |
| 认证 (auth) | 5 |
| 资产 (assets/groups/discovery) | 22 |
| 凭证 (credentials) | 4 |
| 配置 (configs) | 7 |
| 采集与状态 (collectors/jobs/states) | 8 |
| 事件 (events) | 3 |
| 告警 (alerts/rules) | 15 |
| 自动化 (scripts/playbooks/policies/executions) | 21 |
| 日志 (logs) | 3 |
| 工单 (tickets) | 8 |
| 知识与AI (knowledge/aiops) | 20 |
| 通知 (notifications) | 3 |
| 平台治理 (users/roles/keys/audit/backups/platform) | 19 |
| WebSocket | 1 |
| **合计** | **145** (含 /docs /openapi.json /redoc = 4 系统端点) |
