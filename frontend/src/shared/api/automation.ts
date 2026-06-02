import client from './client'
import { API } from './routes'

export const automationService = {
  listScripts: (params?: Record<string, any>) => client.get(API.SCRIPTS, { params }),
  createScript: (data: Record<string, any>) => client.post(API.SCRIPTS, data),
  listPlaybooks: (params?: Record<string, any>) => client.get(API.PLAYBOOKS, { params }),
  createPlaybook: (data: Record<string, any>) => client.post(API.PLAYBOOKS, data),
  listExecutions: (params?: Record<string, any>) => client.get(API.EXECUTIONS, { params }),
  getExecution: (id: string) => client.get(API.EXECUTION_DETAIL(id)),
  triggerExecution: (data: Record<string, any>) => client.post(API.EXECUTIONS, data),
  cancelExecution: (id: string) => client.post(API.EXECUTION_CANCEL(id)),
  rollback: (id: string) => client.post(API.EXECUTION_ROLLBACK(id)),
  getVerification: (id: string) => client.get(API.EXECUTION_VERIFICATION(id)),
  dryRun: (data: Record<string, any>) => client.post(API.AUTOMATION.DRY_RUN, data),
  getDryRunDetail: (id: string) => client.get(API.AUTOMATION.DRY_RUN_DETAIL(id)),
  listApprovals: (params?: Record<string, any>) => client.get(API.AUTOMATION.APPROVALS, { params }),
  approve: (id: string, data: { approved: boolean; comment?: string }) => client.post(API.AUTOMATION.APPROVAL_APPROVE(id), data),
  reject: (id: string, data: { comment?: string }) => client.post(API.AUTOMATION.APPROVAL_REJECT(id), data),
  overview: () => client.get(API.AUTOMATION.STATS),
}
