import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', name: 'login', component: () => import('@/features/auth/LoginPage.vue'), meta: { public: true } },
    { path: '/', component: () => import('@/app/layout/MainLayout.vue'), redirect: '/dashboard', children: [
      { path: 'dashboard', name: 'dashboard', component: () => import('@/features/command-center/CommandCenterPage.vue'), meta: { title: '运维指挥台', icon: 'Monitor' } },
      { path: 'assets', name: 'assets', component: () => import('@/features/asset-config/AssetListPage.vue'), meta: { title: '资产管理', icon: 'Grid' } },
      { path: 'collectors', name: 'collectors', component: () => import('@/features/asset-config/CollectorPage.vue'), meta: { title: '采集器管理', icon: 'Connection' } },
      { path: 'configs', name: 'configs', component: () => import('@/features/asset-config/ConfigPage.vue'), meta: { title: '配置管理', icon: 'Setting' } },
      { path: 'events', name: 'events', component: () => import('@/features/monitoring-event/EventListPage.vue'), meta: { title: '事件列表', icon: 'InfoFilled' } },
      { path: 'alerts', name: 'alerts', component: () => import('@/features/monitoring-event/AlertListPage.vue'), meta: { title: '告警中心', icon: 'Bell' } },
      { path: 'incident', name: 'incident', component: () => import('@/features/command-center/IncidentResponsePage.vue'), meta: { title: '故障处置', icon: 'Warning' } },
      { path: 'automation', name: 'automation', component: () => import('@/features/command-center/AutomationPage.vue'), meta: { title: '自动化编排', icon: 'VideoPlay' } },
      { path: 'ai-diagnosis', name: 'ai-diagnosis', component: () => import('@/features/command-center/AIDiagnosisPage.vue'), meta: { title: 'AI 诊断', icon: 'MagicStick' } },
      { path: 'tickets', name: 'tickets', component: () => import('@/features/monitoring-event/TicketPage.vue'), meta: { title: '工单中心', icon: 'Tickets' } },
      { path: 'knowledge', name: 'knowledge', component: () => import('@/features/asset-config/KnowledgePage.vue'), meta: { title: '知识库', icon: 'Collection' } },
      { path: 'admin', name: 'admin', component: () => import('@/features/platform-admin/UserManagementPage.vue'), meta: { title: '用户管理', icon: 'User' } },
      { path: 'audit', name: 'audit', component: () => import('@/features/platform-admin/AuditLogPage.vue'), meta: { title: '审计日志', icon: 'Document' } },
    ]},
  ],
})

export default router
