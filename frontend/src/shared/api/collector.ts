import client from './client'
import { API } from './routes'

export const collectorService = {
  list: (params?: Record<string, any>) => client.get(API.COLLECTORS, { params }),
  create: (data: Record<string, any>) => client.post(API.COLLECTORS, data),
  trigger: (id: string) => client.post(API.COLLECTORS + '/' + id + '/trigger'),
  getResults: (params?: Record<string, any>) => client.get(API.COLLECTION_JOBS, { params }),
  getResult: (jobId: string) => client.get(API.COLLECTION_JOB_RESULTS(jobId)),
  healthOverview: () => client.get(API.MONITORING.COLLECTOR_HEALTH),
  listEdge: (params?: Record<string, any>) => client.get(API.COLLECTOR_EDGE, { params }),
  getEdge: (id: string) => client.get(API.COLLECTOR_EDGE_DETAIL(id)),
  registerEdge: (data: Record<string, any>) => client.post(API.EDGE_REGISTER, data),
  edgeHeartbeat: (id: string) => client.post(API.EDGE_HEARTBEAT, { id }),
  edgeStatus: (id: string) => client.get(API.EDGE_STATUS(id)),
  edgeTasks: (id: string) => client.get(API.EDGE_TASKS(id)),
}
