<template>
  <span :class="['status-badge', 'status-badge--' + type]">
    <span v-if="dot" class="status-badge__dot" />
    <span class="status-badge__text">{{ label || text }}</span>
  </span>
</template>

<script setup lang="ts">
import type { TagType } from '@/shared/types'
import { computed } from 'vue'
import {
  SEVERITY_MAP, SEVERITY_TAG, ASSET_STATUS_MAP, ASSET_STATUS_TAG,
  REACHABILITY_MAP, REACHABILITY_TAG, HEALTH_MAP, HEALTH_TAG,
  ALERT_STATUS_MAP, ALERT_STATUS_TAG, TICKET_STATUS_MAP, TICKET_STATUS_TAG,
  PRIORITY_MAP, PRIORITY_TAG, EXEC_STATUS_MAP, EXEC_STATUS_TAG,
  POLICY_STATUS_MAP, POLICY_STATUS_TAG, KNOWLEDGE_STATUS_MAP, RISK_MAP, RISK_TAG_TYPE,
} from '@/shared/utils/labels'

const props = defineProps<{
  status?: string
  type?: string
  label?: string
  text?: string
  dot?: boolean
}>()

// 全部取值映射统一来自 shared/utils/labels.ts（单一事实源），合并为通用徽标。
// 合并顺序：通用/健康在前，具体业务状态在后覆盖，避免同义键冲突。
const labelMap: Record<string, string> = {
  ...HEALTH_MAP, ...SEVERITY_MAP, ...REACHABILITY_MAP, ...POLICY_STATUS_MAP,
  ...KNOWLEDGE_STATUS_MAP, ...RISK_MAP, ...ASSET_STATUS_MAP, ...EXEC_STATUS_MAP,
  ...TICKET_STATUS_MAP, ...PRIORITY_MAP, ...ALERT_STATUS_MAP,
  error: '异常', reopened: '已重开',
}
const typeMap: Record<string, TagType> = {
  ...HEALTH_TAG, ...SEVERITY_TAG, ...REACHABILITY_TAG, ...POLICY_STATUS_TAG,
  ...RISK_TAG_TYPE, ...ASSET_STATUS_TAG, ...EXEC_STATUS_TAG,
  ...TICKET_STATUS_TAG, ...PRIORITY_TAG, ...ALERT_STATUS_TAG,
  error: 'danger', reopened: 'warning',
} as Record<string, TagType>

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
