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
  ASSET_RELATION_DELETE: (assetId: string, relId: string) => `/api/v1/assets/${assetId}/relations/${relId}`,
  ASSET_TIMELINE: (id: string) => `/api/v1/assets/${id}/timeline`,
  ASSET_CREDENTIALS: (id: string) => `/api/v1/assets/${id}/credentials`,
  ASSET_CREDENTIAL_UNBIND: (assetId: string, credId: string) => `/api/v1/assets/${assetId}/credentials/${credId}`,
  ASSET_COLLECTION_CONFIGS: (id: string) => `/api/v1/assets/${id}/collection-configs`,
  ASSET_COLLECTION_TRIGGER: (id: string) => `/api/v1/assets/${id}/collection-trigger`,
  ASSET_POLICIES: (id: string) => `/api/v1/assets/${id}/policies`,
  ASSET_POLICY_UNBIND: (assetId: string, policyId: string) => `/api/v1/assets/${assetId}/policies/${policyId}`,

  // 资产发现
  DISCOVERY: '/api/v1/discovery',
  DISCOVERY_TASKS: '/api/v1/discovery/tasks',
  DISCOVERY_RESULTS: '/api/v1/discovery/results',

  // 备份恢复
  BACKUPS: '/api/v1/backups',
  BACKUP_DETAIL: (id: string) => `/api/v1/backups/${id}`,
  BACKUP_DOWNLOAD: (id: string) => `/api/v1/backups/${id}/download`,
  BACKUP_RESTORE: (id: string) => `/api/v1/backups/${id}/restore`,
  BACKUP_SETTINGS: '/api/v1/backups/settings',
  BACKUP_STORAGE: '/api/v1/backups/storage',

  // 资产分组
  ASSET_GROUPS: '/api/v1/asset-groups',
  ASSET_GROUP_DETAIL: (id: string) => `/api/v1/asset-groups/${id}`,
  ASSET_GROUP_MEMBERS: (groupId: string) => `/api/v1/asset-groups/${groupId}/members`,
  ASSET_GROUP_MEMBER: (groupId: string, assetId: string) => `/api/v1/asset-groups/${groupId}/members/${assetId}`,

  // 告警规则
  ALERT_RULES: '/api/v1/alert-rules',
  ALERT_RULE_DETAIL: (id: string) => `/api/v1/alert-rules/${id}`,
  ALERT_RULE_TEST: (id: string) => `/api/v1/alert-rules/${id}/test`,

  // 告警
  ALERTS: '/api/v1/alerts',
  ALERT_DETAIL: (id: string) => `/api/v1/alerts/${id}`,
  ALERT_ACKNOWLEDGE: (id: string) => `/api/v1/alerts/${id}/acknowledge`,
  ALERT_ESCALATE: (id: string) => `/api/v1/alerts/${id}/escalate`,
  ALERT_RESOLVE: (id: string) => `/api/v1/alerts/${id}/resolve`,
  ALERT_STATS: '/api/v1/alerts/stats/overview',

  // 事件
  EVENTS: '/api/v1/events',
  EVENT_DETAIL: (id: string) => `/api/v1/events/${id}`,

  // 工单
  TICKETS: '/api/v1/tickets',
  TICKET_DETAIL: (id: string) => `/api/v1/tickets/${id}`,
  TICKET_STATS: '/api/v1/tickets/stats/overview',
  TICKET_COMMENTS: (id: string) => `/api/v1/tickets/${id}/comments`,
  TICKET_ATTACHMENTS: (id: string) => `/api/v1/tickets/${id}/attachments`,
  TICKET_ATTACHMENT: (ticketId: string, attachmentId: string) => `/api/v1/tickets/${ticketId}/attachments/${attachmentId}`,

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
  EXECUTION_CANCEL: (id: string) => `/api/v1/executions/${id}/cancel`,
  EXECUTION_ROLLBACK: (id: string) => `/api/v1/executions/${id}/rollback`,
  EXECUTION_VERIFICATION: (id: string) => `/api/v1/executions/${id}/verification`,

  // 采集器
  COLLECTORS: '/api/v1/collectors',
  COLLECTOR_EDGE: '/api/v1/collectors/edge',
  COLLECTOR_EDGE_DETAIL: (id: string) => `/api/v1/collectors/edge/${id}`,
  COLLECTION_JOBS: '/api/v1/collection-jobs',
  COLLECTION_JOB_RESULTS: (id: string) => `/api/v1/collection-jobs/${id}/results`,

  // 配置
  CONFIGS: '/api/v1/configs/definitions',
  CONFIG_DETAIL: (id: string) => `/api/v1/configs/definitions/${id}`,
  CONFIG_VERSIONS: (defId: string) => `/api/v1/configs/definitions/${defId}/versions`,
  CONFIG_DIFF: (defId: string) => `/api/v1/configs/definitions/${defId}/diff`,
  CONFIG_DRIFT: (defId: string) => `/api/v1/configs/definitions/${defId}/drift`,
  CONFIG_ROLLBACK: (defId: string) => `/api/v1/configs/definitions/${defId}/rollback`,
  CONFIG_INHERITANCE: '/api/v1/configs/inheritance',
  CONFIG_PUBLISH: (versionId: string) => `/api/v1/configs/versions/${versionId}/publish`,

  // 凭证
  CREDENTIALS: '/api/v1/credentials',
  CREDENTIAL_DETAIL: (id: string) => `/api/v1/credentials/${id}`,
  CREDENTIAL_BIND: (id: string) => `/api/v1/credentials/${id}/bind`,

  // 知识库
  KNOWLEDGE: '/api/v1/knowledge',
  KNOWLEDGE_DETAIL: (id: string) => `/api/v1/knowledge/${id}`,
  KNOWLEDGE_PUBLISH: (id: string) => `/api/v1/knowledge/${id}/publish`,
  KNOWLEDGE_EXPORT: '/api/v1/knowledge/export',
  KNOWLEDGE_VIEW: (id: string) => `/api/v1/knowledge/${id}/view`,
  KNOWLEDGE_RELATED: (id: string) => `/api/v1/knowledge/${id}/related`,
  KNOWLEDGE_VERSIONS: (id: string) => `/api/v1/knowledge/${id}/versions`,
  KNOWLEDGE_FEEDBACK: (id: string) => `/api/v1/knowledge/${id}/feedback`,
  KNOWLEDGE_CONVERT_RUNBOOK: (id: string) => `/api/v1/knowledge/${id}/convert-runbook`,
  KNOWLEDGE_IMPORT_VALIDATE: '/api/v1/knowledge/import/validate',
  KNOWLEDGE_IMPORT_BATCH: '/api/v1/knowledge/import/batch',
  KNOWLEDGE_STATS: '/api/v1/knowledge/stats',

  // AIops
  AIOPS: {
    HEALTH: '/api/v1/aiops/health',
    DIAGNOSE: '/api/v1/aiops/diagnose',
    ANALYSES: '/api/v1/aiops/analyses',
    ANALYSIS_DETAIL: (id: string) => `/api/v1/aiops/analyses/${id}`,
    FEEDBACK: (id: string) => `/api/v1/aiops/analyses/${id}/feedback`,
    // Agent
    AGENT_RUN: '/api/v1/aiops/agent/run',
    AGENT_RESULTS: '/api/v1/aiops/agent/results',
    AGENT_APPROVE: (id: string) => `/api/v1/aiops/agent/${id}/approve`,
  },

  // 证据链
  ALERT_EVIDENCE_CHAIN: (id: string) => `/api/v1/alerts/${id}/evidence-chain`,

  // 工单转知识
  TICKET_CONVERT_KNOWLEDGE: (id: string) => `/api/v1/tickets/${id}/convert-knowledge`,

  // Edge Collector
  EDGE_REGISTER: '/api/v1/collectors/edge/register',
  EDGE_HEARTBEAT: '/api/v1/collectors/edge/heartbeat',
  EDGE_STATUS: (id: string) => `/api/v1/collectors/edge/${id}/status`,
  EDGE_TASKS: (id: string) => `/api/v1/collectors/edge/${id}/tasks`,

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
    STEP: (execId: string, stepId: string) => `/api/v1/logs/execution/${execId}/step/${stepId}`,
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

  // 通知渠道
  NOTIFICATION_CHANNELS: '/api/v1/notification-channels',
  NOTIFICATION_CHANNEL_DETAIL: (name: string) => `/api/v1/notification-channels/${name}`,
  NOTIFICATION_CHANNEL_TEST: (name: string) => `/api/v1/notification-channels/${name}/test`,

  // 平台
  PLATFORM_STATUS: '/api/v1/platform/status',

  // 通知
  NOTIFICATIONS: '/api/v1/notifications',
  NOTIFICATION_READ: (id: string) => `/api/v1/notifications/${id}/read`,
  NOTIFICATION_READ_ALL: '/api/v1/notifications/read-all',

  // ============================================================
  // V3 新增模块 API 常量
  // ============================================================

  // M1 首页指挥台
  DASHBOARD: {
    STATS: '/api/v1/dashboard/stats',
    ASSET_DISCOVERY_SUMMARY: '/api/v1/dashboard/asset-discovery',
    INSPECTION_SUMMARY: '/api/v1/dashboard/inspection',
    ANOMALY_SUMMARY: '/api/v1/dashboard/anomaly',
    AUTOMATION_SUMMARY: '/api/v1/dashboard/automation',
    REPORT_SUMMARY: '/api/v1/dashboard/report',
    PLATFORM_HEALTH: '/api/v1/dashboard/platform-health',
    MY_PENDING: '/api/v1/dashboard/my-pending',
  },

  // M2 资源中心
  BUSINESS_SYSTEMS: '/api/v1/business-systems',
  BUSINESS_SYSTEM_DETAIL: (id: string) => `/api/v1/business-systems/${id}`,
  AGENTS: '/api/v1/agents',
  AGENT_DETAIL: (id: string) => `/api/v1/agents/${id}`,
  RESOURCE_IMPORT: '/api/v1/resources/import',

  // M3 巡检中心
  INSPECTION: {
    TEMPLATES: '/api/v1/inspection/templates',
    TEMPLATE_DETAIL: (id: string) => `/api/v1/inspection/templates/${id}`,
    PLANS: '/api/v1/inspection/plans',
    PLAN_DETAIL: (id: string) => `/api/v1/inspection/plans/${id}`,
    TASKS: '/api/v1/inspection/tasks',
    TASK_DETAIL: (id: string) => `/api/v1/inspection/tasks/${id}`,
    RESULTS: '/api/v1/inspection/results',
    RESULT_DETAIL: (id: string) => `/api/v1/inspection/results/${id}`,
    REPORTS: '/api/v1/inspection/reports',
    REPORT_DETAIL: (id: string) => `/api/v1/inspection/reports/${id}`,
    PAGE_CHECKS: '/api/v1/inspection/page-checks',
    CONFIG_CHECKS: '/api/v1/inspection/config-checks',
    LOG_CHECKS: '/api/v1/inspection/log-checks',
    BASELINE_CHECKS: '/api/v1/inspection/baseline-checks',
    STATS: '/api/v1/inspection/stats',
  },

  // M4 监控中心
  MONITORING: {
    COLLECTION_RESULTS: '/api/v1/collection-results',
    METRICS_TREND: (assetId: string) => `/api/v1/metrics/trend/${assetId}`,
    STATE_SNAPSHOTS: '/api/v1/states/snapshots',
    LOG_SOURCES: '/api/v1/log-sources',
    COLLECTOR_HEALTH: '/api/v1/collectors/health',
  },

  // M5 处置中心
  ANOMALY: {
    LIST: '/api/v1/anomalies',
    DETAIL: (id: string) => `/api/v1/anomalies/${id}`,
    STATS: '/api/v1/anomalies/stats',
    ACKNOWLEDGE: (id: string) => `/api/v1/anomalies/${id}/acknowledge`,
    ASSIGN: (id: string) => `/api/v1/anomalies/${id}/assign`,
    CLOSE: (id: string) => `/api/v1/anomalies/${id}/close`,
    ESCALATE: (id: string) => `/api/v1/anomalies/${id}/escalate`,
    CONVERT_TICKET: (id: string) => `/api/v1/anomalies/${id}/convert-ticket`,
    IMPACT_ANALYSIS: (id: string) => `/api/v1/anomalies/${id}/impact-analysis`,
  },

  // M6 自动化中心
  AUTOMATION: {
    STATS: '/api/v1/automation/stats',
    APPROVALS: '/api/v1/approvals',
    APPROVAL_DETAIL: (id: string) => `/api/v1/approvals/${id}`,
    APPROVAL_APPROVE: (id: string) => `/api/v1/approvals/${id}/approve`,
    APPROVAL_REJECT: (id: string) => `/api/v1/approvals/${id}/reject`,
    DRY_RUN: '/api/v1/dry-run',
    DRY_RUN_DETAIL: (id: string) => `/api/v1/dry-run/${id}`,
  },

  // M9 报表审计中心
  REPORT: {
    TEMPLATES: '/api/v1/report/templates',
    TEMPLATE_DETAIL: (id: string) => `/api/v1/report/templates/${id}`,
    GENERATE: '/api/v1/report/generate',
    TASKS: '/api/v1/report/tasks',
    TASK_DETAIL: (id: string) => `/api/v1/report/tasks/${id}`,
    PREVIEW: (id: string) => `/api/v1/report/tasks/${id}/preview`,
    DOWNLOAD: (id: string) => `/api/v1/report/tasks/${id}/download`,
    ARCHIVE: '/api/v1/report/archive',
    ARCHIVE_DETAIL: (id: string) => `/api/v1/report/archive/${id}`,
    STATS: '/api/v1/report/stats',
  },

  // M10 平台管理
  PLATFORM: {
    DICTIONARIES: '/api/v1/dictionaries',
    INTEGRATIONS: '/api/v1/integrations',
    INTEGRATION_TEST: (name: string) => `/api/v1/integrations/${name}/test`,
    TASK_QUEUE: '/api/v1/task-queue',
    SELF_CHECK: '/api/v1/platform/self-check',
    TENANTS: '/api/v1/tenants',
    TENANT_DETAIL: (id: string) => `/api/v1/tenants/${id}`,
  },

  // G0 全局搜索
  GLOBAL_SEARCH: '/api/v1/search',
} as const
