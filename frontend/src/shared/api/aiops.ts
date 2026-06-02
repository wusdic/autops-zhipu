import client from './client'
import { API } from './routes'

export const aiopsService = {
  health: () => client.get(API.AIOPS.HEALTH),
  diagnose: (data: Record<string, any>) => client.post(API.AIOPS.DIAGNOSE, data),
  listAnalyses: (params?: Record<string, any>) => client.get(API.AIOPS.ANALYSES, { params }),
  getAnalysis: (id: string) => client.get(API.AIOPS.ANALYSIS_DETAIL(id)),
  feedback: (id: string, data: Record<string, any>) => client.post(API.AIOPS.FEEDBACK(id), data),
  agentRun: (data: Record<string, any>) => client.post(API.AIOPS.AGENT_RUN, data),
  agentResults: (params?: Record<string, any>) => client.get(API.AIOPS.AGENT_RESULTS, { params }),
  agentApprove: (id: string, data: Record<string, any>) => client.post(API.AIOPS.AGENT_APPROVE(id), data),
}
