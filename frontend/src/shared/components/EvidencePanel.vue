<template>
  <div class="evidence-panel">
    <div class="ep-header">
      <span class="ep-title">{{ title }}</span>
      <div class="ep-actions">
        <el-button text type="primary" size="small" @click="$emit('collect')">收集证据</el-button>
        <el-button v-if="evidences.length" text size="small" @click="$emit('export')">导出</el-button>
      </div>
    </div>

    <!-- Evidence stats -->
    <div v-if="evidences.length" class="ep-stats">
      <el-tag size="small">共 {{ evidences.length }} 条证据</el-tag>
      <el-tag v-for="g in groupStats" :key="g.type" size="small" :type="g.tagType">
        {{ g.type }}: {{ g.count }}
      </el-tag>
    </div>

    <div class="ep-body">
      <div v-for="(group, gIdx) in grouped" :key="gIdx" class="ep-group">
        <div class="ep-group-title">
          <el-icon :size="14"><component :is="getGroupIcon(group.type)" /></el-icon>
          {{ group.type }}
          <span class="ep-group-count">{{ group.items.length }}</span>
        </div>
        <div v-for="(item, iIdx) in group.items" :key="iIdx" class="ep-item" :class="{ 'ep-item-critical': item.severity === 'critical' }">
          <div class="ep-item-header">
            <div class="ep-item-source">
              <el-tag size="small" :type="sourceType(item.source)">{{ item.source }}</el-tag>
              <el-tag v-if="item.severity" size="small" :type="severityType(item.severity)">{{ item.severity }}</el-tag>
            </div>
            <span class="ep-time">{{ formatTime(item.collected_at) }}</span>
          </div>
          <div class="ep-summary">{{ item.summary }}</div>
          <div v-if="item.detail" class="ep-detail-toggle" @click="toggleDetail(gIdx, iIdx)">
            <el-icon :size="12">
              <ArrowDown v-if="!expanded[gIdx + '-' + iIdx]" />
              <ArrowUp v-else />
            </el-icon>
            {{ expanded[gIdx + '-' + iIdx] ? '收起' : '展开详情' }}
          </div>
          <div v-if="item.detail && expanded[gIdx + '-' + iIdx]" class="ep-detail">
            <pre>{{ item.detail }}</pre>
          </div>
        </div>
      </div>
      <el-empty v-if="!evidences.length" :description="emptyText" :image-size="60" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive } from 'vue'
import { ArrowDown, ArrowUp, Monitor, Warning, Document, Connection } from '@element-plus/icons-vue'

interface Evidence {
  type: string
  source: string
  summary: string
  detail?: string
  collected_at: string
  severity?: string
}

const props = withDefaults(defineProps<{
  evidences: Evidence[]
  title?: string
  emptyText?: string
}>(), { title: '证据链', emptyText: '暂无证据' })

defineEmits<{ collect: []; export: [] }>()

const expanded = reactive<Record<string, boolean>>({})

function toggleDetail(g: number, i: number) {
  const key = g + '-' + i
  expanded[key] = !expanded[key]
}

const grouped = computed(() => {
  const map: Record<string, Evidence[]> = {}
  for (const e of props.evidences) {
    ;(map[e.type] ||= []).push(e)
  }
  return Object.entries(map).map(([type, items]) => ({ type, items }))
})

const groupStats = computed(() => {
  return grouped.value.map(g => ({
    type: g.type,
    count: g.items.length,
    tagType: severityType(g.items[0]?.severity || ''),
  }))
})

function severityType(s: string) {
  return { critical: 'danger', high: 'warning', medium: '', low: 'info' }[s] || 'info'
}

function sourceType(s: string) {
  return { collector: '', ai: 'success', manual: 'warning', system: 'info' }[s] || ''
}

function getGroupIcon(type: string) {
  return { metric: Monitor, alert: Warning, log: Document, topology: Connection }[type] || Document
}

function formatTime(ts: string) {
  if (!ts) return ''
  const d = new Date(ts)
  if (isNaN(d.getTime())) return ts
  return d.toLocaleString('zh-CN', { hour12: false })
}
</script>

<style scoped>
.evidence-panel { border: 1px solid var(--autops-bg-4); border-radius: var(--autops-radius-md); background: var(--autops-bg-1); }
.ep-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: var(--autops-space-md) 16px; border-bottom: 1px solid var(--autops-bg-3);
}
.ep-title { font-weight: 600; color: var(--autops-text-1); font-size: var(--autops-font-14); }
.ep-actions { display: flex; gap: 4px; }
.ep-stats { display: flex; gap: 6px; padding: var(--autops-space-sm) 16px; border-bottom: 1px solid var(--autops-bg-2); flex-wrap: wrap; }
.ep-body { padding: var(--autops-space-md) 16px; max-height: 600px; overflow-y: auto; }
.ep-group { margin-bottom: var(--autops-space-md); }
.ep-group-title {
  font-size: var(--autops-font-13); font-weight: 600; color: var(--autops-info); margin-bottom: var(--autops-space-sm);
  padding-left: 8px; border-left: 3px solid var(--autops-primary); display: flex; align-items: center; gap: 6px;
}
.ep-group-count { background: var(--autops-bg-3); padding: 0 6px; border-radius: 10px; font-size: 11px; }
.ep-item {
  padding: 10px 12px; border: 1px solid var(--autops-bg-3); border-radius: 6px; margin-bottom: 6px;
  transition: border-color 0.2s;
}
.ep-item:hover { border-color: var(--autops-text-4); }
.ep-item-critical { border-left: 3px solid var(--autops-danger); }
.ep-item-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.ep-item-source { display: flex; gap: 4px; }
.ep-time { font-size: var(--autops-font-12); color: var(--autops-text-4); }
.ep-summary { font-size: var(--autops-font-13); color: var(--autops-text-1); line-height: 1.5; }
.ep-detail-toggle {
  display: flex; align-items: center; gap: 4px; font-size: var(--autops-font-12); color: var(--autops-primary);
  cursor: pointer; margin-top: 6px;
}
.ep-detail pre {
  font-size: var(--autops-font-12); white-space: pre-wrap; background: var(--autops-bg-2);
  padding: var(--autops-space-sm) 10px; border-radius: var(--autops-radius-sm); margin-top: 4px; max-height: 300px; overflow-y: auto;
  font-family: 'Menlo', 'Monaco', 'Consolas', monospace;
}
</style>
