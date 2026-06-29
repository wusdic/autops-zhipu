<template>
  <div class="collector-health-page autops-page-container">
    <PageHeader title="采集器健康" desc="在线状态、心跳、成功率、平均延迟" />

    <!-- ========== Statistics Row ========== -->
    <el-row :gutter="16" class="stats-row mb-lg">
      <el-col :span="8">
        <div class="autops-card stat-card stat-card--healthy">
          <div class="stat-card__body">
            <div class="stat-card__icon">
              <el-icon :size="32"><CircleCheckFilled /></el-icon>
            </div>
            <div class="stat-card__info">
              <div class="stat-card__value">{{ stats.healthy }}</div>
              <div class="stat-card__label">健康</div>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="autops-card stat-card stat-card--degraded">
          <div class="stat-card__body">
            <div class="stat-card__icon">
              <el-icon :size="32"><WarningFilled /></el-icon>
            </div>
            <div class="stat-card__info">
              <div class="stat-card__value">{{ stats.degraded }}</div>
              <div class="stat-card__label">降级</div>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="autops-card stat-card stat-card--down">
          <div class="stat-card__body">
            <div class="stat-card__icon">
              <el-icon :size="32"><CircleCloseFilled /></el-icon>
            </div>
            <div class="stat-card__info">
              <div class="stat-card__value">{{ stats.down }}</div>
              <div class="stat-card__label">离线</div>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- ========== Main Card ========== -->
    <div class="autops-card main-card">
      <div class="autops-card-header">
        <span class="autops-card-title">采集器状态列表</span>
        <el-button :icon="Refresh" circle size="small" @click="loadData" />
      </div>
      <div class="autops-card-body">
        <!-- ========== Table ========== -->
        <el-table stripe
 :data="tableData"
 v-loading="loading"border
 empty-text="暂无数据"
 class="health-table"
 >
          <el-table-column prop="collector_name" label="采集器名称" min-width="160" show-overflow-tooltip />
          <el-table-column prop="collector_type" label="类型" min-width="120" show-overflow-tooltip />
          <el-table-column prop="status" label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag
                :type="(healthTagType(row.status)) as TagType"
                size="small"
                effect="light"
              >
                <el-icon v-if="row.status === 'healthy'" class="tag-icon"><SuccessFilled /></el-icon>
                <el-icon v-else-if="row.status === 'down'" class="tag-icon"><CircleCloseFilled /></el-icon>
                <el-icon v-else class="tag-icon"><WarningFilled /></el-icon>
                {{ healthLabel(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="version" label="版本" width="90" align="center">
            <template #default="{ row }">
              {{ row.version || '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="last_heartbeat" label="最后心跳" width="175">
            <template #default="{ row }">
              {{ formatTime(row.last_heartbeat) }}
            </template>
          </el-table-column>
          <el-table-column prop="task_backlog" label="任务积压" width="100" align="right">
            <template #default="{ row }">
              <span :class="{ 'text-danger': row.task_backlog > 100 }">
                {{ row.task_backlog ?? '-' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="success_rate" label="成功率" width="100" align="center">
            <template #default="{ row }">
              <span
                v-if="row.success_rate != null"
                :class="['rate-value', rateClass(row.success_rate)]"
              >
                {{ (row.success_rate * 100).toFixed(1) }}%
              </span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="avg_latency" label="平均延迟" width="110" align="right">
            <template #default="{ row }">
              <span v-if="row.avg_latency != null">{{ formatLatency(row.avg_latency) }}</span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100" fixed="right" align="center">
            <template #default="{ row }">
              <el-button type="primary" plain @click="viewDetail(row)">详情</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <!-- ========== Detail Dialog ========== -->
    <el-dialog
      v-model="detailVisible"
      title="采集器详情"
      width="600px"
      destroy-on-close
    >
      <el-descriptions :column="2" border v-if="currentRow">
        <el-descriptions-item label="采集器名称">{{ currentRow.collector_name }}</el-descriptions-item>
        <el-descriptions-item label="类型">{{ currentRow.collector_type }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="(healthTagType(currentRow.status)) as TagType" size="small">
            {{ healthLabel(currentRow.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="版本">{{ currentRow.version || '-' }}</el-descriptions-item>
        <el-descriptions-item label="最后心跳">{{ formatTime(currentRow.last_heartbeat) }}</el-descriptions-item>
        <el-descriptions-item label="任务积压">{{ currentRow.task_backlog ?? '-' }}</el-descriptions-item>
        <el-descriptions-item label="成功率">
          {{ currentRow.success_rate != null ? (currentRow.success_rate * 100).toFixed(1) + '%' : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="平均延迟">
          {{ currentRow.avg_latency != null ? formatLatency(currentRow.avg_latency) : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">
          {{ currentRow.description || '-' }}
        </el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import type { TagType } from '@/shared/types'
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Refresh,
  CircleCheckFilled,
  CircleCloseFilled,
  WarningFilled,
  SuccessFilled,
} from '@element-plus/icons-vue'
import { monitoringService } from '@/shared/api'
import PageHeader from '@/shared/components/PageHeader.vue'
import { healthLabel as healthLabelFn } from '@/shared/utils/labels'

// ── State ──────────────────────────────────────────────────────────
const loading = ref(false)
const tableData = ref<any[]>([])
const detailVisible = ref(false)
const currentRow = ref<any>(null)

const stats = reactive({
  healthy: 0,
  degraded: 0,
  down: 0,
})

// ── Helpers ─────────────────────────────────────────────────────────
function formatTime(val: string | null | undefined): string {
  if (!val) return '-'
  const d = new Date(val)
  if (isNaN(d.getTime())) return '-'
  const pad = (n: number) => String(n).padStart(2, '0')
  return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()) + ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes()) + ':' + pad(d.getSeconds())
}

function formatLatency(ms: number | null | undefined): string {
  if (ms == null) return '-'
  if (ms < 1000) return Math.round(ms) + 'ms'
  return (ms / 1000).toFixed(2) + 's'
}

function healthTagType(status: string): TagType {
  const map: Record<string, TagType> = {
    healthy: 'success',
    degraded: 'warning',
    down: 'danger',
  }
  return (map[status] || 'info') as TagType
}

const healthLabel = (status: string): string => healthLabelFn(status)

function rateClass(rate: number): string {
  if (rate >= 0.95) return 'rate-good'
  if (rate >= 0.8) return 'rate-warn'
  return 'rate-bad'
}

// ── Data Loading ────────────────────────────────────────────────────
async function loadData() {
  loading.value = true
  try {
    const { data } = await monitoringService.collectorHealth()
    if (data.code === 0) {
      const items = data.data?.items || data.data?.list || data.data || []
      tableData.value = Array.isArray(items) ? items : []

      // Compute stats
      stats.healthy = tableData.value.filter((r) => r.status === 'healthy').length
      stats.degraded = tableData.value.filter((r) => r.status === 'degraded').length
      stats.down = tableData.value.filter((r) => r.status === 'down').length
    }
  } catch {
    ElMessage.error('加载采集器健康状态失败')
  } finally {
    loading.value = false
  }
}

// ── Detail Dialog ───────────────────────────────────────────────────
function viewDetail(row: any) {
  currentRow.value = row
  detailVisible.value = true
}

// ── Lifecycle ───────────────────────────────────────────────────────
onMounted(() => {
  loadData()
})
</script>

<style scoped>
.collector-health-page {
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

.autops-metric-card--healthy .stat-card__icon {
  background: rgba(103, 194, 58, 0.12);
  color: var(--autops-success);
}
.autops-metric-card--healthy .stat-card__value {
  color: var(--autops-success);
}

.autops-metric-card--degraded .stat-card__icon {
  background: rgba(230, 162, 60, 0.12);
  color: var(--autops-warning);
}
.autops-metric-card--degraded .stat-card__value {
  color: var(--autops-warning);
}

.autops-metric-card--down .stat-card__icon {
  background: rgba(245, 108, 108, 0.12);
  color: var(--autops-danger);
}
.autops-metric-card--down .stat-card__value {
  color: var(--autops-danger);
}

/* ── Main Card ── */
.main-card {
  border-radius: var(--autops-radius-md);
}

.health-table {
  width: 100%;
}

.tag-icon {
  margin-right: 4px;
  vertical-align: middle;
}

.rate-value {
  font-weight: 500;
}

.rate-good {
  color: var(--autops-success);
}

.rate-warn {
  color: var(--autops-warning);
}

.rate-bad {
  color: var(--autops-danger);
}

.text-danger {
  color: var(--autops-danger);
  font-weight: 500;
}
</style>
