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

  function connect() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = protocol + '//' + window.location.host + path

    ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      connected.value = true
      error.value = null
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
      // Auto reconnect after 3 seconds
      reconnectTimer = setTimeout(connect, 3000)
    }

    ws.onerror = () => {
      error.value = 'WebSocket connection error'
    }
  }

  function disconnect() {
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
