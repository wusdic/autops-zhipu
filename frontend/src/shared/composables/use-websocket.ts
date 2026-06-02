import { ref, onUnmounted } from 'vue'

export function useWebSocket(url: string, options?: { onMessage?: (data: any) => void; onOpen?: () => void; onClose?: () => void }) {
  const connected = ref(false)
  const lastMessage = ref<any>(null)
  const messages = ref<any[]>([])
  let ws: WebSocket | null = null
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null

  function connect() {
    if (ws && ws.readyState === WebSocket.OPEN) return
    ws = new WebSocket(url)
    ws.onopen = () => { connected.value = true; options?.onOpen?.() }
    ws.onmessage = (event) => {
      const data = event.data.startsWith('{') ? JSON.parse(event.data) : event.data
      lastMessage.value = data
      messages.value.push(data)
      if (messages.value.length > 200) messages.value = messages.value.slice(-200)
      options?.onMessage?.(data)
    }
    ws.onclose = () => { connected.value = false; options?.onClose?.(); reconnectTimer = setTimeout(connect, 3000) }
    ws.onerror = () => { ws?.close() }
  }

  function send(data: any) {
    if (ws && ws.readyState === WebSocket.OPEN) ws.send(typeof data === 'string' ? data : JSON.stringify(data))
  }

  function disconnect() {
    if (reconnectTimer) clearTimeout(reconnectTimer)
    if (ws) { ws.close(); ws = null }
    connected.value = false
  }

  function clearMessages() { messages.value = [] }

  onUnmounted(disconnect)

  return { connected, lastMessage, messages, connect, send, disconnect, clearMessages }
}
