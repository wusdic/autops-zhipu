import { ref } from 'vue'

export function useLoading(initial = false) {
  const loading = ref(initial)

  async function wrap<T>(fn: () => Promise<T>): Promise<T> {
    loading.value = true
    try { return await fn() } finally { loading.value = false }
  }

  function start() { loading.value = true }
  function stop() { loading.value = false }

  return { loading, wrap, start, stop }
}
