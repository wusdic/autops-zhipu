<template>
  <div class="filter-bar">
    <el-form :inline="true" @submit.prevent="$emit('search')">
      <slot />
      <el-form-item>
        <el-button type="primary" @click="$emit('search')">
          <el-icon><Search /></el-icon> 查询
        </el-button>
        <el-button @click="$emit('reset')">重置</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { Search } from "@element-plus/icons-vue"
defineEmits<{ search: []; reset: [] }>()
</script>

<style scoped>
.filter-bar {
  padding: var(--autops-space-md) 16px; background: var(--autops-bg-1); border-radius: var(--autops-radius-md);
  border: 1px solid var(--autops-bg-4); margin-bottom: var(--autops-space-lg);
}
.filter-bar :deep(.el-form-item) { margin-bottom: 0; }
</style>
