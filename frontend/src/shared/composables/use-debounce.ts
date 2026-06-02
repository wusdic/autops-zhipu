import { ref, onUnmounted } from 'vue'

export function useDebounce<T>(value: T, delay = 300) {
  let timer: ReturnType<typeof setTimeout> | null = null
  const debounced = ref(value) as any

  function set(val: T) {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => { debounced.value = val }, delay)
  }

  function cancel() { if (timer) clearTimeout(timer) }
  onUnmounted(cancel)

  return { debounced, set, cancel }
}

export function useDebounceFn(fn: (...args: any[]) => void, delay = 300) {
  let timer: ReturnType<typeof setTimeout> | null = null
  function debounced(...args: any[]) {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => fn(...args), delay)
  }
  function cancel() { if (timer) clearTimeout(timer) }
  onUnmounted(cancel)
  return { debounced, cancel }
}
