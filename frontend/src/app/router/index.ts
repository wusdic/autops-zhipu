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
    // M1 运维驾驶舱
    // ============================================================
    { path: '/', name: 'dashboard', component: () => import('@/features/command-dashboard/CommandDashboardPage.vue'), meta: { module: 'M1', title: '指挥台' } },
    { path: '/business-health-map', name: 'business-health-map', component: () => import('@/features/command-dashboard/BusinessHealthMapPage.vue'), meta: { module: 'M1', title: '业务健康地图' } },
    { path: '/daily-summary', name: 'daily-summary', component: () => import('@/features/command-dashboard/DailySummaryPage.vue'), meta: { module: 'M1', title: '今日摘要' } },

    // ============================================================
    // M2 资源中心
    // ============================================================
    { path: '/resources', name: 'resources-overview', component: () => import('@/features/resource-center/ResourceOverviewPage.vue'), meta: { module: 'M2', title: '资源总览' } },
    { path: '/assets', name: 'assets', component: () => import('@/features/resource-center/AssetListPage.vue'), meta: { module: 'M2', title: '资源列表' } },
    { path: '/assets/:id', name: 'asset-detail', component: () => import('@/features/resource-center/AssetDetailPage.vue'), meta: { module: 'M2', title: '资源详情' } },
    { path: '/business-systems', name: 'business-systems', component: () => import('@/features/resource-center/BusinessSystemPage.vue'), meta: { module: 'M2', title: '业务系统' } },
    { path: '/topology', name: 'topology', component: () => import('@/features/resource-center/AssetTopologyPage.vue'), meta: { module: 'M2', title: '拓扑视图' } },
    { path: '/asset-groups', name: 'asset-groups', component: () => import('@/features/resource-center/AssetGroupPage.vue'), meta: { module: 'M2', title: '资源分组' } },
    { path: '/lifecycle', name: 'lifecycle', component: () => import('@/features/resource-center/LifecyclePage.vue'), meta: { module: 'M2', title: '生命周期' } },
    { path: '/resources/discovery', name: 'discovery-tasks', component: () => import('@/features/resource-center/AssetDiscoveryPage.vue'), meta: { module: 'M2', title: '资源发现' } },
    // 去重：发现结果已并入资源发现页"发现结果"tab，旧路径重定向保留外链/书签
    { path: '/resources/discovery-results', redirect: '/resources/discovery?tab=results' },
    { path: '/resources/import', name: 'resource-import', component: () => import('@/features/resource-center/ResourceImportPage.vue'), meta: { module: 'M2', title: '资源导入' } },

    // ============================================================
    // M3 巡检中心
    // ============================================================
    { path: '/inspections', name: 'inspections-overview', component: () => import('@/features/inspection-center/InspectionOverviewPage.vue'), meta: { module: 'M3', title: '巡检总览' } },
    { path: '/inspection/plans', name: 'inspection-plans', component: () => import('@/features/inspection-center/InspectionPlanPage.vue'), meta: { module: 'M3', title: '巡检计划' } },
    { path: '/inspection/tasks', name: 'inspection-tasks', component: () => import('@/features/inspection-center/InspectionTaskPage.vue'), meta: { module: 'M3', title: '巡检任务' } },
    { path: '/inspection/results', name: 'inspection-results', component: () => import('@/features/inspection-center/InspectionResultPage.vue'), meta: { module: 'M3', title: '巡检结果' } },
    { path: '/inspection/page-check', name: 'page-inspection', component: () => import('@/features/inspection-center/PageInspectionPage.vue'), meta: { module: 'M3', title: '页面巡检' } },
    { path: '/inspection/config-check', name: 'config-inspection', component: () => import('@/features/inspection-center/ConfigInspectionPage.vue'), meta: { module: 'M3', title: '配置巡检' } },
    { path: '/inspection/log-check', name: 'log-inspection', component: () => import('@/features/inspection-center/LogInspectionPage.vue'), meta: { module: 'M3', title: '日志巡检' } },
    { path: '/inspection/baseline-check', name: 'baseline-inspection', component: () => import('@/features/inspection-center/BaselineInspectionPage.vue'), meta: { module: 'M3', title: '基线巡检' } },
    { path: '/inspection/:id', name: 'inspection-detail', component: () => import('@/features/inspection-center/InspectionDetailPage.vue'), meta: { module: 'M3', title: '巡检详情' } },
    { path: '/inspection/reports', name: 'inspection-reports', component: () => import('@/features/inspection-center/InspectionReportPage.vue'), meta: { module: 'M3', title: '巡检报告' } },
    { path: '/inspection/templates', name: 'inspection-templates', component: () => import('@/features/inspection-center/InspectionTemplatePage.vue'), meta: { module: 'M3', title: '巡检模板' } },

    // ============================================================
    // M4 监控告警
    // ============================================================
    // 监控采集
    { path: '/monitoring', name: 'monitoring', component: () => import('@/features/monitoring-center/MonitoringOverviewPage.vue'), meta: { module: 'M4', title: '监控总览' } },
    { path: '/monitoring/collectors', name: 'collectors', component: () => import('@/features/monitoring-center/CollectorPage.vue'), meta: { module: 'M4', title: '采集任务' } },
    { path: '/monitoring/collection-results', name: 'collection-results', component: () => import('@/features/monitoring-center/CollectionResultPage.vue'), meta: { module: 'M4', title: '采集结果' } },
    { path: '/monitoring/collector-health', name: 'collector-health', component: () => import('@/features/monitoring-center/CollectorHealthPage.vue'), meta: { module: 'M4', title: '采集器健康' } },
    { path: '/monitoring/metrics', name: 'metrics-trend', component: () => import('@/features/monitoring-center/MetricsTrendPage.vue'), meta: { module: 'M4', title: '指标趋势' } },
    { path: '/monitoring/states', name: 'state-monitor', component: () => import('@/features/monitoring-center/StateMonitorPage.vue'), meta: { module: 'M4', title: '状态监控' } },
    // 去重 B4：状态变化已并入状态监控页"变更历史"tab，旧路径重定向保留外链/书签
    { path: '/monitoring/state-changes', redirect: '/monitoring/states?tab=changes' },
    { path: '/events', name: 'events', component: () => import('@/features/monitoring-center/EventListPage.vue'), meta: { module: 'M4', title: '事件流' } },
    { path: '/monitoring/log-sources', name: 'log-sources', component: () => import('@/features/monitoring-center/LogSourcePage.vue'), meta: { module: 'M4', title: '日志接入' } },
    { path: '/monitoring/config-facts', name: 'config-facts', component: () => import('@/features/monitoring-center/ConfigPage.vue'), meta: { module: 'M4', title: '配置快照' } },
    // 告警管理
    { path: '/alerts', name: 'alerts', component: () => import('@/features/monitoring-center/AlertListPage.vue'), meta: { module: 'M4', title: '告警列表' } },
    { path: '/alerts/:id', name: 'alert-detail', component: () => import('@/features/monitoring-center/AlertDetailPage.vue'), meta: { module: 'M4', title: '告警详情' } },
    { path: '/alert-rules', name: 'alert-rules', component: () => import('@/features/monitoring-center/AlertRulePage.vue'), meta: { module: 'M4', title: '告警规则' } },
    { path: '/alert-correlation', name: 'alert-correlation', component: () => import('@/features/response-center/AlertCorrelationPage.vue'), meta: { module: 'M4', title: '告警收敛' } },
    { path: '/anomalies', name: 'anomaly-center', component: () => import('@/features/response-center/AnomalyCenterPage.vue'), meta: { module: 'M4', title: '异常中心' } },
    // 去重 C：异常列表已并入异常中心页"列表"tab，旧路径重定向保留外链/书签
    { path: '/anomaly/list', redirect: '/anomalies?tab=list' },
    { path: '/anomaly/:id', name: 'anomaly-detail', component: () => import('@/features/response-center/AnomalyDetailPage.vue'), meta: { module: 'M4', title: '异常详情' } },

    // ============================================================
    // M5 分析中心
    // ============================================================
    // 去重 B1/B2：分析中心 5 个单步页收敛为故障工作台内 tab，菜单只留一个入口
    { path: '/incident', name: 'incident', component: () => import('@/features/response-center/IncidentWorkbenchPage.vue'), meta: { module: 'M5', title: '故障工作台' } },
    { path: '/incident/:alertId', name: 'incident-detail', component: () => import('@/features/response-center/IncidentResponsePage.vue'), meta: { module: 'M5', title: '故障处置详情' } },
    { path: '/ai-diagnosis', redirect: '/incident?tab=ai' },
    { path: '/impact-analysis', redirect: '/incident?tab=impact' },
    { path: '/risk-grading', redirect: '/incident?tab=risk' },
    { path: '/response-suggestion', redirect: '/incident?tab=suggestion' },
    { path: '/closure-verification', redirect: '/incident?tab=closure' },

    // ============================================================
    // M6 自动化中心
    // ============================================================
    { path: '/automation', name: 'automation-overview', component: () => import('@/features/automation-center/AutomationOverviewPage.vue'), meta: { module: 'M6', title: '自动化总览' } },
    { path: '/policies', name: 'policies', component: () => import('@/features/automation-center/PolicyListPage.vue'), meta: { module: 'M6', title: '策略管理' } },
    { path: '/policies/:id/edit', name: 'policy-edit', component: () => import('@/features/automation-center/PolicyEditPage.vue'), meta: { module: 'M6', title: '策略编辑' } },
    { path: '/policies/:id/simulate', name: 'policy-simulate', component: () => import('@/features/automation-center/PolicySimulatePage.vue'), meta: { module: 'M6', title: '策略模拟' } },
    // 去重：处置模板与剧本库同源（同读 PLAYBOODS），重定向到剧本库
    { path: '/remediation-templates', redirect: '/playbooks' },
    { path: '/scripts', name: 'scripts', component: () => import('@/features/automation-center/ScriptListPage.vue'), meta: { module: 'M6', title: '脚本库' } },
    { path: '/playbooks', name: 'playbooks', component: () => import('@/features/automation-center/PlaybookListPage.vue'), meta: { module: 'M6', title: '剧本库' } },
    { path: '/approvals', name: 'approvals', component: () => import('@/features/automation-center/ApprovalCenterPage.vue'), meta: { module: 'M6', title: '审批中心' } },
    { path: '/executions', name: 'executions', component: () => import('@/features/automation-center/ExecutionListPage.vue'), meta: { module: 'M6', title: '执行历史' } },
    { path: '/executions/:id', name: 'execution-detail', component: () => import('@/features/automation-center/ExecutionDetailPage.vue'), meta: { module: 'M6', title: '执行详情' } },
    { path: '/dry-run/:id', name: 'dry-run-detail', component: () => import('@/features/automation-center/DryRunDetailPage.vue'), meta: { module: 'M6', title: 'Dry-run 详情' } },
    { path: '/rollback-center', name: 'rollback-center', component: () => import('@/features/automation-center/RollbackCenterPage.vue'), meta: { module: 'M6', title: '回滚中心' } },
    { path: '/execution-locks', name: 'execution-locks', component: () => import('@/features/automation-center/ExecutionLockPage.vue'), meta: { module: 'M6', title: '执行锁' } },

    // ============================================================
    // M7 工单协同
    // ============================================================
    { path: '/ticket-overview', name: 'ticket-overview', component: () => import('@/features/ticket-center/TicketOverviewPage.vue'), meta: { module: 'M7', title: '工单总览' } },
    { path: '/tickets', name: 'tickets', component: () => import('@/features/ticket-center/TicketListPage.vue'), meta: { module: 'M7', title: '工单列表' } },
    { path: '/tickets/:id', name: 'ticket-detail', component: () => import('@/features/ticket-center/TicketDetailPage.vue'), meta: { module: 'M7', title: '工单详情' } },
    { path: '/ticket-create', name: 'ticket-create', component: () => import('@/features/ticket-center/TicketCreatePage.vue'), meta: { module: 'M7', title: '新建工单' } },
    { path: '/manual-handling', name: 'manual-workbench', component: () => import('@/features/ticket-center/ManualWorkbenchPage.vue'), meta: { module: 'M7', title: '人工工作台' } },
    // 去重 B3：人工确认台已并入人工工作台"待确认"tab，旧路径重定向保留外链/书签
    { path: '/manual-confirm', redirect: '/manual-handling?tab=confirm' },
    { path: '/assignment-rules', name: 'assignment-rules', component: () => import('@/features/ticket-center/AssignmentRulePage.vue'), meta: { module: 'M7', title: '派单规则' } },
    { path: '/sla-management', name: 'sla-management', component: () => import('@/features/ticket-center/SlaManagementPage.vue'), meta: { module: 'M7', title: 'SLA 管理' } },
    { path: '/postmortem', name: 'postmortem', component: () => import('@/features/ticket-center/PostmortemPage.vue'), meta: { module: 'M7', title: '故障复盘' } },
    { path: '/ticket-report', name: 'ticket-report', component: () => import('@/features/ticket-center/TicketReportPage.vue'), meta: { module: 'M7', title: '工单报告' } },

    // ============================================================
    // M8 智能知识库
    // ============================================================
    { path: '/knowledge-overview', name: 'knowledge-overview', component: () => import('@/features/knowledge-center/KnowledgeOverviewPage.vue'), meta: { module: 'M8', title: '知识总览' } },
    { path: '/knowledge', name: 'knowledge', component: () => import('@/features/knowledge-center/KnowledgeListPage.vue'), meta: { module: 'M8', title: '知识列表' } },
    { path: '/knowledge/import', name: 'knowledge-import', component: () => import('@/features/knowledge-center/KnowledgeImportPage.vue'), meta: { module: 'M8', title: '知识导入' } },
    { path: '/knowledge-review', name: 'knowledge-review', component: () => import('@/features/knowledge-center/KnowledgeReviewPage.vue'), meta: { module: 'M8', title: '知识审核' } },
    { path: '/knowledge/:id', name: 'knowledge-detail', component: () => import('@/features/knowledge-center/KnowledgeDetailPage.vue'), meta: { module: 'M8', title: '知识详情' } },
    { path: '/knowledge/:id/edit', name: 'knowledge-edit', component: () => import('@/features/knowledge-center/KnowledgeEditPage.vue'), meta: { module: 'M8', title: '知识编辑' } },
    // 归位：AI 诊断工具已并入故障工作台(M5) AI诊断 tab，旧入口重定向
    { path: '/aiops', redirect: '/incident?tab=ai' },
    { path: '/similar-cases', name: 'similar-cases', component: () => import('@/features/knowledge-center/SimilarCasePage.vue'), meta: { module: 'M8', title: '相似案例' } },
    { path: '/rule-gap', name: 'rule-gap', component: () => import('@/features/knowledge-center/RuleGapPage.vue'), meta: { module: 'M6', title: '规则覆盖度' } },
    { path: '/prompt-templates', name: 'prompt-templates', component: () => import('@/features/knowledge-center/PromptTemplatePage.vue'), meta: { module: 'M11', title: 'Prompt 模板' } },
    { path: '/ai-tool-policy', name: 'ai-tool-policy', component: () => import('@/features/knowledge-center/AIToolPolicyPage.vue'), meta: { module: 'M11', title: 'AI 工具策略' } },

    // ============================================================
    // M9 报表审计中心
    // ============================================================
    { path: '/reports', name: 'reports-overview', component: () => import('@/features/report-audit-center/ReportOverviewPage.vue'), meta: { module: 'M9', title: '报表总览' } },
    { path: '/report/generate', name: 'report-generate', component: () => import('@/features/report-audit-center/ReportGeneratePage.vue'), meta: { module: 'M9', title: '报告生成' } },
    { path: '/report/tasks', name: 'report-tasks', component: () => import('@/features/report-audit-center/ReportTaskPage.vue'), meta: { module: 'M9', title: '报告任务' } },
    { path: '/report/archive', name: 'report-archive', component: () => import('@/features/report-audit-center/ReportArchivePage.vue'), meta: { module: 'M9', title: '报告归档' } },
    { path: '/export-center', name: 'export-center', component: () => import('@/features/report-audit-center/ExportCenterPage.vue'), meta: { module: 'M9', title: '导出中心' } },
    { path: '/report/templates', name: 'report-templates', component: () => import('@/features/report-audit-center/ReportTemplatePage.vue'), meta: { module: 'M9', title: '报告模板' } },
    { path: '/report/:id/preview', name: 'report-preview', component: () => import('@/features/report-audit-center/ReportPreviewPage.vue'), meta: { module: 'M9', title: '报告预览' } },
    // 步骤5：成品报告按类型收敛为业务报告宿主，旧路径重定向
    { path: '/business-report', name: 'business-report', component: () => import('@/features/report-audit-center/BusinessReportPage.vue'), meta: { module: 'M9', title: '业务报告' } },
    { path: '/ops-report', redirect: '/business-report?tab=ops' },
    { path: '/asset-report', redirect: '/business-report?tab=asset' },
    { path: '/automation-report', redirect: '/business-report?tab=automation' },
    { path: '/compliance-report', redirect: '/business-report?tab=compliance' },
    // 与 /inspection/reports 重复，统一重定向到巡检中心巡检报告页（去重）
    { path: '/inspection-report', redirect: '/inspection/reports' },
    { path: '/audit', name: 'audit', component: () => import('@/features/platform-management/AuditLogPage.vue'), meta: { module: 'M9', title: '审计查询' } },
    { path: '/logs/search', name: 'log-search', component: () => import('@/features/report-audit-center/LogSearchPage.vue'), meta: { module: 'M9', title: '日志检索' } },
    { path: '/evidence', name: 'evidence-archive', component: () => import('@/features/report-audit-center/EvidenceArchivePage.vue'), meta: { module: 'M9', title: '证据归档' } },

    // ============================================================
    // M10 AI 助手
    // ============================================================
    { path: '/ai-assistant', name: 'ai-assistant', component: () => import('@/features/ai-center/AiAssistantPage.vue'), meta: { module: 'M10', title: 'AI 助手' } },

    // ============================================================
    // M11 配置中心
    // ============================================================
    { path: '/config/overview', name: 'config-overview', component: () => import('@/features/config-center/ConfigOverviewPage.vue'), meta: { module: 'M11', title: '配置总览' } },
    { path: '/credentials', name: 'credentials', component: () => import('@/features/resource-center/CredentialPage.vue'), meta: { module: 'M11', title: '凭证库' } },
    { path: '/config/versions', name: 'config-versions', component: () => import('@/features/config-center/ConfigVersionPage.vue'), meta: { module: 'M11', title: '配置版本' } },
    { path: '/config/discovery-templates', name: 'discovery-templates', component: () => import('@/features/config-center/DiscoveryTemplatePage.vue'), meta: { module: 'M11', title: '发现模板' } },
    { path: '/config/inspection-rules', name: 'inspection-rules', component: () => import('@/features/config-center/InspectionRulesPage.vue'), meta: { module: 'M11', title: '巡检规则' } },
    { path: '/config/threshold-rules', name: 'threshold-rules', component: () => import('@/features/config-center/ThresholdRulePage.vue'), meta: { module: 'M11', title: '阈值规则' } },
    { path: '/config/notification-rules', name: 'notification-rules', component: () => import('@/features/config-center/NotificationRulePage.vue'), meta: { module: 'M11', title: '通知规则' } },

    // ============================================================
    // M12 平台管理
    // ============================================================
    { path: '/users', name: 'admin-users', component: () => import('@/features/platform-management/UserManagementPage.vue'), meta: { module: 'M12', title: '用户管理' } },
    { path: '/roles', name: 'admin-roles', component: () => import('@/features/platform-management/RoleManagementPage.vue'), meta: { module: 'M12', title: '角色管理' } },
    { path: '/tenants', name: 'admin-tenants', component: () => import('@/features/platform-management/TenantManagementPage.vue'), meta: { module: 'M12', title: '租户管理' } },
    { path: '/permission-policy', name: 'permission-policy', component: () => import('@/features/platform-management/PermissionPolicyPage.vue'), meta: { module: 'M12', title: '权限策略' } },
    { path: '/api-keys', name: 'admin-api-keys', component: () => import('@/features/platform-management/ApiKeyPage.vue'), meta: { module: 'M12', title: 'API Key' } },
    { path: '/system-config', name: 'admin-config', component: () => import('@/features/platform-management/SystemConfigPage.vue'), meta: { module: 'M12', title: '系统配置' } },
    { path: '/dictionaries', name: 'admin-dictionaries', component: () => import('@/features/platform-management/DictionaryPage.vue'), meta: { module: 'M12', title: '字典管理' } },
    { path: '/integrations', name: 'admin-integrations', component: () => import('@/features/platform-management/IntegrationPage.vue'), meta: { module: 'M12', title: '集成管理' } },
    { path: '/model-service', name: 'model-service', component: () => import('@/features/platform-management/ModelServicePage.vue'), meta: { module: 'M11', title: '模型服务' } },
    { path: '/agents', name: 'agents', component: () => import('@/features/resource-center/AgentManagementPage.vue'), meta: { module: 'M12', title: '采集节点' } },
    // 去重：安全基线与基线巡检同源（同读 INSPECTION），重定向到基线巡检
    { path: '/security-baseline', redirect: '/inspection/baseline-check' },
    { path: '/platform-status', name: 'admin-status', component: () => import('@/features/platform-management/PlatformHealthPage.vue'), meta: { module: 'M12', title: '平台健康' } },
    { path: '/task-queue', name: 'admin-tasks', component: () => import('@/features/platform-management/TaskQueuePage.vue'), meta: { module: 'M12', title: '任务队列' } },
    { path: '/system-check', name: 'admin-self-check', component: () => import('@/features/platform-management/SelfCheckPage.vue'), meta: { module: 'M12', title: '系统自检' } },
    { path: '/backup', name: 'admin-backup', component: () => import('@/features/platform-management/BackupPage.vue'), meta: { module: 'M12', title: '备份恢复' } },
    { path: '/upgrade-maintenance', name: 'upgrade-maintenance', component: () => import('@/features/platform-management/UpgradeMaintenancePage.vue'), meta: { module: 'M12', title: '升级维护' } },
    { path: '/license', name: 'license', component: () => import('@/features/platform-management/LicensePage.vue'), meta: { module: 'M12', title: '授权许可' } },

    // 404
    { path: '/:pathMatch(.*)*', name: 'not-found', component: () => import('@/app/NotFoundPage.vue') },
  ],
})

setupAuthGuard(router)

export default router
