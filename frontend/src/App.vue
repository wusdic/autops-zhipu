<template>
  <!-- 公开页 / 未登录：只渲染路由视图，不挂 MainLayout，避免其子组件在无 token 时调 API 触发 401 -->
  <router-view v-if="isPublicPage || !isAuthenticated" />
  <MainLayout v-else />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/app/store/auth'
import MainLayout from '@/app/layout/MainLayout.vue'

const route = useRoute()
const authStore = useAuthStore()

const PUBLIC_PATHS = ['/login', '/forbidden', '/session-expired']
const isPublicPage = computed(
  () => PUBLIC_PATHS.includes(route.path) || route.name === 'login'
)
const isAuthenticated = computed(() => !!authStore.token)
</script>

<style>
body {
  margin: 0;
  padding: 0;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
}
#app {
  width: 100%;
  height: 100vh;
}
</style>
