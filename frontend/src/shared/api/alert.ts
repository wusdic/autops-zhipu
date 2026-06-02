import client from './client'
import { API } from './routes'

export const alertService = {
  list: (params?: Record<string, any>) => client.get(API.ALERTS, { params }),
  get: (id: string) => client.get(API.ALERT_DETAIL(id)),
  acknowledge: (id: string) => client.post(API.ALERT_ACKNOWLEDGE(id)),
  escalate: (id: string, data?: Record<string, any>) => client.post(API.ALERT_ESCALATE(id), data),
  resolve: (id: string, data?: Record<string, any>) => client.post(API.ALERT_RESOLVE(id), data),
  stats: () => client.get(API.ALERT_STATS),
  listRules: (params?: Record<string, any>) => client.get(API.ALERT_RULES, { params }),
  getRule: (id: string) => client.get(API.ALERT_RULE_DETAIL(id)),
  createRule: (data: Record<string, any>) => client.post(API.ALERT_RULES, data),
  updateRule: (id: string, data: Record<string, any>) => client.put(API.ALERT_RULE_DETAIL(id), data),
  deleteRule: (id: string) => client.delete(API.ALERT_RULE_DETAIL(id)),
  testRule: (id: string) => client.post(API.ALERT_RULE_TEST(id)),
}
