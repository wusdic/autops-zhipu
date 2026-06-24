import { defineStore } from 'pinia'
import { ref } from 'vue'
import { APP_CONFIG } from '@/shared/config'
import { authService } from '@/shared/api'

interface User {
  id: string
  username: string
  display_name: string
  email?: string | null
  status?: string
  roles: string[]
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem(APP_CONFIG.TOKEN_KEY) || '')
  const user = ref<User | null>(null)
  const isAuthenticated = ref(!!token.value)

  function setToken(newToken: string) {
    token.value = newToken
    isAuthenticated.value = true
    localStorage.setItem(APP_CONFIG.TOKEN_KEY, newToken)
  }

  function clearAuth() {
    token.value = ''
    user.value = null
    isAuthenticated.value = false
    localStorage.removeItem(APP_CONFIG.TOKEN_KEY)
    // 同时清理 username 缓存
    localStorage.removeItem(APP_CONFIG.USERNAME_KEY)
  }

  /** 从后端 /auth/me 拉取用户信息（页面刷新后恢复 user 状态） */
  async function fetchUser() {
    if (!token.value) return null
    try {
      const res = await authService.me()
      const data = res.data?.data || res.data
      if (data) {
        user.value = {
          id: data.id,
          username: data.username,
          display_name: data.display_name || data.username,
          email: data.email,
          status: data.status,
          // roles 可能不在 /auth/me 响应中，默认空数组
          roles: (data as any).roles || [],
        }
        isAuthenticated.value = true
        return user.value
      }
    } catch {
      // token 无效或过期 — 清理认证状态
      clearAuth()
    }
    return null
  }

  return { token, user, isAuthenticated, setToken, clearAuth, fetchUser }
})
