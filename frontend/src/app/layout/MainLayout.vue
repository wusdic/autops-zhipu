<template>
  <el-container class="main-layout">
    <el-aside :width="isCollapsed ? '64px' : '220px'" class="sidebar">
      <div class="logo">
        <h1 v-if="!isCollapsed">AUTOPS</h1>
        <span v-else>A</span>
      </div>
      <el-menu
        :default-active="currentRoute"
        :collapse="isCollapsed"
        router
        background-color="#1a1a2e"
        text-color="#b0b0b0"
        active-text-color="#409eff"
      >
        <el-menu-item index="/command-center">
          <el-icon><Monitor /></el-icon>
          <template #title>运维指挥台</template>
        </el-menu-item>
        <el-menu-item index="/assets">
          <el-icon><Box /></el-icon>
          <template #title>资产管理</template>
        </el-menu-item>
        <el-menu-item index="/alerts">
          <el-icon><Bell /></el-icon>
          <template #title>告警管理</template>
        </el-menu-item>
        <el-menu-item index="/admin/users">
          <el-icon><User /></el-icon>
          <template #title>用户管理</template>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        <el-icon class="collapse-btn" @click="isCollapsed = !isCollapsed">
          <Fold v-if="!isCollapsed" /><Expand v-else />
        </el-icon>
        <div class="header-right">
          <el-dropdown>
            <span class="user-info">
              <el-icon><UserFilled /></el-icon>
              admin
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="handleLogout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/app/store/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const isCollapsed = ref(false)
const currentRoute = computed(() => route.path)

function handleLogout() {
  authStore.clearAuth()
  router.push('/login')
}
</script>

<style scoped>
.main-layout {
  height: 100vh;
}
.sidebar {
  background: #1a1a2e;
  transition: width 0.3s;
  overflow: hidden;
}
.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #409eff;
  font-size: 20px;
  border-bottom: 1px solid #2a2a3e;
}
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #e4e7ed;
  background: #fff;
}
.collapse-btn {
  cursor: pointer;
  font-size: 20px;
}
.header-right {
  display: flex;
  align-items: center;
}
.user-info {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
}
.main-content {
  background: #f5f7fa;
}
</style>
