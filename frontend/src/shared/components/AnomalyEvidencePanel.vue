<template>
  <div class="evidence-panel">
    <div class="ep-header">
      <span class="ep-title">证据链</span>
      <el-button text type="primary" size="small" @click="$emit('collect')">收集证据</el-button>
    </div>
    <div class="ep-body">
      <div v-for="(group, gIdx) in grouped" :key="gIdx" class="ep-group">
        <div class="ep-group-title">{{ group.type }}</div>
        <div v-for="(item, iIdx) in group.items" :key="iIdx" class="ep-item">
          <div class="ep-item-header">
            <el-tag size="small">{{ item.source }}</el-tag>
            <span class="ep-time">{{ item.collected_at }}</span>
          </div>
          <div class="ep-summary">{{ item.summary }}</div>
          <div class="ep-detail" v-if="item.detail" @click="toggleDetail(gIdx, iIdx)">
            {{ expanded[gIdx + '-' + iIdx] ? item.detail : "展开详情..." }}
          </div>
        </div>
      </div>
      <el-empty v-if="!evidences.length" description="暂无证据" :image-size="60" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive } from "vue"

const props = defineProps<{
  evidences: { type: string; source: string; summary: string; detail?: string; collected_at: string }[]
}>()

defineEmits<{ collect: [] }>()

const expanded = reactive<Record<string, boolean>>({})

function toggleDetail(g: number, i: number) {
  const key = g + '-' + i
  expanded[key] = !expanded[key]
}

const grouped = computed(() => {
  const map: Record<string, any[]> = {}
  for (const e of props.evidences) {
    ;(map[e.type] ||= []).push(e)
  }
  return Object.entries(map).map(([type, items]) => ({ type, items }))
})
</script>

<style scoped>
.evidence-panel { border: 1px solid var(--autops-bg-4); border-radius: var(--autops-radius-md); background: var(--autops-bg-1); }
.ep-header { display: flex; justify-content: space-between; align-items: center; padding: var(--autops-space-md) 16px; border-bottom: 1px solid var(--autops-bg-3); }
.ep-title { font-weight: 600; color: var(--autops-text-1); }
.ep-body { padding: var(--autops-space-md) 16px; max-height: 500px; overflow-y: auto; }
.ep-group { margin-bottom: var(--autops-space-md); }
.ep-group-title { font-size: var(--autops-font-13); font-weight: 600; color: var(--autops-info); margin-bottom: var(--autops-space-sm); padding-left: 8px; border-left: 3px solid var(--autops-primary); }
.ep-item { padding: var(--autops-space-sm) 12px; border: 1px solid var(--autops-bg-3); border-radius: 6px; margin-bottom: 6px; }
.ep-item-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
.ep-time { font-size: var(--autops-font-12); color: var(--autops-text-4); }
.ep-summary { font-size: var(--autops-font-13); color: var(--autops-text-1); }
.ep-detail { font-size: var(--autops-font-12); color: var(--autops-primary); cursor: pointer; margin-top: 4px; white-space: pre-wrap; background: var(--autops-bg-2); padding: 6px 8px; border-radius: var(--autops-radius-sm); max-height: 200px; overflow-y: auto; }
</style>
