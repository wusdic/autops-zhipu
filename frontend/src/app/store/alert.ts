import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { alertService } from '@/shared/api'

export const useAlertStore = defineStore('alert', () => {
  const alerts = ref<any[]>([])
  const total = ref(0)
  const stats = ref<Record<string, any>>({})
  const loading = ref(false)

  const unacknowledgedCount = computed(() =>
    alerts.value.filter(a => a.status === 'firing' || a.status === 'active').length
  )

  async function fetchList(params?: Record<string, any>) {
    loading.value = true
    try {
      const res = await alertService.list(params)
      alerts.value = res.data?.items || []
      total.value = res.data?.total || 0
    } finally {
      loading.value = false
    }
  }

  async function fetchStats() {
    const res = await alertService.stats()
    stats.value = res.data || {}
  }

  async function acknowledge(id: string) {
    await alertService.acknowledge(id)
    await fetchList()
  }

  async function resolve(id: string, data?: Record<string, any>) {
    await alertService.resolve(id, data)
    await fetchList()
  }

  async function escalate(id: string, data?: Record<string, any>) {
    await alertService.escalate(id, data)
    await fetchList()
  }

  return { alerts, total, stats, loading, unacknowledgedCount, fetchList, fetchStats, acknowledge, resolve, escalate }
})
