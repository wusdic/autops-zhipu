import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  const sidebarCollapsed = ref(false)
  const globalSearchVisible = ref(false)
  const notificationCenterVisible = ref(false)
  const theme = ref<'light' | 'dark'>('light')
  const breadcrumb = ref<{ title: string; path?: string }[]>([])

  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  function showGlobalSearch() {
    globalSearchVisible.value = true
  }

  function hideGlobalSearch() {
    globalSearchVisible.value = false
  }

  function showNotificationCenter() {
    notificationCenterVisible.value = true
  }

  function hideNotificationCenter() {
    notificationCenterVisible.value = false
  }

  function toggleTheme() {
    theme.value = theme.value === 'light' ? 'dark' : 'light'
    document.documentElement.classList.toggle('dark', theme.value === 'dark')
  }

  function setBreadcrumb(items: { title: string; path?: string }[]) {
    breadcrumb.value = items
  }

  return {
    sidebarCollapsed, globalSearchVisible, notificationCenterVisible, theme, breadcrumb,
    toggleSidebar, showGlobalSearch, hideGlobalSearch, showNotificationCenter, hideNotificationCenter,
    toggleTheme, setBreadcrumb,
  }
})
