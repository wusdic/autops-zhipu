# AUTOPS 前端页面结构

> 文档状态：current
> 建议路径：`docs/04-frontend/PAGE_STRUCTURE.md`

---

## 1. 前端目录

```text
frontend/src/
  app/
    router/index.ts          # 路由定义
    store/                   # Pinia 全局 store
    permission/index.ts      # 权限守卫
    layout/                  # 主布局
  features/
    command-center/          # 运维指挥台
    asset-config/            # 资产与配置台
    monitoring-event/        # 监控与事件台
    incident-response/       # 故障处置台
    automation-orchestration/ # 自动化编排台
    aiops-knowledge/         # AI 与知识台
    ticket/                  # 工单
    platform-admin/          # 平台管理台
  shared/
    api/                     # API Client
    components/              # 公共组件
    hooks/                   # Composition API hooks
    utils/                   # 工具函数
    types/                   # TypeScript 类型
    constants/               # 常量
```

## 2. 页面列表

### 2.1 运维指挥台 (Command Center)

| 页面 | 路由 | 说明 |
|---|---|---|
| 指挥仪表盘 | /command-center | 总体概览仪表盘 |

组件：
- 平台健康状态卡片
- 严重告警实时列表
- 采集成功率趋势图
- 自动化执行统计
- 待审批列表
- 快速操作面板

### 2.2 资产与配置台 (Asset & Config)

| 页面 | 路由 | 说明 |
|---|---|---|
| 资产列表 | /assets | 资产管理主页面 |
| 资产详情 | /assets/:id | 单资产完整信息 |
| 资产发现 | /assets/discovery | 资产发现任务 |
| 资产分组 | /asset-groups | 分组管理 |
| 资产关系图 | /assets/:id/topology | 资产拓扑 |
| 配置管理 | /configs | 配置定义和版本 |
| 凭证管理 | /credentials | 凭证管理（脱敏展示） |

### 2.3 监控与事件台 (Monitoring & Events)

| 页面 | 路由 | 说明 |
|---|---|---|
| 监控总览 | /monitoring | 状态分布和指标趋势 |
| 事件列表 | /events | 事件流 |
| 告警列表 | /alerts | 告警管理 |
| 告警详情 | /alerts/:id | 告警上下文和时间线 |
| 告警规则 | /alert-rules | 告警规则管理 |

### 2.4 故障处置台 (Incident Response)

| 页面 | 路由 | 说明 |
|---|---|---|
| 故障处置 | /incident/:alertId | 故障处置主界面 |

布局：
```
┌──────────┬───────────────────┬──────────────┐
│          │                   │              │
│ 时间线    │   证据与分析       │  推荐动作     │
│ (事件流)  │  (指标/日志/AI)    │ (策略/执行)   │
│          │                   │              │
├──────────┴───────────────────┴──────────────┤
│              实时日志流                       │
└─────────────────────────────────────────────┘
```

### 2.5 自动化编排台 (Automation)

| 页面 | 路由 | 说明 |
|---|---|---|
| 脚本库 | /scripts | 脚本管理 |
| Playbook | /playbooks | Playbook 编排 |
| 策略管理 | /policies | 策略 CRUD |
| 策略模拟 | /policies/:id/simulate | 策略模拟 |
| 执行列表 | /executions | 执行历史 |
| 执行详情 | /executions/:id | 执行详情+日志 |

### 2.6 AI 与知识台 (AI & Knowledge)

| 页面 | 路由 | 说明 |
|---|---|---|
| AI 分析记录 | /aiops | AI 分析历史 |
| 知识库 | /knowledge | 知识文章列表 |
| 知识详情 | /knowledge/:id | 知识文章阅读 |
| 知识编辑 | /knowledge/:id/edit | 知识编辑 |
| 知识导入 | /knowledge/import | 批量导入 |

### 2.7 工单

| 页面 | 路由 | 说明 |
|---|---|---|
| 工单列表 | /tickets | 工单管理 |
| 工单详情 | /tickets/:id | 工单详情+上下文 |

### 2.8 平台管理台 (Platform Admin)

| 页面 | 路由 | 说明 |
|---|---|---|
| 用户管理 | /admin/users | 用户 CRUD |
| 角色管理 | /admin/roles | 角色权限 |
| API Key | /admin/api-keys | Key 管理 |
| 审计日志 | /admin/audit | 审计查询 |
| 系统配置 | /admin/config | 平台参数 |
| 平台状态 | /admin/status | 组件健康 |
| 备份恢复 | /admin/backup | 备份管理 |

---

## 3. 公共组件

| 组件 | 说明 |
|---|---|
| AssetSelector | 资产选择器（单选/多选） |
| StatusBadge | 状态标签（健康/告警/离线） |
| SeverityBadge | 严重度标签 |
| TimelineView | 时间线组件 |
| LogStream | 实时日志流组件 |
| MetricChart | 指标图表组件 |
| JsonViewer | JSON 查看器 |
| ConfigDiffView | 配置差异对比 |
| TopologyGraph | 拓扑图组件 |
| ApprovalDialog | 审批对话框 |
| AiAnalysisCard | AI 分析结果卡片 |
