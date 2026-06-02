<template>
  <div class="overview-card" :style="borderStyle">
    <div class="oc-icon" v-if="icon" :style="{ background: bgColor, color: iconColor }">
      <el-icon :size="20"><component :is="icon" /></el-icon>
    </div>
    <div class="oc-content">
      <div class="oc-label">{{ label }}</div>
      <div class="oc-value" :style="{ color: valueColor }">{{ displayValue }}</div>
      <div class="oc-footer" v-if="trend !== undefined">
        <span :class="trend >= 0 ? 'trend-up' : 'trend-down'">
          {{ trend >= 0 ? "↑" : "↓" }} {{ Math.abs(trend) }}%
        </span>
        <span class="oc-sub">{{ subLabel }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue"

const props = withDefaults(defineProps<{
  label: string
  value: string | number
  icon?: any
  iconColor?: string
  bgColor?: string
  borderColor?: string
  valueColor?: string
  trend?: number
  subLabel?: string
  suffix?: string
}>(), {
  iconColor: "#165dff",
  bgColor: "#e8f3ff",
  valueColor: "#1d2129",
})

const displayValue = computed(() => props.suffix ? `${props.value}${props.suffix}` : String(props.value))
const borderStyle = computed(() => props.borderColor ? { borderLeft: `4px solid ${props.borderColor}` } : {})
</script>

<style scoped>
.overview-card {
  display: flex; align-items: center; gap: 12px;
  padding: 16px 20px; background: #fff; border-radius: 8px;
  border: 1px solid #e5e6eb; transition: box-shadow 0.2s;
}
.overview-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.06); }
.oc-icon { width: 44px; height: 44px; border-radius: 8px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.oc-label { font-size: 13px; color: #86909c; margin-bottom: 4px; }
.oc-value { font-size: 24px; font-weight: 700; line-height: 1.2; }
.oc-footer { font-size: 12px; margin-top: 4px; display: flex; align-items: center; gap: 8px; }
.trend-up { color: #00b42a; } .trend-down { color: #f53f3f; }
.oc-sub { color: #c9cdd4; }
</style>
