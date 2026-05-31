<template>
  <el-card shadow="hover" :body-style="{ padding: '16px' }">
    <template #header>
      <div :style="{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }">
        <span :style="{ fontWeight: 600 }">
          <el-icon style="margin-right: 6px"><MagicStick /></el-icon>
          AI 分析结果
        </span>
        <el-tag v-if="confidence" :type="confidence > 0.8 ? 'success' : confidence > 0.5 ? 'warning' : 'info'" size="small">
          置信度: {{ (confidence * 100).toFixed(0) }}%
        </el-tag>
      </div>
    </template>
    <div v-if="rootCause" :style="{ marginBottom: '12px' }">
      <div :style="{ fontWeight: 600, marginBottom: '4px' }">根因分析</div>
      <div :style="{ color: '#606266' }">{{ rootCause }}</div>
    </div>
    <div v-if="recommendations?.length">
      <div :style="{ fontWeight: 600, marginBottom: '4px' }">建议操作</div>
      <el-timeline>
        <el-timeline-item v-for="(rec, idx) in recommendations" :key="idx" :type="rec.risk === 'high' ? 'danger' : rec.risk === 'medium' ? 'warning' : 'primary'">
          {{ rec.action || rec.description || rec }}
        </el-timeline-item>
      </el-timeline>
    </div>
    <div v-if="summary" :style="{ marginTop: '12px', padding: '8px', background: '#f5f7fa', borderRadius: '4px', fontSize: '13px' }">{{ summary }}</div>
  </el-card>
</template>

<script setup lang="ts">
import { MagicStick } from '@element-plus/icons-vue'

defineProps<{
  rootCause?: string
  recommendations?: Array<string | { action: string; risk?: string; description?: string }>
  confidence?: number
  summary?: string
}>()
</script>
