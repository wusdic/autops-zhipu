<template>
  <el-container class="main-layout">
    <el-aside :width="isCollapsed ? '64px' : '220px'" class="sidebar">
      <div class="logo" @click="$router.push('/')" style="cursor:pointer">
        <h2 v-if="!isCollapsed">AUTOPS</h2>
        <span v-else style="font-size:20px;color:#fff;font-weight:bold">A</span>
        <div v-if="!isCollapsed" class="subtitle">自治运维操作系统</div>
      </div>
      <el-menu :default-active="$route.path" router class="sidebar-menu" :collapse="isCollapsed" background-color="#304156" text-color="#bfcbd9" active-text-color="#409eff">
        <el-menu-item-group v-if="!isCollapsed" title="指挥中心">
          <el-menu-item index="/"><el-icon><Monitor /></el-icon><span>运维指挥台</span></el-menu-item>
          <el-menu-item index="/incident"><el-icon><Warning /></el-icon><span>故障处置</span></el-menu-item>
          <el-menu-item index="/aiops"><el-icon><MagicStick /></el-icon><span>AI 诊断</span></el-menu-item>
        </el-menu-item-group>
        <el-menu-item-group v-if="!isCollapsed" title="资产配置">
          <el-menu-item index="/assets"><el-icon><Grid /></el-icon><span>资产管理</span></el-menu-item>
          <el-menu-item index="/collectors"><el-icon><Connection /></el-icon><span>采集器管理</span></el-menu-item>
          <el-menu-item index="/config"><el-icon><Setting /></el-icon><span>配置管理</span></el-menu-item>
        </el-menu-item-group>
        <el-menu-item-group v-if="!isCollapsed" title="监控事件">
          <el-menu-item index="/events"><el-icon><InfoFilled /></el-icon><span>事件列表</span></el-menu-item>
          <el-menu-item index="/alerts"><el-icon><Bell /></el-icon><span>告警中心</span></el-menu-item>
          <el-menu-item index="/tickets"><el-icon><Tickets /></el-icon><span>工单中心</span></el-menu-item>
        </el-menu-item-group>
        <el-menu-item-group v-if="!isCollapsed" title="自动化">
          <el-menu-item index="/automation"><el-icon><VideoPlay /></el-icon><span>自动化编排</span></el-menu-item>
          <el-menu-item index="/knowledge"><el-icon><Collection /></el-icon><span>知识库</span></el-menu-item>
        </el-menu-item-group>
        <el-menu-item-group v-if="!isCollapsed" title="管理">
          <el-menu-item index="/admin/users"><el-icon><User /></el-icon><span>用户管理</span></el-menu-item>
          <el-menu-item index="/audit"><el-icon><Document /></el-icon><span>审计日志</span></el-menu-item>
        </el-menu-item-group>
        <!-- Collapsed mode -->
        <template v-if="isCollapsed">
          <el-menu-item index="/"><el-icon><Monitor /></el-icon></el-menu-item>
          <el-menu-item index="/incident"><el-icon><Warning /></el-icon></el-menu-item>
          <el-menu-item index="/assets"><el-icon><Grid /></el-icon></el-menu-item>
          <el-menu-item index="/alerts"><el-icon><Bell /></el-icon></el-menu-item>
          <el-menu-item index="/automation"><el-icon><VideoPlay /></el-icon></el-menu-item>
          <el-menu-item index="/audit"><el-icon><Document /></el-icon></el-menu-item>
          <el-menu-item index="/admin/users"><el-icon><User /></el-icon></el-menu-item>
        </template>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        <div class="header-left">
          <el-icon class="collapse-btn" @click="isCollapsed = !isCollapsed" :size="20">
            <component :is="isCollapsed ? 'Expand' : 'Fold'" />
          </el-icon>
          <span class="page-title">{{ pageTitle }}</span>
        </div>
        <div class="header-right">
          <el-badge :value="alertCount" :max="99" class="alert-badge" :hidden="alertCount === 0">
            <el-icon :size="20" @click="$router.push('/alerts')" style="cursor:pointer"><Bell /></el-icon>
          </el-badge>
          <el-dropdown>
            <span class="user-info">
              <el-avatar :size="28" icon="UserFilled" />
              <span style="margin-left:8px">{{ username }}</span>
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
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Monitor, Grid, Bell, Tickets, Collection, Setting, Warning, Connection,
  InfoFilled, VideoPlay, MagicStick, User, Document, Expand, Fold } from '@element-plus/icons-vue'
import api from '@/shared/api/client'
import { API as R } from '@/shared/api/routes'
import { useAuthStore } from '@/app/store/auth'
import { clearToken } from '@/app/router/guards'

const router = useRouter()
const route = useRoute()
const isCollapsed = ref(false)
const alertCount = ref(0)
const username = ref(localStorage.getItem('username') || 'admin')

const pageTitle = computed(() => {
  const map: Record<string, string> = {
    '/': '运维指挥台', '/assets': '资产管理', '/config': '配置管理', '/collectors': '采集器管理',
    '/events': '事件列表', '/alerts': '告警中心', '/tickets': '工单中心',
    '/incident': '故障处置', '/automation': '自动化编排', '/aiops': 'AI 诊断',
    '/knowledge': '知识库', '/audit': '审计日志', '/admin/users': '用户管理',
  }
  return map[route.path] || ''
})

async function loadAlertCount() {
  try {
    const { data } = await api.get(R.ALERTS, { params: { page: 1, page_size: 1, status: 'firing' } })
    if (data.code === 0) alertCount.value = data.data.total || 0
  } catch { /* ignore */ }
}

async function logout() {
  try {
    await api.post(R.AUTH.LOGOUT)
  } catch { /* ignore */ }
  const authStore = useAuthStore()
  authStore.clearAuth()
  clearToken()
  localStorage.removeItem('username')
  router.push('/login')
}

onMounted(() => loadAlertCount())
</script>

<style scoped>
.main-layout { height: 100vh; }
.sidebar { background: #304156; overflow-y: auto; transition: width 0.3s; }
.sidebar::-webkit-scrollbar { width: 0; }
.logo { padding: 20px 16px; text-align: center; color: #fff; min-height: 60px; }
.logo h2 { margin: 0; font-size: 24px; }
.logo .subtitle { font-size: 12px; color: #bfcbd9; margin-top: 4px; }
.sidebar-menu { border-right: none; }
.sidebar-menu .el-menu-item { background-color: #304156 !important; }
.sidebar-menu .el-menu-item:hover { background-color: #263445 !important; }
.sidebar-menu .el-menu-item.is-active { background-color: #263445 !important; }
.header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #e6e6e6; background: #fff; padding: 0 20px; height: 56px; }
.header-left { display: flex; align-items: center; gap: 12px; }
.collapse-btn { cursor: pointer; color: #606266; }
.collapse-btn:hover { color: #409eff; }
.page-title { font-size: 16px; font-weight: 600; color: #303133; }
.header-right { display: flex; align-items: center; gap: 20px; }
.user-info { display: flex; align-items: center; cursor: pointer; }
.alert-badge { margin-right: 8px; }
.main-content { background: #f0f2f5; min-height: calc(100vh - 56px); overflow-y: auto; }
</style>
