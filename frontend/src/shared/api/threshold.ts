import client from './client'
import { API } from './routes'

export const thresholdService = {
  list: (params?: Record<string, any>) => client.get(API.THRESHOLD_RULES, { params }),
  get: (id: string) => client.get(API.THRESHOLD_RULE_DETAIL(id)),
  create: (data: Record<string, any>) => client.post(API.THRESHOLD_RULES, data),
  update: (id: string, data: Record<string, any>) => client.put(API.THRESHOLD_RULE_DETAIL(id), data),
  delete: (id: string) => client.delete(API.THRESHOLD_RULE_DETAIL(id)),
  toggle: (id: string) => client.post(API.THRESHOLD_RULE_TOGGLE(id)),
}
