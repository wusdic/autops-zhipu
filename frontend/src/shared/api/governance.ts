import client from './client'
import { API } from './routes'

export const governanceService = {
  listUsers: (params?: Record<string, any>) => client.get(API.GOVERNANCE.USERS, { params }),
  getUser: (id: string) => client.get(API.GOVERNANCE.USER_DETAIL(id)),
  createUser: (data: Record<string, any>) => client.post(API.GOVERNANCE.USERS, data),
  updateUser: (id: string, data: Record<string, any>) => client.put(API.GOVERNANCE.USER_DETAIL(id), data),
  deleteUser: (id: string) => client.delete(API.GOVERNANCE.USER_DETAIL(id)),
  listRoles: (params?: Record<string, any>) => client.get(API.GOVERNANCE.ROLES, { params }),
  listApiKeys: (params?: Record<string, any>) => client.get(API.GOVERNANCE.API_KEYS, { params }),
  createApiKey: (data: Record<string, any>) => client.post(API.GOVERNANCE.API_KEYS, data),
  revokeApiKey: (id: string) => client.delete(API.GOVERNANCE.API_KEY_DETAIL(id)),
  getPlatformStatus: () => client.get(API.PLATFORM_STATUS),
}
