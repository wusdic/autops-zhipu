<template>
  <div class="risk-decision-card" :class="'risk-' + riskLevel">
    <div class="rdc-header">
      <span class="rdc-title">{{ title }}</span>
      <el-tag :type="riskTagType" size="small">{{ riskLabel }}</el-tag>
    </div>
    <div class="rdc-body">
      <slot />
    </div>
    <div class="rdc-footer">
      <el-button type="primary" size="small" @click="$emit('approve')" :disabled="!canApprove">批准执行</el-button>
      <el-button size="small" @click="$emit('dry-run')">Dry-run</el-button>
      <el-button size="small" @click="$emit('reject')">拒绝</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { TagType } from '@/shared/types'
import { computed } from "vue"

const props = withDefaults(defineProps<{
  title?: string
  riskLevel: "low" | "medium" | "high" | "critical"
  canApprove?: boolean
}>(), { title: "风险评估", canApprove: true })

defineEmits<{ approve: []; reject: []; "dry-run": [] }>()

const riskLabel = computed(() => ({ low: "低风险", medium: "中风险", high: "高风险", critical: "极高风险" } as any)[props.riskLevel])
const riskTagType = computed(() => ({ low: "success", medium: "warning", high: "danger", critical: "danger" } as any)[props.riskLevel])
</script>

<style scoped>
.risk-decision-card { border-radius: var(--autops-radius-md); border: 1px solid var(--autops-bg-4); background: var(--autops-bg-1); overflow: hidden; }
.risk-decision-card.risk-critical { border-color: var(--autops-danger); }
.risk-decision-card.risk-high { border-color: var(--autops-warning); }
.risk-decision-card.risk-medium { border-color: var(--autops-gold); }
.rdc-header { display: flex; justify-content: space-between; align-items: center; padding: var(--autops-space-md) 16px; border-bottom: 1px solid var(--autops-bg-3); }
.rdc-title { font-weight: 600; color: var(--autops-text-1); }
.rdc-body { padding: var(--autops-space-lg); }
.rdc-footer { display: flex; gap: 8px; padding: var(--autops-space-md) 16px; border-top: 1px solid var(--autops-bg-3); background: var(--autops-bg-1); }
</style>
