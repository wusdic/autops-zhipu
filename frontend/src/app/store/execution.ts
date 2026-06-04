import { defineStore } from 'pinia'
import { ref } from 'vue'
import { automationService } from '@/shared/api'

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

  function connectLogs(executionId: string) {
    disconnectLogs()
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.hostname
    const ws = new WebSocket(protocol + '//' + host + ':8001/api/v1/ws/execution/' + executionId + '/logs')
    ws.onmessage = (event) => {
      realtimeLogs.value.push(event.data)
    }
    ws.onclose = () => { wsConnection.value = null }
    wsConnection.value = ws
  }

  function disconnectLogs() {
    if (wsConnection.value) {
      wsConnection.value.close()
      wsConnection.value = null
    }
    realtimeLogs.value = []
  }

  return { executions, currentExecution, realtimeLogs, loading, fetchList, fetchDetail, fetchLogs, connectLogs, disconnectLogs }
})
