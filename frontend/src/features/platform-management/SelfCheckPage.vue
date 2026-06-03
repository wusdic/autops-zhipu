<template>
  <div class="page-container">
    <!-- ── API Not Available: Coming Soon ────────────────── -->
    <div v-if="apiNotAvailable" class="coming-soon-wrapper">
      <el-empty :image-size="160" description=" ">
        <template #image>
          <el-icon :size="120" color="#c9cdd4"><Monitor /></el-icon>
        </template>
        <template #description>
          <div class="coming-soon-title">平台自检功能即将上线</div>
          <div class="coming-soon-desc">
            后端自检服务正在开发中，届时将支持对数据库、缓存、磁盘、服务等组件的健康检查。
          </div>
        </template>
      </el-empty>
    </div>

    <!-- ── Normal Content (API available) ────────────────── -->
    <template v-else>
      <div class="autops-page-header">
        <div>
          <div class="autops-page-title">平台自检</div>
          <div class="autops-page-desc">检查平台各组件的运行状态与健康情况</div>
        </div>
        <div class="header-actions">
          <el-button @click="loadHistory" :loading="historyLoading">刷新记录</el-button>
          <el-button type="primary" @click="runCheck" :loading="checking">
            <el-icon><CircleCheck /></el-icon> 开始自检
          </el-button>
        </div>
      </div>

      <!-- ── Category Filter ───────────────────────────────── -->
      <div class="category-bar">
        <span
          v-for="cat in categories"
          :key="cat.key"
          class="category-tag"
          :class="{ active: activeCategory === cat.key }"
          @click="filterCategory(cat.key)"
        >
          <el-icon style="margin-right: 4px"><component :is="cat.icon" /></el-icon>
          {{ cat.label }}
          <el-badge
            :value="getCategoryCount(cat.key)"
            :type="getCategoryBadgeType(cat.key)"
            class="category-badge"
          />
        </span>
      </div>

      <!-- ── Check Results Grid ────────────────────────────── -->
      <el-row :gutter="16" class="check-grid" v-if="checkResults.length > 0">
        <el-col :xs="24" :sm="12" :md="8" v-for="item in filteredResults" :key="item.name">
          <div class="check-card" :class="item.status">
            <div class="check-card-header">
              <el-icon size="22" :color="statusColor(item.status)">
                <component :is="statusIcon(item.status)" />
              </el-icon>
              <span class="check-name">{{ item.name }}</span>
              <el-tag
                :type="statusTagType(item.status)"
                size="small"
                effect="dark"
                class="check-status-tag"
              >
                {{ statusLabel(item.status) }}
              </el-tag>
            </div>
            <div class="check-detail">
              <span class="detail-label">详情：</span>
              <span class="detail-value">{{ item.detail || '等待检查' }}</span>
            </div>
            <div class="check-meta">
              <span class="check-category">
                <el-tag size="small" type="info">{{ getCategoryLabel(item.category) }}</el-tag>
              </span>
              <span class="check-time">{{ item.checked_at || '' }}</span>
            </div>
            <div class="check-extra" v-if="item.latency">
              <span class="extra-label">延迟：</span>
              <span>{{ item.latency }}ms</span>
            </div>
            <div class="check-extra" v-if="item.error">
              <span class="extra-label error">错误：</span>
              <span class="error-text">{{ item.error }}</span>
            </div>
          </div>
        </el-col>
      </el-row>

      <el-empty v-else description="点击「开始自检」执行平台组件检查" :image-size="120" />

      <!-- ── Summary ───────────────────────────────────────── -->
      <div class="summary-bar" v-if="checkResults.length > 0 && !checking">
        <div class="summary-item">
          <span class="summary-dot success" />
          正常：<strong>{{ passCount }}</strong>
        </div>
        <div class="summary-item">
          <span class="summary-dot error" />
          异常：<strong>{{ failCount }}</strong>
        </div>
        <div class="summary-item">
          <span class="summary-dot warning" />
          警告：<strong>{{ warnCount }}</strong>
        </div>
        <div class="summary-item">
          <span class="summary-dot pending" />
          未检查：<strong>{{ pendingCount }}</strong>
        </div>
        <div class="summary-time">
          检查时间：{{ lastCheckTime || '-' }}
        </div>
      </div>

      <!-- ── History Table ─────────────────────────────────── -->
      <div class="section-title" style="margin-top: 24px">历史自检记录</div>
      <el-table stripe
 :data="history"
 v-loading="historyLoading"border
 size="small"
 empty-text="暂无历史记录"
 style="width: 100%"
 >
        <el-table-column prop="checked_at" label="检查时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.checked_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="total" label="检查项" width="80" align="center" />
        <el-table-column prop="pass" label="通过" width="70" align="center">
          <template #default="{ row }">
            <span style="color: #00b42a">{{ row.pass }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="fail" label="异常" width="70" align="center">
          <template #default="{ row }">
            <span style="color: #f53f3f">{{ row.fail }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="warn" label="警告" width="70" align="center">
          <template #default="{ row }">
            <span style="color: #ff7d00">{{ row.warn }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="duration" label="耗时(ms)" width="100" align="center" />
        <el-table-column prop="operator" label="操作人" width="100" />
        <el-table-column label="操作" width="100" align="center">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click="viewHistoryDetail(row)">
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  CircleCheck,
  CircleClose,
  Clock,
  WarningFilled,
  Monitor,
  Coin,
  Coin as HardDisk,
  Cpu,
  Connection,
} from '@element-plus/icons-vue'
import { platformService } from '@/shared/api'

// ── Categories ───────────────────────────────────────────
const categories = [
  { key: 'all', label: '全部', icon: Monitor },
  { key: 'database', label: '数据库', icon: Coin },
  { key: 'redis', label: '缓存', icon: HardDisk },
  { key: 'disk', label: '磁盘', icon: HardDisk },
  { key: 'service', label: '服务', icon: Cpu },
  { key: 'network', label: '网络', icon: Connection },
]

function getCategoryLabel(key: string): string {
  return categories.find((c) => c.key === key)?.label ?? key
}

// ── State ────────────────────────────────────────────────
const apiNotAvailable = ref(false)
const checking = ref(false)
const historyLoading = ref(false)
const checkResults = ref<any[]>([])
const history = ref<any[]>([])
const activeCategory = ref('all')
const lastCheckTime = ref('')

// ── Computed ─────────────────────────────────────────────
const filteredResults = computed(() => {
  if (activeCategory.value === 'all') return checkResults.value
  return checkResults.value.filter((r) => r.category === activeCategory.value)
})

const passCount = computed(() => checkResults.value.filter((r) => r.status === 'ok').length)
const failCount = computed(() => checkResults.value.filter((r) => r.status === 'error').length)
const warnCount = computed(() => checkResults.value.filter((r) => r.status === 'warning').length)
const pendingCount = computed(() => checkResults.value.filter((r) => r.status === 'pending').length)

function getCategoryCount(cat: string): number {
  if (cat === 'all') return checkResults.value.length
  return checkResults.value.filter((r) => r.category === cat).length
}

function getCategoryBadgeType(cat: string): string {
  if (cat === 'all') {
    if (failCount.value > 0) return 'danger'
    if (warnCount.value > 0) return 'warning'
    return 'success'
  }
  const items = checkResults.value.filter((r) => r.category === cat)
  if (items.some((r) => r.status === 'error')) return 'danger'
  if (items.some((r) => r.status === 'warning')) return 'warning'
  if (items.every((r) => r.status === 'ok')) return 'success'
  return 'info'
}

// ── Status Helpers ───────────────────────────────────────
function statusColor(s: string): string {
  const map: Record<string, string> = { ok: '#00b42a', error: '#f53f3f', warning: '#ff7d00', pending: '#86909c' }
  return map[s] ?? '#86909c'
}

function statusIcon(s: string) {
  const map: Record<string, any> = { ok: CircleCheck, error: CircleClose, warning: WarningFilled, pending: Clock }
  return map[s] ?? Clock
}

function statusTagType(s: string): string {
  const map: Record<string, string> = { ok: 'success', error: 'danger', warning: 'warning', pending: 'info' }
  return map[s] ?? 'info'
}

function statusLabel(s: string): string {
  const map: Record<string, string> = { ok: '正常', error: '异常', warning: '警告', pending: '待检' }
  return map[s] ?? s
}

function formatTime(val: string | undefined): string {
  if (!val) return '-'
  try {
    return new Date(val).toLocaleString('zh-CN')
  } catch {
    return val
  }
}

// ── Category Filter ──────────────────────────────────────
function filterCategory(key: string) {
  activeCategory.value = activeCategory.value === key ? 'all' : key
}

// ── Run Self Check ───────────────────────────────────────
async function runCheck() {
  checking.value = true
  try {
    const res = await platformService.selfCheck()
    const data = res.data?.data ?? res.data

    if (Array.isArray(data)) {
      checkResults.value = data
    } else if (data?.items) {
      checkResults.value = data.items
    } else if (data?.results) {
      checkResults.value = data.results
    } else {
      // Parse structured response
      const results: any[] = []
      const categoryMap: Record<string, string[]> = {
        database: ['MySQL数据库', 'PostgreSQL数据库'],
        redis: ['Redis缓存'],
        disk: ['磁盘空间', '磁盘IO'],
        service: ['后端API', '采集器Worker', '定时任务Scheduler', '消息队列'],
        network: ['网络连通性', 'DNS解析'],
      }
      for (const [cat, names] of Object.entries(categoryMap)) {
        for (const name of names) {
          const matched = Array.isArray(data)
            ? data.find((d: any) => d.name === name)
            : null
          results.push({
            name,
            category: cat,
            status: matched?.status ?? (data?.[cat] ? 'ok' : 'pending'),
            detail: matched?.detail ?? (data?.[cat] ? '正常' : '未检查'),
            checked_at: matched?.checked_at ?? new Date().toISOString(),
            latency: matched?.latency,
            error: matched?.error,
          })
        }
      }
      checkResults.value = results
    }

    lastCheckTime.value = new Date().toLocaleString('zh-CN')

    if (failCount.value > 0) {
      ElMessage.warning(`自检完成：${failCount.value} 项异常`)
    } else {
      ElMessage.success('自检完成，全部正常')
    }
  } catch (err: any) {
    const status = err?.response?.status
    if (status === 404 || status === 501 || !err.response) {
      apiNotAvailable.value = true
      ElMessage.info('自检功能即将上线，后端服务正在开发中')
    } else {
      ElMessage.warning(err.message || '自检执行失败，请稍后重试')
    }
  } finally {
    checking.value = false
  }
}

// ── History ──────────────────────────────────────────────
async function loadHistory() {
  historyLoading.value = true
  try {
    const res = await platformService.selfCheck()
    const data = res.data?.data ?? res.data
    if (data?.history && Array.isArray(data.history)) {
      history.value = data.history
    }
  } catch (err: any) {
    const status = err?.response?.status
    if (status === 404 || status === 501 || !err.response) {
      apiNotAvailable.value = true
    }
  } finally {
    historyLoading.value = false
  }
}

function viewHistoryDetail(row: any) {
  // Populate check results from a history entry if available
  if (row.results && Array.isArray(row.results)) {
    checkResults.value = row.results
    lastCheckTime.value = row.checked_at ? new Date(row.checked_at).toLocaleString('zh-CN') : ''
    activeCategory.value = 'all'
  }
}

// ── Init ─────────────────────────────────────────────────
onMounted(() => {
  loadHistory()
})
</script>

<style scoped>
.autops-page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.autops-page-title {
  font-size: 18px;
  font-weight: 600;
  color: #1d2129;
}
.header-actions {
  display: flex;
  gap: 8px;
}

/* Category bar */
.category-bar {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
.category-tag {
  display: inline-flex;
  align-items: center;
  padding: 6px 14px;
  border: 1px solid #e5e6eb;
  border-radius: 20px;
  cursor: pointer;
  font-size: 13px;
  color: #4e5969;
  transition: all 0.15s;
  background: #fff;
}
.category-tag:hover {
  border-color: #165dff;
  color: #165dff;
}
.category-tag.active {
  background: #e8f3ff;
  border-color: #165dff;
  color: #165dff;
}
.category-badge {
  margin-left: 4px;
}

/* Check grid */
.check-grid {
  margin-bottom: 16px;
}
.check-card {
  background: #fff;
  border: 1px solid #e5e6eb;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  border-left: 3px solid #86909c;
  transition: all 0.2s;
}
.check-card.ok {
  border-left-color: #00b42a;
}
.check-card.error {
  border-left-color: #f53f3f;
}
.check-card.warning {
  border-left-color: #ff7d00;
}
.check-card.pending {
  border-left-color: #86909c;
}
.check-card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}
.check-name {
  flex: 1;
  font-weight: 600;
  font-size: 14px;
  color: #1d2129;
}
.check-status-tag {
  margin-left: auto;
}
.check-detail {
  font-size: 13px;
  color: #4e5969;
  margin-bottom: 8px;
}
.detail-label {
  color: #86909c;
}
.check-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.check-time {
  font-size: 12px;
  color: #c9cdd4;
}
.check-extra {
  font-size: 12px;
  color: #4e5969;
  margin-top: 4px;
}
.extra-label {
  color: #86909c;
}
.extra-label.error {
  color: #f53f3f;
}
.error-text {
  color: #f53f3f;
}

/* Summary bar */
.summary-bar {
  display: flex;
  gap: 24px;
  align-items: center;
  padding: 12px 16px;
  background: #f7f8fa;
  border-radius: 8px;
  font-size: 13px;
  color: #4e5969;
}
.summary-item {
  display: flex;
  align-items: center;
  gap: 4px;
}
.summary-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
.summary-dot.success { background: #00b42a; }
.summary-dot.error { background: #f53f3f; }
.summary-dot.warning { background: #ff7d00; }
.summary-dot.pending { background: #c9cdd4; }
.summary-time {
  margin-left: auto;
  color: #86909c;
}

/* Section title */
.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #1d2129;
  margin-bottom: 12px;
}

/* Coming soon */
.coming-soon-wrapper {
  display: flex;
  justify-content: center;
  padding: 60px 20px;
}
.coming-soon-title {
  font-size: 18px;
  font-weight: 600;
  color: #1d2129;
  margin-bottom: 8px;
}
.coming-soon-desc {
  font-size: 14px;
  color: #86909c;
  line-height: 1.6;
  max-width: 420px;
  text-align: center;
  margin: 0 auto;
}
</style>
