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

/** 全局主题色板 — 所有页面必须从此处引用，禁止硬编码颜色值 */
export const THEME_COLORS = {
  PRIMARY:  '#165dff',
  SUCCESS:  '#00b42a',
  WARNING:  '#ff7d00',
  DANGER:   '#f53f3f',
  PURPLE:   '#722ed1',
  CYAN:     '#0fc6c2',
  GRAY:     '#86909c',
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
