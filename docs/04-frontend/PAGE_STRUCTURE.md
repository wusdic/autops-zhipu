# AUTOPS 前端页面结构

> 文档路径：`docs/04-frontend/PAGE_STRUCTURE.md`
> 状态：current | 事实源：yes
> 反向同步时间：2026-05-31（从实际前端代码提取）
> 
> **本文件是前端页面和路由的唯一事实源。所有页面变更必须先更新此文档。**

---

## 1. 技术栈

| 技术 | 版本 | 用途 |
|---|---|---|
| Vue | 3.x | UI 框架 |
| TypeScript | 5.x | 类型系统 |
| Vite | 5.x | 构建工具 |
| Element Plus | 2.x | UI 组件库 |
| ECharts | 5.x | 图表 |
| Vue Router | 4.x | 路由 |
| Pinia | 2.x | 状态管理 |

---

## 2. 编码规范

### 2.1 导入约定

```typescript
// API 客户端 — default export
import api from '@/shared/api/client'

// API 路由常量 — named export
import { API } from '@/shared/api/routes'

// 共享组件 — 统一路径
import NotificationBell from '@/shared/components/NotificationBell.vue'

// 禁止硬编码 API 路径
// ❌ api.get('/api/v1/assets')
// ✅ api.get(API.ASSETS.LIST)
```

### 2.2 文件组织

```
src/
├── app/
│   ├── router/index.ts        — 路由定义
│   ├── layout/MainLayout.vue  — 主布局
│   └── App.vue                — 根组件
├── features/                   — 按工作台划分
│   ├── command-center/         — 运维指挥台 + 故障处置台
│   ├── asset-config/           — 资产与配置台
│   ├── monitoring-event/       — 监控与事件台 + 工单
│   ├── automation-orchestration/ — 自动化编排台
│   ├── aiops-knowledge/        — AI 与知识台
│   └── platform-admin/         — 平台管理台
└── shared/
    ├── api/
    │   ├── client.ts           — HTTP 客户端（default export）
    │   ├── routes.ts           — API 路径常量
    │   └── websocket.ts        — WebSocket 客户端
    └── components/             — 共享组件
```

---

## 3. 路由与页面清单（38 条路由，36 个页面）

### 3.1 认证

| 路由 | 组件 | 行数 | 说明 | 布局 |
|---|---|---|---|---|
| `/login` | `platform-admin/LoginPage.vue` | 94 | 登录页 | 独立 |

### 3.2 运维指挥台

| 路由 | 组件 | 行数 | 说明 | 依赖API |
|---|---|---|---|---|
| `/` | `command-center/CommandCenterPage.vue` | 807 | 总览仪表盘 | alerts/stats, platform/status, assets, executions |

### 3.3 资产与配置台

| 路由 | 组件 | 行数 | 说明 | 依赖API |
|---|---|---|---|---|
| `/assets` | `asset-config/AssetListPage.vue` | 854 | 资产列表 | assets |
| `/assets/:id` | `asset-config/AssetDetailPage.vue` | 779 | 资产详情 | assets/{id}, timeline, credentials, policies |
| `/assets/:id/topology` | `asset-config/AssetTopologyPage.vue` | 254 | 拓扑图 | assets/{id}/relations |
| `/assets/discovery` | `asset-config/AssetDiscoveryPage.vue` | 536 | 资产发现 | discovery/tasks, discovery/results |
| `/asset-groups` | `asset-config/AssetGroupPage.vue` | 414 | 资产分组 | asset-groups |
| `/credentials` | `asset-config/CredentialPage.vue` | 454 | 凭证管理 | credentials |
| `/config` | `asset-config/ConfigPage.vue` | 637 | 配置管理 | configs/definitions, configs/versions |
| `/collectors` | `asset-config/CollectorPage.vue` | 770 | 采集器管理 | collectors, collection-jobs |

### 3.4 监控与事件台

| 路由 | 组件 | 行数 | 说明 | 依赖API |
|---|---|---|---|---|
| `/monitoring` | `monitoring-event/MonitoringOverviewPage.vue` | 579 | 监控总览 | states/latest, states/changes |
| `/events` | `monitoring-event/EventListPage.vue` | 1036 | 事件列表 | events |
| `/alerts` | `monitoring-event/AlertListPage.vue` | 670 | 告警列表 | alerts |
| `/alerts/:id` | `monitoring-event/AlertDetailPage.vue` | 1121 | 告警详情 | alerts/{id}, alerts/acknowledge/resolve |
| `/alert-rules` | `monitoring-event/AlertRulePage.vue` | 314 | 告警规则 | alert-rules |

### 3.5 故障处置台

| 路由 | 组件 | 行数 | 说明 | 依赖API |
|---|---|---|---|---|
| `/incident` | `command-center/IncidentResponsePage.vue` | 1181 | 故障处置 | alerts, executions, knowledge, tickets |
| `/incident/:alertId` | `command-center/IncidentResponsePage.vue` | 1181 | 故障详情 | alerts/{id}, executions, aiops |

### 3.6 自动化编排台

| 路由 | 组件 | 行数 | 说明 | 依赖API |
|---|---|---|---|---|
| `/scripts` | `automation-orchestration/ScriptListPage.vue` | 1197 | 脚本库 | scripts |
| `/playbooks` | `automation-orchestration/PlaybookListPage.vue` | 322 | Playbook | playbooks |
| `/policies` | `automation-orchestration/PolicyListPage.vue` | 352 | 策略管理 | policies |
| `/policies/:id/simulate` | `automation-orchestration/PolicySimulatePage.vue` | 164 | 策略模拟 | policies/{id}/simulate |
| `/executions` | `automation-orchestration/ExecutionListPage.vue` | 905 | 执行历史 | executions |
| `/executions/:id` | `automation-orchestration/ExecutionDetailPage.vue` | 542 | 执行详情 | executions/{id}, logs/execution |

### 3.7 AI 与知识台

| 路由 | 组件 | 行数 | 说明 | 依赖API |
|---|---|---|---|---|
| `/aiops` | `aiops-knowledge/AiOpsPage.vue` | 1090 | AI 运维 | aiops/diagnose, aiops/analyses |
| `/knowledge` | `aiops-knowledge/KnowledgePage.vue` | 447 | 知识库 | knowledge |
| `/knowledge/:id` | `aiops-knowledge/KnowledgeDetailPage.vue` | 568 | 知识详情 | knowledge/{id} |
| `/knowledge/:id/edit` | `aiops-knowledge/KnowledgeEditPage.vue` | 263 | 知识编辑 | knowledge/{id} |
| `/knowledge/import` | `aiops-knowledge/KnowledgeImportPage.vue` | 731 | 知识导入 | knowledge/import |

### 3.8 工单

| 路由 | 组件 | 行数 | 说明 | 依赖API |
|---|---|---|---|---|
| `/tickets` | `monitoring-event/TicketPage.vue` | 1223 | 工单列表 | tickets |
| `/tickets/:id` | `monitoring-event/TicketDetailPage.vue` | 646 | 工单详情 | tickets/{id}, comments |

### 3.9 平台管理台

| 路由 | 组件 | 行数 | 说明 | 依赖API |
|---|---|---|---|---|
| `/admin/users` | `platform-admin/UserManagementPage.vue` | 303 | 用户管理 | users |
| `/admin/roles` | `platform-admin/RoleManagementPage.vue` | 310 | 角色管理 | roles |
| `/admin/api-keys` | `platform-admin/ApiKeyPage.vue` | 286 | API Key | api-keys |
| `/admin/config` | `platform-admin/SystemConfigPage.vue` | 632 | 系统配置 | platform/status |
| `/admin/status` | `platform-admin/PlatformStatusPage.vue` | 392 | 平台状态 | platform/status |
| `/admin/backup` | `platform-admin/BackupPage.vue` | 552 | 备份恢复 | backups |
| `/audit` | `platform-admin/AuditLogPage.vue` | 310 | 审计日志 | audit-logs |

---

## 4. 共享组件

| 组件 | 路径 | 行数 | 说明 | 使用页面 |
|---|---|---|---|---|
| `MainLayout` | `app/layout/MainLayout.vue` | 309 | 主布局+侧边栏+通知铃铛 | 所有认证后页面 |
| `NotificationBell` | `shared/components/NotificationBell.vue` | 177 | 通知铃铛 | MainLayout |
| `ConfigInheritance` | `shared/components/ConfigInheritance.vue` | 143 | 配置继承链可视化 | ConfigPage |
| `MetricChart` | `shared/components/MetricChart.vue` | 123 | ECharts 指标图表 | 多个监控页面 |
| `TopologyGraph` | `shared/components/TopologyGraph.vue` | 56 | 拓扑图 | AssetTopologyPage |
| `AssetSelector` | `shared/components/AssetSelector.vue` | 50 | 资产选择器 | 多个页面 |
| `StatusBadge` | `shared/components/StatusBadge.vue` | 39 | 状态徽章 | 多个页面 |
| `AiAnalysisCard` | `shared/components/AiAnalysisCard.vue` | 39 | AI 分析卡片 | AiOpsPage |
| `ApprovalDialog` | `shared/components/ApprovalDialog.vue` | 38 | 审批对话框 | ExecutionDetailPage |
| `LogStream` | `shared/components/LogStream.vue` | 26 | 实时日志流 | ExecutionDetailPage |
| `TimelineView` | `shared/components/TimelineView.vue` | 24 | 时间线视图 | AlertDetailPage |
| `JsonViewer` | `shared/components/JsonViewer.vue` | 23 | JSON 查看器 | 多个页面 |
| `SeverityBadge` | `shared/components/SeverityBadge.vue` | 21 | 严重性徽章 | 告警相关页面 |
| `ConfigDiffView` | `shared/components/ConfigDiffView.vue` | 18 | 配置差异视图 | ConfigPage |

---

## 5. 前端 API 层

### 5.1 client.ts

- HTTP 客户端封装（axios）
- 自动添加 Bearer Token
- 自动刷新 Token
- 统一错误处理
- **export default**（非 named export）

### 5.2 routes.ts

- 所有 API 路径常量的唯一前端事实源
- 结构：`API.{模块}.{动作}` （如 `API.ASSETS.LIST`）
- **禁止**在前端代码中硬编码任何 `/api/v1/xxx` 路径

### 5.3 websocket.ts

- WebSocket 客户端，支持自动重连和心跳
- 17 种事件类型
- 事件分发机制

---

## 6. 统计

| 类别 | 数量 |
|---|---|
| 路由 | 38 条 |
| 页面组件 | 36 个 |
| 共享组件 | 14 个 |
| 特性目录 | 6 个 |
| 总代码行数 | 22,967 行 |
