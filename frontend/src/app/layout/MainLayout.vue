<template>
  <el-container class="main-layout">
    <el-aside width="220px" class="sidebar">
      <div class="logo">
        <h2>AUTOPS</h2>
        <div class="subtitle">自治运维操作系统</div>
      </div>
      <el-menu :default-active="$route.path" router class="sidebar-menu">
        <el-menu-item index="/dashboard">
          <el-icon><Monitor /></el-icon>
          <span>运维指挥台</span>
        </el-menu-item>
        <el-menu-item index="/assets">
          <el-icon><Grid /></el-icon>
          <span>资产管理</span>
        </el-menu-item>
        <el-menu-item index="/alerts">
          <el-icon><Bell /></el-icon>
          <span>告警中心</span>
        </el-menu-item>
        <el-menu-item index="/tickets">
          <el-icon><Tickets /></el-icon>
          <span>工单中心</span>
        </el-menu-item>
        <el-menu-item index="/knowledge">
          <el-icon><Collection /></el-icon>
          <span>知识库</span>
        </el-menu-item>
        <el-menu-item index="/admin">
          <el-icon><Setting /></el-icon>
          <span>平台管理</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        <div class="header-left">
          <span class="page-title">{{ $route.meta.title || '' }}</span>
        </div>
        <div class="header-right">
          <el-dropdown>
            <span class="user-info">
              <el-avatar :size="28" icon="UserFilled" />
              <span style="margin-left:8px">admin</span>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="logout">退出登录</el-dropdown-item>
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
import { useRouter } from 'vue-router'
import { Monitor, Grid, Bell, Tickets, Collection, Setting } from '@element-plus/icons-vue'

const router = useRouter()

function logout() {
  localStorage.removeItem('token')
  router.push('/login')
}
</script>

<style scoped>
.main-layout { height: 100vh; }
.sidebar { background: #304156; overflow-y: auto; }
.logo { padding: 20px 16px; text-align: center; color: #fff; }
.logo h2 { margin: 0; font-size: 24px; }
.logo .subtitle { font-size: 12px; color: #bfcbd9; margin-top: 4px; }
.sidebar-menu { border-right: none; }
.header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #e6e6e6; background: #fff; }
.page-title { font-size: 16px; font-weight: 600; color: #303133; }
.user-info { display: flex; align-items: center; cursor: pointer; }
.main-content { background: #f0f2f5; min-height: calc(100vh - 60px); }
</style>
