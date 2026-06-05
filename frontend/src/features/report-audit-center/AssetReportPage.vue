<template>
  <div class="asset-report-page">
    <!-- Page Header -->
    <div class="autops-page-header">
      <div>
        <div class="autops-page-title">资产报告</div>
        <div class="autops-page-desc">资产清单统计与状态分析报告</div>
      </div>
      <div class="header-actions">
        <el-button :icon="Refresh" circle size="small" @click="loadAll" />
        <el-button type="primary" @click="exportReport">
          <el-icon style="margin-right: 4px"><Download /></el-icon>
          导出报表
        </el-button>
      </div>
    </div>

    <!-- Summary Statistics -->
    <el-row :gutter="16" class="stats-row mb-lg">
      <el-col :xs="12" :sm="6">
        <div class="autops-card stat-card stat-card--total">
          <div class="stat-card__body">
            <div class="stat-card__icon">
              <el-icon :size="28"><Monitor /></el-icon>
            </div>
            <div class="stat-card__info">
              <div class="stat-card__value">{{ summaryStats.total }}</div>
              <div class="stat-card__label">资产总数</div>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="autops-card stat-card stat-card--online">
          <div class="stat-card__body">
            <div class="stat-card__icon">
              <el-icon :size="28"><CircleCheckFilled /></el-icon>
            </div>
            <div class="stat-card__info">
              <div class="stat-card__value">{{ summaryStats.online }}</div>
              <div class="stat-card__label">在线</div>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="autops-card stat-card stat-card--offline">
          <div class="stat-card__body">
            <div class="stat-card__icon">
              <el-icon :size="28"><SwitchButton /></el-icon>
            </div>
            <div class="stat-card__info">
              <div class="stat-card__value">{{ summaryStats.offline }}</div>
              <div class="stat-card__label">离线</div>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="autops-card stat-card stat-card--abnormal">
          <div class="stat-card__body">
            <div class="stat-card__icon">
              <el-icon :size="28"><WarningFilled /></el-icon>
            </div>
            <div class="stat-card__info">
              <div class="stat-card__value">{{ summaryStats.abnormal }}</div>
              <div class="stat-card__label">异常</div>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- Asset Overview & Type Distribution -->
    <el-row :gutter="16" class="mb-lg">
      <el-col :span="12">
        <div class="autops-card">
          <div class="autops-card-header">
            <span class="autops-card-title">资产概况</span>
          </div>
          <div class="autops-card-body">
            <el-descriptions :column="2" border size="small">
              <el-descriptions-item label="资产总数">{{ summaryStats.total }}</el-descriptions-item>
              <el-descriptions-item label="在线数">{{ summaryStats.online }}</el-descriptions-item>
              <el-descriptions-item label="离线数">{{ summaryStats.offline }}</el-descriptions-item>
              <el-descriptions-item label="异常数">{{ summaryStats.abnormal }}</el-descriptions-item>
              <el-descriptions-item label="今日新增">{{ summaryStats.todayNew }}</el-descriptions-item>
              <el-descriptions-item label="今日变更">{{ summaryStats.todayChanged }}</el-descriptions-item>
            </el-descriptions>
          </div>
        </div>
      </el-col>
      <el-col :span="12">
        <div class="autops-card">
          <div class="autops-card-header">
            <span class="autops-card-title">资产类型分布</span>
          </div>
          <div class="autops-card-body">
            <el-table stripe
 :data="typeDistribution"
 v-loading="statsLoading"size="small"
 empty-text="暂无数据"
 max-height="200"
 >
              <el-table-column prop="type" label="类型" min-width="120">
                <template #default="{ row }">
                  <span>{{ assetTypeLabel(row.type) }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="count" label="数量" width="80" align="center" />
              <el-table-column label="占比" width="160">
                <template #default="{ row }">
                  <el-progress
                    :percentage="Math.round((row.count / Math.max(summaryStats.total, 1)) * 100)"
                    :stroke-width="14"
                    :text-inside="true"
                    style="max-width: 140px"
                  />
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- Asset List Table -->
    <div class="autops-card">
      <div class="autops-card-header">
        <span class="autops-card-title">资产清单</span>
      </div>
      <div class="autops-card-body">
        <!-- Filters -->
        <el-form :inline="true" class="autops-toolbar filter-form" @submit.prevent="handleSearch">
          <el-form-item label="类型">
            <el-select v-model="filters.type" placeholder="全部类型" clearable style="width: 140px">
              <el-option label="Linux服务器" value="linux_server" />
              <el-option label="Web服务器" value="web_server" />
              <el-option label="Windows服务器" value="windows_server" />
              <el-option label="服务器" value="server" />
              <el-option label="网络设备" value="network" />
              <el-option label="数据库" value="database" />
              <el-option label="中间件" value="middleware" />
              <el-option label="应用" value="application" />
              <el-option label="云资源" value="cloud" />
            </el-select>
          </el-form-item>
          <el-form-item label="状态">
            <el-select v-model="filters.status" placeholder="全部状态" clearable style="width: 130px">
              <el-option label="在线" value="online" />
              <el-option label="离线" value="offline" />
              <el-option label="异常" value="abnormal" />
              <el-option label="未知" value="unknown" />
            </el-select>
          </el-form-item>
          <el-form-item label="关键词">
            <el-input
              v-model="filters.keyword"
              placeholder="搜索资产名称/IP"
              clearable
              :prefix-icon="Search"
              style="width: 180px"
              @keyup.enter="handleSearch"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
            <el-button :icon="RefreshLeft" @click="resetFilters">重置</el-button>
          </el-form-item>
        </el-form>

        <el-table stripe
 :data="assets"
 v-loading="loading"border
 row-key="id"
 class="asset-table"
 >
          <el-table-column prop="name" label="资产名称" min-width="160" show-overflow-tooltip />
          <el-table-column prop="asset_type" label="类型" width="110" align="center">
            <template #default="{ row }">
              <el-tag size="small">{{ assetTypeLabel(row.asset_type) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="ip" label="IP地址" width="140" show-overflow-tooltip />
          <el-table-column prop="status" label="状态" width="90" align="center">
            <template #default="{ row }">
              <el-tag :type="assetStatusType(row.status)" size="small">{{ assetStatusLabel(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作系统" min-width="140" show-overflow-tooltip>
            <template #default="{ row }">{{ formatOs(row.os_type, row.os_version) }}</template>
          </el-table-column>
          <el-table-column prop="business_system" label="所属业务" min-width="120" show-overflow-tooltip />
          <el-table-column prop="updated_at" label="更新时间" width="170">
            <template #default="{ row }">{{ formatTime(row.updated_at) }}</template>
          </el-table-column>
        </el-table>

        <!-- Pagination -->
        <div class="pagination-wrapper">
          <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.pageSize"
            :total="pagination.total"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            background
            @change="loadAssets"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh, RefreshLeft, Download } from '@element-plus/icons-vue'
import { Monitor, CircleCheckFilled, SwitchButton, WarningFilled } from '@element-plus/icons-vue'
import client from '@/shared/api/client'
import { API } from '@/shared/api/routes'

// ── State ──────────────────────────────────────────────────────────
const loading = ref(false)
const statsLoading = ref(false)
const assets = ref<any[]>([])
const typeDistribution = ref<any[]>([])

const summaryStats = reactive({
  total: 0,
  online: 0,
  offline: 0,
  abnormal: 0,
  todayNew: 0,
  todayChanged: 0,
})

const filters = reactive({
  type: '',
  status: '',
  keyword: '',
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
})

// ── Helpers ────────────────────────────────────────────────────────
function formatTime(val: string | null | undefined): string {
  if (!val) return '-'
  const d = new Date(val)
  if (isNaN(d.getTime())) return '-'
  const pad = (n: number) => String(n).padStart(2, '0')
  return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()) + ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes()) + ':' + pad(d.getSeconds())
}

function formatOs(osType: string | null | undefined, osVersion: string | null | undefined): string {
  if (!osType && !osVersion) return '-'
  if (osType && osVersion) return osType + ' ' + osVersion
  return osType || osVersion || '-'
}

function assetTypeLabel(t: string): string {
  var map: Record<string, string> = {
    server: '服务器', network: '网络设备', database: '数据库',
    middleware: '中间件', application: '应用', cloud: '云资源', storage: '存储',
    linux_server: 'Linux服务器', web_server: 'Web服务器', windows_server: 'Windows服务器',
  }
  return map[t] || t || '-'
}

function assetStatusType(s: string): string {
  const map: Record<string, string> = { online: 'success', offline: 'info', abnormal: 'danger', unknown: 'warning' }
  return map[s] || 'info'
}

function assetStatusLabel(s: string): string {
  const map: Record<string, string> = { online: '在线', offline: '离线', abnormal: '异常', unknown: '未知' }
  return map[s] || s || '-'
}

// ── Data Loading ───────────────────────────────────────────────────
async function loadDashboardStats() {
  statsLoading.value = true
  try {
    const { data } = await client.get(API.DASHBOARD.STATS)
    if (data.code === 0 && data.data) {
      const d = data.data
      const assetStats = d.asset_stats || d.assets || d
      summaryStats.total = assetStats.total ?? assetStats.total_assets ?? 0
      summaryStats.online = assetStats.online ?? assetStats.online_count ?? 0
      summaryStats.offline = assetStats.offline ?? assetStats.offline_count ?? 0
      summaryStats.abnormal = assetStats.abnormal ?? assetStats.abnormal_count ?? 0
      summaryStats.todayNew = assetStats.today_new ?? assetStats.today_added ?? 0
      summaryStats.todayChanged = assetStats.today_changed ?? 0

      // Type distribution
      typeDistribution.value = assetStats.by_type || assetStats.type_distribution || []
    }
  } catch {
    // silently ignore
  } finally {
    statsLoading.value = false
  }
}

async function loadAssets() {
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: pagination.page,
      page_size: pagination.pageSize,
    }
    if (filters.type) params.asset_type = filters.type
    if (filters.status) params.status = filters.status
    if (filters.keyword) params.keyword = filters.keyword

    const { data } = await client.get(API.ASSETS, { params })
    if (data.code === 0) {
      assets.value = data.data?.items || data.data?.list || []
      pagination.total = data.data?.total || 0

      // Derive summary if dashboard stats not loaded
      if (summaryStats.total === 0) {
        summaryStats.total = pagination.total
      }
    }
  } catch (err: any) {
    ElMessage.error(err.message || '加载资产列表失败')
  } finally {
    loading.value = false
  }
}

function loadAll() {
  loadDashboardStats()
  loadAssets()
}

function handleSearch() {
  pagination.page = 1
  loadAssets()
}

function resetFilters() {
  filters.type = ''
  filters.status = ''
  filters.keyword = ''
  pagination.page = 1
  loadAssets()
}

// ── Export ──────────────────────────────────────────────────────────
function exportReport() {
  if (!assets.value.length) {
    ElMessage.warning('暂无数据可导出')
    return
  }
  const headers = ['资产名称', '类型', 'IP地址', '状态', '操作系统', '所属业务', '更新时间']
  var rows = assets.value.map(function(a) {
    return [
      a.name || '',
      assetTypeLabel(a.asset_type),
      a.ip || '',
      assetStatusLabel(a.status),
      formatOs(a.os_type, a.os_version),
      a.business_system || '',
      formatTime(a.updated_at),
    ]
  })
  const csvContent = [headers.join(','), ...rows.map((r) => r.map(c => '"' + c + '"').join(','))].join('\n')
  const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'asset_report_' + new Date().toISOString().slice(0, 10) + '.csv'
  link.click()
  URL.revokeObjectURL(url)
  ElMessage.success('导出成功')
}

// ── Lifecycle ──────────────────────────────────────────────────────
onMounted(() => {
  loadAll()
})
</script>

<style scoped>
.asset-report-page {
  padding: var(--autops-space-xl);
}
.mb-lg {
  margin-bottom: var(--autops-space-lg);
}

.stats-row {
  margin-bottom: var(--autops-space-lg);
}
.stat-card__body {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: var(--autops-space-xs) 0;
}

.stat-card__icon {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-card__info {
  flex: 1;
  min-width: 0;
}

.stat-card__value {
  font-size: 24px;
  font-weight: 700;
  line-height: 1.2;
}

.stat-card__label {
  font-size: var(--autops-font-12);
  color: var(--autops-info);
  margin-top: 2px;
}

.autops-metric-card--total .stat-card__icon { background: rgba(64, 158, 255, 0.12); color: var(--autops-primary); }
.autops-metric-card--total .stat-card__value { color: var(--autops-primary); }
.autops-metric-card--online .stat-card__icon { background: rgba(103, 194, 58, 0.12); color: var(--autops-success); }
.autops-metric-card--online .stat-card__value { color: var(--autops-success); }
.autops-metric-card--offline .stat-card__icon { background: rgba(144, 147, 153, 0.12); color: var(--autops-info); }
.autops-metric-card--offline .stat-card__value { color: var(--autops-info); }
.autops-metric-card--abnormal .stat-card__icon { background: rgba(245, 108, 108, 0.12); color: var(--autops-danger); }
.autops-metric-card--abnormal .stat-card__value { color: var(--autops-danger); }

.filter-form {
  margin-bottom: var(--autops-space-lg);
  padding-bottom: 16px;
  border-bottom: 1px solid var(--autops-bg-4);
}

.filter-form :deep(.el-form-item) {
  margin-bottom: var(--autops-space-md);
}

.asset-table {
  width: 100%;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: var(--autops-space-lg);
}
</style>
