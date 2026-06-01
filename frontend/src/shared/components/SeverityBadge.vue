<template>
  <el-tag :type="typeMap[severity] || 'info'" effect="dark" :size="size">
    {{ labelMap[severity] || severity }}
  </el-tag>
</template>

<script setup lang="ts">
defineProps<{ severity: string; size?: 'large' | 'default' | 'small' }>()

const typeMap: Record<string, string> = {
  critical: 'danger', severe: 'danger',
  high: 'warning', major: 'warning',
  warning: 'warning', medium: '', minor: '',
  low: 'info', info: 'info', normal: 'success',
}

const labelMap: Record<string, string> = {
  critical: '严重', severe: '严重', high: '高危', major: '重要',
  warning: '警告', medium: '中', minor: '次要',
  low: '低', info: '信息', normal: '正常',
}
</script>
