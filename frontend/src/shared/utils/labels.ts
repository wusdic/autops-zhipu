/**
 * AUTOPS 统一标签格式化
 * 所有状态、严重度、类型等标签的中英文映射统一在此定义
 * 页面中使用 severityLabel(s) / statusTag(s) 等函数，不再散落定义
 */

// ─── 严重度 ───
export const SEVERITY_MAP: Record<string, string> = {
  critical: '严重', critical_severe: '严重',
  high: '高危',
  warning: '警告', medium: '警告',
  info: '提示', low: '低', normal: '正常',
}
export const SEVERITY_TAG_TYPE: Record<string, string> = {
  critical: 'danger', critical_severe: 'danger',
  high: 'danger',
  warning: 'warning', medium: 'warning',
  info: 'info', low: 'info', normal: 'success',
}
export function severityLabel(s: string): string { return SEVERITY_MAP[s] ?? s }
export function severityTagType(s: string): string { return SEVERITY_TAG_TYPE[s] ?? 'info' }

// ─── 通用状态 ───
export const STATUS_MAP: Record<string, string> = {
  active: '运行中', inactive: '已停用', enabled: '已启用', disabled: '已禁用',
  online: '在线', offline: '离线',
  healthy: '健康', unhealthy: '异常', unknown: '未知', degraded: '降级',
}
export const STATUS_TAG_TYPE: Record<string, string> = {
  active: 'success', enabled: 'success', online: 'success', healthy: 'success',
  inactive: 'info', disabled: 'info', offline: 'danger', unhealthy: 'danger',
  unknown: 'info', degraded: 'warning',
}

// ─── 资产状态 ───
export const ASSET_STATUS_MAP: Record<string, string> = {
  active: '活跃', maintenance: '维护中', retired: '已退役', decommissioned: '已下线',
  provisioning: '配置中', discovering: '发现中',
}
export const ASSET_HEALTH_MAP: Record<string, string> = {
  healthy: '健康', warning: '警告', critical: '严重', unknown: '未知',
}

// ─── 告警状态 ───
export const ALERT_STATUS_MAP: Record<string, string> = {
  firing: '告警中', pending: '待处理', acknowledged: '已确认', resolved: '已恢复', suppressed: '已静默',
}
export const ALERT_STATUS_TAG: Record<string, string> = {
  firing: 'danger', pending: 'warning', acknowledged: '', resolved: 'success', suppressed: 'info',
}

// ─── 工单状态 ───
export const TICKET_STATUS_MAP: Record<string, string> = {
  open: '待处理', in_progress: '处理中', resolved: '已解决', closed: '已关闭', cancelled: '已取消',
}
export const TICKET_STATUS_TAG: Record<string, string> = {
  open: 'danger', in_progress: 'warning', resolved: 'success', closed: 'info', cancelled: 'info',
}

// ─── 执行状态 ───
export const EXEC_STATUS_MAP: Record<string, string> = {
  pending: '等待中', running: '执行中', completed: '已完成', failed: '失败',
  cancelled: '已取消', timeout: '超时', approved: '已审批', rejected: '已驳回',
  rollback: '已回滚', dry_run: '试运行',
}
export const EXEC_STATUS_TAG: Record<string, string> = {
  pending: 'info', running: '', completed: 'success', failed: 'danger',
  cancelled: 'info', timeout: 'warning', approved: 'success', rejected: 'danger',
  rollback: 'warning', dry_run: '',
}

// ─── 策略/Playbook 状态 ───
export const POLICY_STATUS_MAP: Record<string, string> = {
  draft: '草稿', active: '已激活', deprecated: '已废弃', disabled: '已禁用',
}

// ─── 风险等级 ───
export const RISK_TAG_TYPE: Record<string, string> = {
  low: 'info', medium: 'warning', high: 'danger', critical: 'danger',
}

// ─── 知识库状态 ───
export const KNOWLEDGE_STATUS_MAP: Record<string, string> = {
  draft: '草稿', published: '已发布', archived: '已归档', review: '待审核',
}

// ─── 资产类型 ───
export const ASSET_TYPE_MAP: Record<string, string> = {
  server: '服务器', linux_server: 'Linux 服务器', windows_server: 'Windows 服务器',
  database: '数据库', web_service: 'Web 服务', network_device: '网络设备',
  container: '容器', virtual_machine: '虚拟机', storage: '存储',
  Linux: 'Linux 服务器', Windows: 'Windows 服务器', Server: '服务器',
  Database: '数据库', WebService: 'Web 服务', NetworkDevice: '网络设备',
}

// ─── 环境标签 ───
export const ENV_MAP: Record<string, string> = {
  production: '生产', staging: '预发布', testing: '测试', development: '开发',
  prod: '生产', stage: '预发布', test: '测试', dev: '开发',
}

// ─── 凭证类型 ───
export const CRED_TYPE_MAP: Record<string, string> = {
  ssh_key: 'SSH 密钥', password: '密码', api_token: 'API Token', certificate: '证书',
  snmp: 'SNMP', winrm: 'WinRM',
}

// ─── 通用 helper ───
export function labelOr(map: Record<string, string>, key: string): string {
  return map[key] ?? key
}

export function tagTypeOr(map: Record<string, string>, key: string): string {
  return map[key] ?? 'info'
}
