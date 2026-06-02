import { createRouter, createWebHistory } from 'vue-router'
import { setupAuthGuard } from './guards'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    // ============================================================
    // G0 全局基础能力
    // ============================================================
    { path: '/login', name: 'login', component: () => import('@/features/platform-management/LoginPage.vue') },
    { path: '/forbidden', name: 'forbidden', component: () => import('@/app/ForbiddenPage.vue') },
    { path: '/session-expired', name: 'session-expired', component: () => import('@/app/SessionExpiredPage.vue') },
    { path: '/profile', name: 'profile', component: () => import('@/app/UserProfilePage.vue') },

    // ============================================================
    // M1 首页指挥台
    // ============================================================
    { path: '/', name: 'dashboard', component: () => import('@/features/command-dashboard/CommandDashboardPage.vue'), meta: { module: 'M1', title: '首页指挥台' } },

    // ============================================================
    // M2 资源中心
    // ============================================================
    { path: '/resources', name: 'resources-overview', component: () => import('@/features/resource-center/ResourceOverviewPage.vue'), meta: { module: 'M2', title: '资源总览' } },
    { path: '/resources/discovery', name: 'discovery-tasks', component: () => import('@/features/resource-center/AssetDiscoveryPage.vue'), meta: { module: 'M2', title: '资源发现任务' } },
    { path: '/resources/discovery-results', name: 'discovery-results', component: () => import('@/features/resource-center/DiscoveryResultPage.vue'), meta: { module: 'M2', title: '发现结果' } },
    { path: '/assets', name: 'assets', component: () => import('@/features/resource-center/AssetListPage.vue'), meta: { module: 'M2', title: '资源列表' } },
    { path: '/assets/:id', name: 'asset-detail', component: () => import('@/features/resource-center/AssetDetailPage.vue'), meta: { module: 'M2', title: '资源详情' } },
    { path: '/business-systems', name: 'business-systems', component: () => import('@/features/resource-center/BusinessSystemPage.vue'), meta: { module: 'M2', title: '业务系统' } },
    { path: '/topology', name: 'topology', component: () => import('@/features/resource-center/AssetTopologyPage.vue'), meta: { module: 'M2', title: '拓扑视图' } },
    { path: '/resources/import', name: 'resource-import', component: () => import('@/features/resource-center/ResourceImportPage.vue'), meta: { module: 'M2', title: '资源导入' } },
    { path: '/asset-groups', name: 'asset-groups', component: () => import('@/features/resource-center/AssetGroupPage.vue'), meta: { module: 'M2', title: '资源分组' } },
    { path: '/credentials', name: 'credentials', component: () => import('@/features/resource-center/CredentialPage.vue'), meta: { module: 'M2', title: '凭证管理' } },
    { path: '/agents', name: 'agents', component: () => import('@/features/resource-center/AgentManagementPage.vue'), meta: { module: 'M2', title: 'Agent 管理' } },

    // ============================================================
    // M3 巡检中心
    // ============================================================
    { path: '/inspections', name: 'inspections-overview', component: () => import('@/features/inspection-center/InspectionOverviewPage.vue'), meta: { module: 'M3', title: '巡检总览' } },
    { path: '/inspection/templates', name: 'inspection-templates', component: () => import('@/features/inspection-center/InspectionTemplatePage.vue'), meta: { module: 'M3', title: '巡检模板' } },
    { path: '/inspection/plans', name: 'inspection-plans', component: () => import('@/features/inspection-center/InspectionPlanPage.vue'), meta: { module: 'M3', title: '巡检计划' } },
    { path: '/inspection/tasks', name: 'inspection-tasks', component: () => import('@/features/inspection-center/InspectionTaskPage.vue'), meta: { module: 'M3', title: '巡检任务' } },
    { path: '/inspection/results', name: 'inspection-results', component: () => import('@/features/inspection-center/InspectionResultPage.vue'), meta: { module: 'M3', title: '巡检结果' } },
    { path: '/inspection/page-check', name: 'page-inspection', component: () => import('@/features/inspection-center/PageInspectionPage.vue'), meta: { module: 'M3', title: '页面巡检' } },
    { path: '/inspection/config-check', name: 'config-inspection', component: () => import('@/features/inspection-center/ConfigInspectionPage.vue'), meta: { module: 'M3', title: '配置巡检' } },
    { path: '/inspection/log-check', name: 'log-inspection', component: () => import('@/features/inspection-center/LogInspectionPage.vue'), meta: { module: 'M3', title: '日志巡检' } },
    { path: '/inspection/baseline-check', name: 'baseline-inspection', component: () => import('@/features/inspection-center/BaselineInspectionPage.vue'), meta: { module: 'M3', title: '基线巡检' } },
    { path: '/inspection/reports', name: 'inspection-reports', component: () => import('@/features/inspection-center/InspectionReportPage.vue'), meta: { module: 'M3', title: '巡检报告' } },

    // ============================================================
    // M4 监控中心
    // ============================================================
    { path: '/monitoring', name: 'monitoring', component: () => import('@/features/monitoring-center/MonitoringOverviewPage.vue'), meta: { module: 'M4', title: '监控总览' } },
    { path: '/monitoring/collectors', name: 'collectors', component: () => import('@/features/monitoring-center/CollectorPage.vue'), meta: { module: 'M4', title: '采集任务' } },
    { path: '/monitoring/collection-results', name: 'collection-results', component: () => import('@/features/monitoring-center/CollectionResultPage.vue'), meta: { module: 'M4', title: '采集结果' } },
    { path: '/monitoring/metrics', name: 'metrics-trend', component: () => import('@/features/monitoring-center/MetricsTrendPage.vue'), meta: { module: 'M4', title: '指标趋势' } },
    { path: '/monitoring/states', name: 'state-snapshot', component: () => import('@/features/monitoring-center/StateSnapshotPage.vue'), meta: { module: 'M4', title: '状态快照' } },
    { path: '/monitoring/state-changes', name: 'state-changes', component: () => import('@/features/monitoring-center/StateChangePage.vue'), meta: { module: 'M4', title: '状态变化' } },
    { path: '/events', name: 'events', component: () => import('@/features/monitoring-center/EventListPage.vue'), meta: { module: 'M4', title: '事件流' } },
    { path: '/monitoring/log-sources', name: 'log-sources', component: () => import('@/features/monitoring-center/LogSourcePage.vue'), meta: { module: 'M4', title: '日志接入' } },
    { path: '/monitoring/collector-health', name: 'collector-health', component: () => import('@/features/monitoring-center/CollectorHealthPage.vue'), meta: { module: 'M4', title: '采集器健康' } },
    { path: '/monitoring/config-facts', name: 'config-facts', component: () => import('@/features/monitoring-center/ConfigPage.vue'), meta: { module: 'M4', title: '配置事实' } },

    // ============================================================
    // M5 处置中心
    // ============================================================
    { path: '/anomalies', name: 'anomaly-overview', component: () => import('@/features/response-center/AnomalyOverviewPage.vue'), meta: { module: 'M5', title: '异常总览' } },
    { path: '/anomaly/list', name: 'anomaly-list', component: () => import('@/features/response-center/AnomalyListPage.vue'), meta: { module: 'M5', title: '异常列表' } },
    { path: '/anomaly/:id', name: 'anomaly-detail', component: () => import('@/features/response-center/AnomalyDetailPage.vue'), meta: { module: 'M5', title: '异常详情' } },
    { path: '/incident', name: 'incident', component: () => import('@/features/response-center/IncidentResponsePage.vue'), meta: { module: 'M5', title: '故障工作台' } },
    { path: '/incident/:alertId', name: 'incident-detail', component: () => import('@/features/response-center/IncidentResponsePage.vue'), meta: { module: 'M5', title: '故障处置详情' } },
    { path: '/alerts', name: 'alerts', component: () => import('@/features/monitoring-center/AlertListPage.vue'), meta: { module: 'M5', title: '告警列表' } },
    { path: '/alerts/:id', name: 'alert-detail', component: () => import('@/features/monitoring-center/AlertDetailPage.vue'), meta: { module: 'M5', title: '告警详情' } },
    { path: '/alert-rules', name: 'alert-rules', component: () => import('@/features/monitoring-center/AlertRulePage.vue'), meta: { module: 'M5', title: '告警规则' } },

    // ============================================================
    // M6 自动化中心
    // ============================================================
    { path: '/automation', name: 'automation-overview', component: () => import('@/features/automation-center/AutomationOverviewPage.vue'), meta: { module: 'M6', title: '自动化总览' } },
    { path: '/policies', name: 'policies', component: () => import('@/features/automation-center/PolicyListPage.vue'), meta: { module: 'M6', title: '策略列表' } },
    { path: '/policies/new', name: 'policy-create', component: () => import('@/features/automation-center/PolicyEditPage.vue'), meta: { module: 'M6', title: '策略编辑' } },
    { path: '/policies/:id/edit', name: 'policy-edit', component: () => import('@/features/automation-center/PolicyEditPage.vue'), meta: { module: 'M6', title: '策略编辑' } },
    { path: '/policies/:id/simulate', name: 'policy-simulate', component: () => import('@/features/automation-center/PolicySimulatePage.vue'), meta: { module: 'M6', title: '策略模拟' } },
    { path: '/scripts', name: 'scripts', component: () => import('@/features/automation-center/ScriptListPage.vue'), meta: { module: 'M6', title: '脚本库' } },
    { path: '/playbooks', name: 'playbooks', component: () => import('@/features/automation-center/PlaybookListPage.vue'), meta: { module: 'M6', title: '剧本库' } },
    { path: '/dry-run/:id', name: 'dry-run-detail', component: () => import('@/features/automation-center/DryRunDetailPage.vue'), meta: { module: 'M6', title: 'Dry-run 详情' } },
    { path: '/approvals', name: 'approvals', component: () => import('@/features/automation-center/ApprovalCenterPage.vue'), meta: { module: 'M6', title: '审批中心' } },
    { path: '/executions', name: 'executions', component: () => import('@/features/automation-center/ExecutionListPage.vue'), meta: { module: 'M6', title: '执行历史' } },
    { path: '/executions/:id', name: 'execution-detail', component: () => import('@/features/automation-center/ExecutionDetailPage.vue'), meta: { module: 'M6', title: '执行详情' } },

    // ============================================================
    // M7 智能知识库
    // ============================================================
    { path: '/aiops', name: 'aiops', component: () => import('@/features/knowledge-center/AiDiagnosisPage.vue'), meta: { module: 'M7', title: 'AI 诊断' } },
    { path: '/knowledge', name: 'knowledge', component: () => import('@/features/knowledge-center/KnowledgeListPage.vue'), meta: { module: 'M7', title: '知识列表' } },
    { path: '/knowledge/:id', name: 'knowledge-detail', component: () => import('@/features/knowledge-center/KnowledgeDetailPage.vue'), meta: { module: 'M7', title: '知识详情' } },
    { path: '/knowledge/:id/edit', name: 'knowledge-edit', component: () => import('@/features/knowledge-center/KnowledgeEditPage.vue'), meta: { module: 'M7', title: '知识编辑' } },
    { path: '/knowledge/import', name: 'knowledge-import', component: () => import('@/features/knowledge-center/KnowledgeImportPage.vue'), meta: { module: 'M7', title: '知识导入' } },

    // ============================================================
    // M8 工单中心
    // ============================================================
    { path: '/tickets', name: 'tickets', component: () => import('@/features/ticket-center/TicketListPage.vue'), meta: { module: 'M8', title: '工单列表' } },
    { path: '/tickets/:id', name: 'ticket-detail', component: () => import('@/features/ticket-center/TicketDetailPage.vue'), meta: { module: 'M8', title: '工单详情' } },

    // ============================================================
    // M9 报表审计中心
    // ============================================================
    { path: '/reports', name: 'reports-overview', component: () => import('@/features/report-audit-center/ReportOverviewPage.vue'), meta: { module: 'M9', title: '报表总览' } },
    { path: '/report/templates', name: 'report-templates', component: () => import('@/features/report-audit-center/ReportTemplatePage.vue'), meta: { module: 'M9', title: '报告模板' } },
    { path: '/report/generate', name: 'report-generate', component: () => import('@/features/report-audit-center/ReportGeneratePage.vue'), meta: { module: 'M9', title: '报告生成' } },
    { path: '/report/tasks', name: 'report-tasks', component: () => import('@/features/report-audit-center/ReportTaskPage.vue'), meta: { module: 'M9', title: '报告任务' } },
    { path: '/report/:id/preview', name: 'report-preview', component: () => import('@/features/report-audit-center/ReportPreviewPage.vue'), meta: { module: 'M9', title: '报告预览' } },
    { path: '/report/archive', name: 'report-archive', component: () => import('@/features/report-audit-center/ReportArchivePage.vue'), meta: { module: 'M9', title: '报告归档' } },
    { path: '/audit', name: 'audit', component: () => import('@/features/platform-management/AuditLogPage.vue'), meta: { module: 'M9', title: '审计查询' } },
    { path: '/logs/search', name: 'log-search', component: () => import('@/features/report-audit-center/LogSearchPage.vue'), meta: { module: 'M9', title: '日志检索' } },
    { path: '/evidence', name: 'evidence-archive', component: () => import('@/features/report-audit-center/EvidenceArchivePage.vue'), meta: { module: 'M9', title: '证据归档' } },

    // ============================================================
    // M10 平台管理
    // ============================================================
    { path: '/users', name: 'admin-users', component: () => import('@/features/platform-management/UserManagementPage.vue'), meta: { module: 'M10', title: '用户管理' } },
    { path: '/roles', name: 'admin-roles', component: () => import('@/features/platform-management/RoleManagementPage.vue'), meta: { module: 'M10', title: '角色管理' } },
    { path: '/tenants', name: 'admin-tenants', component: () => import('@/features/platform-management/TenantManagementPage.vue'), meta: { module: 'M10', title: '租户管理' } },
    { path: '/api-keys', name: 'admin-api-keys', component: () => import('@/features/platform-management/ApiKeyPage.vue'), meta: { module: 'M10', title: 'API Key' } },
    { path: '/system-config', name: 'admin-config', component: () => import('@/features/platform-management/SystemConfigPage.vue'), meta: { module: 'M10', title: '系统配置' } },
    { path: '/dictionaries', name: 'admin-dictionaries', component: () => import('@/features/platform-management/DictionaryPage.vue'), meta: { module: 'M10', title: '字典管理' } },
    { path: '/integrations', name: 'admin-integrations', component: () => import('@/features/platform-management/IntegrationPage.vue'), meta: { module: 'M10', title: '集成管理' } },
    { path: '/platform-status', name: 'admin-status', component: () => import('@/features/platform-management/PlatformHealthPage.vue'), meta: { module: 'M10', title: '平台健康' } },
    { path: '/task-queue', name: 'admin-tasks', component: () => import('@/features/platform-management/TaskQueuePage.vue'), meta: { module: 'M10', title: '任务队列' } },
    { path: '/backup', name: 'admin-backup', component: () => import('@/features/platform-management/BackupPage.vue'), meta: { module: 'M10', title: '备份恢复' } },
    { path: '/system-check', name: 'admin-self-check', component: () => import('@/features/platform-management/SelfCheckPage.vue'), meta: { module: 'M10', title: '系统自检' } },

    // 404
    { path: '/:pathMatch(.*)*', name: 'not-found', component: () => import('@/app/NotFoundPage.vue') },
  ],
})

setupAuthGuard(router)

export default router
