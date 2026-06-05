<template>
  <div class="timeline-view">
    <div v-if="title" class="timeline-header">
      <span class="timeline-title">{{ title }}</span>
      <slot name="header-actions" />
    </div>

    <!-- Filter bar -->
    <div v-if="showFilter && types.length" class="timeline-filter">
      <el-radio-group v-model="activeType" size="small" @change="emitFilter">
        <el-radio-button label="">全部</el-radio-button>
        <el-radio-button v-for="t in types" :key="t" :label="t">{{ t }}</el-radio-button>
      </el-radio-group>
    </div>

    <el-timeline>
      <el-timeline-item
        v-for="(item, idx) in filteredItems"
        :key="idx"
        :timestamp="formatTime(item.time || item.created_at)"
        :type="typeMap[item.type || item.severity] || 'primary'"
        :hollow="item.hollow || false"
        placement="top"
      >
        <el-card shadow="hover" :body-style="{ padding: '12px 16px' }">
          <div class="timeline-item-header">
            <span v-if="item.title" class="timeline-item-title">{{ item.title }}</span>
            <el-tag v-if="item.type" size="small" :type="typeMap[item.type] || ''">{{ item.type }}</el-tag>
            <el-tag v-if="item.severity && !item.type" size="small" :type="typeMap[item.severity] || ''">{{ severityLabels[item.severity] || item.severity }}</el-tag>
          </div>
          <div class="timeline-item-desc">{{ item.description || item.content || item.message }}</div>
          <div v-if="item.user || item.operator" class="timeline-item-meta">
            <span>操作人: {{ item.user || item.operator }}</span>
            <span v-if="item.action"> · {{ item.action }}</span>
          </div>
          <!-- Slot for custom content -->
          <slot name="item-detail" :item="item" :index="idx" />
        </el-card>
      </el-timeline-item>
    </el-timeline>
    <el-empty v-if="!filteredItems.length" :description="emptyText" :image-size="60" />

    <!-- Load more -->
    <div v-if="hasMore" class="timeline-load-more">
      <el-button link type="primary" @click="$emit('load-more')">加载更多</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

interface TimelineItem {
  title?: string
  description?: string
  content?: string
  message?: string
  time?: string
  created_at?: string
  type?: string
  severity?: string
  user?: string
  operator?: string
  action?: string
  hollow?: boolean
  [key: string]: any
}

const props = withDefaults(defineProps<{
  items: TimelineItem[]
  title?: string
  showFilter?: boolean
  emptyText?: string
  hasMore?: boolean
}>(), {
  title: '',
  showFilter: false,
  emptyText: '暂无时间线记录',
  hasMore: false,
})

const emit = defineEmits(['load-more', 'filter'])

const activeType = ref('')
const typeMap: Record<string, string> = {
  critical: 'danger', high: 'warning', warning: 'warning',
  info: 'primary', success: 'success', error: 'danger',
  alert: 'danger', event: 'primary', action: 'warning',
}
const severityLabels: Record<string, string> = {
  critical: '紧急', high: '高危', medium: '中危', low: '低危',
}

const types = computed(() => {
  const set = new Set<string>()
  props.items.forEach(item => {
    if (item.type) set.add(item.type)
  })
  return Array.from(set)
})

const filteredItems = computed(() => {
  if (!activeType.value) return props.items
  return props.items.filter(item => item.type === activeType.value)
})

function formatTime(ts: string | undefined) {
  if (!ts) return ''
  const d = new Date(ts)
  if (isNaN(d.getTime())) return ts
  return d.toLocaleString('zh-CN', { hour12: false })
}

function emitFilter() {
  emit('filter', activeType.value)
}
</script>

<style scoped>
.timeline-view { width: 100%; }
.timeline-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: var(--autops-space-lg);
}
.timeline-title { font-size: var(--autops-font-16); font-weight: 600; color: var(--autops-text-1); }
.timeline-filter { margin-bottom: var(--autops-space-md); }
.timeline-item-header { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.timeline-item-title { font-weight: 600; color: var(--autops-text-1); }
.timeline-item-desc { color: var(--autops-text-2); font-size: var(--autops-font-13); line-height: 1.5; }
.timeline-item-meta { color: var(--autops-info); font-size: var(--autops-font-12); margin-top: 4px; }
.timeline-load-more { text-align: center; margin-top: 12px; }
</style>
