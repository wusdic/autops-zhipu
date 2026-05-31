<template>
  <el-container class="main-layout">
    <el-aside :width="isCollapsed ? '64px' : '220px'" class="sidebar">
      <div class="logo" @click="$router.push('/')" style="cursor:pointer">
        <h2 v-if="!isCollapsed">AUTOPS</h2>
        <span v-else style="font-size:20px;color:#fff;font-weight:bold">A</span>
        <div v-if="!isCollapsed" class="subtitle">自治运维操作系统</div>
      </div>
      <el-menu :default-active="activeMenu" router class="sidebar-menu" :collapse="isCollapsed" background-color="#304156" text-color="#bfcbd9" active-text-color="#409eff">
        <!-- 指挥中心 -->
        <el-sub-menu v-if="!isCollapsed" index="cmd">
          <template #title><el-icon><Monitor /></el-icon><span>指挥中心</span></template>
          <el-menu-item index="/"><span>运维指挥台</span></el-menu-item>
          <el-menu-item index="/incident"><span>故障处置</span></el-menu-item>
          <el-menu-item index="/aiops"><span>AI 诊断</span></el-menu-item>
        </el-sub-menu>
        <!-- 资产配置 -->
        <el-sub-menu v-if="!isCollapsed" index="asset">
          <template #title><el-icon><Grid /></el-icon><span>资产配置</span></template>
          <el-menu-item index="/assets"><span>资产列表</span></el-menu-item>
          <el-menu-item index="/assets/discovery"><span>资产发现</span></el-menu-item>
          <el-menu-item index="/asset-groups"><span>资产分组</span></el-menu-item>
          <el-menu-item index="/credentials"><span>凭证管理</span></el-menu-item>
          <el-menu-item index="/config"><span>配置管理</span></el-menu-item>
          <el-menu-item index="/collectors"><span>采集器管理</span></el-menu-item>
        </el-sub-menu>
        <!-- 监控事件 -->
        <el-sub-menu v-if="!isCollapsed" index="monitor">
          <template #title><el-icon><Bell /></el-icon><span>监控事件</span></template>
          <el-menu-item index="/monitoring"><span>监控总览</span></el-menu-item>
          <el-menu-item index="/events"><span>事件列表</span></el-menu-item>
          <el-menu-item index="/alerts"><span>告警中心</span></el-menu-item>
          <el-menu-item index="/alert-rules"><span>告警规则</span></el-menu-item>
          <el-menu-item index="/tickets"><span>工单中心</span></el-menu-item>
        </el-sub-menu>
        <!-- 自动化 -->
        <el-sub-menu v-if="!isCollapsed" index="auto">
          <template #title><el-icon><VideoPlay /></el-icon><span>自动化</span></template>
          <el-menu-item index="/scripts"><span>脚本库</span></el-menu-item>
          <el-menu-item index="/playbooks"><span>Playbook</span></el-menu-item>
          <el-menu-item index="/policies"><span>策略管理</span></el-menu-item>
          <el-menu-item index="/executions"><span>执行历史</span></el-menu-item>
        </el-sub-menu>
        <!-- 知识 -->
        <el-sub-menu v-if="!isCollapsed" index="kb">
          <template #title><el-icon><Collection /></el-icon><span>知识</span></template>
          <el-menu-item index="/knowledge"><span>知识库</span></el-menu-item>
          <el-menu-item index="/knowledge/import"><span>知识导入</span></el-menu-item>
        </el-sub-menu>
        <!-- 管理 -->
        <el-sub-menu v-if="!isCollapsed" index="admin">
          <template #title><el-icon><User /></el-icon><span>平台管理</span></template>
          <el-menu-item index="/admin/users"><span>用户管理</span></el-menu-item>
          <el-menu-item index="/admin/roles"><span>角色管理</span></el-menu-item>
          <el-menu-item index="/admin/api-keys"><span>API Key</span></el-menu-item>
          <el-menu-item index="/admin/config"><span>系统配置</span></el-menu-item>
          <el-menu-item index="/admin/status"><span>平台状态</span></el-menu-item>
          <el-menu-item index="/admin/backup"><span>备份恢复</span></el-menu-item>
          <el-menu-item index="/audit"><span>审计日志</span></el-menu-item>
        </el-sub-menu>
        <!-- Collapsed mode -->
        <template v-if="isCollapsed">
          <el-menu-item index="/"><el-icon><Monitor /></el-icon></el-menu-item>
          <el-menu-item index="/incident"><el-icon><Warning /></el-icon></el-menu-item>
          <el-menu-item index="/assets"><el-icon><Grid /></el-icon></el-menu-item>
          <el-menu-item index="/monitoring"><el-icon><DataLine /></el-icon></el-menu-item>
          <el-menu-item index="/alerts"><el-icon><Bell /></el-icon></el-menu-item>
          <el-menu-item index="/scripts"><el-icon><VideoPlay /></el-icon></el-menu-item>
          <el-menu-item index="/knowledge"><el-icon><Collection /></el-icon></el-menu-item>
          <el-menu-item index="/admin/users"><el-icon><User /></el-icon></el-menu-item>
          <el-menu-item index="/audit"><el-icon><Document /></el-icon></el-menu-item>
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
          <!-- Global Search -->
          <el-input
            v-model="searchQuery"
            placeholder="搜索资产/告警/工单/知识... (Ctrl+K)"
            style="width: 280px"
            clearable
            @keyup.enter="doSearch"
            @focus="showSearchResults = true"
            @blur="hideSearchResults"
            :prefix-icon="Search"
            size="default"
          >
            <template #append>
              <el-button @click="doSearch" :icon="Search" />
            </template>
          </el-input>
          <!-- Search Results Dropdown -->
          <div v-if="showSearchResults && searchResults.length" class="search-dropdown">
            <div v-for="item in searchResults" :key="item.type + item.id"
              class="search-item" @mousedown.prevent="goSearchResult(item)">
              <el-tag size="small" :type="searchTagType(item.type)" style="width:50px;text-align:center">{{ item.typeLabel }}</el-tag>
              <span class="search-item-title">{{ item.title }}</span>
              <span class="search-item-sub">{{ item.sub || '' }}</span>
            </div>
            <div v-if="searchResults.length === 0" class="search-empty">无结果</div>
          </div>

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
                <el-dropdown-item @click="$router.push('/admin/config')">系统设置</el-dropdown-item>
                <el-dropdown-item divided @click="logout">退出登录</el-dropdown-item>
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
  InfoFilled, VideoPlay, MagicStick, User, Document, Expand, Fold, DataLine, Search } from '@element-plus/icons-vue'
import api from '@/shared/api/client'
import { API as R } from '@/shared/api/routes'
import { useAuthStore } from '@/app/store/auth'
import { clearToken } from '@/app/router/guards'

const router = useRouter()
const route = useRoute()
const isCollapsed = ref(false)
const alertCount = ref(0)
const username = ref(localStorage.getItem('username') || 'admin')

// ─── Global Search ───
const searchQuery = ref('')
const showSearchResults = ref(false)
const searchResults = ref<Array<{type: string; typeLabel: string; id: string; title: string; sub?: string; path: string}>>([])

function searchTagType(type: string) {
  const m: Record<string, string> = { asset: '', alert: 'danger', ticket: 'warning', knowledge: 'success' }
  return (m[type] || 'info') as any
}

async function doSearch() {
  const q = searchQuery.value.trim()
  if (!q) { searchResults.value = []; return }
  showSearchResults.value = true
  const results: typeof searchResults.value = []
  try {
    // Search assets
    const { data: aData } = await api.get(R.ASSETS, { params: { search: q, page_size: 5 } })
    if (aData.code === 0) {
      (aData.data.items || []).forEach((a: any) => results.push({ type: 'asset', typeLabel: '资产', id: a.id, title: a.name || a.hostname, sub: a.ip, path: `/assets/${a.id}` }))
    }
  } catch {}
  try {
    // Search alerts
    const { data: alData } = await api.get(R.ALERTS, { params: { search: q, page_size: 5 } })
    if (alData.code === 0) {
      (alData.data.items || []).forEach((a: any) => results.push({ type: 'alert', typeLabel: '告警', id: a.id, title: a.title, sub: a.severity, path: `/alerts/${a.id}` }))
    }
  } catch {}
  try {
    // Search tickets
    const { data: tData } = await api.get(R.TICKETS, { params: { search: q, page_size: 5 } })
    if (tData.code === 0) {
      (tData.data.items || []).forEach((t: any) => results.push({ type: 'ticket', typeLabel: '工单', id: t.id, title: t.title, sub: t.status, path: `/tickets/${t.id}` }))
    }
  } catch {}
  searchResults.value = results.slice(0, 10)
}

function goSearchResult(item: typeof searchResults.value[0]) {
  showSearchResults.value = false
  searchQuery.value = ''
  router.push(item.path)
}

function hideSearchResults() {
  setTimeout(() => { showSearchResults.value = false }, 200)
}

// Ctrl+K shortcut
function handleKeydown(e: KeyboardEvent) {
  if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
    e.preventDefault()
    const input = document.querySelector('.header-right .el-input__inner') as HTMLInputElement
    input?.focus()
  }
}

// Active menu: use base path for dynamic routes
const activeMenu = computed(() => {
  const path = route.path
  // For dynamic routes, match the base path
  if (path.startsWith('/assets/') && path !== '/assets/discovery') return '/assets'
  if (path.startsWith('/alerts/')) return '/alerts'
  if (path.startsWith('/incident/')) return '/incident'
  if (path.startsWith('/policies/')) return '/policies'
  if (path.startsWith('/executions/')) return '/executions'
  if (path.startsWith('/knowledge/')) return '/knowledge'
  return path
})

const pageTitle = computed(() => {
  const map: Record<string, string> = {
    '/': '运维指挥台',
    '/assets': '资产列表', '/assets/discovery': '资产发现', '/asset-groups': '资产分组', '/credentials': '凭证管理',
    '/config': '配置管理', '/collectors': '采集器管理',
    '/monitoring': '监控总览', '/events': '事件列表', '/alerts': '告警中心',
    '/alert-rules': '告警规则', '/tickets': '工单中心',
    '/incident': '故障处置', '/aiops': 'AI 诊断',
    '/scripts': '脚本库', '/playbooks': 'Playbook', '/policies': '策略管理',
    '/executions': '执行历史', '/automation': '自动化编排',
    '/knowledge': '知识库', '/knowledge/import': '知识导入',
    '/admin/users': '用户管理', '/admin/roles': '角色管理',
    '/admin/api-keys': 'API Key', '/admin/config': '系统配置',
    '/admin/status': '平台状态', '/admin/backup': '备份恢复',
    '/audit': '审计日志',
  }
  // For dynamic routes, show parent title + context
  if (route.path.match(/^\/assets\/.+\/topology/)) return '资产拓扑图'
  if (route.path.match(/^\/assets\/.+/) && !route.path.endsWith('/discovery')) return '资产详情'
  if (route.path.match(/^\/alerts\/.+/)) return '告警详情'
  if (route.path.match(/^\/incident\/.+/)) return '故障处置'
  if (route.path.match(/^\/tickets\/.+/)) return '工单详情'
  if (route.path.match(/^\/policies\/.+\/simulate/)) return '策略模拟'
  if (route.path.match(/^\/executions\/.+/)) return '执行详情'
  if (route.path.match(/^\/knowledge\/.+\/edit/)) return '知识编辑'
  if (route.path.match(/^\/knowledge\/.+/) && !route.path.endsWith('/import')) return '知识详情'
  return map[route.path] || 'AUTOPS'
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

onMounted(() => {
  loadAlertCount()
  window.addEventListener('keydown', handleKeydown)
})
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
.sidebar-menu .el-sub-menu__title { background-color: #304156 !important; }
.sidebar-menu .el-sub-menu__title:hover { background-color: #263445 !important; }
.header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #e6e6e6; background: #fff; padding: 0 20px; height: 56px; }
.header-left { display: flex; align-items: center; gap: 12px; }
.collapse-btn { cursor: pointer; color: #606266; }
.collapse-btn:hover { color: #409eff; }
.page-title { font-size: 16px; font-weight: 600; color: #303133; }
.header-right { display: flex; align-items: center; gap: 12px; position: relative; }
.user-info { display: flex; align-items: center; cursor: pointer; }
.alert-badge { margin-right: 4px; }
.search-dropdown {
  position: absolute; top: 40px; right: 200px; width: 400px;
  background: #fff; border: 1px solid #dcdfe6; border-radius: 4px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15); z-index: 999; max-height: 320px; overflow-y: auto;
}
.search-item { display: flex; align-items: center; gap: 8px; padding: 10px 12px; cursor: pointer; border-bottom: 1px solid #f0f0f0; }
.search-item:hover { background: #f5f7fa; }
.search-item-title { flex: 1; font-size: 13px; color: #303133; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.search-item-sub { font-size: 12px; color: #909399; }
.search-empty { padding: 20px; text-align: center; color: #909399; }
.main-content { background: #f0f2f5; min-height: calc(100vh - 56px); overflow-y: auto; }
</style>
