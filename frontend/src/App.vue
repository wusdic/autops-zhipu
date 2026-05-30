<template>
  <router-view v-if="isLoginPage" />
  <MainLayout v-else />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import MainLayout from '@/app/layout/MainLayout.vue'

const route = useRoute()
const isLoginPage = computed(() => route.path === '/login' || route.name === 'login')
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
