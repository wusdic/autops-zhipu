<template>
  <el-tag :type="typeMap[status] || 'info'" :effect="effect" :size="size">
    <el-icon v-if="showIcon" style="margin-right: 4px"><component :is="iconMap[status] || 'InfoFilled'" /></el-icon>
    {{ labelMap[status] || status }}
  </el-tag>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { SuccessFilled, WarningFilled, CircleCloseFilled, InfoFilled, QuestionFilled } from '@element-plus/icons-vue'

const props = defineProps<{
  status: string
  effect?: 'dark' | 'light' | 'plain'
  size?: 'large' | 'default' | 'small'
  showIcon?: boolean
}>()

const typeMap: Record<string, string> = {
  healthy: 'success', online: 'success', active: 'success', running: 'success', ok: 'success',
  completed: 'success', enabled: 'success',
  warning: 'warning', degraded: 'warning', in_progress: 'warning', processing: 'warning',
  critical: 'danger', error: 'danger', offline: 'danger', failed: 'danger', down: 'danger',
  disabled: 'info', cancelled: 'info',
  unknown: 'info', pending: 'info', draft: 'info',
  acknowledged: '', resolved: 'success', firing: 'danger', suppressed: 'info',
}

const labelMap: Record<string, string> = {
  healthy: '健康', online: '在线', active: '活跃', running: '运行中', ok: '正常',
  completed: '已完成', enabled: '已启用',
  warning: '警告', degraded: '降级', in_progress: '处理中', processing: '处理中',
  critical: '严重', error: '错误', offline: '离线', failed: '失败', down: '停机',
  disabled: '已禁用', cancelled: '已取消',
  unknown: '未知', pending: '待处理', draft: '草稿',
  acknowledged: '已确认', resolved: '已恢复', firing: '告警中', suppressed: '已静默',
}

const iconMap: Record<string, string> = {
  healthy: 'SuccessFilled', warning: 'WarningFilled', critical: 'CircleCloseFilled',
  error: 'CircleCloseFilled', unknown: 'QuestionFilled',
}
</script>
