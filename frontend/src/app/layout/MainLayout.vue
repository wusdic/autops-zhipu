<template>
  <el-container class="layout-container">
    <!-- ─── Sidebar ─── -->
    <el-aside :width="isCollapsed ? '64px' : '220px'" class="autops-sidebar" :class="{ 'autops-sidebar--collapsed': isCollapsed }">
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
          <!-- M1 首页指挥台 -->
          <el-menu-item index="/">
            <el-icon><DataBoard /></el-icon><span>首页指挥台</span>
          </el-menu-item>

          <!-- M2 资源中心 -->
          <el-sub-menu index="m2">
            <template #title>
              <el-icon><Box /></el-icon><span>资源中心</span>
            </template>
            <el-menu-item index="/resources">资源总览</el-menu-item>
            <el-menu-item index="/resources/discovery">资源发现任务</el-menu-item>
            <el-menu-item index="/resources/discovery-results">发现结果</el-menu-item>
            <el-menu-item index="/assets">资源列表</el-menu-item>
            <el-menu-item index="/business-systems">业务系统</el-menu-item>
            <el-menu-item index="/topology">拓扑视图</el-menu-item>
            <el-menu-item index="/resources/import">资源导入</el-menu-item>
            <el-menu-item index="/asset-groups">资源分组</el-menu-item>
            <el-menu-item index="/credentials">凭证管理</el-menu-item>
            <el-menu-item index="/agents">Agent 管理</el-menu-item>
          </el-sub-menu>

          <!-- M3 巡检中心 -->
          <el-sub-menu index="m3">
            <template #title>
              <el-icon><Checked /></el-icon><span>巡检中心</span>
            </template>
            <el-menu-item index="/inspections">巡检总览</el-menu-item>
            <el-menu-item index="/inspection/templates">巡检模板</el-menu-item>
            <el-menu-item index="/inspection/plans">巡检计划</el-menu-item>
            <el-menu-item index="/inspection/tasks">巡检任务</el-menu-item>
            <el-menu-item index="/inspection/results">巡检结果</el-menu-item>
            <el-menu-item index="/inspection/page-check">页面巡检</el-menu-item>
            <el-menu-item index="/inspection/config-check">配置巡检</el-menu-item>
            <el-menu-item index="/inspection/log-check">日志巡检</el-menu-item>
            <el-menu-item index="/inspection/baseline-check">基线巡检</el-menu-item>
            <el-menu-item index="/inspection/reports">巡检报告</el-menu-item>
          </el-sub-menu>

          <!-- M4 监控中心 -->
          <el-sub-menu index="m4">
            <template #title>
              <el-icon><TrendCharts /></el-icon><span>监控中心</span>
            </template>
            <el-menu-item index="/monitoring">监控总览</el-menu-item>
            <el-menu-item index="/monitoring/collectors">采集任务</el-menu-item>
            <el-menu-item index="/monitoring/collection-results">采集结果</el-menu-item>
            <el-menu-item index="/monitoring/metrics">指标趋势</el-menu-item>
            <el-menu-item index="/monitoring/states">状态快照</el-menu-item>
            <el-menu-item index="/monitoring/state-changes">状态变化</el-menu-item>
            <el-menu-item index="/events">事件流</el-menu-item>
            <el-menu-item index="/monitoring/log-sources">日志接入</el-menu-item>
            <el-menu-item index="/monitoring/collector-health">采集器健康</el-menu-item>
            <el-menu-item index="/monitoring/config-facts">配置事实</el-menu-item>
          </el-sub-menu>

          <!-- M5 处置中心 -->
          <el-sub-menu index="m5">
            <template #title>
              <el-icon><Warning /></el-icon><span>处置中心</span>
            </template>
            <el-menu-item index="/anomalies">异常总览</el-menu-item>
            <el-menu-item index="/anomaly/list">异常列表</el-menu-item>
            <el-menu-item index="/alerts">告警列表</el-menu-item>
            <el-menu-item index="/alert-rules">告警规则</el-menu-item>
            <el-menu-item index="/incident">故障工作台</el-menu-item>
          </el-sub-menu>

          <!-- M6 自动化中心 -->
          <el-sub-menu index="m6">
            <template #title>
              <el-icon><Cpu /></el-icon><span>自动化中心</span>
            </template>
            <el-menu-item index="/automation">自动化总览</el-menu-item>
            <el-menu-item index="/policies">策略列表</el-menu-item>
            <el-menu-item index="/scripts">脚本库</el-menu-item>
            <el-menu-item index="/playbooks">剧本库</el-menu-item>
            <el-menu-item index="/approvals">审批中心</el-menu-item>
            <el-menu-item index="/executions">执行历史</el-menu-item>
          </el-sub-menu>

          <!-- M7 智能知识库 -->
          <el-sub-menu index="m7">
            <template #title>
              <el-icon><MagicStick /></el-icon><span>智能知识库</span>
            </template>
            <el-menu-item index="/aiops">AI 诊断</el-menu-item>
            <el-menu-item index="/knowledge">知识列表</el-menu-item>
            <el-menu-item index="/knowledge/import">知识导入</el-menu-item>
          </el-sub-menu>

          <!-- M8 工单中心 -->
          <el-sub-menu index="m8">
            <template #title>
              <el-icon><Tickets /></el-icon><span>工单中心</span>
            </template>
            <el-menu-item index="/tickets">工单列表</el-menu-item>
          </el-sub-menu>

          <!-- M9 报表审计中心 -->
          <el-sub-menu index="m9">
            <template #title>
              <el-icon><Document /></el-icon><span>报表审计</span>
            </template>
            <el-menu-item index="/reports">报表总览</el-menu-item>
            <el-menu-item index="/report/templates">报告模板</el-menu-item>
            <el-menu-item index="/report/generate">报告生成</el-menu-item>
            <el-menu-item index="/report/tasks">报告任务</el-menu-item>
            <el-menu-item index="/report/archive">报告归档</el-menu-item>
            <el-menu-item index="/audit">审计查询</el-menu-item>
            <el-menu-item index="/logs/search">日志检索</el-menu-item>
            <el-menu-item index="/evidence">证据归档</el-menu-item>
          </el-sub-menu>

          <!-- M10 平台管理 -->
          <el-sub-menu index="m10">
            <template #title>
              <el-icon><Tools /></el-icon><span>平台管理</span>
            </template>
            <el-menu-item index="/users">用户管理</el-menu-item>
            <el-menu-item index="/roles">角色管理</el-menu-item>
            <el-menu-item index="/tenants">租户管理</el-menu-item>
            <el-menu-item index="/api-keys">API Key</el-menu-item>
            <el-menu-item index="/system-config">系统配置</el-menu-item>
            <el-menu-item index="/dictionaries">字典管理</el-menu-item>
            <el-menu-item index="/integrations">集成管理</el-menu-item>
            <el-menu-item index="/platform-status">平台健康</el-menu-item>
            <el-menu-item index="/task-queue">任务队列</el-menu-item>
            <el-menu-item index="/backup">备份恢复</el-menu-item>
            <el-menu-item index="/system-check">系统自检</el-menu-item>
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
            <el-breadcrumb-item v-for="item in breadcrumbs" :key="item.path || item.title" :to="item.path || undefined">
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
                <el-dropdown-item command="profile" :icon="UserFilled">个人中心</el-dropdown-item>
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
import {
  Search, Fold, Expand, Bell, ArrowDown, UserFilled, Setting, SwitchButton,
  Monitor, DataBoard, Box, TrendCharts, Warning, Cpu, MagicStick, Tickets,
  Document, Tools, Checked
} from '@element-plus/icons-vue'
import api from '@/shared/api/client'
import { API } from '@/shared/api/routes'
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
  const allMenus = Object.keys(menuMap)
  if (allMenus.includes(path)) return path
  const sorted = allMenus.filter(m => m !== '/' && path.startsWith(m + '/')).sort((a, b) => b.length - a.length)
  if (sorted.length > 0) return sorted[0]
  const seg = path.split('/').filter(Boolean)
  if (seg.length > 0) return '/' + seg[0]
  return path
})

// ─── V3 菜单映射 ───
const menuMap: Record<string, string> = {
  '/': '首页指挥台',
  // M2 资源中心
  '/resources': '资源总览',
  '/resources/discovery': '资源发现任务',
  '/resources/discovery-results': '发现结果',
  '/assets': '资源列表',
  '/business-systems': '业务系统',
  '/topology': '拓扑视图',
  '/resources/import': '资源导入',
  '/asset-groups': '资源分组',
  '/credentials': '凭证管理',
  '/agents': 'Agent 管理',
  // M3 巡检中心
  '/inspections': '巡检总览',
  '/inspection/templates': '巡检模板',
  '/inspection/plans': '巡检计划',
  '/inspection/tasks': '巡检任务',
  '/inspection/results': '巡检结果',
  '/inspection/page-check': '页面巡检',
  '/inspection/config-check': '配置巡检',
  '/inspection/log-check': '日志巡检',
  '/inspection/baseline-check': '基线巡检',
  '/inspection/reports': '巡检报告',
  // M4 监控中心
  '/monitoring': '监控总览',
  '/monitoring/collectors': '采集任务',
  '/monitoring/collection-results': '采集结果',
  '/monitoring/metrics': '指标趋势',
  '/monitoring/states': '状态快照',
  '/monitoring/state-changes': '状态变化',
  '/events': '事件流',
  '/monitoring/log-sources': '日志接入',
  '/monitoring/collector-health': '采集器健康',
  '/monitoring/config-facts': '配置事实',
  // M5 处置中心
  '/anomalies': '异常总览',
  '/anomaly/list': '异常列表',
  '/alerts': '告警列表',
  '/alert-rules': '告警规则',
  '/incident': '故障工作台',
  // M6 自动化中心
  '/automation': '自动化总览',
  '/policies': '策略列表',
  '/scripts': '脚本库',
  '/playbooks': '剧本库',
  '/approvals': '审批中心',
  '/executions': '执行历史',
  // M7 智能知识库
  '/aiops': 'AI 诊断',
  '/knowledge': '知识列表',
  '/knowledge/import': '知识导入',
  // M8 工单中心
  '/tickets': '工单列表',
  // M9 报表审计中心
  '/reports': '报表总览',
  '/report/templates': '报告模板',
  '/report/generate': '报告生成',
  '/report/tasks': '报告任务',
  '/report/archive': '报告归档',
  '/audit': '审计查询',
  '/logs/search': '日志检索',
  '/evidence': '证据归档',
  // M10 平台管理
  '/users': '用户管理',
  '/roles': '角色管理',
  '/tenants': '租户管理',
  '/api-keys': 'API Key',
  '/system-config': '系统配置',
  '/dictionaries': '字典管理',
  '/integrations': '集成管理',
  '/platform-status': '平台健康',
  '/task-queue': '任务队列',
  '/backup': '备份恢复',
  '/system-check': '系统自检',
  '/profile': '个人中心',
}

const groupMap: Record<string, string> = {
  '/': '首页指挥台',
  '/resources': '资源中心', '/resources/discovery': '资源中心', '/resources/discovery-results': '资源中心',
  '/assets': '资源中心', '/business-systems': '资源中心', '/topology': '资源中心',
  '/resources/import': '资源中心', '/asset-groups': '资源中心', '/credentials': '资源中心', '/agents': '资源中心',
  '/inspections': '巡检中心', '/inspection/templates': '巡检中心', '/inspection/plans': '巡检中心',
  '/inspection/tasks': '巡检中心', '/inspection/results': '巡检中心', '/inspection/page-check': '巡检中心',
  '/inspection/config-check': '巡检中心', '/inspection/log-check': '巡检中心',
  '/inspection/baseline-check': '巡检中心', '/inspection/reports': '巡检中心',
  '/monitoring': '监控中心', '/monitoring/collectors': '监控中心', '/monitoring/collection-results': '监控中心',
  '/monitoring/metrics': '监控中心', '/monitoring/states': '监控中心', '/monitoring/state-changes': '监控中心',
  '/events': '监控中心', '/monitoring/log-sources': '监控中心', '/monitoring/collector-health': '监控中心',
  '/monitoring/config-facts': '监控中心',
  '/anomalies': '处置中心', '/anomaly/list': '处置中心', '/alerts': '处置中心',
  '/alert-rules': '处置中心', '/incident': '处置中心',
  '/automation': '自动化中心', '/policies': '自动化中心', '/scripts': '自动化中心',
  '/playbooks': '自动化中心', '/approvals': '自动化中心', '/executions': '自动化中心',
  '/aiops': '智能知识库', '/knowledge': '智能知识库', '/knowledge/import': '智能知识库',
  '/tickets': '工单中心',
  '/reports': '报表审计', '/report/templates': '报表审计', '/report/generate': '报表审计',
  '/report/tasks': '报表审计', '/report/archive': '报表审计', '/audit': '报表审计',
  '/logs/search': '报表审计', '/evidence': '报表审计',
  '/users': '平台管理', '/roles': '平台管理', '/tenants': '平台管理', '/api-keys': '平台管理',
  '/system-config': '平台管理', '/dictionaries': '平台管理', '/integrations': '平台管理',
  '/platform-status': '平台管理', '/task-queue': '平台管理', '/backup': '平台管理',
  '/system-check': '平台管理', '/profile': '个人中心',
}

const breadcrumbs = computed(() => {
  const path = route.path
  let group = groupMap[path] || ''
  let title = menuMap[path] || ''

  // For detail pages
  if (!title) {
    const allMenus = Object.keys(menuMap)
    const parent = allMenus.filter(m => m !== '/' && path.startsWith(m + '/')).sort((a, b) => b.length - a.length)[0]
    if (parent) {
      group = groupMap[parent] || ''
      if (path.match(/\/alerts\/[\w-]+$/)) title = '告警详情'
      else if (path.match(/\/assets\/[\w-]+\/topology/)) title = '拓扑图'
      else if (path.match(/\/assets\/[\w-]+$/)) title = '资源详情'
      else if (path.match(/\/executions\/[\w-]+$/)) title = '执行详情'
      else if (path.match(/\/tickets\/[\w-]+$/)) title = '工单详情'
      else if (path.match(/\/knowledge\/[\w-]+\/edit/)) title = '编辑知识'
      else if (path.match(/\/knowledge\/[\w-]+$/)) title = '知识详情'
      else if (path.match(/\/incident\//)) title = '故障处置详情'
      else if (path.match(/\/policies\/[\w-]+\/simulate/)) title = '策略模拟'
      else if (path.match(/\/policies\/[\w-]+\/edit/)) title = '策略编辑'
      else if (path.match(/\/anomaly\/[\w-]+$/)) title = '异常详情'
      else if (path.match(/\/dry-run\//)) title = 'Dry-run 详情'
      else if (path.match(/\/report\/[\w-]+\/preview/)) title = '报告预览'
      else title = (menuMap[parent] || '') + '详情'
    }
  }

  if (!title) title = (route.meta?.title as string) || (route.name as string) || path

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
    router.push('/profile').catch(() => {})
  } else if (cmd === 'settings') {
    router.push('/system-config').catch(() => {})
  }
}

// ─── Search ───
const searchKeyword = ref('')

function handleSearch() {
  if (!searchKeyword.value.trim()) return
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
    const resp = await api.get(API.ALERTS, { params: { page_size: 1, status: 'active' } })
    if (resp.data?.code === 0) {
      unreadCount.value = resp.data?.data?.total || 0
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

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
