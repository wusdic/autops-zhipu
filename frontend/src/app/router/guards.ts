import type { Router } from 'vue-router'

const TOKEN_KEY = 'autops_token'
const LOGIN_PATH = '/login'

// Routes that don't require authentication
const publicRoutes = ['/login']

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
