import type { Router } from 'vue-router'
import { APP_CONFIG } from '@/shared/config'

const TOKEN_KEY = APP_CONFIG.TOKEN_KEY
const LOGIN_PATH = '/login'

// Routes that don't require authentication
// 含 session-expired / forbidden，否则 401 跳转后会被本守卫再次弹回 /login
const publicRoutes = ['/login', '/session-expired', '/forbidden']

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
