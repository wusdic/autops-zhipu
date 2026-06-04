import client from './client'
import { API } from './routes'

export const platformService = {
  dictionaries: (params?: Record<string, any>) => client.get(API.PLATFORM.DICTIONARIES, { params }),
  dictionaryCreate: (data: Record<string, any>) => client.post(API.PLATFORM.DICTIONARIES, data),
  dictionaryUpdate: (id: string, data: Record<string, any>) => client.put('/api/v1/dictionaries/' + id, data),
  dictionaryDelete: (id: string) => client.delete('/api/v1/dictionaries/' + id),
  integrations: (params?: Record<string, any>) => client.get(API.PLATFORM.INTEGRATIONS, { params }),
  integrationTest: (name: string) => client.post(API.PLATFORM.INTEGRATION_TEST(name)),
  taskQueue: (params?: Record<string, any>) => client.get(API.PLATFORM.TASK_QUEUE, { params }),
  selfCheck: () => client.post(API.PLATFORM.SELF_CHECK),
  tenants: (params?: Record<string, any>) => client.get(API.PLATFORM.TENANTS, { params }),
  tenantCreate: (data: Record<string, any>) => client.post(API.PLATFORM.TENANTS, data),
  tenantUpdate: (id: string, data: Record<string, any>) => client.put(API.PLATFORM.TENANT_DETAIL(id), data),
}
