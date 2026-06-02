import { defineStore } from 'pinia'
import { ref } from 'vue'
import { inspectionService } from '@/shared/api'

export const useInspectionStore = defineStore('inspection', () => {
  const templates = ref<any[]>([])
  const plans = ref<any[]>([])
  const tasks = ref<any[]>([])
  const results = ref<any[]>([])
  const overview = ref<Record<string, any>>({})
  const loading = ref(false)

  async function fetchTemplates(params?: Record<string, any>) {
    loading.value = true
    try {
      const res = await inspectionService.listTemplates(params)
      templates.value = res.data?.items || []
    } finally {
      loading.value = false
    }
  }

  async function fetchPlans(params?: Record<string, any>) {
    loading.value = true
    try {
      const res = await inspectionService.listPlans(params)
      plans.value = res.data?.items || []
    } finally {
      loading.value = false
    }
  }

  async function fetchTasks(params?: Record<string, any>) {
    loading.value = true
    try {
      const res = await inspectionService.listTasks(params)
      tasks.value = res.data?.items || []
    } finally {
      loading.value = false
    }
  }

  async function fetchResults(params?: Record<string, any>) {
    loading.value = true
    try {
      const res = await inspectionService.listResults(params)
      results.value = res.data?.items || []
    } finally {
      loading.value = false
    }
  }

  async function fetchOverview() {
    const res = await inspectionService.overview()
    overview.value = res.data || {}
  }

  return { templates, plans, tasks, results, overview, loading, fetchTemplates, fetchPlans, fetchTasks, fetchResults, fetchOverview }
})
