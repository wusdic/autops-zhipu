/**
 * AUTOPS 前端运行时配置
 * 所有环境相关的常量统一在此定义
 */
export const APP_CONFIG = {
  /** localStorage 中存储 auth token 的 key */
  TOKEN_KEY: 'autops_token',
  /** localStorage 中存储用户名的 key */
  USERNAME_KEY: 'username',
  /** API 请求超时（毫秒） */
  API_TIMEOUT: 30000,
  /** WebSocket 地址（自动从当前页面协议推导） */
  WS_URL: `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws`,
  /** 默认分页大小 */
  DEFAULT_PAGE_SIZE: 20,
} as const
