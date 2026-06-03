# P1 骨架页充实设计

> 状态：accepted  
> 日期：2026-06-03  
> 目标：将 76 个骨架页（<100行）充实为有真实API调用和完整交互的页面

---

## 1. 页面增强标准模式

每个骨架页增强后必须满足：

1. **真实API调用** — 使用 `@/shared/api/` 下的 service 函数
2. **加载状态** — `v-loading` 指令
3. **错误处理** — ElMessage 错误提示
4. **空状态** — `el-empty` 组件
5. **分页** — 表格类页面必须有分页
6. **搜索/过滤** — 至少支持关键词搜索
7. **操作** — 新增/编辑/删除/查看 按钮和逻辑
8. **TypeScript** — 正确的类型定义

## 2. 页面分组与优先级

### Group A — 模块入口页（6页，最高优先级）
- InspectionOverviewPage, AutomationOverviewPage, AnomalyOverviewPage
- ReportOverviewPage, KnowledgeOverviewPage, ResourceOverviewPage

### Group B — 关键列表页（7页）
- InspectionTemplatePage, InspectionTaskPage, InspectionPlanPage
- BusinessSystemPage, AgentManagementPage, ApprovalCenterPage, DryRunDetailPage

### Group C — 监控页（6页）
- CollectionResultPage, MetricsTrendPage, LogSourcePage
- CollectorHealthPage, StateChangePage, StateSnapshotPage

### Group D — 巡检子类型页（4页）
- PageInspectionPage, ConfigInspectionPage, LogInspectionPage, BaselineInspectionPage

### Group E — 报表页（10页）
- InspectionReportPage, AutomationReportPage, AssetReportPage
- TicketReportPage, OpsReportPage, ReportTemplatePage
- ReportGeneratePage, ReportPreviewPage, ReportTaskPage, ReportArchivePage

### Group F — 平台管理页（7页）
- DictionaryPage, IntegrationPage, TaskQueuePage
- TenantManagementPage, SelfCheckPage, LicensePage, UpgradeMaintenancePage

### Group G — 知识/AI页（7页）
- PromptTemplatePage, PostmortemPage, SimilarCasePage
- ResponseSuggestionPage, AiToolPolicyPage, RuleGapPage, KnowledgeReviewPage

### Group H — 工单/流程页（5页）
- TicketCreatePage, TicketOverviewPage, SlaManagementPage
- AssignmentRulePage, ClosureVerificationPage

### Group I — 其他（24页）
- AnomalyDetailPage, AnomalyListPage, AlertCorrelationPage
- ImpactAnalysisPage, DailySummaryPage, BusinessHealthMapPage
- AuditQueryPage, EvidenceArchivePage, LogSearchPage
- SecurityBaselinePage, ExecutionLockPage, PolicyEditPage
- PermissionPolicyPage, RollbackCenterPage, InspectionResultPage
- DiscoveryResultPage, ResourceImportPage, AiDiagnosisPanelPage
- UserProfilePage, InspectionReportPage(dup), DailySummaryPage
- RiskGradingPage(159行→增强)

### 排除（无需增强）
- NotFoundPage(8), ForbiddenPage(12), SessionExpiredPage(16), LoginPage(94) — 功能性页面

## 3. 每页目标行数

| 类型 | 目标行数 | 示例 |
|------|----------|------|
| Overview页 | 250-400 | 统计卡片 + 图表 + 快捷列表 |
| List页 | 300-500 | 搜索栏 + 表格 + 分页 + 操作 |
| Detail页 | 300-600 | Tab布局 + 关联数据 + 操作 |
| 表单页 | 200-400 | 表单 + 验证 + 提交 |
| 统计页 | 250-400 | 图表 + 数据表 + 筛选 |

## 4. API映射

每个页面使用 `@/shared/api/` 下对应的 service：
- 资产相关 → `asset.ts` (ASSETS, ASSET_DISCOVERY, ASSET_GROUPS...)
- 告警相关 → `alert.ts` (ALERTS, ALERT_RULES...)
- 巡检相关 → `inspection.ts` (INSPECTION.TEMPLATES, .TASKS...)
- 执行相关 → `execution.ts` (EXECUTIONS...)
- 策略相关 → `policy.ts` (POLICIES...)
- 知识相关 → `knowledge.ts` (KNOWLEDGE...)
- 工单相关 → `ticket.ts` (TICKETS...)
- 收集器相关 → `collector.ts` (COLLECTORS...)
- 配置相关 → `config.ts` (CONFIGS...)
- 仪表盘相关 → `dashboard.ts` (DASHBOARD.*)

## 5. 共享组件复用

优先使用已有共享组件：
- `@/shared/components/` 下的 StatCard, PageHeader, StatusTag
- Element Plus 的 el-table, el-form, el-card, el-tabs
