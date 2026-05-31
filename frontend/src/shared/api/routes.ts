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

  // 资产
  ASSETS: '/api/v1/assets',
  ASSET_DETAIL: (id: string) => `/api/v1/assets/${id}`,
  ASSET_IMPORT: '/api/v1/assets/import',
  ASSET_RELATIONS: (id: string) => `/api/v1/assets/${id}/relations`,
  ASSET_TIMELINE: (id: string) => `/api/v1/assets/${id}/timeline`,

  // 资产分组
  ASSET_GROUPS: '/api/v1/asset-groups',
  ASSET_GROUP_DETAIL: (id: string) => `/api/v1/asset-groups/${id}`,
  ASSET_GROUP_MEMBERS: (groupId: string) => `/api/v1/asset-groups/${groupId}/members`,
  ASSET_GROUP_MEMBER: (groupId: string, assetId: string) => `/api/v1/asset-groups/${groupId}/members/${assetId}`,

  // 告警
  ALERTS: '/api/v1/alerts',
  ALERT_DETAIL: (id: string) => `/api/v1/alerts/${id}`,
  ALERT_ACKNOWLEDGE: (id: string) => `/api/v1/alerts/${id}/acknowledge`,
  ALERT_RESOLVE: (id: string) => `/api/v1/alerts/${id}/resolve`,
  ALERT_STATS: '/api/v1/alerts/stats/overview',
  ALERT_RULES: '/api/v1/alert-rules',

  // 事件
  EVENTS: '/api/v1/events',
  EVENT_DETAIL: (id: string) => `/api/v1/events/${id}`,

  // 工单
  TICKETS: '/api/v1/tickets',
  TICKET_DETAIL: (id: string) => `/api/v1/tickets/${id}`,
  TICKET_COMMENTS: (id: string) => `/api/v1/tickets/${id}/comments`,

  // 策略
  POLICIES: '/api/v1/policies',
  POLICY_DETAIL: (id: string) => `/api/v1/policies/${id}`,
  POLICY_SIMULATE: (id: string) => `/api/v1/policies/${id}/simulate`,

  // 脚本
  SCRIPTS: '/api/v1/scripts',

  // Playbook
  PLAYBOOKS: '/api/v1/playbooks',

  // 执行
  EXECUTIONS: '/api/v1/executions',
  EXECUTION_DETAIL: (id: string) => `/api/v1/executions/${id}`,
  EXECUTION_APPROVE: (id: string) => `/api/v1/executions/${id}/approve`,

  // 采集器
  COLLECTORS: '/api/v1/collectors',
  COLLECTION_JOBS: '/api/v1/collection-jobs',
  COLLECTION_JOB_RESULTS: (id: string) => `/api/v1/collection-jobs/${id}/results`,

  // 配置
  CONFIGS: '/api/v1/configs/definitions',
  CONFIG_DETAIL: (id: string) => `/api/v1/configs/definitions/${id}`,
  CONFIG_VERSIONS: (defId: string) => `/api/v1/configs/definitions/${defId}/versions`,
  CONFIG_PUBLISH: (versionId: string) => `/api/v1/configs/versions/${versionId}/publish`,

  // 凭证
  CREDENTIALS: '/api/v1/credentials',
  CREDENTIAL_DETAIL: (id: string) => `/api/v1/credentials/${id}`,
  CREDENTIAL_BIND: (id: string) => `/api/v1/credentials/${id}/bind`,

  // 知识库
  KNOWLEDGE: '/api/v1/knowledge',
  KNOWLEDGE_DETAIL: (id: string) => `/api/v1/knowledge/${id}`,
  KNOWLEDGE_PUBLISH: (id: string) => `/api/v1/knowledge/${id}/publish`,

  // AIops
  AIOPS: {
    HEALTH: '/api/v1/aiops/health',
    DIAGNOSE: '/api/v1/aiops/diagnose',
    ANALYSES: '/api/v1/aiops/analyses',
    ANALYSIS_DETAIL: (id: string) => `/api/v1/aiops/analyses/${id}`,
    FEEDBACK: (id: string) => `/api/v1/aiops/analyses/${id}/feedback`,
  },

  // 状态
  STATES: {
    SNAPSHOTS: '/api/v1/states/snapshots',
    LATEST: (assetId: string) => `/api/v1/states/latest/${assetId}`,
    CHANGES: (assetId: string) => `/api/v1/states/changes/${assetId}`,
    ALL_CHANGES: '/api/v1/states/changes',
  },

  // 日志
  LOGS: {
    EXECUTION: (execId: string) => `/api/v1/logs/execution/${execId}`,
  },

  // 审计
  AUDIT: '/api/v1/audit-logs',

  // 平台治理
  GOVERNANCE: {
    USERS: '/api/v1/users',
    USER_DETAIL: (id: string) => `/api/v1/users/${id}`,
    ROLES: '/api/v1/roles',
    API_KEYS: '/api/v1/api-keys',
    API_KEY_DETAIL: (id: string) => `/api/v1/api-keys/${id}`,
  },

  // 平台
  PLATFORM_STATUS: '/api/v1/platform/status',
} as const
