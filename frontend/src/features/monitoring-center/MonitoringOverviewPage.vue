<template>
  <div class="monitoring-overview">
    <!-- ========== Page Header ========== -->
    <div class="autops-page-header">
      <div>
        <div class="autops-page-title">监控总览</div>
        <div class="autops-page-subtitle">实时监控概览，包括事件趋势、告警分布与状态变更</div>
      </div>
    </div>

    <!-- ===== 顶部统计卡片 ===== -->
    <el-row :gutter="16" class="stat-cards mb-lg">
      <el-col :span="6">
        <div class="autops-card stat-card stat-events">
          <div class="autops-card-body">
            <div class="stat-card-inner">
              <el-icon :size="36" color="#E6A23C"><Bell /></el-icon>
              <div class="stat-card-info">
                <div class="stat-card-value">{{ overview.activeEvents24h }}</div>
                <div class="stat-card-label">24h 活跃事件</div>
              </div>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="autops-card stat-card stat-alerts">
          <div class="autops-card-body">
            <div class="stat-card-inner">
              <el-icon :size="36" color="#F56C6C"><WarningFilled /></el-icon>
              <div class="stat-card-info">
                <div class="stat-card-value">{{ overview.activeAlerts }}</div>
                <div class="stat-card-label">活跃告警</div>
              </div>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="autops-card stat-card stat-assets">
          <div class="autops-card-body">
            <div class="stat-card-inner">
              <el-icon :size="36" color="#409EFF"><Monitor /></el-icon>
              <div class="stat-card-info">
                <div class="stat-card-value">{{ overview.totalAssets }}</div>
                <div class="stat-card-label">监控资产总数</div>
              </div>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="autops-card stat-card stat-rate">
          <div class="autops-card-body">
            <div class="stat-card-inner">
              <el-icon :size="36" color="#67C23A"><CircleCheckFilled /></el-icon>
              <div class="stat-card-info">
                <div class="stat-card-value">{{ overview.collectionRate }}<span class="stat-unit">%</span></div>
                <div class="stat-card-label">采集成功率</div>
              </div>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- ===== 主内容区 ===== -->
    <el-row :gutter="16">
      <!-- 左栏 span=16 -->
      <el-col :span="16">
        <!-- 事件趋势图（24h，按严重级别分组） -->
        <div class="autops-card">
          <div class="autops-card-header">
            <span class="autops-card-title">事件趋势（近 24 小时）</span>
            <el-button text type="primary" @click="loadEventTrend">刷新</el-button>
          </div>
          <div class="autops-card-body">
            <div v-loading="trendLoading">
              <MetricChart
                :multiple="trendSeries"
                :data="[]"
                title="每小时事件数"
                height="320px"
                unit=" 次"
              />
            </div>
          </div>
        </div>

        <!-- 告警严重级别分布饼图 -->
        <div class="autops-card" style="margin-top: 16px">
          <div class="autops-card-header">
            <span class="autops-card-title">告警严重级别分布</span>
            <el-button text type="primary" @click="loadSeverityDist">刷新</el-button>
          </div>
          <div class="autops-card-body">
            <div v-loading="severityLoading">
              <MetricChart
                :data="severityData"
                title=""
                chart-type="pie"
                height="300px"
              />
            </div>
          </div>
        </div>
      </el-col>

      <!-- 右栏 span=8 -->
      <el-col :span="8">
        <!-- 最近事件列表 -->
        <div class="autops-card">
          <div class="autops-card-header">
            <span class="autops-card-title">最近事件</span>
            <el-button text type="primary" @click="$router.push('/monitoring/events')">查看全部</el-button>
          </div>
          <div class="autops-card-body">
            <div v-loading="eventsLoading" class="recent-events-list">
              <div
                v-for="item in recentEvents"
                :key="item.id"
                class="recent-event-item"
              >
                <SeverityBadge :severity="item.severity" size="small" />
                <div class="recent-event-content">
                  <span class="recent-event-title" :title="item.title">{{ item.title }}</span>
                  <span class="recent-event-time">{{ formatTime(item.created_at) }}</span>
                </div>
              </div>
              <el-empty v-if="!eventsLoading && recentEvents.length === 0" description="暂无事件" :image-size="60" />
            </div>
          </div>
        </div>

        <!-- 告警最多的资产 -->
        <div class="autops-card" style="margin-top: 16px">
          <div class="autops-card-header">
            <span class="autops-card-title">告警最多资产 TOP 10</span>
          </div>
          <div class="autops-card-body">
            <div v-loading="topAssetsLoading" class="top-assets-list">
              <div
                v-for="(item, idx) in topAlertAssets"
                :key="item.asset_id ?? idx"
                class="top-asset-item"
              >
                <span class="top-asset-rank">{{ idx + 1 }}</span>
                <span class="top-asset-name" :title="item.asset_name">{{ item.asset_name }}</span>
                <div class="top-asset-bar-wrap">
                  <div
                    class="top-asset-bar"
                    :style="{
                      width: barWidth(item.alert_count),
                      backgroundColor: barColor(item.alert_count),
                    }"
                  />
                  <span class="top-asset-count">{{ item.alert_count }}</span>
                </div>
              </div>
              <el-empty v-if="!topAssetsLoading && topAlertAssets.length === 0" description="暂无数据" :image-size="60" />
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- ===== 底部：状态变更时间线 ===== -->
    <div class="autops-card" style="margin-top: 16px">
      <div class="autops-card-header">
        <span class="autops-card-title">最近状态变更</span>
        <el-button text type="primary" @click="loadChanges">刷新</el-button>
      </div>
      <div class="autops-card-body">
        <el-table :data="changes" v-loading="changesLoading" stripe>
          <el-table-column label="资产" min-width="140" show-overflow-tooltip>
            <template #default="{ row }">
              <span style="font-family:monospace;font-size:12px">{{ row.asset_id?.substring(0,8) || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="state_type" label="类型" width="100">
            <template #default="{ row }">
              <el-tag size="small" type="info">{{ row.state_type || '-' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="变更前" width="120">
            <template #default="{ row }">
              <StatusBadge :status="row.old_status" size="small" />
            </template>
          </el-table-column>
          <el-table-column label="变更后" width="120">
            <template #default="{ row }">
              <StatusBadge :status="row.new_status" size="small" show-icon />
            </template>
          </el-table-column>
          <el-table-column prop="old_value" label="旧值" width="80" show-overflow-tooltip />
          <el-table-column prop="new_value" label="新值" width="80" show-overflow-tooltip />
          <el-table-column prop="created_at" label="变更时间" width="180">
            <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
          </el-table-column>
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Bell, WarningFilled, Monitor, CircleCheckFilled } from '@element-plus/icons-vue'
import api from '@/shared/api/client'
import { API as R } from '@/shared/api/routes'
import MetricChart from '@/shared/components/MetricChart.vue'
import StatusBadge from '@/shared/components/StatusBadge.vue'
import SeverityBadge from '@/shared/components/SeverityBadge.vue'

// ===================== 顶部概览统计 =====================
const overview = reactive({
  activeEvents24h: 0,
  activeAlerts: 0,
  totalAssets: 0,
  collectionRate: 0,
})

async function loadOverview() {
  try {
    // 并行拉取三项数据
    const [alertStatsRes, assetsRes, collectionRes] = await Promise.allSettled([
      api.get(R.ALERT_STATS),
      api.get(R.ASSETS, { params: { page: 1, page_size: 1 } }),
      api.get(R.COLLECTION_JOBS, { params: { page: 1, page_size: 1 } }),
    ])

    // 告警统计
    if (alertStatsRes.status === 'fulfilled') {
      const d = alertStatsRes.value.data?.data
      if (alertStatsRes.value.data?.code === 0 && d) {
        overview.activeAlerts = d.active ?? d.active_alerts ?? 0
        overview.activeEvents24h = d.events_24h ?? d.active_events_24h ?? 0
      }
    }

    // 资产总数
    if (assetsRes.status === 'fulfilled') {
      const d = assetsRes.value.data?.data
      if (assetsRes.value.data?.code === 0) {
        overview.totalAssets = d?.total ?? d?.items?.length ?? 0
      }
    }

    // 采集成功率
    if (collectionRes.status === 'fulfilled') {
      const d = collectionRes.value.data?.data
      if (collectionRes.value.data?.code === 0) {
        overview.collectionRate = d?.success_rate ?? d?.collection_rate ?? 0
      }
    }
  } catch {
    // 静默处理，卡片显示 0
  }
}

// ===================== 事件趋势（24h，severity 分组） =====================
const trendLoading = ref(false)
const trendSeries = ref<Array<{ name: string; data: Array<{ time: string; value: number }>; color: string }>>([])

const severityColors: Record<string, string> = {
  critical: '#F56C6C',
  high: '#E6A23C',
  medium: '#409EFF',
  low: '#67C23A',
  info: '#909399',
}

async function loadEventTrend() {
  trendLoading.value = true
  try {
    const { data } = await api.get(R.EVENTS, {
      params: { range: '24h', aggregation: 'hourly', group_by: 'severity' },
    })
    if (data.code === 0 && Array.isArray(data.data?.series)) {
      trendSeries.value = data.data.series.map((s: any) => ({
        name: s.name ?? s.severity ?? '事件',
        data: (s.items ?? s.data ?? []).map((t: any) => ({
          time: t.time ?? t.hour ?? '',
          value: t.value ?? t.count ?? 0,
        })),
        color: severityColors[s.severity ?? s.name] ?? '#409EFF',
      }))
    } else if (data.code === 0 && Array.isArray(data.data?.items)) {
      // 降级：接口不按 severity 分组时单线显示
      trendSeries.value = [{
        name: '事件',
        data: data.data.items.map((t: any) => ({
          time: t.time ?? t.hour ?? '',
          value: t.value ?? t.count ?? 1,
        })),
        color: '#409EFF',
      }]
    }
  } catch {
    ElMessage.error('加载事件趋势失败')
  } finally {
    trendLoading.value = false
  }
}

// ===================== 告警严重级别分布（饼图） =====================
const severityLoading = ref(false)
const severityData = ref<Array<{ time: string; value: number }>>([])

async function loadSeverityDist() {
  severityLoading.value = true
  try {
    const { data } = await api.get(R.ALERT_STATS, { params: { group_by: 'severity' } })
    if (data.code === 0 && data.data) {
      const d = data.data
      // 适配后端返回格式: { severity_dist: [...] } 或直接 { critical: N, high: N, ... }
      if (Array.isArray(d.severity_dist)) {
        severityData.value = d.severity_dist.map((s: any) => ({
          time: s.severity ?? s.name,
          value: s.count ?? s.value ?? 0,
        }))
      } else {
        const severityLabels: Record<string, string> = {
          critical: '严重', high: '高', medium: '中', low: '低', info: '信息',
        }
        const entries = Object.entries(d)
          .filter(([k]) => severityLabels[k])
          .map(([k, v]) => ({ time: severityLabels[k], value: Number(v) ?? 0 }))
        severityData.value = entries.length ? entries : defaultSeverityData()
      }
    }
  } catch {
    severityData.value = defaultSeverityData()
  } finally {
    severityLoading.value = false
  }
}

function defaultSeverityData() {
  return [
    { time: '严重', value: 0 },
    { time: '高', value: 0 },
    { time: '中', value: 0 },
    { time: '低', value: 0 },
    { time: '信息', value: 0 },
  ]
}

// ===================== 最近事件列表 =====================
const eventsLoading = ref(false)
const recentEvents = ref<any[]>([])

async function loadRecentEvents() {
  eventsLoading.value = true
  try {
    const { data } = await api.get(R.EVENTS, { params: { page: 1, page_size: 20 } })
    if (data.code === 0) {
      recentEvents.value = data.data?.items ?? data.data ?? []
    }
  } catch {
    ElMessage.error('加载最近事件失败')
  } finally {
    eventsLoading.value = false
  }
}

// ===================== 告警最多资产 TOP 10 =====================
const topAssetsLoading = ref(false)
const topAlertAssets = ref<Array<{ asset_id?: string; asset_name: string; alert_count: number }>>([])

const maxAlertCount = computed(() => {
  if (topAlertAssets.value.length === 0) return 1
  return Math.max(...topAlertAssets.value.map(a => a.alert_count), 1)
})

function barWidth(count: number) {
  return `${Math.max((count / maxAlertCount.value) * 100, 4)}%`
}

function barColor(count: number) {
  const ratio = count / maxAlertCount.value
  if (ratio > 0.7) return '#F56C6C'
  if (ratio > 0.4) return '#E6A23C'
  return '#409EFF'
}

async function loadTopAlertAssets() {
  topAssetsLoading.value = true
  try {
    const { data } = await api.get(R.ALERT_STATS, { params: { group_by: 'asset', top: 10 } })
    if (data.code === 0) {
      const d = data.data
      if (Array.isArray(d.top_assets)) {
        topAlertAssets.value = d.top_assets.map((a: any) => ({
          asset_id: a.asset_id ?? a.id,
          asset_name: a.asset_name ?? a.name ?? '未知',
          alert_count: a.alert_count ?? a.count ?? 0,
        }))
      } else if (Array.isArray(d)) {
        topAlertAssets.value = d.slice(0, 10).map((a: any) => ({
          asset_id: a.asset_id ?? a.id,
          asset_name: a.asset_name ?? a.name ?? '未知',
          alert_count: a.alert_count ?? a.count ?? 0,
        }))
      }
    }
  } catch {
    ElMessage.error('加载告警资产排名失败')
  } finally {
    topAssetsLoading.value = false
  }
}

// ===================== 状态变更时间线 =====================
const changesLoading = ref(false)
const changes = ref<any[]>([])

async function loadChanges() {
  changesLoading.value = true
  try {
    const { data } = await api.get(R.STATES.ALL_CHANGES, { params: { page: 1, page_size: 20 } })
    if (data.code === 0) {
      changes.value = data.data?.items ?? data.data ?? []
    }
  } catch {
    ElMessage.error('加载状态变更失败')
  } finally {
    changesLoading.value = false
  }
}

// ===================== 工具函数 =====================
function formatTime(t: string) {
  return t ? new Date(t).toLocaleString('zh-CN') : ''
}

// ===================== 初始化 =====================
onMounted(() => {
  loadOverview()
  loadEventTrend()
  loadSeverityDist()
  loadRecentEvents()
  loadTopAlertAssets()
  loadChanges()
})
</script>

<style scoped>
/* ---- 顶部统计卡片 ---- */
.stat-cards {
  margin-bottom: 0;
}

.stat-card-inner {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-card-info {
  display: flex;
  flex-direction: column;
}

.stat-card-value {
  font-size: 28px;
  font-weight: 700;
  line-height: 1.2;
}

.stat-unit {
  font-size: 14px;
  font-weight: 400;
  color: #909399;
  margin-left: 2px;
}

.stat-card-label {
  font-size: 13px;
  color: #909399;
  margin-top: 2px;
}

/* ---- 通用卡片头部 ---- */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* ---- 最近事件列表 ---- */
.recent-events-list {
  max-height: 520px;
  overflow-y: auto;
}

.recent-event-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 0;
  border-bottom: 1px solid #f0f0f0;
}

.recent-event-item:last-child {
  border-bottom: none;
}

.recent-event-content {
  display: flex;
  flex-direction: column;
  min-width: 0;
  flex: 1;
}

.recent-event-title {
  font-size: 14px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.recent-event-time {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

/* ---- 告警最多资产 ---- */
.top-assets-list {
  max-height: 420px;
  overflow-y: auto;
}

.top-asset-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 0;
}

.top-asset-rank {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #f5f7fa;
  color: #606266;
  font-size: 12px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.top-asset-item:nth-child(1) .top-asset-rank {
  background: #fef0f0;
  color: #f56c6c;
}

.top-asset-item:nth-child(2) .top-asset-rank {
  background: #fdf6ec;
  color: #e6a23c;
}

.top-asset-item:nth-child(3) .top-asset-rank {
  background: #ecf5ff;
  color: #409eff;
}

.top-asset-name {
  font-size: 14px;
  font-weight: 500;
  min-width: 0;
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex-shrink: 0;
}

.top-asset-bar-wrap {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.top-asset-bar {
  height: 8px;
  border-radius: 4px;
  transition: width 0.4s ease;
  min-width: 4px;
}

.top-asset-count {
  font-size: 13px;
  font-weight: 600;
  color: #606266;
  flex-shrink: 0;
}
</style>
