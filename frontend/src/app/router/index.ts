import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/features/auth/LoginPage.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/',
    name: 'Layout',
    component: () => import('@/app/layout/MainLayout.vue'),
    redirect: '/command-center',
    children: [
      {
        path: 'command-center',
        name: 'CommandCenter',
        component: () => import('@/features/command-center/CommandCenterPage.vue'),
        meta: { title: '运维指挥台', icon: 'Monitor' },
      },
      {
        path: 'assets',
        name: 'AssetList',
        component: () => import('@/features/asset-config/AssetListPage.vue'),
        meta: { title: '资产列表', icon: 'Server' },
      },
      {
        path: 'alerts',
        name: 'AlertList',
        component: () => import('@/features/monitoring-event/AlertListPage.vue'),
        meta: { title: '告警列表', icon: 'Bell' },
      },
      {
        path: 'admin/users',
        name: 'UserManagement',
        component: () => import('@/features/platform-admin/UserManagementPage.vue'),
        meta: { title: '用户管理', icon: 'User' },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 权限守卫
router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('token')
  if (to.meta.requiresAuth !== false && !token) {
    next({ name: 'Login' })
  } else {
    next()
  }
})

export default router
