import { createRouter, createWebHistory } from 'vue-router'
import { setupAuthGuard } from './guards'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', name: 'login', component: () => import('@/features/platform-admin/LoginPage.vue') },
    { path: '/', name: 'dashboard', component: () => import('@/features/command-center/CommandCenterPage.vue') },
    { path: '/assets', name: 'assets', component: () => import('@/features/asset-config/AssetListPage.vue') },
    { path: '/config', name: 'config', component: () => import('@/features/asset-config/ConfigPage.vue') },
    { path: '/collectors', name: 'collectors', component: () => import('@/features/asset-config/CollectorPage.vue') },
    { path: '/events', name: 'events', component: () => import('@/features/monitoring-event/EventListPage.vue') },
    { path: '/alerts', name: 'alerts', component: () => import('@/features/monitoring-event/AlertListPage.vue') },
    { path: '/incident', name: 'incident', component: () => import('@/features/command-center/IncidentResponsePage.vue') },
    { path: '/automation', name: 'automation', component: () => import('@/features/command-center/AutomationPage.vue') },
    { path: '/aiops', name: 'aiops', component: () => import('@/features/command-center/AIDiagnosisPage.vue') },
    { path: '/tickets', name: 'tickets', component: () => import('@/features/monitoring-event/TicketPage.vue') },
    { path: '/knowledge', name: 'knowledge', component: () => import('@/features/asset-config/KnowledgePage.vue') },
    { path: '/audit', name: 'audit', component: () => import('@/features/platform-admin/AuditLogPage.vue') },
    { path: '/admin/users', name: 'admin-users', component: () => import('@/features/platform-admin/UserManagementPage.vue') },
    { path: '/:pathMatch(.*)*', name: 'not-found', component: () => import('@/features/command-center/CommandCenterPage.vue') },
  ],
})

setupAuthGuard(router)

export default router
