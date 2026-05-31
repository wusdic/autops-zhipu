/**
 * WebSocket 实时推送服务
 * 支持自动重连、心跳检测、事件分发
 */

export interface WSMessage {
  type: string
  payload: any
  timestamp?: string
}

export type WSHandler = (msg: WSMessage) => void

class WebSocketService {
  private ws: WebSocket | null = null
  private url = ''
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null
  private handlers = new Map<string, Set<WSHandler>>()
  private globalHandlers = new Set<WSHandler>()
  private _connected = false
  private reconnectAttempts = 0
  private maxReconnectAttempts = 10
  private reconnectDelay = 3000
  private heartbeatInterval = 30000

  get connected() { return this._connected }

  /** 连接 WebSocket */
  connect(token?: string) {
    if (this.ws?.readyState === WebSocket.OPEN) return

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.hostname
    const port = import.meta.env.VITE_WS_PORT || import.meta.env.VITE_API_PORT || '8001'
    this.url = `${protocol}//${host}:${port}/api/v1/ws`

    if (token) this.url += `?token=${token}`

    try {
      this.ws = new WebSocket(this.url)

      this.ws.onopen = () => {
        this._connected = true
        this.reconnectAttempts = 0
        this.startHeartbeat()
        this.emit({ type: '_connected', payload: { url: this.url } })
      }

      this.ws.onmessage = (event) => {
        try {
          const msg: WSMessage = JSON.parse(event.data)
          if (msg.type === '_pong') return // heartbeat response
          this.emit(msg)
        } catch {
          // non-JSON message, ignore
        }
      }

      this.ws.onclose = () => {
        this._connected = false
        this.stopHeartbeat()
        this.emit({ type: '_disconnected', payload: {} })
        this.scheduleReconnect()
      }

      this.ws.onerror = () => {
        this._connected = false
      }
    } catch {
      this.scheduleReconnect()
    }
  }

  /** 断开连接 */
  disconnect() {
    this.stopHeartbeat()
    if (this.reconnectTimer) { clearTimeout(this.reconnectTimer); this.reconnectTimer = null }
    if (this.ws) { this.ws.close(); this.ws = null }
    this._connected = false
  }

  /** 订阅特定类型消息 */
  on(type: string, handler: WSHandler): () => void {
    if (!this.handlers.has(type)) this.handlers.set(type, new Set())
    this.handlers.get(type)!.add(handler)
    return () => this.handlers.get(type)?.delete(handler)
  }

  /** 订阅所有消息 */
  onAny(handler: WSHandler): () => void {
    this.globalHandlers.add(handler)
    return () => this.globalHandlers.delete(handler)
  }

  /** 发送消息 */
  send(type: string, payload: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, payload, timestamp: new Date().toISOString() }))
    }
  }

  private emit(msg: WSMessage) {
    // type-specific handlers
    const handlers = this.handlers.get(msg.type)
    if (handlers) handlers.forEach(h => h(msg))
    // global handlers
    this.globalHandlers.forEach(h => h(msg))
  }

  private startHeartbeat() {
    this.stopHeartbeat()
    this.heartbeatTimer = setInterval(() => {
      this.send('_ping', {})
    }, this.heartbeatInterval)
  }

  private stopHeartbeat() {
    if (this.heartbeatTimer) { clearInterval(this.heartbeatTimer); this.heartbeatTimer = null }
  }

  private scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) return
    if (this.reconnectTimer) return

    const delay = this.reconnectDelay * Math.min(this.reconnectAttempts + 1, 5)
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null
      this.reconnectAttempts++
      this.connect()
    }, delay)
  }
}

// Singleton
export const wsService = new WebSocketService()

/**
 * 预定义事件类型
 */
export const WSEvents = {
  ALERT_NEW: 'alert:new',
  ALERT_UPDATED: 'alert:updated',
  ALERT_ESCALATED: 'alert:escalated',
  EVENT_NEW: 'event:new',
  EXECUTION_STARTED: 'execution:started',
  EXECUTION_PROGRESS: 'execution:progress',
  EXECUTION_COMPLETED: 'execution:completed',
  EXECUTION_FAILED: 'execution:failed',
  EXECUTION_LOG: 'execution:log',
  TICKET_CREATED: 'ticket:created',
  TICKET_UPDATED: 'ticket:updated',
  POLICY_TRIGGERED: 'policy:triggered',
  ASSET_STATUS_CHANGED: 'asset:status_changed',
  COLLECTOR_STATUS: 'collector:status',
  AI_ANALYSIS_DONE: 'ai:analysis_done',
  NOTIFICATION: 'notification',
  APPROVAL_REQUEST: 'approval:request',
} as const
