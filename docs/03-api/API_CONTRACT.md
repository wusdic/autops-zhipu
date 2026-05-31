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
  "page_size": 20
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
| POST | `/api/v1/auth/logout` | 用户登出 | 是 |
| POST | `/api/v1/auth/refresh` | 刷新 Token | 是 |
| GET | `/api/v1/auth/me` | 获取当前用户 | 是 |
| PUT | `/api/v1/auth/password` | 修改密码 | 是 |

---

## 4. 资产中心 (assets / asset-groups)

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/v1/assets` | 资产列表（分页、筛选） |
| POST | `/api/v1/assets` | 创建资产 |
| GET | `/api/v1/assets/{asset_id}` | 资产详情 |
| PUT | `/api/v1/assets/{asset_id}` | 更新资产 |
| DELETE | `/api/v1/assets/{asset_id}` | 删除资产 |
| POST | `/api/v1/assets/import` | 批量导入资产 |
| GET | `/api/v1/assets/{asset_id}/relations` | 资产关系图 |
| POST | `/api/v1/assets/{asset_id}/relations` | 创建资产关系 |
| DELETE | `/api/v1/assets/{asset_id}/relations/{relation_id}` | 删除关系 |
| GET | `/api/v1/assets/{asset_id}/timeline` | 资产时间线 |
| GET | `/api/v1/assets/{asset_id}/credentials` | 资产绑定凭证 |
| DELETE | `/api/v1/assets/{asset_id}/credentials/{cred_id}` | 解绑凭证 |
| GET | `/api/v1/assets/{asset_id}/policies` | 资产绑定策略 |
| DELETE | `/api/v1/assets/{asset_id}/policies/{policy_id}` | 解绑策略 |
| GET | `/api/v1/assets/{asset_id}/collection-configs` | 采集配置 |
| POST | `/api/v1/assets/{asset_id}/collection-trigger` | 触发采集 |
| GET | `/api/v1/asset-groups` | 资产分组列表 |
| POST | `/api/v1/asset-groups` | 创建分组 |
| GET | `/api/v1/asset-groups/{group_id}` | 分组详情 |
| POST | `/api/v1/asset-groups/{group_id}/members` | 添加组成员 |
| DELETE | `/api/v1/asset-groups/{group_id}/members/{asset_id}` | 移除组成员 |
| GET | `/api/v1/discovery/tasks` | 资产发现任务 |
| POST | `/api/v1/discovery/tasks` | 创建发现任务 |
| GET | `/api/v1/discovery/results` | 发现结果 |

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

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/v1/scripts` | 脚本列表 |
| POST | `/api/v1/scripts` | 创建脚本 |
| PUT | `/api/v1/scripts/{script_id}` | 更新脚本 |
| DELETE | `/api/v1/scripts/{script_id}` | 删除脚本 |
| GET | `/api/v1/playbooks` | Playbook 列表 |
| POST | `/api/v1/playbooks` | 创建 Playbook |
| GET | `/api/v1/playbooks/{playbook_id}` | Playbook 详情 |
| PUT | `/api/v1/playbooks/{playbook_id}` | 更新 Playbook |
| DELETE | `/api/v1/playbooks/{playbook_id}` | 删除 Playbook |
| GET | `/api/v1/policies` | 策略列表 |
| POST | `/api/v1/policies` | 创建策略 |
| GET | `/api/v1/policies/{policy_id}` | 策略详情 |
| PUT | `/api/v1/policies/{policy_id}` | 更新策略 |
| DELETE | `/api/v1/policies/{policy_id}` | 删除策略 |
| POST | `/api/v1/policies/{policy_id}/simulate` | 模拟策略 |
| GET | `/api/v1/executions` | 执行列表 |
| POST | `/api/v1/executions` | 创建执行 |
| GET | `/api/v1/executions/{exec_id}` | 执行详情 |
| POST | `/api/v1/executions/{exec_id}/approve` | 审批执行 |
| POST | `/api/v1/executions/{exec_id}/cancel` | 取消执行 |
| GET | `/api/v1/executions/{exec_id}/verification` | 验证结果 |

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

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/v1/users` | 用户列表 |
| POST | `/api/v1/users` | 创建用户 |
| GET | `/api/v1/users/{user_id}` | 用户详情 |
| PUT | `/api/v1/users/{user_id}` | 更新用户 |
| DELETE | `/api/v1/users/{user_id}` | 删除用户 |
| GET | `/api/v1/roles` | 角色列表 |
| POST | `/api/v1/roles` | 创建角色 |
| GET | `/api/v1/api-keys` | API Key 列表 |
| POST | `/api/v1/api-keys` | 创建 API Key |
| PATCH | `/api/v1/api-keys/{key_id}` | 更新 API Key |
| DELETE | `/api/v1/api-keys/{key_id}` | 删除 API Key |
| GET | `/api/v1/audit-logs` | 审计日志 |
| GET | `/api/v1/platform/status` | 平台状态 |
| GET | `/api/v1/backups` | 备份列表 |
| POST | `/api/v1/backups` | 创建备份 |
| GET | `/api/v1/backups/{backup_id}` | 备份详情 |
| GET | `/api/v1/backups/{backup_id}/download` | 下载备份 |
| POST | `/api/v1/backups/{backup_id}/restore` | 恢复备份 |
| GET | `/api/v1/backups/settings` | 备份设置 |
| GET | `/api/v1/backups/storage` | 存储信息 |

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
