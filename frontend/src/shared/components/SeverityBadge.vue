<template>
  <el-tag :type="(severityTagType(severity)) as TagType" effect="dark" :size="size">
    {{ severityLabel(severity) }}
  </el-tag>
</template>

<script setup lang="ts">
// 严重度统一取自 shared/utils/labels.ts（单一事实源）
import type { TagType } from '@/shared/types'
import { severityLabel, severityTagType } from '@/shared/utils/labels'
defineProps<{ severity: string; size?: 'large' | 'default' | 'small' }>()
</script>
