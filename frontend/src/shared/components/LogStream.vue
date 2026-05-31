<template>
  <div class="log-stream" :style="{ height: height, overflow: 'auto', background: '#1e1e1e', color: '#d4d4d4', padding: '12px', borderRadius: '6px', fontFamily: 'monospace', fontSize: '13px', lineHeight: '1.6' }">
    <div v-for="(line, idx) in lines" :key="idx" :class="getLineClass(line)">
      <span class="line-number" :style="{ color: '#666', marginRight: '12px' }">{{ idx + 1 }}</span>
      <span :style="{ color: getLineColor(line) }">{{ line }}</span>
    </div>
    <div v-if="!lines.length" :style="{ color: '#666', textAlign: 'center', padding: '20px' }">等待日志输出...</div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ lines: string[]; height?: string }>()

function getLineClass(line: string): string {
  if (line.toLowerCase().includes('error')) return 'log-error'
  if (line.toLowerCase().includes('warning') || line.toLowerCase().includes('warn')) return 'log-warn'
  return ''
}

function getLineColor(line: string): string {
  if (line.toLowerCase().includes('error')) return '#f44747'
  if (line.toLowerCase().includes('warning') || line.toLowerCase().includes('warn')) return '#cca700'
  if (line.toLowerCase().includes('success') || line.toLowerCase().includes('ok')) return '#6a9955'
  return '#d4d4d4'
}
</script>
