import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

export function useTableData<T = any>(
  fetchFn: (params: Record<string, any>) => Promise<{ data: { items: T[]; total: number } }>,
  options?: { immediate?: boolean; pageSize?: number }
) {
  const data = ref<T[]>([]) as any
  const loading = ref(false)
  const page = ref(1)
  const pageSize = ref(options?.pageSize || 20)
  const total = ref(0)
  const filters = ref<Record<string, any>>({})

  async function fetchData() {
    loading.value = true
    try {
      const res = await fetchFn({ page: page.value, page_size: pageSize.value, ...filters.value })
      data.value = res.data?.items || []
      total.value = res.data?.total || 0
    } catch (e: any) {
      ElMessage.error(e?.response?.data?.detail || '加载失败')
    } finally {
      loading.value = false
    }
  }

  function handlePageChange(p: number) { page.value = p; fetchData() }
  function handleSizeChange(s: number) { pageSize.value = s; page.value = 1; fetchData() }
  function handleSearch() { page.value = 1; fetchData() }
  function handleFilter(newFilters: Record<string, any>) { filters.value = { ...filters.value, ...newFilters }; page.value = 1; fetchData() }
  function resetFilters() { filters.value = {}; page.value = 1; fetchData() }
  function refresh() { fetchData() }

  if (options?.immediate !== false) { onMounted(fetchData) }

  return { data, loading, page, pageSize, total, filters, fetchData, handlePageChange, handleSizeChange, handleSearch, handleFilter, resetFilters, refresh }
}
