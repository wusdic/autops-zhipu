import { defineStore } from 'pinia'
import { ref } from 'vue'
import { APP_CONFIG } from '@/shared/config'

interface User {
  id: string
  username: string
  display_name: string
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
  }

  return { token, user, isAuthenticated, setToken, clearAuth }
})
