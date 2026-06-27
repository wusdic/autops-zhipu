import type { Router } from 'vue-router'
import { APP_CONFIG } from '@/shared/config'

const TOKEN_KEY = APP_CONFIG.TOKEN_KEY
const LOGIN_PATH = '/login'

// Routes that don't require authentication
// 含 session-expired / forbidden，否则 401 跳转后会被本守卫再次弹回 /login
const publicRoutes = ['/login', '/session-expired', '/forbidden']

// 管理员角色名
const ADMIN_ROLES = ['admin', 'super_admin']

function isAdmin(): boolean {
  try {
    const roles = JSON.parse(localStorage.getItem(APP_CONFIG.ROLES_KEY) || '[]')
    return Array.isArray(roles) && roles.some((r: string) => ADMIN_ROLES.includes(r))
  } catch {
    return false
  }
}

// 需要管理员的路由：平台管理(M12) 全部 + 审计查询。
// 仅为体验级拦截（后端 require_admin 仍是权威授权）。
function requiresAdmin(to: { meta?: Record<string, unknown>; path: string }): boolean {
  return to.meta?.module === 'M12' || to.path === '/audit'
}

export function setupAuthGuard(router: Router) {
  router.beforeEach((to, _from, next) => {
    const token = localStorage.getItem(TOKEN_KEY)

    // Public routes are always accessible
    if (publicRoutes.includes(to.path)) {
      // If already logged in, redirect to home
      if (token && to.path === LOGIN_PATH) {
        next('/')
        return
      }
      next()
      return
    }

    // Check authentication
    if (!token) {
      next({ path: LOGIN_PATH, query: { redirect: to.fullPath } })
      return
    }

    // 体验级权限拦截：管理员路由对非管理员跳转 /forbidden
    // （roles 缓存为空时放行，避免刷新瞬间误拦；后端仍会拒绝越权请求）
    if (requiresAdmin(to)) {
      const rolesRaw = localStorage.getItem(APP_CONFIG.ROLES_KEY)
      if (rolesRaw && !isAdmin()) {
        next('/forbidden')
        return
      }
    }

    next()
  })
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY)
}
