<template>
  <div class="config-diff">
    <div :style="{ display: 'flex', gap: '16px' }">
      <div :style="{ flex: 1 }">
        <div :style="{ fontWeight: 600, marginBottom: '8px' }">{{ oldLabel || '旧版本' }}</div>
        <pre :style="{ background: '#fef0f0', padding: '12px', borderRadius: '6px', fontSize: '13px', whiteSpace: 'pre-wrap' }">{{ typeof oldValue === 'string' ? oldValue : JSON.stringify(oldValue, null, 2) }}</pre>
      </div>
      <div :style="{ flex: 1 }">
        <div :style="{ fontWeight: 600, marginBottom: '8px' }">{{ newLabel || '新版本' }}</div>
        <pre :style="{ background: '#f0f9eb', padding: '12px', borderRadius: '6px', fontSize: '13px', whiteSpace: 'pre-wrap' }">{{ typeof newValue === 'string' ? newValue : JSON.stringify(newValue, null, 2) }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ oldValue: any; newValue: any; oldLabel?: string; newLabel?: string }>()
</script>
