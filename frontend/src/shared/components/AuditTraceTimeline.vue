<template>
  <div class="audit-trace-timeline">
    <el-timeline v-if="events.length">
      <el-timeline-item v-for="(evt, idx) in events" :key="idx"
        :timestamp="evt.time" :type="eventType(evt)" placement="top">
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
defineProps<{ events: { time: string; user?: string; action: string; resource?: string; detail?: string; type?: string }[] }>()

function eventType(evt: any): string {
  if (evt.type) return evt.type
  const map: Record<string, string> = { create: "success", update: "primary", delete: "danger", login: "warning" }
  return map[evt.action] || "info"
}
</script>

<style scoped>
.audit-trace-timeline { padding: 8px 0; }
.trace-event { font-size: 13px; }
.trace-user { font-weight: 600; color: #165dff; margin-right: 6px; }
.trace-action { color: #1d2129; margin-right: 6px; }
.trace-resource { color: #86909c; }
.trace-detail { color: #86909c; font-size: 12px; margin-top: 4px; padding: 4px 8px; background: #f7f8fa; border-radius: 4px; }
</style>
