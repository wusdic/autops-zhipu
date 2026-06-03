import client from './client'
import { API } from './routes'

export const notificationRuleService = {
  list: (params?: Record<string, any>) => client.get(API.NOTIFICATION_RULES, { params }),
  get: (id: string) => client.get(API.NOTIFICATION_RULE_DETAIL(id)),
  create: (data: Record<string, any>) => client.post(API.NOTIFICATION_RULES, data),
  update: (id: string, data: Record<string, any>) => client.put(API.NOTIFICATION_RULE_DETAIL(id), data),
  delete: (id: string) => client.delete(API.NOTIFICATION_RULE_DETAIL(id)),
  toggle: (id: string) => client.post(API.NOTIFICATION_RULE_TOGGLE(id)),
}
