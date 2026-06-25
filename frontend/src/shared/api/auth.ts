import client from './client'
import { API } from './routes'

export const authService = {
  login: (data: { username: string; password: string }) => client.post(API.AUTH.LOGIN, data),
  logout: () => client.post(API.AUTH.LOGOUT),
  me: () => client.get(API.AUTH.ME),
  refresh: (refreshToken: string) => client.post(API.AUTH.REFRESH, { refresh_token: refreshToken }),
  changePassword: (data: { old_password: string; new_password: string }) => client.put(API.AUTH.PASSWORD, data),
}
