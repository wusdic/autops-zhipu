<template>
  <div class="event-list-page autops-page-container">
    <PageHeader title="事件流" desc="统一查看与关联分析所有监控事件" />

    <!-- ========== Statistics Row ========== -->
    <el-row :gutter="16" class="stats-row mb-lg">
      <el-col :span="6">
        <div class="autops-card stat-card stat-card--total">
          <div class="stat-card__body">
            <div class="stat-card__icon">
              <el-icon :size="32"><Document /></el-icon>
            </div>
            <div class="stat-card__info">
              <div class="stat-card__value">{{ stats.total }}</div>
              <div class="stat-card__label">事件总数</div>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="autops-card stat-card stat-card--today">
          <div class="stat-card__body">
            <div class="stat-card__icon">
              <el-icon :size="32"><Clock /></el-icon>
            </div>
            <div class="stat-card__info">
              <div class="stat-card__value">{{ stats.today }}</div>
              <div class="stat-card__label">今日事件</div>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="autops-card stat-card stat-card--pending">
          <div class="stat-card__body">
            <div class="stat-card__icon">
              <el-icon :size="32"><Warning /></el-icon>
            </div>
            <div class="stat-card__info">
              <div class="stat-card__value">{{ stats.pending }}</div>
              <div class="stat-card__label">待处理</div>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="autops-card stat-card stat-card--critical">
          <div class="stat-card__body">
            <div class="stat-card__icon">
              <el-icon :size="32"><WarningFilled /></el-icon>
            </div>
            <div class="stat-card__info">
              <div class="stat-card__value">{{ stats.critical }}</div>
              <div class="stat-card__label">严重事件</div>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- ========== Main Card ========== -->
    <div class="autops-card main-card">
      <div class="autops-card-header">
        <span class="autops-card-title">事件列表</span>
        <div class="card-header__actions">
          <el-switch
            v-model="autoRefresh"
            active-text="自动刷新"
            inactive-text=""
            style="margin-right: 12px"
            @change="toggleAutoRefresh"
          />
          <el-button :icon="Download" size="small" @click="exportEvents">导出</el-button>
          <el-button :icon="Refresh" circle size="small" @click="handleSearch" />
        </div>
      </div>
      <div class="autops-card-body">
        <!-- ========== Filters ========== -->
        <el-form :inline="true" class="autops-toolbar filter-form" @submit.prevent="handleSearch">
        <el-form-item label="事件来源">
          <el-select v-model="filters.source" placeholder="全部来源" clearable style="width: 140px">
            <el-option label="采集器" value="collector" />
            <el-option label="状态变更" value="state_change" />
            <el-option label="日志" value="log" />
            <el-option label="配置变更" value="config_change" />
            <el-option label="执行" value="execution" />
          </el-select>
        </el-form-item>
        <el-form-item label="严重级别">
          <el-select v-model="filters.severity" placeholder="全部级别" clearable style="width: 120px">
            <el-option label="严重" value="critical" />
            <el-option label="警告" value="warning" />
            <el-option label="信息" value="info" />
          </el-select>
        </el-form-item>
        <el-form-item label="时间范围">
          <el-select
            v-model="filters.timePreset"
            placeholder="选择范围"
            clearable
            style="width: 130px; margin-right: 8px"
            @change="applyTimePreset"
          >
            <el-option label="最近1小时" value="1h" />
            <el-option label="最近6小时" value="6h" />
            <el-option label="最近24小时" value="24h" />
            <el-option label="最近7天" value="7d" />
            <el-option label="自定义" value="custom" />
          </el-select>
          <el-date-picker
            v-if="filters.timePreset === 'custom'"
            v-model="filters.dateRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            format="YYYY-MM-DD HH:mm"
            value-format="YYYY-MM-DDTHH:mm:ssZ"
            style="width: 360px"
          />
        </el-form-item>
        <el-form-item label="关联资产">
          <el-input
            v-model="filters.asset"
            placeholder="搜索资产名称/ID"
            clearable
            :prefix-icon="Search"
            style="width: 170px"
          />
        </el-form-item>
        <el-form-item label="关键词">
          <el-input
            v-model="filters.keyword"
            placeholder="搜索事件描述"
            clearable
            :prefix-icon="Search"
            style="width: 170px"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
          <el-button :icon="RefreshLeft" @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- ========== Event Table ========== -->
      <el-table stripe
 ref="tableRef"
 :data="events"
 v-loading="loading"border
 row-key="id"
 class="event-table"
 @row-click="handleRowClick"
 :row-class-name="rowClassName"
 >
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="expand-content">
              <el-row :gutter="24">
                <el-col :span="12">
                  <h4 style="margin-bottom: 8px">事件详情</h4>
                  <el-descriptions :column="1" border size="small">
                    <el-descriptions-item label="事件ID">
                      <span style="font-family:monospace;font-size:12px">{{ row.id && row.id.length > 16 ? row.id.slice(0, 8) + '...' + row.id.slice(-4) : (row.id || '-') }}</span>
                    </el-descriptions-item>
                    <el-descriptions-item label="事件类型">
                      <el-tag size="small" :type="(eventTypeTagType(row.event_type)) as TagType">{{ eventTypeLabel(row.event_type) }}</el-tag>
                    </el-descriptions-item>
                    <el-descriptions-item label="来源">
                      <el-tag :type="(sourceTagType(row.source)) as TagType" size="small">{{ sourceLabel(row.source) }}</el-tag>
                    </el-descriptions-item>
                    <el-descriptions-item label="严重级别">
                      <SeverityBadge :severity="row.severity" size="small" />
                    </el-descriptions-item>
                    <el-descriptions-item label="状态">
                      <StatusBadge :status="row.status" size="small" show-icon />
                    </el-descriptions-item>
                    <el-descriptions-item label="关联资产">{{ row.asset_name || row.asset_id || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="创建时间">{{ formatTime(row.created_at) }}</el-descriptions-item>
                    <el-descriptions-item label="更新时间">{{ formatTime(row.updated_at) }}</el-descriptions-item>
                  </el-descriptions>
                </el-col>
                <el-col :span="12">
                  <h4 style="margin-bottom: 8px">描述</h4>
                  <div class="expand-description">{{ row.description || row.title || '无描述' }}</div>
                  <div v-if="row.raw_data" class="mt-md">
                    <h4 style="margin-bottom: 8px">原始数据</h4>
                    <JsonViewer :data="parseJsonSafe(row.raw_data)" />
                  </div>
                </el-col>
              </el-row>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="时间" width="175" sortable="custom">
          <template #default="{ row }">
            <span class="time-cell">{{ formatTime(row.created_at) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="source" label="来源" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="(sourceTagType(row.source)) as TagType" size="small" effect="plain">
              {{ sourceLabel(row.source) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="severity" label="级别" width="90" align="center" sortable="custom">
          <template #default="{ row }">
            <SeverityBadge :severity="row.severity" size="small" />
          </template>
        </el-table-column>
        <el-table-column prop="asset_id" label="关联资产" min-width="140" show-overflow-tooltip>
          <template #default="{ row }">
            <span style="font-family:monospace;font-size:12px">{{ row.asset_id?.substring(0,8) || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="detail" label="描述" min-width="220" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.detail || row.title || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="event_type" label="类型" width="120" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="(eventTypeTagType(row.event_type)) as TagType">{{ eventTypeLabel(row.event_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" plain @click.stop="openDetailDrawer(row)">详情</el-button>
            <el-button size="small" plain @click.stop="viewRelatedEvents(row)">关联</el-button>
          </template>
        </el-table-column>
      </el-table>

        <!-- ========== Pagination ========== -->
        <div class="pagination-wrapper">
          <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.pageSize"
            :total="pagination.total"
            :page-sizes="[20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            background
            @change="loadEvents"
          />
        </div>
      </div>
    </div>

    <!-- ========== Event Detail Drawer ========== -->
    <el-drawer
      v-model="drawerVisible"
      :title="drawerTitle"
      size="620px"
      :destroy-on-close="true"
    >
      <template v-if="currentEvent">
        <el-tabs v-model="drawerTab">
          <!-- Tab: Basic Info -->
          <el-tab-pane label="基本信息" name="info">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="事件ID">
                <span style="font-family:monospace;font-size:12px">{{ currentEvent.id && currentEvent.id.length > 16 ? currentEvent.id.slice(0, 8) + '...' + currentEvent.id.slice(-4) : (currentEvent.id || '-') }}</span>
              </el-descriptions-item>
              <el-descriptions-item label="事件类型">
                <el-tag size="small" :type="(eventTypeTagType(currentEvent.event_type)) as TagType">{{ eventTypeLabel(currentEvent.event_type) }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="来源">
                <el-tag :type="(sourceTagType(currentEvent.source)) as TagType" size="small">
                  {{ sourceLabel(currentEvent.source) }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="严重级别">
                <SeverityBadge :severity="currentEvent.severity" size="small" />
              </el-descriptions-item>
              <el-descriptions-item label="状态">
                <StatusBadge :status="currentEvent.status" size="small" show-icon />
              </el-descriptions-item>
              <el-descriptions-item label="关联资产">
                {{ currentEvent.asset_name || currentEvent.asset?.name || currentEvent.asset_id || '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="创建时间">{{ formatTime(currentEvent.created_at) }}</el-descriptions-item>
              <el-descriptions-item label="更新时间">{{ formatTime(currentEvent.updated_at) }}</el-descriptions-item>
              <el-descriptions-item label="描述" :span="2">
                {{ currentEvent.description || currentEvent.title || '无描述' }}
              </el-descriptions-item>
            </el-descriptions>

            <!-- Raw Data -->
            <div v-if="currentEvent.raw_data" class="mt-lg">
              <h4 style="margin-bottom: 8px">原始数据</h4>
              <JsonViewer :data="parseJsonSafe(currentEvent.raw_data)" />
            </div>
          </el-tab-pane>

          <!-- Tab: Related Alerts -->
          <el-tab-pane name="alerts">
            <template #label>
              <span>关联告警 <el-badge :value="relatedAlerts.length" :max="99" class="tab-badge" /></span>
            </template>
            <el-table stripe :data="relatedAlerts" v-loading="relatedLoading"size="small" max-height="400">
              <el-table-column prop="severity" label="级别" width="80" align="center">
                <template #default="{ row }">
                  <SeverityBadge :severity="row.severity" size="small" />
                </template>
              </el-table-column>
              <el-table-column prop="title" label="告警标题" min-width="180" show-overflow-tooltip />
              <el-table-column prop="status" label="状态" width="100" align="center">
                <template #default="{ row }">
                  <StatusBadge :status="row.status" size="small" />
                </template>
              </el-table-column>
              <el-table-column prop="triggered_at" label="触发时间" width="160">
                <template #default="{ row }">{{ formatTime(row.triggered_at || row.created_at) }}</template>
              </el-table-column>
            </el-table>
            <el-empty v-if="!relatedLoading && relatedAlerts.length === 0" description="暂无关联告警" />
          </el-tab-pane>

          <!-- Tab: Related Logs -->
          <el-tab-pane name="logs">
            <template #label>
              <span>相关日志 <el-badge :value="relatedLogs.length" :max="99" class="tab-badge" /></span>
            </template>
            <div v-if="relatedLogs.length > 0" class="log-list">
              <div v-for="(log, idx) in relatedLogs" :key="idx" class="log-item">
                <div class="log-item__header">
                  <span class="log-item__time">{{ formatTime(log.created_at || log.timestamp) }}</span>
                  <el-tag v-if="log.level" :type="(logLevelType(log.level)) as TagType" size="small">{{ log.level }}</el-tag>
                </div>
                <div class="log-item__message">{{ log.message || log.content || log.output || '-' }}</div>
              </div>
            </div>
            <el-empty v-if="relatedLogs.length === 0" description="暂无相关日志" />
          </el-tab-pane>

          <!-- Tab: Timeline -->
          <el-tab-pane label="时间线" name="timeline">
            <TimelineView :items="eventTimeline" />
          </el-tab-pane>
        </el-tabs>
      </template>
    </el-drawer>

    <!-- ========== Event Correlation Drawer ========== -->
    <el-drawer
      v-model="correlationVisible"
      title="事件关联分析"
      size="620px"
      :destroy-on-close="true"
    >
      <div v-if="correlationEvent" class="correlation-drawer">
        <el-alert
          :title="'基于事件: ' + correlationEvent.description || correlationEvent.title || correlationEvent.id"
          type="info"
          :closable="false"
          show-icon
          class="mb-lg"
        />

        <el-descriptions :column="2" border size="small" class="mb-lg">
          <el-descriptions-item label="来源">{{ sourceLabel(correlationEvent.source) }}</el-descriptions-item>
          <el-descriptions-item label="严重级别">
            <SeverityBadge :severity="correlationEvent.severity" size="small" />
          </el-descriptions-item>
          <el-descriptions-item label="关联资产">{{ correlationEvent.asset_name || correlationEvent.asset_id || '-' }}</el-descriptions-item>
          <el-descriptions-item label="时间">{{ formatTime(correlationEvent.created_at) }}</el-descriptions-item>
        </el-descriptions>

        <h4 style="margin-bottom: 8px">相关事件 (同一资产 / 相似来源)</h4>
        <el-table stripe
 :data="correlatedEvents"
 v-loading="correlationLoading"size="small"
 max-height="400"
 >
          <el-table-column prop="created_at" label="时间" width="160">
            <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
          </el-table-column>
          <el-table-column prop="source" label="来源" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="(sourceTagType(row.source)) as TagType" size="small">{{ sourceLabel(row.source) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="severity" label="级别" width="80" align="center">
            <template #default="{ row }">
              <SeverityBadge :severity="row.severity" size="small" />
            </template>
          </el-table-column>
          <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip>
            <template #default="{ row }">{{ row.description || row.title || '-' }}</template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="90" align="center">
            <template #default="{ row }">
              <StatusBadge :status="row.status" size="small" />
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-if="!correlationLoading && correlatedEvents.length === 0" description="未发现相关事件" />
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import type { TagType } from '@/shared/types'
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Search,
  Refresh,
  RefreshLeft,
  Download,
  Document,
  Clock,
  Warning,
  WarningFilled,
} from '@element-plus/icons-vue'
import api from '@/shared/api/client'
import PageHeader from '@/shared/components/PageHeader.vue'
import { API as R } from '@/shared/api/routes'
import StatusBadge from '@/shared/components/StatusBadge.vue'
import SeverityBadge from '@/shared/components/SeverityBadge.vue'
import JsonViewer from '@/shared/components/JsonViewer.vue'
import TimelineView from '@/shared/components/TimelineView.vue'

// ── State ──────────────────────────────────────────────────────────
const loading = ref(false)
const events = ref<any[]>([])
const tableRef = ref()

const stats = reactive({
  total: 0,
  today: 0,
  pending: 0,
  critical: 0,
})

const filters = reactive({
  source: '',
  severity: '',
  timePreset: '' as string,
  dateRange: null as [string, string] | null,
  asset: '',
  keyword: '',
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
})

// Auto-refresh
const autoRefresh = ref(false)
let refreshTimer: ReturnType<typeof setInterval> | null = null

// Detail drawer
const drawerVisible = ref(false)
const drawerTab = ref('info')
const currentEvent = ref<any>(null)
const relatedAlerts = ref<any[]>([])
const relatedLogs = ref<any[]>([])
const relatedLoading = ref(false)

// Correlation drawer
const correlationVisible = ref(false)
const correlationEvent = ref<any>(null)
const correlatedEvents = ref<any[]>([])
const correlationLoading = ref(false)

// ── Computed ────────────────────────────────────────────────────────
const drawerTitle = computed(() => {
  if (!currentEvent.value) return '事件详情'
  const desc = currentEvent.value.description || currentEvent.value.title || '事件'
  return desc.length > 30 ? desc.substring(0, 30) + '...' : desc
})

const eventTimeline = computed(() => {
  if (!currentEvent.value) return []
  const items: Array<Record<string, any>> = []

  // Created
  items.push({
    time: currentEvent.value.created_at,
    title: '事件创建',
    description: currentEvent.value.description || currentEvent.value.title,
    type: currentEvent.value.severity || 'info',
  })

  // Status changes
  if (currentEvent.value.acknowledged_at) {
    items.push({
      time: currentEvent.value.acknowledged_at,
      title: '事件确认',
      description: '事件已被确认处理',
      type: 'warning',
    })
  }

  if (currentEvent.value.resolved_at) {
    items.push({
      time: currentEvent.value.resolved_at,
      title: '事件恢复',
      description: '事件已恢复正常',
      type: 'success',
    })
  }

  if (currentEvent.value.updated_at && currentEvent.value.updated_at !== currentEvent.value.created_at) {
    items.push({
      time: currentEvent.value.updated_at,
      title: '最后更新',
      description: '事件信息已更新',
      type: '',
    })
  }

  // Sort by time
  items.sort((a, b) => new Date(a.time || 0).getTime() - new Date(b.time || 0).getTime())
  return items
})

// ── Helpers ─────────────────────────────────────────────────────────
function formatTime(val: string | null | undefined): string {
  if (!val) return '-'
  const d = new Date(val)
  if (isNaN(d.getTime())) return '-'
  const pad = (n: number) => String(n).padStart(2, '0')
  return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()) + ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes()) + ':' + pad(d.getSeconds())
}

function parseJsonSafe(raw: any): any {
  if (typeof raw === 'object') return raw
  try { return JSON.parse(raw) } catch { return raw }
}

function sourceLabel(source: string): string {
  const map: Record<string, string> = {
    collector: '采集器',
    state_change: '状态变更',
    log: '日志',
    config_change: '配置变更',
    execution: '执行',
  }
  return map[source] || source || '-'
}

function sourceTagType(source: string): TagType {
  const map: Record<string, string> = {
    collector: '',
    state_change: 'warning',
    log: 'info',
    config_change: 'success',
    execution: '',
  }
  return (map[source] || 'info') as TagType
}

function eventTypeLabel(type: string): string {
  var map: Record<string, string> = {
    alert_triggered: '告警触发',
    alert_resolved: '告警恢复',
    alert_suppressed: '告警抑制',
    state_changed: '状态变更',
    config_changed: '配置变更',
    asset_discovered: '资产发现',
    asset_offline: '资产离线',
    asset_online: '资产上线',
    execution_started: '执行开始',
    execution_completed: '执行完成',
    execution_failed: '执行失败',
    threshold_exceeded: '阈值超限',
    anomaly_detected: '异常检测',
    health_check: '健康检查',
    system: '系统事件',
  }
  return map[type] || type || '-'
}

function eventTypeTagType(type: string): TagType {
  var map: Record<string, string> = {
    alert_triggered: 'danger',
    alert_resolved: 'success',
    alert_suppressed: 'info',
    state_changed: 'warning',
    config_changed: '',
    asset_discovered: 'success',
    asset_offline: 'danger',
    asset_online: 'success',
    execution_started: '',
    execution_completed: 'success',
    execution_failed: 'danger',
    threshold_exceeded: 'danger',
    anomaly_detected: 'warning',
    health_check: 'info',
    system: 'info',
  }
  return (map[type] || 'info') as TagType
}

function logLevelType(level: string): TagType {
  const map: Record<string, string> = {
    error: 'danger',
    ERROR: 'danger',
    warn: 'warning',
    WARNING: 'warning',
    info: 'info',
    INFO: '',
    debug: 'info',
    DEBUG: 'info',
  }
  return (map[level] || 'info') as TagType
}

function rowClassName({ row }: { row: any }): string {
  if (row.severity === 'critical' && row.status !== 'resolved') return 'row--critical'
  return ''
}

// ── Time Preset ─────────────────────────────────────────────────────
function applyTimePreset(val: string) {
  if (!val || val === 'custom') return
  const now = new Date()
  let start: Date
  switch (val) {
    case '1h': start = new Date(now.getTime() - 3600_000); break
    case '6h': start = new Date(now.getTime() - 6 * 3600_000); break
    case '24h': start = new Date(now.getTime() - 24 * 3600_000); break
    case '7d': start = new Date(now.getTime() - 7 * 86400_000); break
    default: return
  }
  filters.dateRange = [start.toISOString(), now.toISOString()] as [string, string]
}

// ── API: Statistics ─────────────────────────────────────────────────
async function loadStats() {
  try {
    const params: Record<string, any> = {}
    const { data } = await api.get(R.EVENTS, { params: { page: 1, page_size: 1 } })
    if (data.code === 0 && data.data) {
      stats.total = data.data.total || 0
    }

    // Today count
    const todayStart = new Date()
    todayStart.setHours(0, 0, 0, 0)
    const { data: todayData } = await api.get(R.EVENTS, {
      params: { page: 1, page_size: 1, start_time: todayStart.toISOString() },
    })
    if (todayData.code === 0 && todayData.data) {
      stats.today = todayData.data.total || 0
    }

    // Pending count (status not resolved)
    const { data: pendingData } = await api.get(R.EVENTS, {
      params: { page: 1, page_size: 1, status: 'pending' },
    })
    if (pendingData.code === 0 && pendingData.data) {
      stats.pending = pendingData.data.total || 0
    }

    // Critical count
    const { data: criticalData } = await api.get(R.EVENTS, {
      params: { page: 1, page_size: 1, severity: 'critical' },
    })
    if (criticalData.code === 0 && criticalData.data) {
      stats.critical = criticalData.data.total || 0
    }
  } catch {
    // stats are non-critical
  }
}

// ── API: Event List ─────────────────────────────────────────────────
async function loadEvents() {
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: pagination.page,
      page_size: pagination.pageSize,
    }
    if (filters.source) params.source = filters.source
    if (filters.severity) params.severity = filters.severity
    if (filters.asset) params.asset_id = filters.asset
    if (filters.keyword) params.keyword = filters.keyword
    if (filters.dateRange && filters.dateRange.length === 2) {
      params.start_time = filters.dateRange[0]
      params.end_time = filters.dateRange[1]
    }

    const { data } = await api.get(R.EVENTS, { params })
    if (data.code === 0) {
      events.value = data.data.items || data.data.list || []
      pagination.total = data.data.total || 0
    }
  } catch {
    ElMessage.error('加载事件列表失败')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  pagination.page = 1
  loadEvents()
  loadStats()
}

function resetFilters() {
  filters.source = ''
  filters.severity = ''
  filters.timePreset = ''
  filters.dateRange = null
  filters.asset = ''
  filters.keyword = ''
  pagination.page = 1
  loadEvents()
  loadStats()
}

// ── Row Click → Toggle Expand ───────────────────────────────────────
function handleRowClick(row: any) {
  tableRef.value?.toggleRowExpansion(row)
}

// ── Detail Drawer ───────────────────────────────────────────────────
async function openDetailDrawer(row: any) {
  currentEvent.value = row
  drawerTab.value = 'info'
  drawerVisible.value = true

  // Fetch full detail
  try {
    const { data } = await api.get(R.EVENT_DETAIL(row.id))
    if (data.code === 0 && data.data) {
      currentEvent.value = data.data
    }
  } catch {
    // Use the row data we already have
  }

  // Load related alerts & logs in parallel
  loadRelatedAlerts(row)
  loadRelatedLogs(row)
}

async function loadRelatedAlerts(event: any) {
  relatedLoading.value = true
  relatedAlerts.value = []
  try {
    const params: Record<string, any> = { page: 1, page_size: 20 }
    if (event.asset_id) params.asset = event.asset_id
    const { data } = await api.get(R.ALERTS, { params })
    if (data.code === 0) {
      relatedAlerts.value = (data.data.items || data.data.list || []).filter(
        (a: any) => a.id !== event.id
      )
    }
  } catch {
    // non-critical
  } finally {
    relatedLoading.value = false
  }
}

async function loadRelatedLogs(event: any) {
  relatedLogs.value = []
  if (!event.execution_id && !event.exec_id) return

  const execId = event.execution_id || event.exec_id
  try {
    const { data } = await api.get(R.LOGS.EXECUTION(execId))
    if (data.code === 0 && data.data) {
      relatedLogs.value = Array.isArray(data.data) ? data.data : (data.data.items || data.data.logs || [])
    }
  } catch {
    // non-critical
  }
}

// ── Correlation Analysis ────────────────────────────────────────────
async function viewRelatedEvents(event: any) {
  correlationEvent.value = event
  correlationVisible.value = true
  correlationLoading.value = true
  correlatedEvents.value = []

  try {
    const params: Record<string, any> = { page: 1, page_size: 20 }
    // Query by same asset or similar source
    if (event.asset_id) params.asset_id = event.asset_id
    if (event.source) params.source = event.source

    const { data } = await api.get(R.EVENTS, { params })
    if (data.code === 0) {
      correlatedEvents.value = (data.data.items || data.data.list || []).filter(
        (e: any) => e.id !== event.id
      )
    }
  } catch {
    ElMessage.error('加载关联事件失败')
  } finally {
    correlationLoading.value = false
  }
}

// ── Auto-Refresh ────────────────────────────────────────────────────
function toggleAutoRefresh(val: string | number | boolean) {
  if (val) {
    refreshTimer = setInterval(() => {
      loadEvents()
      loadStats()
    }, 30_000)
    ElMessage.success('已开启自动刷新（每30秒）')
  } else {
    if (refreshTimer) {
      clearInterval(refreshTimer)
      refreshTimer = null
    }
    ElMessage.info('已关闭自动刷新')
  }
}

// ── Export ──────────────────────────────────────────────────────────
function exportEvents() {
  if (events.value.length === 0) {
    ElMessage.warning('暂无数据可导出')
    return
  }

  const headers = ['ID', '时间', '来源', '严重级别', '关联资产', '描述', '状态']
  const rows = events.value.map((e) => [
    e.id,
    formatTime(e.created_at),
    sourceLabel(e.source),
    e.severity || '',
    e.asset_name || e.asset_id || '',
    (e.description || e.title || '').replace(/"/g, '""'),
    e.status || '',
  ])

  const csvContent = [
    headers.join(','),
    ...rows.map((r) => r.map((cell) => '"' + cell + '"').join(',')),
  ].join('\n')

  const BOM = '\uFEFF'
  const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = 'events_' + new Date().toISOString().slice(0, 10) + '.csv'
  link.click()
  URL.revokeObjectURL(link.href)
  ElMessage.success('导出成功')
}

// ── Lifecycle ───────────────────────────────────────────────────────
onMounted(() => {
  loadStats()
  loadEvents()
})

onBeforeUnmount(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
})
</script>

<style scoped>
.event-list-page {
  padding: var(--autops-space-xl);
}

/* ── Statistics Cards ── */
.stats-row {
  margin-bottom: var(--autops-space-lg);
}
.stat-card__body {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-card__icon {
  width: 56px;
  height: 56px;
  border-radius: var(--autops-radius-lg);
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
  font-size: 28px;
  font-weight: 700;
  line-height: 1.2;
}

.stat-card__label {
  font-size: var(--autops-font-13);
  color: var(--autops-info);
  margin-top: 4px;
}

.autops-metric-card--total .stat-card__icon {
  background: rgba(64, 158, 255, 0.12);
  color: var(--autops-primary);
}
.autops-metric-card--total .stat-card__value {
  color: var(--autops-primary);
}

.autops-metric-card--today .stat-card__icon {
  background: rgba(103, 194, 58, 0.12);
  color: var(--autops-success);
}
.autops-metric-card--today .stat-card__value {
  color: var(--autops-success);
}

.autops-metric-card--pending .stat-card__icon {
  background: rgba(230, 162, 60, 0.12);
  color: var(--autops-warning);
}
.autops-metric-card--pending .stat-card__value {
  color: var(--autops-warning);
}

.autops-metric-card--critical .stat-card__icon {
  background: rgba(245, 108, 108, 0.12);
  color: var(--autops-danger);
}
.autops-metric-card--critical .stat-card__value {
  color: var(--autops-danger);
}

/* ── Main Card ── */
.main-card {
  border-radius: var(--autops-radius-md);
}
/* ── Filter Form ── */
.filter-form {
  margin-bottom: var(--autops-space-lg);
  padding-bottom: 16px;
  border-bottom: 1px solid var(--autops-bg-4);
}

.filter-form :deep(.el-form-item) {
  margin-bottom: var(--autops-space-md);
}

/* ── Event Table ── */
.event-table {
  width: 100%;
}

.event-table :deep(.row--critical) {
  background-color: var(--autops-danger-light) !important;
}

.event-table :deep(.row--critical:hover > td) {
  background-color: var(--autops-danger-light) !important;
}

.event-table :deep(.el-table__expanded-cell) {
  padding: var(--autops-space-lg) 24px;
}

.time-cell {
  font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
  font-size: var(--autops-font-13);
  color: var(--autops-text-2);
}

/* ── Expand Content ── */
.expand-content {
  padding: var(--autops-space-xs) 0;
}

.expand-description {
  background: var(--autops-bg-2);
  padding: var(--autops-space-md);
  border-radius: 6px;
  font-size: var(--autops-font-13);
  line-height: 1.6;
  color: var(--autops-text-2);
  white-space: pre-wrap;
  word-break: break-all;
}

/* ── Pagination ── */
.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: var(--autops-space-lg);
}

/* ── Tab Badge ── */
.tab-badge :deep(.el-badge__content) {
  top: 2px;
}

/* ── Log List ── */
.log-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.log-item {
  background: var(--autops-bg-2);
  border-radius: 6px;
  padding: 10px 12px;
}

.log-item__header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.log-item__time {
  font-size: var(--autops-font-12);
  color: var(--autops-info);
  font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
}

.log-item__message {
  font-size: var(--autops-font-13);
  color: var(--autops-text-1);
  white-space: pre-wrap;
  word-break: break-all;
  line-height: 1.5;
  max-height: 120px;
  overflow-y: auto;
}

/* ── Correlation Drawer ── */
.correlation-drawer {
  padding: 0 4px;
}

/* ── Responsive ── */
@media (max-width: 1200px) {
  .filter-form :deep(.el-form-item__content) {
    max-width: 160px;
  }
  .filter-form :deep(.el-date-editor) {
    width: 280px !important;
  }
}
</style>
