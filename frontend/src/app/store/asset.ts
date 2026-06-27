import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { assetService } from '@/shared/api'

export const useAssetStore = defineStore('asset', () => {
  const assets = ref<any[]>([])
  const total = ref(0)
  const currentAsset = ref<any | null>(null)
  const loading = ref(false)

  const assetById = computed(() => {
    const map = new Map<string, any>()
    assets.value.forEach(a => map.set(a.id, a))
    return map
  })

  async function fetchList(params?: Record<string, any>) {
    loading.value = true
    try {
      const res = await assetService.list(params)
      // 响应包裹为 {code,message,data:{items,total}}，须取 res.data.data
      const payload = res.data?.data || {}
      assets.value = payload.items || []
      total.value = payload.total || 0
    } finally {
      loading.value = false
    }
  }

  async function fetchDetail(id: string) {
    const res = await assetService.get(id)
    currentAsset.value = res.data?.data ?? null
    return currentAsset.value
  }

  async function create(data: Record<string, any>) {
    const res = await assetService.create(data)
    await fetchList()
    return res.data?.data
  }

  async function update(id: string, data: Record<string, any>) {
    const res = await assetService.update(id, data)
    await fetchList()
    return res.data?.data
  }

  async function remove(id: string) {
    await assetService.delete(id)
    await fetchList()
  }

  return { assets, total, currentAsset, loading, assetById, fetchList, fetchDetail, create, update, remove }
})
