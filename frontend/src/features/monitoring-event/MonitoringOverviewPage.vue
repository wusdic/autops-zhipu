<template>
  <div class="monitoring-overview">
    <!-- 顶部状态分布卡片 -->
    <el-row :gutter="16" class="status-cards">
      <el-col :span="6">
        <el-card shadow="hover" class="status-card status-online">
          <div class="status-card-inner">
            <el-icon :size="36" color="#67C23A"><SuccessFilled /></el-icon>
            <div class="status-card-info">
              <div class="status-card-value">{{ stats.online }}</div>
              <div class="status-card-label">在线</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="status-card status-offline">
          <div class="status-card-inner">
            <el-icon :size="36" color="#F56C6C"><CircleCloseFilled /></el-icon>
            <div class="status-card-info">
              <div class="status-card-value">{{ stats.offline }}</div>
              <div class="status-card-label">离线</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="status-card status-unknown">
          <div class="status-card-inner">
            <el-icon :size="36" color="#909399"><QuestionFilled /></el-icon>
            <div class="status-card-info">
              <div class="status-card-value">{{ stats.unknown }}</div>
              <div class="status-card-label">未知</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="status-card status-total">
          <div class="status-card-inner">
            <el-icon :size="36" color="#409EFF"><Monitor /></el-icon>
            <div class="status-card-info">
              <div class="status-card-value">{{ stats.total }}</div>
              <div class="status-card-label">资产总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top: 16px">
      <!-- 指标趋势折线图 -->
      <el-col :span="16">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>指标趋势</span>
              <el-radio-group v-model="metricRange" size="small" @change="loadMetrics">
                <el-radio-button value="1h">1小时</el-radio-button>
                <el-radio-button value="6h">6小时</el-radio-button>
                <el-radio-button value="24h">24小时</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <div v-loading="metricsLoading">
            <MetricChart
              :data="metricData"
              title="告警趋势"
              color="#E6A23C"
              height="320px"
              unit=" 次"
            />
          </div>
        </el-card>
      </el-col>

      <!-- 资产健康概览 -->
      <el-col :span="8">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>资产健康概览</span>
              <el-button text type="primary" @click="$router.push('/assets')">查看全部</el-button>
            </div>
          </template>
          <div v-loading="healthLoading">
            <div v-for="item in healthList" :key="item.id" class="health-item">
              <div class="health-item-main">
                <span class="health-item-name">{{ item.name || item.hostname }}</span>
                <StatusBadge :status="item.status" size="small" show-icon />
              </div>
              <el-progress
                :percentage="item.health_score ?? 0"
                :color="healthColor(item.health_score ?? 0)"
                :stroke-width="8"
                style="margin-top: 6px"
              />
            </div>
            <el-empty v-if="!healthLoading && healthList.length === 0" description="暂无资产数据" :image-size="60" />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最近状态变更列表 -->
    <el-card style="margin-top: 16px">
      <template #header>
        <div class="card-header">
          <span>最近状态变更</span>
          <el-button text type="primary" @click="loadChanges">刷新</el-button>
        </div>
      </template>
      <el-table :data="changes" v-loading="changesLoading" stripe>
        <el-table-column prop="asset_name" label="资产" min-width="140" show-overflow-tooltip />
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
        <el-table-column prop="reason" label="原因" min-width="200" show-overflow-tooltip />
        <el-table-column prop="changed_at" label="变更时间" width="180">
          <template #default="{ row }">{{ formatTime(row.changed_at) }}</template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { SuccessFilled, CircleCloseFilled, QuestionFilled, Monitor } from '@element-plus/icons-vue'
import api from '@/shared/api/client'
import { API as R } from '@/shared/api/routes'
import MetricChart from '@/shared/components/MetricChart.vue'
import StatusBadge from '@/shared/components/StatusBadge.vue'

// ---- 状态分布 ----
const stats = reactive({ online: 0, offline: 0, unknown: 0, total: 0 })

async function loadStats() {
  try {
    const { data } = await api.get(R.ALERT_STATS)
    if (data.code === 0) {
      const d = data.data
      stats.online = d.online ?? d.healthy ?? 0
      stats.offline = d.offline ?? d.down ?? 0
      stats.unknown = d.unknown ?? 0
      stats.total = d.total ?? 0
    }
  } catch {
    // 静默失败，状态卡片显示 0
  }
}

// ---- 指标趋势 ----
const metricRange = ref('6h')
const metricsLoading = ref(false)
const metricData = ref<Array<{ time: string; value: number }>>([])

async function loadMetrics() {
  metricsLoading.value = true
  try {
    const { data } = await api.get(R.ALERTS, { params: { range: metricRange.value, aggregation: true } })
    if (data.code === 0 && Array.isArray(data.data?.items)) {
      metricData.value = data.data.items.map((t: any) => ({
        time: t.time || t.created_at,
        value: t.value ?? t.count ?? 1,
      }))
    }
  } catch {
    ElMessage.error('加载指标趋势失败')
  } finally {
    metricsLoading.value = false
  }
}

// ---- 资产健康概览 ----
const healthLoading = ref(false)
const healthList = ref<any[]>([])

async function loadHealth() {
  healthLoading.value = true
  try {
    const { data } = await api.get(R.ASSETS, { params: { page: 1, page_size: 8 } })
    if (data.code === 0) {
      healthList.value = (data.data?.items || []).slice(0, 8)
    }
  } catch {
    ElMessage.error('加载资产健康概览失败')
  } finally {
    healthLoading.value = false
  }
}

function healthColor(score: number) {
  if (score >= 80) return '#67C23A'
  if (score >= 50) return '#E6A23C'
  return '#F56C6C'
}

// ---- 最近状态变更 ----
const changesLoading = ref(false)
const changes = ref<any[]>([])

async function loadChanges() {
  changesLoading.value = true
  try {
    const { data } = await api.get(R.STATES.ALL_CHANGES, { params: { page: 1, page_size: 20 } })
    if (data.code === 0) {
      changes.value = data.data?.items || data.data || []
    }
  } catch {
    ElMessage.error('加载状态变更失败')
  } finally {
    changesLoading.value = false
  }
}

// ---- 工具函数 ----
function formatTime(t: string) {
  return t ? new Date(t).toLocaleString('zh-CN') : ''
}

// ---- 初始化 ----
onMounted(() => {
  loadStats()
  loadMetrics()
  loadHealth()
  loadChanges()
})
</script>

<style scoped>
.status-cards { margin-bottom: 0; }
.status-card-inner {
  display: flex;
  align-items: center;
  gap: 16px;
}
.status-card-info {
  display: flex;
  flex-direction: column;
}
.status-card-value {
  font-size: 28px;
  font-weight: 700;
  line-height: 1.2;
}
.status-card-label {
  font-size: 13px;
  color: #909399;
  margin-top: 2px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.health-item {
  margin-bottom: 14px;
}
.health-item:last-child {
  margin-bottom: 0;
}
.health-item-main {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.health-item-name {
  font-weight: 500;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 180px;
}
</style>
