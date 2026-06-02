import { computed } from 'vue'
import { useAuthStore } from '@/app/store/auth'

export function usePermission() {
  const authStore = useAuthStore()

  const userRoles = computed(() => authStore.user?.roles || [])

  function hasRole(role: string | string[]): boolean {
    const roles = Array.isArray(role) ? role : [role]
    return roles.some(r => userRoles.value.includes(r))
  }

  function hasPermission(_permission: string): boolean {
    // TODO: implement fine-grained permission check when backend provides permission list
    return true
  }

  function isAdmin(): boolean {
    return hasRole('admin')
  }

  return { userRoles, hasRole, hasPermission, isAdmin }
}
