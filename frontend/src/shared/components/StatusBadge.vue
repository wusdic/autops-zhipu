<template>
  <span :class="['status-badge', 'status-badge--' + type]">
    <span v-if="dot" class="status-badge__dot" />
    <span class="status-badge__text">{{ label || text }}</span>
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  status?: string
  type?: string
  label?: string
  text?: string
  dot?: boolean
}>()

const typeMap: Record<string, string> = {
  // 通用状态
  active: 'success',
  inactive: 'info',
  running: 'primary',
  pending: 'warning',
  completed: 'success',
  failed: 'danger',
  cancelled: 'info',
  timeout: 'danger',
  // 健康状态
  healthy: 'success',
  unhealthy: 'danger',
  degraded: 'warning',
  unknown: 'info',
  // 告警状态
  firing: 'danger',
  resolved: 'success',
  acknowledged: 'warning',
  suppressed: 'info',
  // 资产状态
  online: 'success',
  offline: 'danger',
  error: 'danger',
  warning: 'warning',
  // 审批状态
  approved: 'success',
  rejected: 'danger',
  // 知识状态
  draft: 'info',
  published: 'success',
  archived: 'info',
  // 工单状态
  open: 'primary',
  in_progress: 'primary',
  closed: 'success',
  reopened: 'warning',
}

const labelMap: Record<string, string> = {
  active: '活跃',
  inactive: '未激活',
  running: '运行中',
  pending: '待处理',
  completed: '已完成',
  failed: '失败',
  cancelled: '已取消',
  timeout: '超时',
  healthy: '健康',
  unhealthy: '不健康',
  degraded: '降级',
  unknown: '未知',
  firing: '告警中',
  resolved: '已恢复',
  acknowledged: '已确认',
  suppressed: '已抑制',
  online: '在线',
  offline: '离线',
  error: '异常',
  warning: '告警',
  approved: '已通过',
  rejected: '已拒绝',
  draft: '草稿',
  published: '已发布',
  archived: '已归档',
  open: '待处理',
  in_progress: '处理中',
  closed: '已关闭',
  reopened: '已重开',
}

const type = computed(() => {
  if (props.type) return props.type
  return typeMap[props.status || ''] || 'info'
})

const text = computed(() => {
  if (props.label) return props.label
  return labelMap[props.status || ''] || props.status || '未知'
})
</script>

<style scoped>
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: var(--autops-radius-sm);
  font-size: var(--autops-font-12);
  line-height: 20px;
  white-space: nowrap;
}

.status-badge__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.status-badge--success {
  color: var(--autops-success);
  background: var(--autops-success-light);
}
.status-badge--success .status-badge__dot {
  background: var(--autops-success);
}

.status-badge--danger {
  color: var(--autops-danger);
  background: var(--autops-danger-light);
}
.status-badge--danger .status-badge__dot {
  background: var(--autops-danger);
}

.status-badge--warning {
  color: var(--autops-gold);
  background: var(--autops-gold-light);
}
.status-badge--warning .status-badge__dot {
  background: var(--autops-gold);
}

.status-badge--primary {
  color: var(--autops-primary);
  background: var(--autops-primary-light-5);
}
.status-badge--primary .status-badge__dot {
  background: var(--autops-primary);
}

.status-badge--info {
  color: var(--autops-info);
  background: var(--autops-bg-3);
}
.status-badge--info .status-badge__dot {
  background: var(--autops-info);
}
</style>
