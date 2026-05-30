import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', name: 'login', component: () => import('@/features/auth/LoginPage.vue'), meta: { public: true } },
    { path: '/', component: () => import('@/app/layout/MainLayout.vue'), redirect: '/dashboard', children: [
      { path: 'dashboard', name: 'dashboard', component: () => import('@/features/command-center/CommandCenterPage.vue'), meta: { title: '运维指挥台' } },
      { path: 'assets', name: 'assets', component: () => import('@/features/asset-config/AssetListPage.vue'), meta: { title: '资产管理' } },
      { path: 'alerts', name: 'alerts', component: () => import('@/features/monitoring-event/AlertListPage.vue'), meta: { title: '告警中心' } },
      { path: 'tickets', name: 'tickets', component: () => import('@/features/monitoring-event/TicketPage.vue'), meta: { title: '工单中心' } },
      { path: 'knowledge', name: 'knowledge', component: () => import('@/features/asset-config/KnowledgePage.vue'), meta: { title: '知识库' } },
      { path: 'admin', name: 'admin', component: () => import('@/features/platform-admin/UserManagementPage.vue'), meta: { title: '平台管理' } },
    ]},
  ],
})

export default router
