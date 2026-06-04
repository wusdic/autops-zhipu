import axios from 'axios'
import { APP_CONFIG } from '@/shared/config'
import router from '@/app/router'

const apiClient = axios.create({
  baseURL: '',
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
      return Promise.reject(new Error(data.message || '请求失败'))
    }
    return response
  },
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem(APP_CONFIG.TOKEN_KEY)
      router.push({ name: 'login' })
    }
    const message = error.response?.data?.message || error.message || '网络错误'
    return Promise.reject(new Error(message))
  }
)

export default apiClient
