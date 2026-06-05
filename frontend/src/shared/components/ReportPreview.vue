<template>
  <div class="report-preview">
    <div class="rp-toolbar" v-if="showToolbar">
      <el-button @click="$emit('back')">返回</el-button>
      <el-button type="primary" @click="$emit('download')"><el-icon><Download /></el-icon> 下载</el-button>
      <el-button @click="$emit('print')"><el-icon><Printer /></el-icon> 打印</el-button>
    </div>
    <div class="rp-content" ref="contentRef">
      <div class="rp-header">
        <h1 class="rp-title">{{ title }}</h1>
        <div class="rp-meta">
          <span v-if="period">周期: {{ period }}</span>
          <span v-if="generatedAt">生成时间: {{ generatedAt }}</span>
        </div>
      </div>
      <div class="rp-body">
        <slot />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue"
import { Download, Printer } from "@element-plus/icons-vue"

defineProps<{
  title: string
  period?: string
  generatedAt?: string
  showToolbar?: boolean
}>()

defineEmits<{ back: []; download: []; print: [] }>()
const contentRef = ref<HTMLElement>()
</script>

<style scoped>
.report-preview { background: var(--autops-bg-1); border-radius: var(--autops-radius-md); border: 1px solid var(--autops-bg-4); }
.rp-toolbar { display: flex; gap: 8px; padding: var(--autops-space-md) 16px; border-bottom: 1px solid var(--autops-bg-3); }
.rp-content { padding: 32px 48px; min-height: 400px; }
.rp-header { text-align: center; margin-bottom: 24px; padding-bottom: 16px; border-bottom: 2px solid var(--autops-text-1); }
.rp-title { font-size: 24px; font-weight: 700; color: var(--autops-text-1); margin: 0 0 8px; }
.rp-meta { font-size: var(--autops-font-13); color: var(--autops-info); display: flex; justify-content: center; gap: 24px; }
.rp-body { line-height: 1.8; }
</style>
