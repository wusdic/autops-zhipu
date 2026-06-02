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
  padding: 12px 16px; background: #fff; border-radius: 8px;
  border: 1px solid #e5e6eb; margin-bottom: 16px;
}
.filter-bar :deep(.el-form-item) { margin-bottom: 0; }
</style>
