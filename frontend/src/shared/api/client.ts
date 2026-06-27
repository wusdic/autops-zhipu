import axios from 'axios'
import { APP_CONFIG } from '@/shared/config'
import router from '@/app/router'

const apiClient = axios.create({
  baseURL: APP_CONFIG.API_BASE_URL,
  timeout: APP_CONFIG.API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截：注入 Token
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem(APP_CONFIG.TOKEN_KEY)
  if (token) {
    config.headers.Authorization = 'Bearer ' + token
  }
  return config
})

// ── refresh token 单飞（并发刷新只发一次请求）──
let _refreshing: Promise<string | null> | null = null

async function _doRefresh(): Promise<string | null> {
  const refreshToken = localStorage.getItem(APP_CONFIG.REFRESH_TOKEN_KEY)
  if (!refreshToken) return null
  try {
    // 用裸 axios 避免触发本拦截器递归
    const resp = await axios.post(
      APP_CONFIG.API_BASE_URL + '/api/v1/auth/refresh',
      { refresh_token: refreshToken },
      { headers: { 'Content-Type': 'application/json' } },
    )
    const d = resp.data?.data || resp.data
    const newAccess = d?.access_token
    if (newAccess) {
      localStorage.setItem(APP_CONFIG.TOKEN_KEY, newAccess)
      if (d.refresh_token) {
        localStorage.setItem(APP_CONFIG.REFRESH_TOKEN_KEY, d.refresh_token)
      }
      return newAccess
    }
  } catch {
    // 刷新失败 → 走登出流程
  }
  return null
}

function _redirectUnauthenticated(hadToken: boolean) {
  localStorage.removeItem(APP_CONFIG.TOKEN_KEY)
  localStorage.removeItem(APP_CONFIG.REFRESH_TOKEN_KEY)
  const current = router.currentRoute.value
  const publicNames = ['login', 'session-expired', 'forbidden']
  if (!publicNames.includes(current.name as string)) {
    router.push({ name: hadToken ? 'session-expired' : 'login' }).catch(() => {})
  }
}

// 响应拦截：统一错误处理
apiClient.interceptors.response.use(
  (response) => {
    const data = response.data
    if (data.code !== undefined && data.code !== 0) {
      // 业务错误：保留原始响应结构，让调用方能取到 response.data（含 code/message）
      const bizError: any = new Error(data.message || '请求失败')
      bizError.response = response
      bizError.code = data.code
      return Promise.reject(bizError)
    }
    return response
  },
  async (error) => {
    const status = error.response?.status
    const original = error.config || {}
    const isRefreshCall = (original.url || '').includes('/auth/refresh')

    if (status === 401 && !original._retry && !isRefreshCall) {
      const hadToken = !!localStorage.getItem(APP_CONFIG.TOKEN_KEY)
      const hasRefresh = !!localStorage.getItem(APP_CONFIG.REFRESH_TOKEN_KEY)
      if (hasRefresh) {
        original._retry = true
        // 单飞：并发 401 共用同一次刷新
        _refreshing = _refreshing || _doRefresh()
        const newToken = await _refreshing
        _refreshing = null
        if (newToken) {
          original.headers = original.headers || {}
          original.headers.Authorization = 'Bearer ' + newToken
          return apiClient(original)
        }
      }
      // 无 refresh token 或刷新失败 → 跳转
      _redirectUnauthenticated(hadToken)
    }
    // 保留原始 axios error（含 response/status），调用方可访问 error.response?.data?.message
    const message = error.response?.data?.message || error.message || '网络错误'
    error.message = message
    return Promise.reject(error)
  }
)

export default apiClient
