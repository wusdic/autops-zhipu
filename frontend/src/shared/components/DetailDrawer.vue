<template>
  <el-drawer v-model="visible" :title="title" :size="size" :direction="direction" :before-close="handleClose" destroy-on-close>
    <div class="detail-drawer-body">
      <slot />
    </div>
    <template #footer v-if="$slots.footer">
      <slot name="footer" />
    </template>
  </el-drawer>
</template>

<script setup lang="ts">
const props = withDefaults(defineProps<{
  modelValue: boolean
  title?: string
  size?: string | number
  direction?: "rtl" | "ltr" | "ttb" | "btt"
}>(), { title: "详情", size: "600px", direction: "rtl" })

const emit = defineEmits<{ "update:modelValue": [v: boolean] }>()
const visible = computed({ get: () => props.modelValue, set: v => emit("update:modelValue", v) })

import { computed } from "vue"
function handleClose(done: () => void) { done() }
</script>

<style scoped>
.detail-drawer-body { padding: 0 4px; }
.detail-drawer-body :deep(.el-descriptions) { margin-bottom: 16px; }
</style>
