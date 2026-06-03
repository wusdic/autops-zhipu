<template>
  <div class="flex items-center justify-center min-h-screen bg-gray-50">
    <div class="text-center">
      <el-icon :size="80" color="#f53f3f"><WarningFilled /></el-icon>
      <h1 class="mt-4 text-2xl font-bold text-gray-800">访问受限</h1>
      <p class="mt-2 text-gray-500">您没有权限访问此页面，请联系管理员</p>
      <el-button type="primary" class="mt-6" @click="$router.push('/')">返回首页</el-button>
    </div>
  </div>
</template>
<script setup lang="ts">
import { WarningFilled } from '@element-plus/icons-vue'
</script>