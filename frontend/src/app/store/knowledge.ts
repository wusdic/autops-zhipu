import { defineStore } from 'pinia'
import { ref } from 'vue'
import { knowledgeService } from '@/shared/api'

export const useKnowledgeStore = defineStore('knowledge', () => {
  const articles = ref<any[]>([])
  const total = ref(0)
  const currentArticle = ref<any | null>(null)
  const loading = ref(false)

  async function fetchList(params?: Record<string, any>) {
    loading.value = true
    try {
      const res = await knowledgeService.list(params)
      const payload = res.data?.data || {}
      articles.value = payload.items || []
      total.value = payload.total || 0
    } finally {
      loading.value = false
    }
  }

  async function fetchDetail(id: string) {
    const res = await knowledgeService.get(id)
    currentArticle.value = res.data?.data ?? null
    return currentArticle.value
  }

  async function create(data: Record<string, any>) {
    const res = await knowledgeService.create(data)
    await fetchList()
    return res.data?.data
  }

  async function update(id: string, data: Record<string, any>) {
    const res = await knowledgeService.update(id, data)
    await fetchList()
    return res.data?.data
  }

  async function remove(id: string) {
    await knowledgeService.delete(id)
    await fetchList()
  }

  async function publish(id: string) {
    await knowledgeService.publish(id)
    await fetchDetail(id)
  }

  return { articles, total, currentArticle, loading, fetchList, fetchDetail, create, update, remove, publish }
})
