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
.evidence-panel { border: 1px solid #e5e6eb; border-radius: 8px; background: #fff; }
.ep-header { display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; border-bottom: 1px solid #f2f3f5; }
.ep-title { font-weight: 600; color: #1d2129; }
.ep-body { padding: 12px 16px; max-height: 500px; overflow-y: auto; }
.ep-group { margin-bottom: 12px; }
.ep-group-title { font-size: 13px; font-weight: 600; color: #86909c; margin-bottom: 8px; padding-left: 8px; border-left: 3px solid #165dff; }
.ep-item { padding: 8px 12px; border: 1px solid #f2f3f5; border-radius: 6px; margin-bottom: 6px; }
.ep-item-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
.ep-time { font-size: 12px; color: #c9cdd4; }
.ep-summary { font-size: 13px; color: #1d2129; }
.ep-detail { font-size: 12px; color: #165dff; cursor: pointer; margin-top: 4px; white-space: pre-wrap; background: #f7f8fa; padding: 6px 8px; border-radius: 4px; max-height: 200px; overflow-y: auto; }
</style>
