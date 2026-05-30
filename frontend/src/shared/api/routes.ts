/**
 * AUTOPS 后端 API 路由常量
 * 所有前端页面必须使用此文件中的常量，禁止硬编码 /api/v1/xxx 路径
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
  ASSET_GROUPS: '/api/v1/asset-groups',
  ALERTS: '/api/v1/alerts',
  ALERT_RULES: '/api/v1/alert-rules',
  EVENTS: '/api/v1/events',
  TICKETS: '/api/v1/tickets',
  POLICIES: '/api/v1/policies',
  SCRIPTS: '/api/v1/scripts',
  PLAYBOOKS: '/api/v1/playbooks',
  EXECUTIONS: '/api/v1/executions',
  COLLECTORS: '/api/v1/collectors',
  COLLECTION_JOBS: '/api/v1/collection-jobs',
  CONFIGS: '/api/v1/configs/definitions',
  CREDENTIALS: '/api/v1/credentials',
  KNOWLEDGE: '/api/v1/knowledge',
  AIOPS: {
    HEALTH: '/api/v1/aiops/health',
    DIAGNOSE: '/api/v1/aiops/diagnose',
    ANALYSES: '/api/v1/aiops/analyses',
  },
  STATES: {
    SNAPSHOTS: '/api/v1/states/snapshots',
    LATEST: (assetId: string) => `/api/v1/states/latest/${assetId}`,
    CHANGES: (assetId: string) => `/api/v1/states/changes/${assetId}`,
  },
  LOGS: {
    EXECUTION: (execId: string) => `/api/v1/logs/execution/${execId}`,
  },
} as const
