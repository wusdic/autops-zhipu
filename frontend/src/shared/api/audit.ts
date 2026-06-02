import client from './client'
import { API } from './routes'

export const auditService = {
  listLogs: (params?: Record<string, any>) => client.get(API.AUDIT, { params }),
  export: (params?: Record<string, any>) => client.get(\`\${API.AUDIT}/export\`, { params, responseType: 'blob' }),
  getExecutionLog: (execId: string) => client.get(API.LOGS.EXECUTION(execId)),
  getStepLog: (execId: string, stepId: string) => client.get(API.LOGS.STEP(execId, stepId)),
  getEvidenceChain: (alertId: string) => client.get(API.ALERT_EVIDENCE_CHAIN(alertId)),
}
