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
          :default-openeds="['m1','m2','m3','m4','m5','m6','m7','m8','m9','m10','m11','m12']"
          background-color="transparent"
          text-color="#c9cdd4"
          active-text-color="#ffffff"
          class="sidebar-menu"
          @select="handleMenuSelect"
        >
          <!-- M1 运维驾驶舱 -->
          <el-sub-menu index="m1">
            <template #title>
              <el-icon><DataBoard /></el-icon><span>运维驾驶舱</span>
            </template>
            <el-menu-item index="/">指挥台</el-menu-item>
            <el-menu-item index="/business-health-map">业务健康地图</el-menu-item>
            <el-menu-item index="/daily-summary">今日摘要</el-menu-item>
          </el-sub-menu>

          <!-- M2 资源中心 -->
          <el-sub-menu index="m2">
            <template #title>
              <el-icon><Box /></el-icon><span>资源中心</span>
            </template>
            <el-menu-item index="/resources">资源总览</el-menu-item>
            <el-menu-item index="/assets">资源列表</el-menu-item>
            <el-menu-item index="/business-systems">业务系统</el-menu-item>
            <el-menu-item index="/topology">拓扑视图</el-menu-item>
            <el-menu-item index="/asset-groups">资源分组</el-menu-item>
            <el-menu-item index="/lifecycle">生命周期</el-menu-item>
            <el-menu-item index="/resources/discovery">资源发现</el-menu-item>
            <el-menu-item index="/resources/import">资源导入</el-menu-item>
          </el-sub-menu>

          <!-- M3 巡检中心 -->
          <el-sub-menu index="m3">
            <template #title>
              <el-icon><Checked /></el-icon><span>巡检中心</span>
            </template>
            <el-menu-item index="/inspections">巡检总览</el-menu-item>
            <el-menu-item index="/inspection/plans">巡检计划</el-menu-item>
            <el-menu-item index="/inspection/tasks">巡检任务</el-menu-item>
            <el-menu-item index="/inspection/results">巡检结果</el-menu-item>
            <el-menu-item index="/inspection/page-check">页面巡检</el-menu-item>
            <el-menu-item index="/inspection/config-check">配置巡检</el-menu-item>
            <el-menu-item index="/inspection/log-check">日志巡检</el-menu-item>
            <el-menu-item index="/inspection/baseline-check">基线巡检</el-menu-item>
            <el-menu-item index="/inspection/reports">巡检报告</el-menu-item>
          </el-sub-menu>

          <!-- M4 监控告警 -->
          <el-sub-menu index="m4">
            <template #title>
              <el-icon><TrendCharts /></el-icon><span>监控告警</span>
            </template>
            <el-menu-item index="/monitoring">监控总览</el-menu-item>
            <el-menu-item index="/monitoring/collectors">采集任务</el-menu-item>
            <el-menu-item index="/monitoring/collection-results">采集结果</el-menu-item>
            <el-menu-item index="/monitoring/collector-health">采集器健康</el-menu-item>
            <el-menu-item index="/monitoring/metrics">指标趋势</el-menu-item>
            <el-menu-item index="/monitoring/states">状态监控</el-menu-item>
            <el-menu-item index="/events">事件流</el-menu-item>
            <el-menu-item index="/monitoring/log-sources">日志接入</el-menu-item>
            <el-menu-item index="/monitoring/config-facts">配置快照</el-menu-item>
            <el-menu-item index="" disabled style="height:1px;padding:0;overflow:hidden;background:#3a414d;margin:4px 16px"></el-menu-item>
            <el-menu-item index="/alerts">告警列表</el-menu-item>
            <el-menu-item index="/alert-rules">告警规则</el-menu-item>
            <el-menu-item index="/alert-correlation">告警收敛</el-menu-item>
            <el-menu-item index="/anomalies">异常中心</el-menu-item>
          </el-sub-menu>

          <!-- M5 分析中心 -->
          <el-sub-menu index="m5">
            <template #title>
              <el-icon><Opportunity /></el-icon><span>分析中心</span>
            </template>
            <el-menu-item index="/incident">故障工作台</el-menu-item>
          </el-sub-menu>

          <!-- M6 自动化中心 -->
          <el-sub-menu index="m6">
            <template #title>
              <el-icon><Cpu /></el-icon><span>自动化中心</span>
            </template>
            <el-menu-item index="/automation">自动化总览</el-menu-item>
            <el-menu-item index="/policies">策略管理</el-menu-item>
            <el-menu-item index="/rule-gap">规则覆盖度</el-menu-item>
            <el-menu-item index="/scripts">脚本库</el-menu-item>
            <el-menu-item index="/playbooks">剧本库</el-menu-item>
            <el-menu-item index="/approvals">审批中心</el-menu-item>
            <el-menu-item index="/executions">执行历史</el-menu-item>
            <el-menu-item index="/rollback-center">回滚中心</el-menu-item>
            <el-menu-item index="/execution-locks">执行锁</el-menu-item>
          </el-sub-menu>

          <!-- M7 工单协同 -->
          <el-sub-menu index="m7">
            <template #title>
              <el-icon><Tickets /></el-icon><span>工单协同</span>
            </template>
            <el-menu-item index="/ticket-overview">工单总览</el-menu-item>
            <el-menu-item index="/tickets">工单列表</el-menu-item>
            <el-menu-item index="/ticket-create">新建工单</el-menu-item>
            <el-menu-item index="/manual-handling">人工工作台</el-menu-item>
            <el-menu-item index="/assignment-rules">派单规则</el-menu-item>
            <el-menu-item index="/sla-management">SLA 管理</el-menu-item>
            <el-menu-item index="/postmortem">故障复盘</el-menu-item>
            <el-menu-item index="/ticket-report">工单报告</el-menu-item>
          </el-sub-menu>

          <!-- M8 智能知识库 -->
          <el-sub-menu index="m8">
            <template #title>
              <el-icon><MagicStick /></el-icon><span>智能知识库</span>
            </template>
            <el-menu-item index="/knowledge-overview">知识总览</el-menu-item>
            <el-menu-item index="/knowledge">知识列表</el-menu-item>
            <el-menu-item index="/knowledge/import">知识导入</el-menu-item>
            <el-menu-item index="/knowledge-review">知识审核</el-menu-item>
            <el-menu-item index="/similar-cases">相似案例</el-menu-item>
          </el-sub-menu>

          <!-- M9 报表审计中心 -->
          <el-sub-menu index="m9">
            <template #title>
              <el-icon><Document /></el-icon><span>报表审计</span>
            </template>
            <el-menu-item index="" disabled style="opacity:.5;font-size:12px;height:28px;line-height:28px">报表生产</el-menu-item>
            <el-menu-item index="/reports">报表总览</el-menu-item>
            <el-menu-item index="/report/generate">报告生成</el-menu-item>
            <el-menu-item index="/report/tasks">报告任务</el-menu-item>
            <el-menu-item index="/report/archive">报告归档</el-menu-item>
            <el-menu-item index="/export-center">导出中心</el-menu-item>
            <el-menu-item index="/report/templates">报告模板</el-menu-item>
            <el-menu-item index="" disabled style="opacity:.5;font-size:12px;height:28px;line-height:28px">业务报告</el-menu-item>
            <el-menu-item index="/business-report">业务报告</el-menu-item>
            <el-menu-item index="" disabled style="opacity:.5;font-size:12px;height:28px;line-height:28px">审计取证</el-menu-item>
            <el-menu-item index="/audit">审计查询</el-menu-item>
            <el-menu-item index="/logs/search">日志检索</el-menu-item>
            <el-menu-item index="/evidence">证据归档</el-menu-item>
          </el-sub-menu>

          <!-- M10 AI 助手 -->
          <el-menu-item index="/ai-assistant">
            <el-icon><ChatLineSquare /></el-icon><span>AI 助手</span>
          </el-menu-item>

          <!-- M11 配置中心 -->
          <el-sub-menu index="m11">
            <template #title>
              <el-icon><Setting /></el-icon><span>配置中心</span>
            </template>
            <el-menu-item index="/config/overview">配置总览</el-menu-item>
            <el-menu-item index="/credentials">凭证库</el-menu-item>
            <el-menu-item index="/config/versions">配置版本</el-menu-item>
            <el-menu-item index="/config/discovery-templates">发现模板</el-menu-item>
            <el-menu-item index="/inspection/templates">巡检模板</el-menu-item>
            <el-menu-item index="/config/inspection-rules">巡检规则</el-menu-item>
            <el-menu-item index="/config/threshold-rules">阈值规则</el-menu-item>
            <el-menu-item index="/config/notification-rules">通知规则</el-menu-item>
            <el-menu-item index="" disabled style="opacity:.5;font-size:12px;height:28px;line-height:28px">AI 设置</el-menu-item>
            <el-menu-item index="/model-service">模型服务</el-menu-item>
            <el-menu-item index="/ai-tool-policy">AI 工具策略</el-menu-item>
            <el-menu-item index="/prompt-templates">Prompt 模板</el-menu-item>
          </el-sub-menu>

          <!-- M12 平台管理 -->
          <el-sub-menu index="m12">
            <template #title>
              <el-icon><Tools /></el-icon><span>平台管理</span>
            </template>
            <el-menu-item index="" disabled style="opacity:.5;font-size:12px;height:28px;line-height:28px">权限治理</el-menu-item>
            <el-menu-item index="/users">用户管理</el-menu-item>
            <el-menu-item index="/roles">角色管理</el-menu-item>
            <el-menu-item index="/tenants">租户管理</el-menu-item>
            <el-menu-item index="/permission-policy">权限策略</el-menu-item>
            <el-menu-item index="/api-keys">API Key</el-menu-item>
            <el-menu-item index="" disabled style="opacity:.5;font-size:12px;height:28px;line-height:28px">系统运维</el-menu-item>
            <el-menu-item index="/system-config">系统配置</el-menu-item>
            <el-menu-item index="/dictionaries">字典管理</el-menu-item>
            <el-menu-item index="/platform-status">平台健康</el-menu-item>
            <el-menu-item index="/task-queue">任务队列</el-menu-item>
            <el-menu-item index="/system-check">系统自检</el-menu-item>
            <el-menu-item index="/backup">备份恢复</el-menu-item>
            <el-menu-item index="/upgrade-maintenance">升级维护</el-menu-item>
            <el-menu-item index="/license">授权许可</el-menu-item>
            <el-menu-item index="" disabled style="opacity:.5;font-size:12px;height:28px;line-height:28px">扩展与集成</el-menu-item>
            <el-menu-item index="/integrations">集成管理</el-menu-item>
            <el-menu-item index="/agents">采集节点</el-menu-item>
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
          <div style="position: relative">
            <el-input
              v-model="searchKeyword"
              placeholder="搜索 (Ctrl+K)"
              :prefix-icon="Search"
              size="default"
              style="width: 240px"
              clearable
              :loading="searchLoading"
              @keydown.enter="handleSearch"
              @blur="hideSearchDropdown"
            />
            <div v-if="showSearchDropdown && searchResults.length" class="search-dropdown">
              <div
                v-for="(item, idx) in searchResults"
                :key="idx"
                class="search-dropdown-item"
                @mousedown.prevent="handleSearchSelect(item)"
              >
                <el-tag size="small" type="info" style="margin-right: 8px">{{ item.type }}</el-tag>
                <span class="search-dropdown-title">{{ item.title }}</span>
                <span v-if="item.description" class="search-dropdown-desc">{{ item.description }}</span>
              </div>
            </div>
          </div>

          <!-- 后台任务进度 -->
          <TaskProgressIndicator />
          <!-- 通知中心 -->
          <NotificationBell />

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
  Document, Tools, Checked, MapLocation, Calendar, ChatLineSquare, Opportunity
} from '@element-plus/icons-vue'
import api from '@/shared/api/client'
import NotificationBell from '@/shared/components/NotificationBell.vue'
import TaskProgressIndicator from '@/shared/components/TaskProgressIndicator.vue'
import { useAuthStore } from '@/app/store/auth'
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

// ─── V3 菜单映射（12模块） ───
const menuMap: Record<string, string> = {
  '/': '指挥台',
  '/business-health-map': '业务健康地图',
  '/daily-summary': '今日摘要',
  // M2 资源中心
  '/resources': '资源总览',
  '/assets': '资源列表',
  '/business-systems': '业务系统',
  '/topology': '拓扑视图',
  '/asset-groups': '资源分组',
  '/lifecycle': '生命周期',
  '/resources/discovery': '资源发现',
  '/resources/import': '资源导入',
  // M3 巡检中心
  '/inspections': '巡检总览',
  '/inspection/plans': '巡检计划',
  '/inspection/tasks': '巡检任务',
  '/inspection/results': '巡检结果',
  '/inspection/page-check': '页面巡检',
  '/inspection/config-check': '配置巡检',
  '/inspection/log-check': '日志巡检',
  '/inspection/baseline-check': '基线巡检',
  '/inspection/reports': '巡检报告',
  '/inspection/templates': '巡检模板',
  // M4 监控告警
  '/monitoring': '监控总览',
  '/monitoring/collectors': '采集任务',
  '/monitoring/collection-results': '采集结果',
  '/monitoring/collector-health': '采集器健康',
  '/monitoring/metrics': '指标趋势',
  '/monitoring/states': '状态监控',
  '/events': '事件流',
  '/monitoring/log-sources': '日志接入',
  '/monitoring/config-facts': '配置快照',
  '/alerts': '告警列表',
  '/alert-rules': '告警规则',
  '/alert-correlation': '告警收敛',
  '/anomalies': '异常中心',
  // M5 分析中心
  '/incident': '故障工作台',
  // M6 自动化中心
  '/automation': '自动化总览',
  '/policies': '策略管理',
  '/scripts': '脚本库',
  '/playbooks': '剧本库',
  '/approvals': '审批中心',
  '/executions': '执行历史',
  '/rollback-center': '回滚中心',
  '/execution-locks': '执行锁',
  // M7 工单协同
  '/ticket-overview': '工单总览',
  '/tickets': '工单列表',
  '/ticket-create': '新建工单',
  '/manual-handling': '人工工作台',
  '/assignment-rules': '派单规则',
  '/sla-management': 'SLA 管理',
  '/postmortem': '故障复盘',
  '/ticket-report': '工单报告',
  // M8 智能知识库
  '/knowledge-overview': '知识总览',
  '/knowledge': '知识列表',
  '/knowledge/import': '知识导入',
  '/knowledge-review': '知识审核',
  '/similar-cases': '相似案例',
  '/rule-gap': '规则缺口',
  '/prompt-templates': 'Prompt 模板',
  '/ai-tool-policy': 'AI 工具策略',
  // M9 报表审计中心
  '/reports': '报表总览',
  '/report/generate': '报告生成',
  '/report/tasks': '报告任务',
  '/report/archive': '报告归档',
  '/export-center': '导出中心',
  '/report/templates': '报告模板',
  '/business-report': '业务报告',
  '/ops-report': '运维报告',
  '/asset-report': '资产报告',
  '/inspection-report': '巡检报告',
  '/automation-report': '自动化报告',
  '/compliance-report': '合规报告',
  '/audit': '审计查询',
  '/logs/search': '日志检索',
  '/evidence': '证据归档',
  // M10 AI 助手
  '/ai-assistant': 'AI 助手',
  // M11 配置中心
  '/config/overview': '配置总览',
  '/credentials': '凭证库',
  '/config/versions': '配置版本',
  '/config/discovery-templates': '发现模板',
  '/config/inspection-rules': '巡检规则',
  '/config/threshold-rules': '阈值规则',
  '/config/notification-rules': '通知规则',
  // M12 平台管理
  '/users': '用户管理',
  '/roles': '角色管理',
  '/tenants': '租户管理',
  '/permission-policy': '权限策略',
  '/api-keys': 'API Key',
  '/system-config': '系统配置',
  '/dictionaries': '字典管理',
  '/integrations': '集成管理',
  '/model-service': '模型服务',
  '/agents': '采集节点',
  '/platform-status': '平台健康',
  '/task-queue': '任务队列',
  '/system-check': '系统自检',
  '/backup': '备份恢复',
  '/upgrade-maintenance': '升级维护',
  '/license': '授权许可',
  '/profile': '个人中心',
}

const groupMap: Record<string, string> = {
  '/': '运维驾驶舱',
  '/business-health-map': '运维驾驶舱', '/daily-summary': '运维驾驶舱',
  '/resources': '资源中心', '/resources/discovery': '资源中心',
  '/assets': '资源中心', '/business-systems': '资源中心', '/topology': '资源中心',
  '/resources/import': '资源中心', '/asset-groups': '资源中心', '/lifecycle': '资源中心',
  '/inspections': '巡检中心', '/inspection/plans': '巡检中心', '/inspection/tasks': '巡检中心',
  '/inspection/results': '巡检中心', '/inspection/page-check': '巡检中心',
  '/inspection/config-check': '巡检中心', '/inspection/log-check': '巡检中心',
  '/inspection/baseline-check': '巡检中心', '/inspection/reports': '巡检中心',
  '/monitoring': '监控告警', '/monitoring/collectors': '监控告警',
  '/monitoring/collection-results': '监控告警', '/monitoring/collector-health': '监控告警',
  '/monitoring/metrics': '监控告警', '/monitoring/states': '监控告警',
  '/events': '监控告警',
  '/monitoring/log-sources': '监控告警', '/monitoring/config-facts': '监控告警',
  '/alerts': '监控告警', '/alert-rules': '监控告警', '/alert-correlation': '监控告警',
  '/anomalies': '监控告警',
  '/incident': '分析中心',
  '/automation': '自动化中心', '/policies': '自动化中心',
  '/scripts': '自动化中心', '/playbooks': '自动化中心', '/approvals': '自动化中心',
  '/executions': '自动化中心', '/rollback-center': '自动化中心', '/execution-locks': '自动化中心',
  '/ticket-overview': '工单协同', '/tickets': '工单协同', '/ticket-create': '工单协同',
  '/manual-handling': '工单协同', '/assignment-rules': '工单协同',
  '/sla-management': '工单协同', '/postmortem': '工单协同', '/ticket-report': '工单协同',
  '/knowledge-overview': '智能知识库', '/knowledge': '智能知识库',
  '/knowledge/import': '智能知识库', '/knowledge-review': '智能知识库', '/similar-cases': '智能知识库',
  '/rule-gap': '自动化中心', '/prompt-templates': '配置中心', '/ai-tool-policy': '配置中心',
  '/reports': '报表审计', '/report/generate': '报表审计', '/report/tasks': '报表审计',
  '/report/archive': '报表审计', '/export-center': '报表审计', '/report/templates': '报表审计',
  '/business-report': '报表审计',
  '/audit': '报表审计', '/logs/search': '报表审计', '/evidence': '报表审计',
  '/ai-assistant': 'AI 助手',
  '/credentials': '配置中心', '/config/versions': '配置中心',
  '/config/inspection-rules': '配置中心', '/config/threshold-rules': '配置中心',
  '/config/notification-rules': '配置中心',
  '/users': '平台管理', '/roles': '平台管理', '/tenants': '平台管理', '/api-keys': '平台管理',
  '/permission-policy': '平台管理', '/system-config': '平台管理', '/dictionaries': '平台管理',
  '/integrations': '平台管理', '/platform-status': '平台管理', '/task-queue': '平台管理',
  '/model-service': '配置中心', '/agents': '平台管理',
  '/backup': '平台管理', '/upgrade-maintenance': '平台管理', '/license': '平台管理',
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
const searchLoading = ref(false)

interface SearchResult {
  type: string
  title: string
  path: string
  description?: string
}
const searchResults = ref<SearchResult[]>([])
const showSearchDropdown = ref(false)
function hideSearchDropdown() { setTimeout(() => { showSearchDropdown.value = false }, 200) }

async function handleSearch() {
  const kw = searchKeyword.value.trim()
  if (!kw) { showSearchDropdown.value = false; return }

  const kwLower = kw.toLowerCase()

  // 1) 本地菜单匹配
  for (const [path, title] of Object.entries(menuMap)) {
    if (title.toLowerCase().includes(kwLower) || path.includes(kwLower)) {
      router.push(path).catch(() => {})
      searchKeyword.value = ''
      showSearchDropdown.value = false
      return
    }
  }

  // 2) 后端全局搜索
  searchLoading.value = true
  try {
    const resp = await api.get(API.GLOBAL_SEARCH, { params: { q: kw, page_size: 10 } })
    if (resp.data?.code === 0 && resp.data?.data?.items?.length) {
      searchResults.value = resp.data.data.items.map((item: any) => ({
        type: item.type || 'unknown',
        title: item.title || item.name || item.id,
        path: item.path || '',
        description: item.description || '',
      }))
      if (searchResults.value.length === 1 && searchResults.value[0].path) {
        router.push(searchResults.value[0].path).catch(() => {})
        searchKeyword.value = ''
        showSearchDropdown.value = false
      } else {
        showSearchDropdown.value = true
      }
    } else {
      ElMessage.info('未找到匹配结果')
    }
  } catch {
    ElMessage.info('未找到匹配页面')
  } finally {
    searchLoading.value = false
  }
}

function handleSearchSelect(item: SearchResult) {
  if (item.path) router.push(item.path).catch(() => {})
  showSearchDropdown.value = false
  searchKeyword.value = ''
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

const authStore = useAuthStore()

onMounted(() => {
  username.value = localStorage.getItem('username') || 'admin'
  // 恢复用户信息（含 roles），使 v-permission 指令在刷新后仍能正确工作
  authStore.fetchUser().catch(() => {})
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
  border-bottom: 1px solid var(--autops-terminal-bg);
  flex-shrink: 0;
}

.logo-text {
  font-size: 18px;
  font-weight: 700;
  color: var(--autops-bg-1);
  letter-spacing: 1px;
}

.sidebar-menu {
  border-right: none !important;
}

.breadcrumb {
  font-size: var(--autops-font-14);
}

.user-trigger {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: var(--autops-space-xs) 8px;
  border-radius: 6px;
  transition: background 0.2s;
}

.user-trigger:hover {
  background: var(--autops-bg-3);
}

.user-name {
  font-size: var(--autops-font-14);
  color: var(--autops-text-2);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.search-dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  width: 360px;
  max-height: 320px;
  overflow-y: auto;
  background: var(--autops-bg-1);
  border-radius: var(--autops-radius-md);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  z-index: 2000;
  margin-top: 4px;
}

.search-dropdown-item {
  display: flex;
  align-items: center;
  padding: 10px 14px;
  cursor: pointer;
  transition: background 0.15s;
  border-bottom: 1px solid var(--autops-bg-3);
}

.search-dropdown-item:last-child {
  border-bottom: none;
}

.search-dropdown-item:hover {
  background: var(--autops-bg-3);
}

.search-dropdown-title {
  font-size: var(--autops-font-13);
  color: var(--autops-text-1);
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.search-dropdown-desc {
  font-size: var(--autops-font-12);
  color: var(--autops-info);
  margin-left: 8px;
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
