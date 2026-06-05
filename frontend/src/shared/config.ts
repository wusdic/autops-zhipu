/**
 * AUTOPS 前端运行时配置
 * 所有环境相关的常量统一在此定义
 */
const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
const defaultWsUrl = wsProtocol + '//' + window.location.host + '/api/v1/ws'

export const APP_CONFIG = {
  /** localStorage 中存储 auth token 的 key */
  TOKEN_KEY: 'autops_token',
  /** localStorage 中存储用户名的 key */
  USERNAME_KEY: 'username',
  /** API 基础路径（空字符串表示同域，走 Nginx 反代） */
  API_BASE_URL: import.meta.env.VITE_API_BASE_URL || '',
  /** API 请求超时（毫秒） */
  API_TIMEOUT: Number(import.meta.env.VITE_API_TIMEOUT || 30000),
  /** WebSocket 地址（自动从当前页面协议推导，走同域 Nginx 反代） */
  WS_URL: import.meta.env.VITE_WS_URL || defaultWsUrl,
  /** 默认分页大小 */
  DEFAULT_PAGE_SIZE: Number(import.meta.env.VITE_DEFAULT_PAGE_SIZE || 20),
} as const

/**
 * 全局主题色板 — 与 global.css CSS 变量保持同步
 * 仅用于 JS/TS 上下文（:color 属性、ECharts、Canvas 等）
 * CSS 中一律使用 var(--autops-*) 变量，禁止硬编码颜色值
 */
export const THEME_COLORS = {
  PRIMARY:        '#165dff',
  PRIMARY_DARK:   '#114bcc',
  PRIMARY_LIGHT:  '#e8f2ff',
  SUCCESS:        '#00b42a',
  SUCCESS_LIGHT:  '#e8ffea',
  WARNING:        '#ff7d00',
  WARNING_LIGHT:  '#fff7e8',
  DANGER:         '#f53f3f',
  DANGER_LIGHT:   '#ffece8',
  PURPLE:         '#722ed1',
  PURPLE_LIGHT:   '#f5e8ff',
  CYAN:           '#0fc6c2',
  GOLD:           '#faad14',
  GRAY:           '#86909c',
  TEXT_1:         '#1d2129',
  TEXT_2:         '#4e5969',
  TEXT_3:         '#86909c',
  TEXT_4:         '#c9cdd4',
  BG_1:           '#ffffff',
  BG_2:           '#f7f8fa',
  BG_3:           '#f2f3f5',
  BG_4:           '#e5e6eb',
  /** 按执行/任务状态映射的颜色 */
  STATUS: {
    running:   '#165dff',
    pending:   '#ff9a2e',
    completed: '#00b42a',
    success:   '#00b42a',
    failed:    '#f53f3f',
    error:     '#f53f3f',
    cancelled: '#86909c',
    warning:   '#ff7d00',
  } as Record<string, string>,
  /** 风险等级颜色 */
  RISK: {
    high:   '#f53f3f',
    medium: '#ff7d00',
    low:    '#00b42a',
  } as Record<string, string>,
} as const
