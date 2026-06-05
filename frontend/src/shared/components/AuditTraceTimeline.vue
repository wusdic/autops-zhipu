<template>
  <div class="audit-trace-timeline">
    <el-timeline v-if="events.length">
      <el-timeline-item v-for="(evt, idx) in events" :key="idx"
        :timestamp="evt.time" :type="(eventType(evt)) as TagType" placement="top">
        <div class="trace-event">
          <span class="trace-user">{{ evt.user || "系统" }}</span>
          <span class="trace-action">{{ evt.action }}</span>
          <span class="trace-resource" v-if="evt.resource">{{ evt.resource }}</span>
          <div class="trace-detail" v-if="evt.detail">{{ evt.detail }}</div>
        </div>
      </el-timeline-item>
    </el-timeline>
    <el-empty v-else description="暂无追踪记录" :image-size="60" />
  </div>
</template>

<script setup lang="ts">
import type { TagType } from '@/shared/types'
defineProps<{ events: { time: string; user?: string; action: string; resource?: string; detail?: string; type?: string }[] }>()

function eventType(evt: any): TagType {
  if (evt.type) return (evt.type) as TagType
  const map: Record<string, TagType> = { create: "success", update: "primary", delete: "danger", login: "warning" }
  return (map[evt.action] ?? "info") as TagType
}
</script>

<style scoped>
.audit-trace-timeline { padding: var(--autops-space-sm) 0; }
.trace-event { font-size: var(--autops-font-13); }
.trace-user { font-weight: 600; color: var(--autops-primary); margin-right: 6px; }
.trace-action { color: var(--autops-text-1); margin-right: 6px; }
.trace-resource { color: var(--autops-info); }
.trace-detail { color: var(--autops-info); font-size: var(--autops-font-12); margin-top: 4px; padding: var(--autops-space-xs) 8px; background: var(--autops-bg-2); border-radius: var(--autops-radius-sm); }
</style>
