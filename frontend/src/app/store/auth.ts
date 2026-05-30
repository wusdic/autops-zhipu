import { defineStore } from 'pinia'
import { ref } from 'vue'

interface User {
  id: string
  username: string
  display_name: string
  roles: string[]
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref<User | null>(null)
  const isAuthenticated = ref(!!token.value)

  function setToken(newToken: string) {
    token.value = newToken
    isAuthenticated.value = true
    localStorage.setItem('token', newToken)
  }

  function clearAuth() {
    token.value = ''
    user.value = null
    isAuthenticated.value = false
    localStorage.removeItem('token')
  }

  return { token, user, isAuthenticated, setToken, clearAuth }
})
