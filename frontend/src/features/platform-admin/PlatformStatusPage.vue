<template>
  <div class="page-container">
    <div class="page-header">
      <h2>平台状态</h2>
      <div style="display:flex;align-items:center;gap:12px">
        <div class="auto-refresh-control">
          <el-switch v-model="autoRefresh" active-text="自动刷新" @change="toggleAutoRefresh" />
          <span v-if="autoRefresh" class="refresh-countdown">{{ countdown }}s</span>
        </div>
        <el-button type="primary" @click="runSelfCheck" :loading="selfChecking">
          <el-icon><CircleCheck /></el-icon>
          自检
        </el-button>
        <el-button @click="loadStatus" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- Overall Health Summary -->
    <el-alert
      v-if="overallStatus"
      :title="overallStatus.title"
      :type="overallStatus.type"
      :description="overallStatus.desc"
      show-icon
      :closable="false"
      style="margin-bottom: 16px"
    />

    <!-- Component Health Cards -->
    <div class="status-grid" v-loading="loading">
      <el-card
        v-for="comp in components"
        :key="comp.key"
        class="status-card"
        shadow="hover"
        :class="{ 'status-card-unhealthy': comp.status === 'unhealthy' }"
      >
        <div class="card-header">
          <span class="card-icon">{{ comp.icon }}</span>
          <span class="card-title">{{ comp.label }}</span>
          <el-tag :type="getTagType(comp.status)" size="small" effect="dark">
            {{ statusLabels[comp.status] || comp.status || '未知' }}
          </el-tag>
        </div>
        <div class="card-body" v-if="comp.detail">
          <div class="detail-row" v-for="(val, key) in comp.detail" :key="key">
            <span class="detail-key">{{ key }}</span>
            <span class="detail-val">{{ val }}</span>
          </div>
        </div>
        <div class="card-body" v-else>
          <span class="text-muted">暂无详情</span>
        </div>
        <div class="card-footer" v-if="comp.latency !== undefined">
          <span class="latency-label">延迟</span>
          <span class="latency-value" :class="{ 'latency-warn': comp.latency > 500 }">
            {{ comp.latency }}ms
          </span>
        </div>
      </el-card>
    </div>

    <!-- Health Check History Chart -->
    <el-card style="margin-top: 20px">
      <template #header>
        <span style="font-weight:600">健康检查历史</span>
      </template>
      <div class="chart-container">
        <div class="chart-placeholder" v-if="!historyData.length">
          <span class="text-muted">暂无历史数据，点击「自检」开始记录</span>
        </div>
        <div class="history-timeline" v-else>
          <div class="history-row" v-for="(entry, idx) in historyData" :key="idx">
            <span class="history-time">{{ entry.time }}</span>
            <div class="history-dots">
              <span
                v-for="comp in entry.components"
                :key="comp.key"
                class="history-dot"
                :class="'dot-' + comp.status"
                :title="comp.label + ': ' + (statusLabels[comp.status] || comp.status)"
              />
            </div>
            <el-tag :type="entry.overall === 'healthy' ? 'success' : entry.overall === 'degraded' ? 'warning' : 'danger'" size="small">
              {{ statusLabels[entry.overall] || entry.overall }}
            </el-tag>
          </div>
        </div>
      </div>
    </el-card>

    <!-- Self-check Result Drawer -->
    <el-drawer v-model="selfCheckVisible" title="自检结果" size="520px">
      <div v-if="selfCheckResult">
        <el-result
          :icon="selfCheckResult.healthy ? 'success' : 'error'"
          :title="selfCheckResult.healthy ? '所有组件正常' : '部分组件异常'"
          :sub-title="`检查时间: ${selfCheckResult.time}`"
        />
        <el-descriptions :column="1" border style="margin-top: 16px">
          <el-descriptions-item v-for="item in selfCheckResult.items" :key="item.key" :label="item.label">
            <div style="display:flex;align-items:center;gap:8px">
              <el-tag :type="getTagType(item.status)" size="small">{{ statusLabels[item.status] || item.status }}</el-tag>
              <span style="color:#909399;font-size:13px">{{ item.message || '' }}</span>
            </div>
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, CircleCheck } from '@element-plus/icons-vue'
import api from '@/shared/api/client'
import { API as R } from '@/shared/api/routes'

interface StatusComponent {
  key: string
  label: string
  icon: string
  status: string
  detail: Record<string, string> | null
  latency?: number
}

interface HistoryEntry {
  time: string
  overall: string
  components: { key: string; label: string; status: string }[]
}

const statusLabels: Record<string, string> = {
  healthy: '正常',
  degraded: '降级',
  unhealthy: '异常',
  unknown: '未知',
}

const loading = ref(false)
const selfChecking = ref(false)
const selfCheckVisible = ref(false)
const selfCheckResult = ref<any>(null)

const components = ref<StatusComponent[]>([
  { key: 'api', label: 'API 服务', icon: '🌐', status: 'unknown', detail: null },
  { key: 'database', label: '数据库', icon: '🗄️', status: 'unknown', detail: null },
  { key: 'redis', label: 'Redis', icon: '⚡', status: 'unknown', detail: null },
  { key: 'llm', label: 'LLM 服务', icon: '🤖', status: 'unknown', detail: null },
  { key: 'collector', label: '采集器', icon: '📡', status: 'unknown', detail: null },
])

const historyData = ref<HistoryEntry[]>([])

// Auto-refresh
const autoRefresh = ref(false)
const countdown = ref(30)
let refreshTimer: ReturnType<typeof setInterval> | null = null
let countdownTimer: ReturnType<typeof setInterval> | null = null

function toggleAutoRefresh(val: boolean) {
  if (val) {
    startAutoRefresh()
  } else {
    stopAutoRefresh()
  }
}

function startAutoRefresh() {
  countdown.value = 30
  countdownTimer = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) {
      countdown.value = 30
      loadStatus()
    }
  }, 1000)
}

function stopAutoRefresh() {
  if (refreshTimer) { clearInterval(refreshTimer); refreshTimer = null }
  if (countdownTimer) { clearInterval(countdownTimer); countdownTimer = null }
}

// Overall status
const overallStatus = computed(() => {
  const comps = components.value.filter(c => c.key !== 'frontend')
  const unhealthy = comps.some(c => c.status === 'unhealthy')
  const degraded = comps.some(c => c.status === 'degraded')
  const allHealthy = comps.every(c => c.status === 'healthy')
  if (unhealthy) {
    return { title: '平台存在异常', type: 'error' as const, desc: '部分组件运行异常，请检查详情' }
  }
  if (degraded) {
    return { title: '平台运行降级', type: 'warning' as const, desc: '部分组件处于降级状态' }
  }
  if (allHealthy) {
    return { title: '平台运行正常', type: 'success' as const, desc: '所有组件状态正常' }
  }
  return null
})

function getTagType(status: string): 'success' | 'warning' | 'danger' | 'info' {
  switch (status) {
    case 'healthy': return 'success'
    case 'degraded': return 'warning'
    case 'unhealthy': return 'danger'
    default: return 'info'
  }
}

function addHistoryEntry() {
  const entry: HistoryEntry = {
    time: new Date().toLocaleString('zh-CN'),
    overall: components.value.every(c => c.status === 'healthy') ? 'healthy'
      : components.value.some(c => c.status === 'unhealthy') ? 'unhealthy' : 'degraded',
    components: components.value.map(c => ({ key: c.key, label: c.label, status: c.status })),
  }
  historyData.value.unshift(entry)
  // Keep last 20 entries
  if (historyData.value.length > 20) historyData.value.pop()
}

async function loadStatus() {
  loading.value = true
  try {
    const { data } = await api.get(R.PLATFORM_STATUS)
    if (data.code === 0) {
      const result = data.data || data
      const statusData = result.components || result
      components.value.forEach(comp => {
        const info = statusData[comp.key]
        if (info) {
          comp.status = info.status || 'unknown'
          comp.detail = info.detail || null
          comp.latency = info.latency
        }
      })
      addHistoryEntry()
    }
  } catch (e: any) {
    ElMessage.error('加载平台状态失败')
  } finally {
    loading.value = false
  }
}

async function runSelfCheck() {
  selfChecking.value = true
  try {
    const { data } = await api.post(R.PLATFORM_STATUS + '/self-check')
    if (data.code === 0) {
      const result = data.data || data
      selfCheckResult.value = {
        healthy: result.healthy !== false,
        time: new Date().toLocaleString('zh-CN'),
        items: components.value.map(comp => {
          const info = result.components?.[comp.key]
          return {
            key: comp.key,
            label: comp.label,
            status: info?.status || comp.status,
            message: info?.message || '',
          }
        }),
      }
      selfCheckVisible.value = true
      // Also refresh status
      await loadStatus()
    }
  } catch (e: any) {
    ElMessage.error('自检请求失败')
  } finally {
    selfChecking.value = false
  }
}

onMounted(() => { loadStatus() })
onUnmounted(() => { stopAutoRefresh() })
</script>

<style scoped>
.page-container { padding: 20px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 8px; }
.page-header h2 { margin: 0; font-size: 20px; color: #303133; }

.auto-refresh-control {
  display: flex;
  align-items: center;
  gap: 6px;
}
.refresh-countdown {
  font-size: 12px;
  color: #909399;
  min-width: 28px;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.status-card {
  border-radius: 8px;
  transition: border-color 0.3s;
}
.status-card-unhealthy {
  border-color: #f56c6c;
}
.status-card :deep(.el-card__body) {
  padding: 16px 20px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-size: 15px;
  font-weight: 600;
}
.card-icon { font-size: 22px; }
.card-title { flex: 1; }

.card-body { font-size: 13px; }
.detail-row {
  display: flex;
  justify-content: space-between;
  padding: 4px 0;
  border-bottom: 1px solid #f0f0f0;
}
.detail-row:last-child { border-bottom: none; }
.detail-key { color: #909399; }
.detail-val { color: #303133; font-weight: 500; }

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
  padding-top: 8px;
  border-top: 1px solid #f0f0f0;
  font-size: 13px;
}
.latency-label { color: #909399; }
.latency-value { color: #67c23a; font-weight: 600; }
.latency-warn { color: #e6a23c; }

.text-muted { color: #909399; font-size: 13px; }

.chart-container { min-height: 80px; }
.chart-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 80px;
}

.history-timeline { max-height: 300px; overflow-y: auto; }
.history-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px solid #f5f5f5;
}
.history-row:last-child { border-bottom: none; }
.history-time {
  font-size: 13px;
  color: #606266;
  white-space: nowrap;
  min-width: 160px;
}
.history-dots { display: flex; gap: 6px; flex: 1; }
.history-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  display: inline-block;
  cursor: default;
}
.dot-healthy { background-color: #67c23a; }
.dot-degraded { background-color: #e6a23c; }
.dot-unhealthy { background-color: #f56c6c; }
.dot-unknown { background-color: #c0c4cc; }
</style>
