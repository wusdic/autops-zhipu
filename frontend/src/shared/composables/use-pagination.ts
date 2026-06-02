import { ref, computed } from 'vue'

export function usePagination(defaultPageSize = 20) {
  const page = ref(1)
  const pageSize = ref(defaultPageSize)
  const total = ref(0)

  const totalPages = computed(() => Math.ceil(total.value / pageSize.value) || 1)

  function setPage(p: number) { page.value = p }
  function setPageSize(s: number) { pageSize.value = s; page.value = 1 }
  function setTotal(t: number) { total.value = t }
  function reset() { page.value = 1; pageSize.value = defaultPageSize; total.value = 0 }

  return { page, pageSize, total, totalPages, setPage, setPageSize, setTotal, reset }
}
