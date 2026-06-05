<template>
  <el-tag :type="(typeMap[severity] || 'info') as TagType" effect="dark" :size="size">
    {{ labelMap[severity] || severity }}
  </el-tag>
</template>

<script setup lang="ts">
import type { TagType } from '@/shared/types'
defineProps<{ severity: string; size?: 'large' | 'default' | 'small' }>()

const typeMap: Record<string, TagType> = {
  critical: 'danger', severe: 'danger',
  high: 'warning', major: 'warning',
  warning: 'warning', medium: 'primary', minor: 'primary',
  low: 'info', info: 'info', normal: 'success',
}

const labelMap: Record<string, string> = {
  critical: '严重', severe: '严重', high: '高危', major: '重要',
  warning: '警告', medium: '中', minor: '次要',
  low: '低', info: '信息', normal: '正常',
}
</script>
