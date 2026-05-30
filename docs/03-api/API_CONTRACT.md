# AUTOPS API 契约

> 文档状态：current
> 是否为事实源：yes
> 建议路径：`docs/03-api/API_CONTRACT.md`

---

## 1. 通用约定

### 1.1 基础 URL

```
开发: http://localhost:8000
生产: http(s)://{host}/api
```

### 1.2 API 前缀

所有 API 版本化：`/api/v1/`

### 1.3 请求格式

- Content-Type: `application/json`
- 认证: `Authorization: Bearer <token>` 或 `X-API-Key: <key>`

### 1.4 统一响应

```json
{
  "code": 0,
  "message": "success",
  "data": {},
  "trace_id": "uuid"
}
```

### 1.5 分页响应

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [],
    "total": 100,
    "page": 1,
    "page_size": 20,
    "total_pages": 5
  },
  "trace_id": "uuid"
}
```

### 1.6 错误响应

```json
{
  "code": 10100,
  "message": "资产不存在",
  "data": null,
  "trace_id": "uuid"
}
```

### 1.7 HTTP 状态码

| 状态码 | 说明 |
|---|---|
| 200 | 成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 409 | 资源冲突 |
| 422 | 参数验证失败 |
| 500 | 服务器错误 |

### 1.8 过滤和排序

```
GET /api/v1/assets?page=1&page_size=20&sort_by=name&sort_order=asc&asset_type=linux_server&status=active&search=web
```

---

## 2. 认证 API

| 方法 | 路径 | 说明 | 认证 |
|---|---|---|---|
| POST | /api/v1/auth/login | 登录 | 否 |
| POST | /api/v1/auth/logout | 登出 | 是 |
| POST | /api/v1/auth/refresh | 刷新Token | 是 |
| GET | /api/v1/auth/me | 当前用户 | 是 |
| PUT | /api/v1/auth/password | 修改密码 | 是 |

---

## 3. 资产 API

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | /api/v1/assets | 资产列表（分页、过滤） |
| POST | /api/v1/assets | 创建资产 |
| GET | /api/v1/assets/{id} | 资产详情 |
| PUT | /api/v1/assets/{id} | 更新资产 |
| DELETE | /api/v1/assets/{id} | 删除资产 |
| POST | /api/v1/assets/import | 批量导入 |
| GET | /api/v1/assets/{id}/relations | 资产关系 |
| POST | /api/v1/assets/{id}/relations | 添加关系 |
| DELETE | /api/v1/assets/{id}/relations/{rid} | 删除关系 |
| GET | /api/v1/assets/{id}/timeline | 资产时间线 |
| GET | /api/v1/assets/{id}/state | 资产当前状态 |
| GET | /api/v1/asset-groups | 分组列表 |
| POST | /api/v1/asset-groups | 创建分组 |
| GET | /api/v1/asset-groups/{id} | 分组详情 |
| PUT | /api/v1/asset-groups/{id} | 更新分组 |
| POST | /api/v1/asset-groups/{id}/members | 添加成员 |
| DELETE | /api/v1/asset-groups/{id}/members/{asset_id} | 移除成员 |
| POST | /api/v1/discovery-tasks | 创建发现任务 |
| GET | /api/v1/discovery-tasks/{id} | 任务状态 |

---

## 4. 配置与凭证 API

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | /api/v1/config-definitions | 配置定义列表 |
| POST | /api/v1/config-definitions | 创建定义 |
| GET | /api/v1/config-definitions/{id}/versions | 版本列表 |
| POST | /api/v1/config-definitions/{id}/versions | 创建版本 |
| POST | /api/v1/config-versions/{id}/publish | 发布 |
| POST | /api/v1/config-versions/{id}/rollback | 回滚 |
| GET | /api/v1/config-bindings | 绑定列表 |
| POST | /api/v1/config-bindings | 绑定配置 |
| DELETE | /api/v1/config-bindings/{id} | 解绑 |
| GET | /api/v1/config-drifts | 漂移列表 |
| GET | /api/v1/credentials | 凭证列表（脱敏） |
| POST | /api/v1/credentials | 创建凭证 |
| GET | /api/v1/credentials/{id} | 凭证详情（脱敏） |
| PUT | /api/v1/credentials/{id} | 更新凭证 |
| DELETE | /api/v1/credentials/{id} | 删除凭证 |
| POST | /api/v1/credentials/{id}/test | 测试凭证 |
| GET | /api/v1/credential-bindings | 绑定列表 |
| POST | /api/v1/credential-bindings | 绑定凭证 |
| GET | /api/v1/change-records | 变更记录 |

---

## 5. 采集与状态 API

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | /api/v1/collectors | 采集器列表 |
| GET | /api/v1/collectors/{id} | 采集器详情 |
| GET | /api/v1/collectors/{id}/health | 健康状态 |
| GET | /api/v1/collection-jobs | 任务列表 |
| POST | /api/v1/collection-jobs | 创建任务 |
| GET | /api/v1/collection-jobs/{id} | 任务详情 |
| PUT | /api/v1/collection-jobs/{id} | 更新任务 |
| POST | /api/v1/collection-jobs/{id}/execute | 手动执行 |
| POST | /api/v1/collection-jobs/{id}/pause | 暂停 |
| POST | /api/v1/collection-jobs/{id}/resume | 恢复 |
| GET | /api/v1/collection-results | 结果列表 |
| GET | /api/v1/collection-results/{id} | 结果详情 |
| GET | /api/v1/states/{asset_id} | 资产最新状态 |
| GET | /api/v1/states/{asset_id}/history | 状态历史 |
| GET | /api/v1/state-changes | 变更列表 |

---

## 6. 事件与告警 API

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | /api/v1/events | 事件列表 |
| GET | /api/v1/events/{id} | 事件详情 |
| GET | /api/v1/alerts | 告警列表 |
| GET | /api/v1/alerts/{id} | 告警详情 |
| POST | /api/v1/alerts/{id}/acknowledge | 确认 |
| POST | /api/v1/alerts/{id}/resolve | 解决 |
| POST | /api/v1/alerts/{id}/suppress | 抑制 |
| POST | /api/v1/alerts/{id}/escalate | 升级 |
| POST | /api/v1/alerts/{id}/create-ticket | 转工单 |
| GET | /api/v1/alert-rules | 规则列表 |
| POST | /api/v1/alert-rules | 创建规则 |
| PUT | /api/v1/alert-rules/{id} | 更新规则 |
| DELETE | /api/v1/alert-rules/{id} | 删除规则 |
| GET | /api/v1/alerts/stats | 告警统计 |

---

## 7. 策略 API

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | /api/v1/policies | 策略列表 |
| POST | /api/v1/policies | 创建策略 |
| GET | /api/v1/policies/{id} | 策略详情 |
| PUT | /api/v1/policies/{id} | 更新策略 |
| DELETE | /api/v1/policies/{id} | 删除策略 |
| GET | /api/v1/policies/{id}/versions | 版本列表 |
| POST | /api/v1/policies/{id}/publish | 发布 |
| POST | /api/v1/policies/{id}/simulate | 模拟 |
| GET | /api/v1/policies/{id}/history | 执行历史 |
| POST | /api/v1/policies/conflict-check | 冲突检测 |

---

## 8. 自动化 API

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | /api/v1/scripts | 脚本列表 |
| POST | /api/v1/scripts | 创建脚本 |
| GET | /api/v1/scripts/{id} | 脚本详情 |
| PUT | /api/v1/scripts/{id} | 更新脚本 |
| DELETE | /api/v1/scripts/{id} | 删除脚本 |
| GET | /api/v1/playbooks | Playbook 列表 |
| POST | /api/v1/playbooks | 创建 Playbook |
| GET | /api/v1/playbooks/{id} | 详情 |
| PUT | /api/v1/playbooks/{id} | 更新 |
| DELETE | /api/v1/playbooks/{id} | 删除 |
| POST | /api/v1/executions | 创建执行 |
| GET | /api/v1/executions | 执行列表 |
| GET | /api/v1/executions/{id} | 执行详情 |
| POST | /api/v1/executions/{id}/dry-run | dry-run |
| POST | /api/v1/executions/{id}/approve | 审批通过 |
| POST | /api/v1/executions/{id}/reject | 审批拒绝 |
| POST | /api/v1/executions/{id}/cancel | 取消 |
| POST | /api/v1/executions/{id}/rollback | 回滚 |
| GET | /api/v1/executions/{id}/logs | 日志 |

---

## 9. AIops 与知识 API

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | /api/v1/aiops/analyze | 触发分析 |
| GET | /api/v1/aiops/analysis/{id} | 分析结果 |
| GET | /api/v1/aiops/analysis | 分析列表 |
| POST | /api/v1/aiops/analysis/{id}/feedback | 反馈 |
| GET | /api/v1/knowledge | 知识列表 |
| POST | /api/v1/knowledge | 创建知识 |
| GET | /api/v1/knowledge/{id} | 详情 |
| PUT | /api/v1/knowledge/{id} | 更新 |
| POST | /api/v1/knowledge/{id}/publish | 发布 |
| POST | /api/v1/knowledge/search | 搜索 |
| POST | /api/v1/knowledge/import | 批量导入 |

---

## 10. 工单 API

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | /api/v1/tickets | 工单列表 |
| POST | /api/v1/tickets | 创建工单 |
| GET | /api/v1/tickets/{id} | 详情 |
| PUT | /api/v1/tickets/{id} | 更新 |
| POST | /api/v1/tickets/{id}/assign | 指派 |
| POST | /api/v1/tickets/{id}/comments | 评论 |
| GET | /api/v1/tickets/{id}/comments | 评论列表 |
| POST | /api/v1/tickets/{id}/resolve | 解决 |
| POST | /api/v1/tickets/{id}/close | 关闭 |
| POST | /api/v1/tickets/{id}/create-knowledge | 生成知识 |

---

## 11. 治理 API

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | /api/v1/users | 用户列表 |
| POST | /api/v1/users | 创建用户 |
| GET | /api/v1/users/{id} | 详情 |
| PUT | /api/v1/users/{id} | 更新 |
| DELETE | /api/v1/users/{id} | 删除 |
| GET | /api/v1/roles | 角色列表 |
| POST | /api/v1/roles | 创建角色 |
| PUT | /api/v1/roles/{id} | 更新 |
| GET | /api/v1/api-keys | Key 列表 |
| POST | /api/v1/api-keys | 创建 |
| DELETE | /api/v1/api-keys/{id} | 撤销 |
| GET | /api/v1/audit-logs | 审计日志 |
| GET | /api/v1/audit-logs/export | 导出 |
| GET | /api/v1/platform/status | 平台状态 |
| GET | /api/v1/platform/config | 系统配置 |
| PUT | /api/v1/platform/config | 更新配置 |
| POST | /api/v1/platform/backup | 触发备份 |
| POST | /api/v1/platform/self-check | 自检 |

---

## 12. WebSocket API

| 路径 | 说明 |
|---|---|
| ws://{host}/ws/events | 实时事件流 |
| ws://{host}/ws/alerts | 实时告警 |
| ws://{host}/ws/executions/{id}/logs | 执行日志流 |
