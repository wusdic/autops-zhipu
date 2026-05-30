/**
 * AUTOPS 后端 API 路由常量
 * 所有前端页面必须使用此文件中的常量，禁止硬编码 /api/v1/xxx 路径
 *
 * 约束来源：docs/03-api/API_CONTRACT.md + docs/01-architecture/FRONTEND_ARCHITECTURE.md
 */
export const API = {
  AUTH: {
    LOGIN: '/api/v1/auth/login',
    LOGOUT: '/api/v1/auth/logout',
    ME: '/api/v1/auth/me',
    REFRESH: '/api/v1/auth/refresh',
    PASSWORD: '/api/v1/auth/password',
  },
  ASSETS: '/api/v1/assets',
  ASSET_DETAIL: (id: string) => `/api/v1/assets/${id}`,
  ASSET_GROUPS: '/api/v1/asset-groups',
  ALERTS: '/api/v1/alerts',
  ALERT_DETAIL: (id: string) => `/api/v1/alerts/${id}`,
  ALERT_ACKNOWLEDGE: (id: string) => `/api/v1/alerts/${id}/acknowledge`,
  ALERT_RESOLVE: (id: string) => `/api/v1/alerts/${id}/resolve`,
  ALERT_RULES: '/api/v1/alert-rules',
  EVENTS: '/api/v1/events',
  TICKETS: '/api/v1/tickets',
  TICKET_DETAIL: (id: string) => `/api/v1/tickets/${id}`,
  POLICIES: '/api/v1/policies',
  POLICY_DETAIL: (id: string) => `/api/v1/policies/${id}`,
  SCRIPTS: '/api/v1/scripts',
  SCRIPT_DETAIL: (id: string) => `/api/v1/scripts/${id}`,
  PLAYBOOKS: '/api/v1/playbooks',
  EXECUTIONS: '/api/v1/executions',
  EXECUTION_DETAIL: (id: string) => `/api/v1/executions/${id}`,
  COLLECTORS: '/api/v1/collectors',
  COLLECTION_JOBS: '/api/v1/collection-jobs',
  CONFIGS: '/api/v1/configs/definitions',
  CONFIG_VERSIONS: (defId: string) => `/api/v1/configs/definitions/${defId}/versions`,
  CONFIG_PUBLISH: (versionId: string) => `/api/v1/configs/versions/${versionId}/publish`,
  CREDENTIALS: '/api/v1/credentials',
  CREDENTIAL_TEST: (id: string) => `/api/v1/credentials/${id}/test`,
  KNOWLEDGE: '/api/v1/knowledge',
  AIOPS: {
    HEALTH: '/api/v1/aiops/health',
    DIAGNOSE: '/api/v1/aiops/diagnose',
    ANALYSES: '/api/v1/aiops/analyses',
    ANALYSIS_DETAIL: (id: string) => `/api/v1/aiops/analyses/${id}`,
    FEEDBACK: (id: string) => `/api/v1/aiops/analyses/${id}/feedback`,
  },
  STATES: {
    SNAPSHOTS: '/api/v1/states/snapshots',
    LATEST: (assetId: string) => `/api/v1/states/latest/${assetId}`,
    CHANGES: (assetId: string) => `/api/v1/states/changes/${assetId}`,
  },
  LOGS: {
    EXECUTION: (execId: string) => `/api/v1/logs/execution/${execId}`,
  },
  AUDIT: '/api/v1/audit-logs',
  GOVERNANCE: {
    USERS: '/api/v1/users',
    ROLES: '/api/v1/roles',
  },
} as const
