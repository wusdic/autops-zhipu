import client from './client'
import { API } from './routes'

export const anomalyService = {
  list: (params?: Record<string, any>) => client.get(API.ANOMALY.LIST, { params }),
  get: (id: string) => client.get(API.ANOMALY.DETAIL(id)),
  stats: () => client.get(API.ANOMALY.STATS),
  acknowledge: (id: string) => client.post(API.ANOMALY.ACKNOWLEDGE(id)),
  assign: (id: string, data: { assignee_id: string }) => client.post(API.ANOMALY.ASSIGN(id), data),
  close: (id: string, data?: Record<string, any>) => client.post(API.ANOMALY.CLOSE(id), data),
  escalate: (id: string, data?: Record<string, any>) => client.post(API.ANOMALY.ESCALATE(id), data),
  convertToTicket: (id: string) => client.post(API.ANOMALY.CONVERT_TICKET(id)),
  impactAnalysis: (id: string) => client.get(API.ANOMALY.IMPACT_ANALYSIS(id)),
}
