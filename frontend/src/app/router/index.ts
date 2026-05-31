import { createRouter, createWebHistory } from 'vue-router'
import { setupAuthGuard } from './guards'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    // 认证
    { path: '/login', name: 'login', component: () => import('@/features/platform-admin/LoginPage.vue') },

    // 2.1 运维指挥台
    { path: '/', name: 'dashboard', component: () => import('@/features/command-center/CommandCenterPage.vue') },

    // 2.2 资产与配置台
    { path: '/assets', name: 'assets', component: () => import('@/features/asset-config/AssetListPage.vue') },
    { path: '/assets/:id', name: 'asset-detail', component: () => import('@/features/asset-config/AssetDetailPage.vue') },
    { path: '/assets/discovery', name: 'asset-discovery', component: () => import('@/features/asset-config/AssetDiscoveryPage.vue') },
    { path: '/asset-groups', name: 'asset-groups', component: () => import('@/features/asset-config/AssetGroupPage.vue') },
    { path: '/credentials', name: 'credentials', component: () => import('@/features/asset-config/CredentialPage.vue') },
    { path: '/config', name: 'config', component: () => import('@/features/asset-config/ConfigPage.vue') },
    { path: '/collectors', name: 'collectors', component: () => import('@/features/asset-config/CollectorPage.vue') },

    // 2.3 监控与事件台
    { path: '/monitoring', name: 'monitoring', component: () => import('@/features/monitoring-event/MonitoringOverviewPage.vue') },
    { path: '/events', name: 'events', component: () => import('@/features/monitoring-event/EventListPage.vue') },
    { path: '/alerts', name: 'alerts', component: () => import('@/features/monitoring-event/AlertListPage.vue') },
    { path: '/alerts/:id', name: 'alert-detail', component: () => import('@/features/monitoring-event/AlertDetailPage.vue') },
    { path: '/alert-rules', name: 'alert-rules', component: () => import('@/features/monitoring-event/AlertRulePage.vue') },

    // 2.4 故障处置台
    { path: '/incident', name: 'incident', component: () => import('@/features/command-center/IncidentResponsePage.vue') },
    { path: '/incident/:alertId', name: 'incident-detail', component: () => import('@/features/command-center/IncidentResponsePage.vue') },

    // 2.5 自动化编排台
    { path: '/scripts', name: 'scripts', component: () => import('@/features/automation-orchestration/ScriptListPage.vue') },
    { path: '/playbooks', name: 'playbooks', component: () => import('@/features/automation-orchestration/PlaybookListPage.vue') },
    { path: '/policies', name: 'policies', component: () => import('@/features/automation-orchestration/PolicyListPage.vue') },
    { path: '/policies/:id/simulate', name: 'policy-simulate', component: () => import('@/features/automation-orchestration/PolicySimulatePage.vue') },
    { path: '/executions', name: 'executions', component: () => import('@/features/automation-orchestration/ExecutionListPage.vue') },
    { path: '/executions/:id', name: 'execution-detail', component: () => import('@/features/automation-orchestration/ExecutionDetailPage.vue') },
    { path: '/automation', name: 'automation', component: () => import('@/features/command-center/AutomationPage.vue') },

    // 2.6 AI 与知识台
    { path: '/aiops', name: 'aiops', component: () => import('@/features/command-center/AIDiagnosisPage.vue') },
    { path: '/knowledge', name: 'knowledge', component: () => import('@/features/asset-config/KnowledgePage.vue') },
    { path: '/knowledge/:id', name: 'knowledge-detail', component: () => import('@/features/aiops-knowledge/KnowledgeDetailPage.vue') },
    { path: '/knowledge/:id/edit', name: 'knowledge-edit', component: () => import('@/features/aiops-knowledge/KnowledgeEditPage.vue') },

    // 2.7 工单
    { path: '/tickets', name: 'tickets', component: () => import('@/features/monitoring-event/TicketPage.vue') },

    // 2.8 平台管理台
    { path: '/admin/users', name: 'admin-users', component: () => import('@/features/platform-admin/UserManagementPage.vue') },
    { path: '/admin/roles', name: 'admin-roles', component: () => import('@/features/platform-admin/RoleManagementPage.vue') },
    { path: '/admin/api-keys', name: 'admin-api-keys', component: () => import('@/features/platform-admin/ApiKeyPage.vue') },
    { path: '/admin/config', name: 'admin-config', component: () => import('@/features/platform-admin/SystemConfigPage.vue') },
    { path: '/admin/status', name: 'admin-status', component: () => import('@/features/platform-admin/PlatformStatusPage.vue') },
    { path: '/admin/backup', name: 'admin-backup', component: () => import('@/features/platform-admin/BackupPage.vue') },
    { path: '/audit', name: 'audit', component: () => import('@/features/platform-admin/AuditLogPage.vue') },

    // 404
    { path: '/:pathMatch(.*)*', name: 'not-found', component: () => import('@/features/command-center/CommandCenterPage.vue') },
  ],
})

setupAuthGuard(router)

export default router
