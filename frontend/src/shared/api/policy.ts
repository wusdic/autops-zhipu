import client from './client'
import { API } from './routes'

export const policyService = {
  list: (params?: Record<string, any>) => client.get(API.POLICIES, { params }),
  get: (id: string) => client.get(API.POLICY_DETAIL(id)),
  create: (data: Record<string, any>) => client.post(API.POLICIES, data),
  update: (id: string, data: Record<string, any>) => client.put(API.POLICY_DETAIL(id), data),
  delete: (id: string) => client.delete(API.POLICY_DETAIL(id)),
  simulate: (id: string, data?: Record<string, any>) => client.post(API.POLICY_SIMULATE(id), data),
}
