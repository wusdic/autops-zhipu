import { defineStore } from 'pinia'
import { ref } from 'vue'
import { automationService } from '@/shared/api'
import { APP_CONFIG } from '@/shared/config'

export const useExecutionStore = defineStore('execution', () => {
  const executions = ref<any[]>([])
  const currentExecution = ref<any | null>(null)
  const realtimeLogs = ref<string[]>([])
  const loading = ref(false)
  const wsConnection = ref<WebSocket | null>(null)

  async function fetchList(params?: Record<string, any>) {
    loading.value = true
    try {
      const res = await automationService.listExecutions(params)
      executions.value = res.data?.items || []
    } finally {
      loading.value = false
    }
  }

  async function fetchDetail(id: string) {
    const res = await automationService.getExecution(id)
    currentExecution.value = res.data
    return res.data
  }

  async function fetchLogs(id: string, params?: Record<string, any>) {
    const res = await automationService.getExecutionLogs(id, params)
    return res.data
  }

  function _formatLog(item: any): string {
    if (typeof item === 'string') return item
    const ts = item.created_at ? `${item.created_at} ` : ''
    const stream = item.stream_type ? `[${item.stream_type}] ` : ''
    return `${ts}${stream}${item.content ?? ''}`
  }

  // 统一走 /api/v1/ws（带 token）+ executions 频道，避免连接不存在的 /execution/{id}/logs。
  function connectLogs(executionId: string) {
    disconnectLogs()

    // 1. 先 REST 拉取已有日志（即便实时流为空也能展示）
    automationService
      .getExecutionLogs(executionId, { page: 1, page_size: 200 })
      .then((res) => {
        const items = res.data?.items || []
        for (const it of items) realtimeLogs.value.push(_formatLog(it))
      })
      .catch(() => { /* 日志非关键，忽略 */ })

    // 2. 订阅 executions 频道接收实时状态/日志
    const token = localStorage.getItem(APP_CONFIG.TOKEN_KEY) || ''
    const ws = new WebSocket(APP_CONFIG.WS_URL + '?token=' + encodeURIComponent(token))
    ws.onopen = () => {
      ws.send(JSON.stringify({ type: 'subscribe', payload: { channels: ['executions'] } }))
    }
    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        const p = msg.payload || {}
        // 仅保留当前执行的消息
        if (p.execution_id && p.execution_id !== executionId) return
        if (typeof msg.type === 'string' && msg.type.startsWith('execution:')) {
          const detail = p.status || p.result || p.error_message || ''
          realtimeLogs.value.push(`[${msg.type}] ${detail}`)
        }
      } catch {
        realtimeLogs.value.push(event.data)
      }
    }
    ws.onclose = () => { wsConnection.value = null }
    wsConnection.value = ws
  }

  function disconnectLogs() {
    if (wsConnection.value) {
      try {
        wsConnection.value.send(
          JSON.stringify({ type: 'unsubscribe', payload: { channels: ['executions'] } }),
        )
      } catch { /* 连接可能已关闭 */ }
      wsConnection.value.close()
      wsConnection.value = null
    }
    realtimeLogs.value = []
  }

  return { executions, currentExecution, realtimeLogs, loading, fetchList, fetchDetail, fetchLogs, connectLogs, disconnectLogs }
})
