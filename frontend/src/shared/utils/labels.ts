/**
 * AUTOPS 统一标签格式化（单一事实源）
 *
 * 所有实体的状态/严重度/类型中英文映射与标签颜色统一在此定义，页面不要再各自写
 * 局部 statusLabel/statusType。取值以后端 canonical 值为准，并对历史/同义值容错。
 *
 * 约定：xxxLabel(v) → 中文文案；xxxTag(v) → Element Plus el-tag 的 type。
 */

type TagType = '' | 'success' | 'warning' | 'info' | 'danger' | 'primary'

function pick(map: Record<string, string>, key: string | null | undefined, fallback = ''): string {
  if (key == null || key === '') return fallback || '-'
  return map[key] ?? key
}
function pickTag(map: Record<string, TagType>, key: string | null | undefined, fallback: TagType = 'info'): TagType {
  if (key == null) return fallback
  return map[key] ?? fallback
}

// ─── 严重度（告警/异常）info/warning/critical，容错 high/medium/low ───
export const SEVERITY_MAP: Record<string, string> = {
  critical: '严重', high: '高危', major: '高', warning: '警告', medium: '中',
  info: '提示', low: '低', minor: '低', normal: '正常',
}
export const SEVERITY_TAG: Record<string, TagType> = {
  critical: 'danger', high: 'danger', major: 'danger', warning: 'warning', medium: 'warning',
  info: 'info', low: 'info', minor: 'info', normal: 'success',
}
export function severityLabel(s: string): string { return pick(SEVERITY_MAP, s) }
export function severityTagType(s: string): TagType { return pickTag(SEVERITY_TAG, s) }

// ─── 资产生命周期 status：active/inactive/maintenance/decommissioned ───
// 容错历史在线性 online/offline（现应放 reachability）
export const ASSET_STATUS_MAP: Record<string, string> = {
  active: '活跃', inactive: '停用', maintenance: '维护中', decommissioned: '已下线',
  provisioning: '配置中', retired: '已退役', online: '在线', offline: '离线',
}
export const ASSET_STATUS_TAG: Record<string, TagType> = {
  active: 'success', online: 'success', inactive: 'info', maintenance: 'warning',
  provisioning: 'warning', decommissioned: 'danger', retired: 'danger', offline: 'danger',
}
export function assetStatusLabel(s: string): string { return pick(ASSET_STATUS_MAP, s) }
export function assetStatusTag(s: string): TagType { return pickTag(ASSET_STATUS_TAG, s, 'warning') }

// ─── 可达性 reachability：reachable/unreachable/unknown ───
export const REACHABILITY_MAP: Record<string, string> = {
  reachable: '可达', unreachable: '不可达', unknown: '未知',
}
export const REACHABILITY_TAG: Record<string, TagType> = {
  reachable: 'success', unreachable: 'danger', unknown: 'info',
}
export function reachabilityLabel(s: string): string { return pick(REACHABILITY_MAP, s) }
export function reachabilityTag(s: string): TagType { return pickTag(REACHABILITY_TAG, s) }

// ─── 健康度 health_status：healthy/warning/critical/unknown ───
export const HEALTH_MAP: Record<string, string> = {
  healthy: '健康', warning: '警告', critical: '严重', unknown: '未知', degraded: '降级',
  unhealthy: '异常', error: '异常', down: '离线',
}
export const HEALTH_TAG: Record<string, TagType> = {
  healthy: 'success', warning: 'warning', critical: 'danger', degraded: 'warning', unknown: 'info',
  unhealthy: 'danger', error: 'danger', down: 'danger',
}
export function healthLabel(s: string): string { return pick(HEALTH_MAP, s) }
export function healthTag(s: string): TagType { return pickTag(HEALTH_TAG, s) }

// ─── 告警状态：firing/acknowledged/resolved/escalated/suppressed ───
export const ALERT_STATUS_MAP: Record<string, string> = {
  firing: '告警中', acknowledged: '已确认', resolved: '已恢复',
  escalated: '已升级', suppressed: '已静默', pending: '待处理', active: '告警中',
}
export const ALERT_STATUS_TAG: Record<string, TagType> = {
  firing: 'danger', active: 'danger', escalated: 'danger', acknowledged: 'warning',
  pending: 'warning', resolved: 'success', suppressed: 'info',
}
export function alertStatusLabel(s: string): string { return pick(ALERT_STATUS_MAP, s) }
export function alertStatusTag(s: string): TagType { return pickTag(ALERT_STATUS_TAG, s) }

// ─── 工单状态：open/assigned/in_progress/pending_approval/resolved/closed/rejected ───
export const TICKET_STATUS_MAP: Record<string, string> = {
  open: '待处理', assigned: '已分派', in_progress: '处理中', pending_approval: '待审批',
  resolved: '已解决', closed: '已关闭', rejected: '已驳回', cancelled: '已取消',
}
export const TICKET_STATUS_TAG: Record<string, TagType> = {
  open: 'danger', assigned: 'warning', in_progress: 'warning', pending_approval: 'warning',
  resolved: 'success', closed: 'info', rejected: 'info', cancelled: 'info',
}
export function ticketStatusLabel(s: string): string { return pick(TICKET_STATUS_MAP, s) }
export function ticketStatusTag(s: string): TagType { return pickTag(TICKET_STATUS_TAG, s) }

// ─── 优先级（工单）low/medium/high/urgent ───
export const PRIORITY_MAP: Record<string, string> = {
  low: '低', medium: '中', high: '高', urgent: '紧急', critical: '严重',
}
export const PRIORITY_TAG: Record<string, TagType> = {
  low: 'info', medium: '', high: 'warning', urgent: 'danger', critical: 'danger',
}
export function priorityLabel(s: string): string { return pick(PRIORITY_MAP, s) }
export function priorityTag(s: string): TagType { return pickTag(PRIORITY_TAG, s) }

// ─── 执行状态（canonical ExecutionStatus，全量）───
export const EXEC_STATUS_MAP: Record<string, string> = {
  pending: '等待中', dry_running: '试运行中', dry_run_completed: '试运行完成',
  dry_run_failed: '试运行失败', awaiting_approval: '待审批', approved: '已审批',
  running: '执行中', verifying: '验证中', completed: '已完成', failed: '失败',
  cancelled: '已取消', rolling_back: '回滚中', rolled_back: '已回滚',
  rollback_failed: '回滚失败', blocked: '已阻断', timeout: '超时',
}
export const EXEC_STATUS_TAG: Record<string, TagType> = {
  pending: 'info', dry_running: '', dry_run_completed: 'success', dry_run_failed: 'danger',
  awaiting_approval: 'warning', approved: 'success', running: '', verifying: 'warning',
  completed: 'success', failed: 'danger', cancelled: 'info', rolling_back: 'warning',
  rolled_back: 'info', rollback_failed: 'danger', blocked: 'danger', timeout: 'warning',
}
export function execStatusLabel(s: string): string { return pick(EXEC_STATUS_MAP, s) }
export function execStatusTag(s: string): TagType { return pickTag(EXEC_STATUS_TAG, s) }

// ─── 策略/Playbook 状态：draft/active/disabled ───
export const POLICY_STATUS_MAP: Record<string, string> = {
  draft: '草稿', active: '已激活', disabled: '已禁用', deprecated: '已废弃',
}
export const POLICY_STATUS_TAG: Record<string, TagType> = {
  draft: 'info', active: 'success', disabled: 'info', deprecated: 'warning',
}
export function policyStatusLabel(s: string): string { return pick(POLICY_STATUS_MAP, s) }
export function policyStatusTag(s: string): TagType { return pickTag(POLICY_STATUS_TAG, s) }

// ─── 风险等级 low/medium/high/critical ───
export const RISK_MAP: Record<string, string> = {
  low: '低', medium: '中', high: '高', critical: '严重',
}
export const RISK_TAG_TYPE: Record<string, TagType> = {
  low: 'info', medium: 'warning', high: 'danger', critical: 'danger',
}
export function riskLabel(s: string): string { return pick(RISK_MAP, s) }
export function riskTag(s: string): TagType { return pickTag(RISK_TAG_TYPE, s) }

// ─── 知识库状态 ───
export const KNOWLEDGE_STATUS_MAP: Record<string, string> = {
  draft: '草稿', published: '已发布', archived: '已归档', review: '待审核',
  pending_review: '待审核', rejected: '已驳回',
}
export const KNOWLEDGE_STATUS_TAG: Record<string, TagType> = {
  draft: 'info', published: 'success', archived: 'info', review: 'warning',
  pending_review: 'warning', rejected: 'danger',
}
export function knowledgeStatusLabel(s: string): string { return pick(KNOWLEDGE_STATUS_MAP, s) }
export function knowledgeStatusTag(s: string): TagType { return pickTag(KNOWLEDGE_STATUS_TAG, s) }

// ─── 通用任务/作业状态（报表/导出/巡检任务/采集结果等）───
export const TASK_STATUS_MAP: Record<string, string> = {
  pending: '待执行', queued: '排队中', generating: '生成中', running: '执行中',
  processing: '处理中', in_progress: '处理中', completed: '已完成', success: '成功',
  failed: '失败', error: '失败', cancelled: '已取消', timeout: '超时', archived: '已归档',
}
export const TASK_STATUS_TAG: Record<string, TagType> = {
  pending: 'info', queued: 'info', generating: 'warning', running: 'warning',
  processing: 'warning', in_progress: 'warning', completed: 'success', success: 'success',
  failed: 'danger', error: 'danger', cancelled: 'info', timeout: 'danger', archived: 'success',
}
export function taskStatusLabel(s: string): string { return pick(TASK_STATUS_MAP, s) }
export function taskStatusTag(s: string): TagType { return pickTag(TASK_STATUS_TAG, s) }

// ─── 检查/巡检结果（巡检/配置巡检/自检）───
export const CHECK_RESULT_MAP: Record<string, string> = {
  normal: '正常', ok: '正常', pass: '通过', passed: '通过',
  abnormal: '异常', fail: '未通过', failed: '失败', error: '异常',
  warning: '警告', warn: '警告', pending: '未执行', skipped: '跳过', skip: '跳过',
}
export const CHECK_RESULT_TAG: Record<string, TagType> = {
  normal: 'success', ok: 'success', pass: 'success', passed: 'success',
  abnormal: 'danger', fail: 'danger', failed: 'danger', error: 'danger',
  warning: 'warning', warn: 'warning', pending: 'info', skipped: 'info', skip: 'info',
}
export function checkResultLabel(s: string): string { return pick(CHECK_RESULT_MAP, s) }
export function checkResultTag(s: string): TagType { return pickTag(CHECK_RESULT_TAG, s) }

// ─── 审批状态（执行审批/Agent 审批）───
export const APPROVAL_STATUS_MAP: Record<string, string> = {
  pending: '待审批', approved: '已批准', rejected: '已拒绝',
}
export const APPROVAL_STATUS_TAG: Record<string, TagType> = {
  pending: 'warning', approved: 'success', rejected: 'danger',
}
export function approvalStatusLabel(s: string): string { return pick(APPROVAL_STATUS_MAP, s) }
export function approvalStatusTag(s: string): TagType { return pickTag(APPROVAL_STATUS_TAG, s) }

// ─── 服务状态（模型服务/集成）───
export const SERVICE_STATUS_MAP: Record<string, string> = {
  active: '正常', inactive: '未激活', error: '异常', testing: '测试中',
  online: '在线', offline: '离线',
}
export const SERVICE_STATUS_TAG: Record<string, TagType> = {
  active: 'success', inactive: 'info', error: 'danger', testing: 'warning',
  online: 'success', offline: 'danger',
}
export function serviceStatusLabel(s: string): string { return pick(SERVICE_STATUS_MAP, s) }
export function serviceStatusTag(s: string): TagType { return pickTag(SERVICE_STATUS_TAG, s) }

// ─── 异常(anomaly)状态 ───
export const ANOMALY_STATUS_MAP: Record<string, string> = {
  open: '待处理', new: '待处理', pending: '待处理', acknowledged: '已确认',
  processing: '处理中', in_progress: '处理中', resolved: '已解决', closed: '已关闭',
  escalated: '已升级', cancelled: '已取消',
}
export const ANOMALY_STATUS_TAG: Record<string, TagType> = {
  open: 'danger', new: 'danger', pending: 'warning', acknowledged: 'warning',
  processing: 'warning', in_progress: 'warning', resolved: 'success', closed: 'info',
  escalated: 'danger', cancelled: 'info',
}
export function anomalyStatusLabel(s: string): string { return pick(ANOMALY_STATUS_MAP, s) }
export function anomalyStatusTag(s: string): TagType { return pickTag(ANOMALY_STATUS_TAG, s) }

// ─── 资产类型 ───
export const ASSET_TYPE_MAP: Record<string, string> = {
  server: '服务器', linux_server: 'Linux 服务器', windows_server: 'Windows 服务器',
  database: '数据库', web_service: 'Web 服务', web_server: 'Web 服务器',
  network_device: '网络设备', cache_server: '缓存', search_engine: '搜索引擎',
  container: '容器', virtual_machine: '虚拟机', storage: '存储',
  business_system: '业务系统', unknown: '未知',
  Linux: 'Linux 服务器', Windows: 'Windows 服务器', Server: '服务器',
  Database: '数据库', WebService: 'Web 服务', NetworkDevice: '网络设备',
}
export function assetTypeLabel(s: string): string { return pick(ASSET_TYPE_MAP, s) }

// ─── 环境 ───
export const ENV_MAP: Record<string, string> = {
  production: '生产', staging: '预发布', testing: '测试', development: '开发',
  prod: '生产', stage: '预发布', test: '测试', dev: '开发',
}
export function envLabel(s: string): string { return pick(ENV_MAP, s) }

// ─── 凭证类型 ───
export const CRED_TYPE_MAP: Record<string, string> = {
  ssh_key: 'SSH 密钥', ssh_password: 'SSH 密码', password: '密码',
  api_token: 'API Token', certificate: '证书', snmp: 'SNMP', winrm: 'WinRM',
}
export function credTypeLabel(s: string): string { return pick(CRED_TYPE_MAP, s) }

// ─── 兼容旧用法（保留别名，逐步迁移）───
export const STATUS_MAP = { ...ASSET_STATUS_MAP, ...HEALTH_MAP }
export const STATUS_TAG_TYPE = { ...ASSET_STATUS_TAG, ...HEALTH_TAG }
export const ASSET_HEALTH_MAP = HEALTH_MAP
export const SEVERITY_TAG_TYPE = SEVERITY_TAG
export const ALERT_STATUS_TAG_TYPE = ALERT_STATUS_TAG
export const TICKET_STATUS_TAG_TYPE = TICKET_STATUS_TAG
export const EXEC_STATUS_TAG_TYPE = EXEC_STATUS_TAG

// ─── 通用 helper ───
export function labelOr(map: Record<string, string>, key: string): string {
  return map[key] ?? key
}
export function tagTypeOr(map: Record<string, string>, key: string): string {
  return map[key] ?? 'info'
}
