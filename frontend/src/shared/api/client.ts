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
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem(APP_CONFIG.TOKEN_KEY)
      router.push({ name: 'login' }).catch(() => {})
    }
    // 保留原始 axios error（含 response/status），调用方可访问 error.response?.data?.message
    const message = error.response?.data?.message || error.message || '网络错误'
    error.message = message
    return Promise.reject(error)
  }
)

export default apiClient
