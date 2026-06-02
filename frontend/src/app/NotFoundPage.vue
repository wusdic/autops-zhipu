<template>
  <div class="flex items-center justify-center min-h-screen bg-gray-50">
    <div class="text-center">
      <h1 class="text-6xl font-bold text-gray-300">404</h1>
      <p class="mt-4 text-lg text-gray-500">页面未找到</p>
      <el-button type="primary" class="mt-6" @click="$router.push('/')">返回首页</el-button>
    </div>
  </div>
</template>