<template>
  <div class="log-stream">
    <div class="log-stream__toolbar" v-if="showToolbar">
      <el-button size="small" :plain="!autoScroll" :type="autoScroll ? 'primary' : 'default'" @click="autoScroll = !autoScroll">
        {{ autoScroll ? '自动滚动: 开' : '自动滚动: 关' }}
      </el-button>
      <el-button size="small" plain @click="clearLogs">清空</el-button>
      <span class="log-stream__count">{{ logs.length }} 行</span>
    </div>
    <div class="log-stream__content" ref="contentRef">
      <div v-if="logs.length === 0" class="log-stream__empty">暂无日志</div>
      <div v-for="(log, idx) in logs" :key="idx" :class="['log-stream__line', 'log-stream__line--' + log.level]">
        <span class="log-stream__time">{{ log.time }}</span>
        <span :class="['log-stream__level', 'log-stream__level--' + log.level]">{{ levelText(log.level) }}</span>
        <span class="log-stream__msg">{{ log.message }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, onBeforeUnmount } from 'vue'

export interface LogEntry {
  time: string
  level: 'info' | 'warn' | 'error' | 'debug'
  message: string
}

const props = withDefaults(defineProps<{
  logs?: LogEntry[]
  showToolbar?: boolean
  maxLines?: number
}>(), {
  logs: () => [],
  showToolbar: true,
  maxLines: 1000,
})

const emit = defineEmits<{
  clear: []
}>()

const contentRef = ref<HTMLElement | null>(null)
const autoScroll = ref(true)

function levelText(level: string) {
  const map: Record<string, string> = { info: 'INFO', warn: 'WARN', error: 'ERR', debug: 'DBG' }
  return map[level] || level.toUpperCase()
}

function clearLogs() {
  emit('clear')
}

function scrollToBottom() {
  if (autoScroll.value && contentRef.value) {
    contentRef.value.scrollTop = contentRef.value.scrollHeight
  }
}

watch(() => props.logs, () => {
  nextTick(scrollToBottom)
}, { deep: true })

onBeforeUnmount(() => {
  // cleanup
})
</script>

<style scoped>
.log-stream {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 200px;
}

.log-stream__toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: var(--autops-space-sm) 12px;
  background: var(--autops-bg-2);
  border-bottom: 1px solid var(--autops-bg-4);
}

.log-stream__count {
  margin-left: auto;
  font-size: var(--autops-font-12);
  color: var(--autops-info);
}

.log-stream__content {
  flex: 1;
  overflow-y: auto;
  padding: var(--autops-space-sm) 12px;
  font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
  font-size: var(--autops-font-12);
  line-height: 1.8;
  background: var(--autops-terminal-bg);
  color: var(--autops-text-4);
}

.log-stream__empty {
  color: var(--autops-text-2);
  text-align: center;
  padding: 40px 0;
}

.log-stream__line {
  display: flex;
  gap: 8px;
}

.log-stream__time {
  color: var(--autops-info);
  white-space: nowrap;
}

.log-stream__level {
  min-width: 40px;
  font-weight: 600;
  white-space: nowrap;
}

.log-stream__level--info { color: var(--autops-success); }
.log-stream__level--warn { color: var(--autops-gold); }
.log-stream__level--error { color: var(--autops-danger); }
.log-stream__level--debug { color: var(--autops-info); }

.log-stream__msg {
  word-break: break-all;
}

.log-stream__line--error {
  background: rgba(255, 77, 79, 0.08);
}
.log-stream__line--warn {
  background: rgba(250, 173, 20, 0.05);
}
</style>
