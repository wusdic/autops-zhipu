<template>
  <div class="flex items-center justify-center min-h-screen bg-gray-50">
    <div class="text-center">
      <el-icon :size="80" color="#ff7d00"><Clock /></el-icon>
      <h1 class="mt-4 text-2xl font-bold text-gray-800">会话已过期</h1>
      <p class="mt-2 text-gray-500">您的登录会话已过期，请重新登录</p>
      <el-button type="primary" class="mt-6" @click="reLogin">重新登录</el-button>
    </div>
  </div>
</template>
<script setup lang="ts">
import { Clock } from '@element-plus/icons-vue'
const reLogin = () => {
  const redirect = encodeURIComponent(window.location.pathname)
  window.location.href = '/login?redirect=' + redirect
}
</script>