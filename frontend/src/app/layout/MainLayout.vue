<template>
  <el-container class="layout-container">
    <!-- ─── Sidebar ─── -->
    <el-aside :width="isCollapsed ? '64px' : '200px'" class="autops-sidebar" :class="{ 'autops-sidebar--collapsed': isCollapsed }">
      <!-- Logo -->
      <div class="sidebar-logo" @click="navigateTo('/')">
        <el-icon size="22" color="#165dff"><Monitor /></el-icon>
        <span v-show="!isCollapsed" class="logo-text">AUTOPS</span>
      </div>

      <!-- Menu -->
      <el-scrollbar>
        <el-menu
          :default-active="activeMenu"
          :collapse="isCollapsed"
          :collapse-transition="false"
          :unique-opened="false"
          background-color="transparent"
          text-color="#c9cdd4"
          active-text-color="#ffffff"
          class="sidebar-menu"
          @select="handleMenuSelect"
        >
          <!-- 指挥中心 -->
          <el-sub-menu index="cmd">
            <template #title>
              <el-icon><Aim /></el-icon>
              <span>指挥中心</span>
            </template>
            <el-menu-item index="/">
              <el-icon><DataBoard /></el-icon><span>运维指挥台</span>
            </el-menu-item>
            <el-menu-item index="/incident">
              <el-icon><Warning /></el-icon><span>故障处置</span>
            </el-menu-item>
            <el-menu-item index="/aiops">
              <el-icon><MagicStick /></el-icon><span>AI 诊断</span>
            </el-menu-item>
          </el-sub-menu>

          <!-- 资产配置 -->
          <el-sub-menu index="asset">
            <template #title>
              <el-icon><Box /></el-icon>
              <span>资产配置</span>
            </template>
            <el-menu-item index="/assets">
              <el-icon><List /></el-icon><span>资产列表</span>
            </el-menu-item>
            <el-menu-item index="/assets/discovery">
              <el-icon><Search /></el-icon><span>资产发现</span>
            </el-menu-item>
            <el-menu-item index="/asset-groups">
              <el-icon><Folder /></el-icon><span>资产分组</span>
            </el-menu-item>
            <el-menu-item index="/credentials">
              <el-icon><Key /></el-icon><span>凭证管理</span>
            </el-menu-item>
            <el-menu-item index="/config">
              <el-icon><Setting /></el-icon><span>配置管理</span>
            </el-menu-item>
            <el-menu-item index="/collectors">
              <el-icon><Connection /></el-icon><span>采集器管理</span>
            </el-menu-item>
          </el-sub-menu>

          <!-- 监控事件 -->
          <el-sub-menu index="mon">
            <template #title>
              <el-icon><Monitor /></el-icon>
              <span>监控事件</span>
            </template>
            <el-menu-item index="/monitoring">
              <el-icon><TrendCharts /></el-icon><span>监控总览</span>
            </el-menu-item>
            <el-menu-item index="/events">
              <el-icon><Bell /></el-icon><span>事件列表</span>
            </el-menu-item>
            <el-menu-item index="/alerts">
              <el-icon><AlarmClock /></el-icon><span>告警中心</span>
            </el-menu-item>
            <el-menu-item index="/alert-rules">
              <el-icon><Document /></el-icon><span>告警规则</span>
            </el-menu-item>
            <el-menu-item index="/tickets">
              <el-icon><Tickets /></el-icon><span>工单中心</span>
            </el-menu-item>
          </el-sub-menu>

          <!-- 自动化 -->
          <el-sub-menu index="auto">
            <template #title>
              <el-icon><Cpu /></el-icon>
              <span>自动化</span>
            </template>
            <el-menu-item index="/scripts">
              <el-icon><Document /></el-icon><span>脚本库</span>
            </el-menu-item>
            <el-menu-item index="/playbooks">
              <el-icon><Notebook /></el-icon><span>Playbook</span>
            </el-menu-item>
            <el-menu-item index="/policies">
              <el-icon><Strategy /></el-icon><span>策略管理</span>
            </el-menu-item>
            <el-menu-item index="/executions">
              <el-icon><VideoPlay /></el-icon><span>执行历史</span>
            </el-menu-item>
          </el-sub-menu>

          <!-- 知识 -->
          <el-sub-menu index="kb">
            <template #title>
              <el-icon><Collection /></el-icon>
              <span>知识</span>
            </template>
            <el-menu-item index="/knowledge">
              <el-icon><Files /></el-icon><span>知识库</span>
            </el-menu-item>
            <el-menu-item index="/knowledge/import">
              <el-icon><Upload /></el-icon><span>知识导入</span>
            </el-menu-item>
          </el-sub-menu>

          <!-- 平台管理 -->
          <el-sub-menu index="admin">
            <template #title>
              <el-icon><Tools /></el-icon>
              <span>平台管理</span>
            </template>
            <el-menu-item index="/users">
              <el-icon><User /></el-icon><span>用户管理</span>
            </el-menu-item>
            <el-menu-item index="/roles">
              <el-icon><UserFilled /></el-icon><span>角色管理</span>
            </el-menu-item>
            <el-menu-item index="/api-keys">
              <el-icon><Lock /></el-icon><span>API Key</span>
            </el-menu-item>
            <el-menu-item index="/system-config">
              <el-icon><Setting /></el-icon><span>系统配置</span>
            </el-menu-item>
            <el-menu-item index="/platform-status">
              <el-icon><Cpu /></el-icon><span>平台状态</span>
            </el-menu-item>
            <el-menu-item index="/backup">
              <el-icon><FolderOpened /></el-icon><span>备份恢复</span>
            </el-menu-item>
            <el-menu-item index="/audit">
              <el-icon><DocumentChecked /></el-icon><span>审计日志</span>
            </el-menu-item>
          </el-sub-menu>
        </el-menu>
      </el-scrollbar>
    </el-aside>

    <!-- ─── Main Area ─── -->
    <el-container>
      <!-- Header -->
      <el-header class="autops-header">
        <div class="autops-header-left">
          <div class="autops-collapse-btn" @click="toggleCollapse">
            <el-icon size="18"><Fold v-if="!isCollapsed" /><Expand v-else /></el-icon>
          </div>
          <el-breadcrumb separator="/" class="breadcrumb">
            <el-breadcrumb-item v-for="item in breadcrumbs" :key="item.path" :to="item.path">
              {{ item.title }}
            </el-breadcrumb-item>
          </el-breadcrumb>
        </div>

        <div class="autops-header-right">
          <!-- 全局搜索 -->
          <el-input
            v-model="searchKeyword"
            placeholder="搜索 (Ctrl+K)"
            :prefix-icon="Search"
            size="default"
            style="width: 240px"
            clearable
            @keydown.enter="handleSearch"
          />

          <!-- 通知 -->
          <el-badge :value="unreadCount" :hidden="unreadCount === 0" :max="99">
            <el-icon size="20" color="#4e5969" style="cursor: pointer;" @click="goToAlerts">
              <Bell />
            </el-icon>
          </el-badge>

          <!-- 用户菜单 -->
          <el-dropdown trigger="click" @command="handleUserCommand">
            <div class="user-trigger">
              <el-avatar :size="32" style="background: #165dff">
                {{ (username || 'U').charAt(0).toUpperCase() }}
              </el-avatar>
              <span class="user-name">{{ username || '用户' }}</span>
              <el-icon size="12"><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile" :icon="UserFilled">个人信息</el-dropdown-item>
                <el-dropdown-item command="settings" :icon="Setting">系统设置</el-dropdown-item>
                <el-dropdown-item divided command="logout" :icon="SwitchButton">
                  <span style="color: #f53f3f">退出登录</span>
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- Content -->
      <el-main class="autops-main">
        <div class="autops-page-container">
          <router-view v-slot="{ Component, route }">
            <transition name="fade" mode="out-in">
              <component :is="Component" :key="route.fullPath" />
            </transition>
          </router-view>
        </div>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import { Search, Fold, Expand, Bell, ArrowDown, UserFilled, Setting, SwitchButton } from '@element-plus/icons-vue'
import { APP_CONFIG } from '@/shared/config'

const router = useRouter()
const route = useRoute()

// ─── Sidebar ───
const isCollapsed = ref(false)

function toggleCollapse() {
  isCollapsed.value = !isCollapsed.value
}

// ─── Active Menu ───
const activeMenu = computed(() => {
  const path = route.path
  // Exact match first
  const allMenus = Object.keys(menuMap)
  if (allMenus.includes(path)) return path
  // Prefix match: longest first
  const sorted = allMenus.filter(m => m !== '/' && path.startsWith(m + '/')).sort((a, b) => b.length - a.length)
  if (sorted.length > 0) return sorted[0]
  // Fallback: first segment
  const seg = path.split('/').filter(Boolean)
  if (seg.length > 0) return '/' + seg[0]
  return path
})

// ─── Breadcrumbs ───
const menuMap: Record<string, string> = {
  '/': '运维指挥台',
  '/incident': '故障处置',
  '/aiops': 'AI 诊断',
  '/assets': '资产列表',
  '/assets/discovery': '资产发现',
  '/asset-groups': '资产分组',
  '/credentials': '凭证管理',
  '/config': '配置管理',
  '/collectors': '采集器管理',
  '/monitoring': '监控总览',
  '/events': '事件列表',
  '/alerts': '告警中心',
  '/alert-rules': '告警规则',
  '/tickets': '工单中心',
  '/scripts': '脚本库',
  '/playbooks': 'Playbook',
  '/policies': '策略管理',
  '/executions': '执行历史',
  '/knowledge': '知识库',
  '/knowledge/import': '知识导入',
  '/users': '用户管理',
  '/roles': '角色管理',
  '/api-keys': 'API Key',
  '/system-config': '系统配置',
  '/platform-status': '平台状态',
  '/backup': '备份恢复',
  '/audit': '审计日志',
}

const groupMap: Record<string, string> = {
  '/': '指挥中心', '/incident': '指挥中心', '/aiops': '指挥中心',
  '/assets': '资产配置', '/assets/discovery': '资产配置', '/asset-groups': '资产配置',
  '/credentials': '资产配置', '/config': '资产配置', '/collectors': '资产配置',
  '/monitoring': '监控事件', '/events': '监控事件', '/alerts': '监控事件',
  '/alert-rules': '监控事件', '/tickets': '监控事件',
  '/scripts': '自动化', '/playbooks': '自动化', '/policies': '自动化', '/executions': '自动化',
  '/knowledge': '知识', '/knowledge/import': '知识',
  '/users': '平台管理', '/roles': '平台管理', '/api-keys': '平台管理',
  '/system-config': '平台管理', '/platform-status': '平台管理', '/backup': '平台管理',
  '/audit': '平台管理',
}

const breadcrumbs = computed(() => {
  const path = route.path

  // Exact match
  let group = groupMap[path] || ''
  let title = menuMap[path] || ''

  // For detail pages, find parent menu item by prefix
  if (!title) {
    const allMenus = Object.keys(menuMap)
    const parent = allMenus.filter(m => m !== '/' && path.startsWith(m + '/')).sort((a, b) => b.length - a.length)[0]
    if (parent) {
      group = groupMap[parent] || ''
      const parentTitle = menuMap[parent] || ''
      // Detail page title
      if (path.startsWith('/alerts/')) title = '告警详情'
      else if (path.startsWith('/assets/') && path.includes('/topology')) title = '拓扑图'
      else if (path.startsWith('/assets/')) title = '资产详情'
      else if (path.startsWith('/executions/')) title = '执行详情'
      else if (path.startsWith('/tickets/')) title = '工单详情'
      else if (path.startsWith('/knowledge/') && path.includes('/edit')) title = '编辑知识'
      else if (path.startsWith('/knowledge/')) title = '知识详情'
      else if (path.startsWith('/incident/')) title = '故障处置'
      else if (path.startsWith('/policies/') && path.includes('/simulate')) title = '策略模拟'
      else title = parentTitle + '详情'
    }
  }

  if (!title) title = route.meta?.title || route.name || path

  const crumbs: { path: string; title: string }[] = []
  if (group) crumbs.push({ path: '', title: group })
  crumbs.push({ path, title })
  return crumbs
})

// ─── Navigation ───
function handleMenuSelect(index: string) {
  if (!index || !index.startsWith('/')) return
  router.push(index).catch(() => {})
}

function navigateTo(path: string) {
  router.push(path).catch(() => {})
}

function goToAlerts() {
  router.push('/alerts').catch(() => {})
}

// ─── User Menu ───
const username = ref('')

function handleUserCommand(cmd: string) {
  if (cmd === 'logout') {
    ElMessageBox.confirm('确定退出登录吗？', '提示', {
      confirmButtonText: '退出',
      cancelButtonText: '取消',
      type: 'warning',
    }).then(() => {
      localStorage.removeItem(APP_CONFIG.TOKEN_KEY)
      localStorage.removeItem('username')
      ElMessage.success('已退出登录')
      router.push('/login').catch(() => {})
    }).catch(() => {})
  } else if (cmd === 'profile') {
    ElMessage.info('个人信息功能开发中')
  } else if (cmd === 'settings') {
    router.push('/admin/config').catch(() => {})
  }
}

// ─── Search ───
const searchKeyword = ref('')

function handleSearch() {
  if (!searchKeyword.value.trim()) return
  // 搜索路由: 先尝试匹配菜单
  const kw = searchKeyword.value.toLowerCase().trim()
  for (const [path, title] of Object.entries(menuMap)) {
    if (title.toLowerCase().includes(kw) || path.includes(kw)) {
      router.push(path).catch(() => {})
      searchKeyword.value = ''
      return
    }
  }
  ElMessage.info('未找到匹配页面')
}

// ─── Keyboard Shortcut ───
function handleKeydown(e: KeyboardEvent) {
  if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
    e.preventDefault()
    const input = document.querySelector('.autops-header-right .el-input__inner') as HTMLInputElement
    if (input) input.focus()
  }
}

// ─── Unread Count ───
const unreadCount = ref(0)

async function fetchUnread() {
  try {
    const token = localStorage.getItem(APP_CONFIG.TOKEN_KEY)
    if (!token) return
    const resp = await fetch('/api/v1/alerts?page_size=1&status=active', {
      headers: { Authorization: `Bearer ${token}` },
    })
    if (resp.ok) {
      const data = await resp.json()
      unreadCount.value = data?.data?.total || 0
    }
  } catch { /* ignore */ }
}

onMounted(() => {
  username.value = localStorage.getItem('username') || 'admin'
  fetchUnread()
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
.layout-container {
  height: 100vh;
}

.sidebar-logo {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  cursor: pointer;
  border-bottom: 1px solid #2a323d;
  flex-shrink: 0;
}

.logo-text {
  font-size: 18px;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: 1px;
}

.sidebar-menu {
  border-right: none !important;
}

.breadcrumb {
  font-size: 14px;
}

.user-trigger {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  transition: background 0.2s;
}

.user-trigger:hover {
  background: #f2f3f5;
}

.user-name {
  font-size: 14px;
  color: #4e5969;
}

/* 过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
