<template>
  <div class="autops-page-container">
    <!-- Page Header -->
    <div class="autops-page-header">
      <div class="autops-page-title">资源总览</div>
      <div class="autops-page-desc">查看资产整体情况，快速访问核心功能</div>
    </div>

    <!-- Stat Cards -->
    <el-row :gutter="16" class="metric-row">
      <el-col :span="6" v-for="stat in statCards" :key="stat.label">
        <div class="autops-metric-card" v-loading="statsLoading">
          <div class="metric-icon" :class="stat.bgClass">
            <el-icon :size="20"><component :is="stat.icon" /></el-icon>
          </div>
          <div class="metric-label">{{ stat.label }}</div>
          <div class="metric-value">{{ stat.value }}</div>
        </div>
      </el-col>
    </el-row>

    <!-- Asset Type Distribution + Status Distribution -->
    <el-row :gutter="16" class="section-row">
      <el-col :span="14">
        <el-card class="main-card" shadow="never">
          <template #header>
            <div class="autops-card-header">
              <span class="card-title">资产类型分布</span>
            </div>
          </template>
          <div class="type-grid" v-loading="statsLoading">
            <div
              v-for="item in typeDistribution"
              :key="item.type"
              class="type-card"
            >
              <div class="type-card-icon" :style="{ background: item.bgColor, color: item.color }">
                <el-icon :size="20"><component :is="item.icon" /></el-icon>
              </div>
              <div class="type-card-info">
                <div class="type-card-label">{{ item.label }}</div>
                <div class="type-card-value">{{ item.count }}</div>
              </div>
            </div>
            <el-empty
              v-if="typeDistribution.length === 0 && !statsLoading"
              description="暂无资产类型数据"
              :image-size="60"
            />
          </div>
        </el-card>
      </el-col>

      <el-col :span="10">
        <el-card class="main-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span class="card-title">状态概览</span>
            </div>
          </template>
          <div class="status-summary" v-loading="statsLoading">
            <div v-for="item in statusDistribution" :key="item.label" class="status-row">
              <div class="status-dot" :style="{ background: item.color }"></div>
              <span class="status-label">{{ item.label }}</span>
              <div class="status-bar-wrap">
                <div class="status-bar" :style="{ width: item.percentage + '%', background: item.color }"></div>
              </div>
              <span class="status-value">{{ item.count }}</span>
            </div>
            <el-empty
              v-if="statusDistribution.length === 0 && !statsLoading"
              description="暂无状态数据"
              :image-size="60"
            />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Recent Assets Table -->
    <el-card class="main-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span class="card-title">最近更新的资产</span>
          <el-button type="primary" plain @click="router.push({ name: 'assets' })">
            查看全部 <el-icon class="el-icon--right"><ArrowRight /></el-icon>
          </el-button>
        </div>
      </template>
      <el-table stripe
 :data="recentAssets"v-loading="tableLoading"
 empty-text="暂无资产数据"
 style="width: 100%"
 >
        <el-table-column prop="name" label="资产名" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">
            <el-link type="primary" @click="router.push('/assets/' + row.id)">
              {{ row.name || row.hostname || '-' }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column prop="asset_type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag size="small" :type="(getAssetTypeTagType(row.asset_type)) as TagType">
              {{ getAssetTypeLabel(row.asset_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="ip" label="IP 地址" width="160">
          <template #default="{ row }">
            <span class="text-muted">{{ row.ip || row.management_ip || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="(getStatusTagType(row.status || row.reachability)) as TagType">
              {{ getStatusLabel(row.status || row.reachability) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" label="更新时间" width="180">
          <template #default="{ row }">
            <span class="text-muted">{{ formatTime(row.updated_at) }}</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Quick Links -->
    <el-card class="main-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span class="card-title">快速访问</span>
        </div>
      </template>
      <el-row :gutter="16">
        <el-col :span="6" v-for="link in quickLinks" :key="link.name">
          <div class="quick-link-item" @click="router.push(link.route)">
            <div class="quick-link-icon" :style="{ background: link.bgColor, color: link.color }">
              <el-icon :size="22"><component :is="link.icon" /></el-icon>
            </div>
            <div class="quick-link-info">
              <div class="quick-link-title">{{ link.title }}</div>
              <div class="quick-link-desc">{{ link.description }}</div>
            </div>
            <el-icon class="quick-link-arrow"><ArrowRight /></el-icon>
          </div>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import type { TagType } from '@/shared/types'
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Monitor,
  Connection,
  Warning,
  CircleCheck,
  Remove,
  ArrowRight,
  Search,
  SetUp,
  Box,
  Key,
  OfficeBuilding,
  Grid,
  Monitor as Server,
  Cpu,
  Coordinate,
} from '@element-plus/icons-vue'
import { assetService, dashboardService } from '@/shared/api'
import client from '@/shared/api/client'
import { API } from '@/shared/api/routes'

const router = useRouter()

// --- State ---
const statsLoading = ref(false)
const tableLoading = ref(false)
const recentAssets = ref<any[]>([])
const typeDistribution = ref<TypeDistItem[]>([])
const statusDistribution = ref<StatusDistItem[]>([])

interface TypeDistItem {
  type: string
  label: string
  count: number
  color: string
  bgColor: string
  icon: any
}

interface StatusDistItem {
  label: string
  key: string
  count: number
  percentage: number
  color: string
}

const statCards = reactive([
  { label: '资产总数', value: 0, icon: Monitor, bgClass: 'bg-brand' },
  { label: '在线', value: 0, icon: CircleCheck, bgClass: 'bg-success' },
  { label: '离线', value: 0, icon: Remove, bgClass: 'bg-info' },
  { label: '告警中', value: 0, icon: Warning, bgClass: 'bg-danger' },
])

const quickLinks = [
  {
    name: 'asset-list',
    title: '资产列表',
    description: '浏览和管理所有资产',
    icon: Box,
    color: '#165dff',
    bgColor: '#e8f3ff',
    route: { name: 'assets' },
  },
  {
    name: 'asset-discovery',
    title: '资源发现',
    description: '自动发现网络中的资产',
    icon: Search,
    color: '#00b42a',
    bgColor: '#e8ffea',
    route: { name: 'discovery-tasks' },
  },
  {
    name: 'credentials',
    title: '凭证管理',
    description: '管理访问资产的凭证',
    icon: Key,
    color: '#ff7d00',
    bgColor: '#fff7e8',
    route: { name: 'credentials' },
  },
  {
    name: 'business-systems',
    title: '业务系统',
    description: '管理业务系统与关联',
    icon: OfficeBuilding,
    color: '#722ed1',
    bgColor: '#f5e8ff',
    route: { name: 'business-systems' },
  },
]

// --- Helpers ---
function formatTime(val: string | number | null | undefined): string {
  if (!val) return '-'
  const d = new Date(val)
  if (isNaN(d.getTime())) return '-'
  const pad = (n: number) => String(n).padStart(2, '0')
  return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()) + ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes())
}

function getAssetTypeLabel(type: string): string {
  const map: Record<string, string> = {
    server: '服务器',
    linux_server: 'Linux 服务器',
    windows_server: 'Windows 服务器',
    web_server: 'Web 服务器',
    network: '网络设备',
    storage: '存储设备',
    database: '数据库',
    middleware: '中间件',
    vm: '虚拟机',
    container: '容器',
    cloud: '云资源',
    other: '其他',
  }
  return map[type] || type || '未知'
}

function getAssetTypeTagType(type: string): TagType {
  const map: Record<string, TagType> = {
    server: 'primary',
    linux_server: 'primary',
    windows_server: 'primary',
    web_server: 'success',
    network: 'success',
    storage: 'warning',
    database: 'danger',
    middleware: 'info',
    vm: 'primary',
    container: 'success',
    cloud: 'warning',
  }
  return (map[type] || 'info') as TagType
}

function getStatusTagType(status: string): TagType {
  const map: Record<string, TagType> = {
    online: 'success',
    active: 'success',
    reachable: 'success',
    running: 'success',
    offline: 'danger',
    unreachable: 'danger',
    unknown: 'info',
    alarming: 'warning',
    maintenance: 'warning',
  }
  return (map[status] || 'info') as TagType
}

function getStatusLabel(status: string): string {
  const map: Record<string, string> = {
    online: '在线',
    active: '运行中',
    reachable: '可达',
    running: '运行中',
    offline: '离线',
    unreachable: '不可达',
    unknown: '未知',
    alarming: '告警中',
    maintenance: '维护中',
  }
  return map[status] || status || '未知'
}

function getAssetTypeIcon(type: string): any {
  const map: Record<string, any> = {
    server: Server,
    linux_server: Server,
    windows_server: Server,
    web_server: Grid,
    network: Coordinate,
    storage: Box,
    database: Cpu,
    middleware: SetUp,
    vm: Monitor,
    container: Grid,
    cloud: Connection,
  }
  return map[type] || Box
}

const assetTypeColors: Record<string, { color: string; bgColor: string }> = {
  server: { color: '#165dff', bgColor: '#e8f3ff' },
  linux_server: { color: '#165dff', bgColor: '#e8f3ff' },
  windows_server: { color: '#165dff', bgColor: '#ecf5ff' },
  web_server: { color: '#3491fa', bgColor: '#e8f3ff' },
  network: { color: '#0fc6c2', bgColor: '#e8fffb' },
  storage: { color: '#722ed1', bgColor: '#f5e8ff' },
  database: { color: '#f53f3f', bgColor: '#ffece8' },
  middleware: { color: '#ff7d00', bgColor: '#fff7e8' },
  vm: { color: '#00b42a', bgColor: '#e8ffea' },
  container: { color: '#3491fa', bgColor: '#e8f3ff' },
  cloud: { color: '#f77234', bgColor: '#fff3e8' },
}

// --- Data Fetching ---
async function fetchStats() {
  statsLoading.value = true
  try {
    // 1) Fetch dashboard stats (asset_total, alert_open) + asset-discovery (type_distribution)
    const [statsRes, discoveryRes] = await Promise.allSettled([
      dashboardService.stats(),
      dashboardService.assetDiscovery(),
    ])

    // Parse dashboard/stats: { asset_total, alert_open, anomaly_open, ... }
    let assetTotal = 0
    let alertOpen = 0
    if (statsRes.status === 'fulfilled') {
      const d = statsRes.value.data?.data ?? statsRes.value.data ?? {}
      assetTotal = d.asset_total ?? 0
      alertOpen = d.alert_open ?? 0
    }

    // Parse dashboard/asset-discovery: { asset_total, type_distribution: {"db":1,...} }
    let typeDistributionRaw: Record<string, number> = {}
    if (discoveryRes.status === 'fulfilled') {
      const d = discoveryRes.value.data?.data ?? discoveryRes.value.data ?? {}
      // Prefer asset-discovery total, fall back to stats total
      assetTotal = d.asset_total ?? assetTotal
      typeDistributionRaw = d.type_distribution ?? {}
    }

    // 2) Fetch all assets to count online/offline/alarming by status
    const assetsRes = await assetService.list({ page: 1, page_size: 500 })
    const assetsData = assetsRes.data?.data ?? assetsRes.data ?? {}
    const allAssets: any[] = assetsData.items ?? assetsData.list ?? []

    let onlineCount = 0
    let offlineCount = 0
    let alarmingCount = alertOpen
    for (const asset of allAssets) {
      const st = (asset.status ?? asset.reachability ?? 'unknown').toLowerCase()
      if (st === 'online' || st === 'active' || st === 'reachable' || st === 'running') {
        onlineCount++
      } else if (st === 'offline' || st === 'unreachable') {
        offlineCount++
      }
    }

    // Populate stat cards
    statCards[0].value = assetTotal
    statCards[1].value = onlineCount
    statCards[2].value = offlineCount
    statCards[3].value = alarmingCount

    // 3) Build type distribution from typeDistributionRaw object {"database": 1, ...}
    if (Object.keys(typeDistributionRaw).length > 0) {
      typeDistribution.value = Object.entries(typeDistributionRaw).map(function (entry) {
        var t = entry[0]
        var count = entry[1]
        var colors = assetTypeColors[t] ?? { color: '#86909c', bgColor: '#f2f3f5' }
        return {
          type: t,
          label: getAssetTypeLabel(t),
          count: count,
          color: colors.color,
          bgColor: colors.bgColor,
          icon: getAssetTypeIcon(t),
        }
      })
    } else {
      // Fallback: build from asset list
      var typeCounts: Record<string, number> = {}
      for (var i = 0; i < allAssets.length; i++) {
        var at = allAssets[i].asset_type ?? 'other'
        typeCounts[at] = (typeCounts[at] ?? 0) + 1
      }
      typeDistribution.value = Object.entries(typeCounts).map(function (entry) {
        var t = entry[0]
        var count = entry[1]
        var colors = assetTypeColors[t] ?? { color: '#86909c', bgColor: '#f2f3f5' }
        return {
          type: t,
          label: getAssetTypeLabel(t),
          count: count,
          color: colors.color,
          bgColor: colors.bgColor,
          icon: getAssetTypeIcon(t),
        }
      })
    }

    // 4) Build status distribution from asset list
    var total = statCards[0].value || 1
    var statusCounts: Record<string, number> = {}
    for (var j = 0; j < allAssets.length; j++) {
      var status = (allAssets[j].status ?? allAssets[j].reachability ?? 'unknown').toLowerCase()
      statusCounts[status] = (statusCounts[status] ?? 0) + 1
    }
    if (Object.keys(statusCounts).length > 0) {
      var statusColors: Record<string, string> = {
        online: '#00b42a',
        active: '#00b42a',
        reachable: '#00b42a',
        running: '#00b42a',
        offline: '#86909c',
        unreachable: '#f53f3f',
        unknown: '#c9cdd4',
        alarming: '#f53f3f',
        maintenance: '#ff7d00',
      }
      statusDistribution.value = Object.entries(statusCounts).map(function (entry) {
        var key = entry[0]
        var count = entry[1]
        return {
          label: getStatusLabel(key),
          key: key,
          count: count,
          percentage: Math.round((count / total) * 100),
          color: statusColors[key] ?? '#86909c',
        }
      })
    } else {
      var statusData = [
        { label: '在线', key: 'online', count: statCards[1].value, color: '#00b42a' },
        { label: '离线', key: 'offline', count: statCards[2].value, color: '#86909c' },
        { label: '告警中', key: 'alarming', count: statCards[3].value, color: '#f53f3f' },
      ]
      statusDistribution.value = statusData.map(function (s) {
        return {
          label: s.label,
          key: s.key,
          count: s.count,
          percentage: Math.round((s.count / total) * 100),
          color: s.color,
        }
      })
    }
  } catch (err: any) {
    console.error('Failed to fetch dashboard stats:', err)
    ElMessage.error('获取资源统计信息失败')
  } finally {
    statsLoading.value = false
  }
}

async function fetchRecentAssets() {
  tableLoading.value = true
  try {
    const res = await assetService.list({ page: 1, page_size: 10 })
    // Backend returns { code: 0, data: { items: [...], total, page, page_size } }
    const wrapper = res.data ?? {}
    const data = wrapper.data ?? wrapper
    recentAssets.value = data.items ?? data.list ?? []
  } catch (err: any) {
    console.error('Failed to fetch recent assets:', err)
    ElMessage.error('获取最近资产列表失败')
  } finally {
    tableLoading.value = false
  }
}

// --- Lifecycle ---
onMounted(() => {
  fetchStats()
  fetchRecentAssets()
})
</script>

<style scoped>
.section-row {
  margin-bottom: var(--autops-space-lg);
}

.main-card {
  margin-bottom: var(--autops-space-lg);
  border-radius: var(--autops-radius-md);
}
/* Type Distribution Grid */
.type-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  min-height: 180px;
}

.type-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: var(--autops-space-lg);
  border-radius: var(--autops-radius-md);
  background: var(--autops-bg-1);
  border: 1px solid var(--autops-bg-3);
  transition: all 0.2s;
}

.type-card:hover {
  border-color: var(--autops-bg-4);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.type-card-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--autops-radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.type-card-info {
  flex: 1;
}

.type-card-label {
  font-size: var(--autops-font-12);
  color: var(--autops-info);
  margin-bottom: 2px;
}

.type-card-value {
  font-size: var(--autops-font-20);
  font-weight: 600;
  color: var(--autops-text-1);
}

/* Status Distribution */
.status-summary {
  min-height: 180px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 20px;
  padding: var(--autops-space-sm) 0;
}

.status-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.status-label {
  font-size: var(--autops-font-14);
  color: var(--autops-text-2);
  width: 50px;
  flex-shrink: 0;
}

.status-bar-wrap {
  flex: 1;
  height: 8px;
  background: var(--autops-bg-3);
  border-radius: var(--autops-radius-sm);
  overflow: hidden;
}

.status-bar {
  height: 100%;
  border-radius: var(--autops-radius-sm);
  transition: width 0.6s ease;
  min-width: 2px;
}

.status-value {
  font-size: var(--autops-font-14);
  font-weight: 600;
  color: var(--autops-text-1);
  width: 40px;
  text-align: right;
  flex-shrink: 0;
}

/* Quick Links */
.quick-link-item {
  display: flex;
  align-items: center;
  padding: var(--autops-space-lg) 12px;
  border-radius: var(--autops-radius-md);
  cursor: pointer;
  transition: background-color 0.2s;
}

.quick-link-item:hover {
  background-color: var(--autops-bg-3);
}

.quick-link-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-right: 12px;
}

.quick-link-info {
  flex: 1;
  min-width: 0;
}

.quick-link-title {
  font-size: var(--autops-font-14);
  font-weight: 500;
  color: var(--autops-text-1);
  margin-bottom: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.quick-link-desc {
  font-size: var(--autops-font-12);
  color: var(--autops-info);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.quick-link-arrow {
  color: var(--autops-text-4);
  font-size: var(--autops-font-14);
  flex-shrink: 0;
}

.text-muted {
  color: var(--autops-info);
  font-size: var(--autops-font-13);
}
</style>
