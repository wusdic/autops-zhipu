<template>
  <div class="verification-panel">
    <div class="vp-header">
      <span class="vp-title">验证结果</span>
      <el-button text type="primary" size="small" @click="$emit('verify-all')" :loading="verifying">全部验证</el-button>
    </div>
    <div class="vp-summary">
      <span class="vp-pass" :style="{ color: allPass ? '#00b42a' : '#f53f3f' }">
        {{ passCount }}/{{ items.length }} 通过
      </span>
    </div>
    <div class="vp-items">
      <div v-for="(item, idx) in items" :key="idx" class="vp-item" :class="'status-' + item.status">
        <el-icon v-if="item.status === 'pass'" style="color:#00b42a"><CircleCheck /></el-icon>
        <el-icon v-else-if="item.status === 'fail'" style="color:#f53f3f"><CircleClose /></el-icon>
        <el-icon v-else style="color:#c9cdd4"><Clock /></el-icon>
        <div class="vp-item-content">
          <div class="vp-item-name">{{ item.name }}</div>
          <div class="vp-item-detail">
            期望: {{ item.expected }} <template v-if="item.actual">| 实际: {{ item.actual }}</template>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue"
import { CircleCheck, CircleClose, Clock } from "@element-plus/icons-vue"

const props = withDefaults(defineProps<{
  items: { name: string; expected: string; actual?: string; status: "pass" | "fail" | "pending" }[]
  verifying?: boolean
}>(), { verifying: false })

defineEmits<{ "verify-all": [] }>()

const passCount = computed(() => props.items.filter(i => i.status === "pass").length)
const allPass = computed(() => props.items.length > 0 && passCount.value === props.items.length)
</script>

<style scoped>
.verification-panel { border: 1px solid #e5e6eb; border-radius: 8px; background: #fff; }
.vp-header { display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; border-bottom: 1px solid #f2f3f5; }
.vp-title { font-weight: 600; color: #1d2129; }
.vp-summary { padding: 12px 16px; font-size: 18px; font-weight: 700; text-align: center; }
.vp-items { padding: 0 16px 12px; }
.vp-item { display: flex; align-items: flex-start; gap: 8px; padding: 8px 0; border-bottom: 1px solid #f7f8fa; }
.vp-item:last-child { border-bottom: none; }
.vp-item-name { font-size: 13px; color: #1d2129; }
.vp-item-detail { font-size: 12px; color: #86909c; margin-top: 2px; }
</style>
