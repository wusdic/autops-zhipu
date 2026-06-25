import { ref, onUnmounted } from 'vue'

interface WebSocketMessage {
  type: string
  data: any
}

export function useWebSocket(path: string = '/ws') {
  const connected = ref(false)
  const messages = ref<WebSocketMessage[]>([])
  const error = ref<string | null>(null)
  let ws: WebSocket | null = null
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null
  // 标记是否为主动关闭：避免 disconnect() 触发的 onclose 再次调度重连（幽灵重连）
  let manualClose = false
  let reconnectAttempts = 0
  const MAX_RECONNECT_ATTEMPTS = 10

  function connect() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = protocol + '//' + window.location.host + path

    manualClose = false
    ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      connected.value = true
      error.value = null
      reconnectAttempts = 0
    }

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        messages.value.push(msg)
        // Keep only last 100 messages
        if (messages.value.length > 100) {
          messages.value = messages.value.slice(-100)
        }
      } catch {
        messages.value.push({ type: 'raw', data: event.data })
      }
    }

    ws.onclose = () => {
      connected.value = false
      // 仅在非主动关闭且未超最大重试次数时自动重连
      if (!manualClose && reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
        reconnectAttempts += 1
        reconnectTimer = setTimeout(connect, 3000)
      }
    }

    ws.onerror = () => {
      error.value = 'WebSocket connection error'
    }
  }

  function disconnect() {
    manualClose = true
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    if (ws) {
      ws.close()
      ws = null
    }
  }

  function send(data: any) {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(typeof data === 'string' ? data : JSON.stringify(data))
    }
  }

  function clearMessages() {
    messages.value = []
  }

  onUnmounted(() => {
    disconnect()
  })

  return {
    connected,
    messages,
    error,
    connect,
    disconnect,
    send,
    clearMessages,
  }
}
