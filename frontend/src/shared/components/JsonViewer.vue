<template>
  <div class="json-viewer">
    <div class="toolbar">
      <el-button size="small" @click="copyJson">复制</el-button>
      <el-button size="small" @click="expanded = !expanded">{{ expanded ? '收起' : '展开' }}</el-button>
    </div>
    <pre :style="{ background: '#f7f8fa', padding: '12px', borderRadius: '6px', fontSize: '13px', maxHeight: expanded ? 'none' : '400px', overflow: 'auto' }">{{ formattedJson }}</pre>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'

const props = defineProps<{ data: any }>()
const expanded = ref(false)

const formattedJson = computed(() => JSON.stringify(props.data, null, 2))

function copyJson() {
  navigator.clipboard.writeText(formattedJson.value).then(() => ElMessage.success('已复制'))
}
</script>
