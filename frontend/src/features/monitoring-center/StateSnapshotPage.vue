<template>
  <div class="state-snapshot-page">
    <!-- ========== Page Header ========== -->
    <div class="autops-page-header">
      <div>
        <div class="autops-page-title">状态快照</div>
        <div class="autops-page-desc">资源当前可达性、健康状态、最新指标</div>
      </div>
    </div>

    <!-- ========== Main Card ========== -->
    <div class="autops-card main-card">
      <div class="autops-card-header">
        <span class="autops-card-title">状态快照列表</span>
        <el-button :icon="Refresh" circle size="small" @click="loadData" />
      </div>
      <div class="autops-card-body">
        <!-- ========== Filters ========== -->
        <el-form :inline="true" class="autops-toolbar filter-form" @submit.prevent="handleSearch">
          <el-form-item label="关键词">
            <el-input
              v-model="filters.keyword"
              placeholder="搜索资产名称"
              clearable
              :prefix-icon="Search"
              style="width: 220px"
              @keyup.enter="handleSearch"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
            <el-button :icon="RefreshLeft" @click="resetFilters">重置</el-button>
          </el-form-item>
        </el-form>

        <!-- ========== Empty State ========== -->
        <el-empty
          v-if="!loading && loadFailed"
          description="状态快照数据暂不可用，请确认后端监控服务已启动"
        >
          <el-button type="primary" @click="loadData">重新加载</el-button>
        </el-empty>

        <!-- ========== Table ========== -->
        <el-table stripe
 v-if="!loadFailed"
 :data="tableData"
 v-loading="loading"border
 empty-text="暂无数据"
 class="snapshot-table"
 >
          <el-table-column prop="asset_name" label="资产名" min-width="160" show-overflow-tooltip />
          <el-table-column prop="collected_at" label="采集时间" width="175">
            <template #default="{ row }">
              {{ formatTime(row.collected_at) }}
            </template>
          </el-table-column>
          <el-table-column prop="cpu_usage" label="CPU" width="100" align="center">
            <template #default="{ row }">
              <span v-if="row.cpu_usage != null" :class="usageClass(row.cpu_usage)">
                {{ (row.cpu_usage * 100).toFixed(1) }}%
              </span>
              <span v-else class="text-muted">-</span>
            </template>
          </el-table-column>
          <el-table-column prop="memory_usage" label="内存" width="100" align="center">
            <template #default="{ row }">
              <span v-if="row.memory_usage != null" :class="usageClass(row.memory_usage)">
                {{ (row.memory_usage * 100).toFixed(1) }}%
              </span>
              <span v-else class="text-muted">-</span>
            </template>
          </el-table-column>
          <el-table-column prop="disk_usage" label="磁盘" width="100" align="center">
            <template #default="{ row }">
              <span v-if="row.disk_usage != null" :class="usageClass(row.disk_usage)">
                {{ (row.disk_usage * 100).toFixed(1) }}%
              </span>
              <span v-else class="text-muted">-</span>
            </template>
          </el-table-column>
          <el-table-column prop="network_status" label="网络状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag
                v-if="row.network_status"
                :type="(networkTagType(row.network_status)) as TagType"
                size="small"
                effect="light"
              >
                {{ networkLabel(row.network_status) }}
              </el-tag>
              <span v-else class="text-muted">-</span>
            </template>
          </el-table-column>
          <el-table-column prop="reachability" label="可达性" width="90" align="center">
            <template #default="{ row }">
              <el-tag
                v-if="row.reachability"
                :type="row.reachability === 'reachable' ? 'success' : 'danger'"
                size="small"
                effect="light"
              >
                {{ row.reachability === 'reachable' ? '可达' : '不可达' }}
              </el-tag>
              <span v-else class="text-muted">-</span>
            </template>
          </el-table-column>
          <el-table-column prop="health" label="健康度" width="90" align="center">
            <template #default="{ row }">
              <el-tag
                v-if="row.health"
                :type="(healthTagType(row.health)) as TagType"
                size="small"
                effect="light"
              >
                {{ healthLabel(row.health) }}
              </el-tag>
              <span v-else class="text-muted">-</span>
            </template>
          </el-table-column>
        </el-table>

        <!-- ========== Pagination ========== -->
        <div v-if="!loadFailed" class="pagination-wrapper">
          <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.pageSize"
            :total="pagination.total"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            background
            @change="loadData"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { TagType } from '@/shared/types'
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh, RefreshLeft } from '@element-plus/icons-vue'
import { monitoringService } from '@/shared/api'

// ── State ──────────────────────────────────────────────────────────
const loading = ref(false)
const loadFailed = ref(false)
const tableData = ref<any[]>([])

const filters = reactive({
  keyword: '',
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
})

// ── Helpers ─────────────────────────────────────────────────────────
function formatTime(val: string | null | undefined): string {
  if (!val) return '-'
  const d = new Date(val)
  if (isNaN(d.getTime())) return '-'
  const pad = (n: number) => String(n).padStart(2, '0')
  return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()) + ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes()) + ':' + pad(d.getSeconds())
}

function usageClass(usage: number): string {
  if (usage >= 0.9) return 'usage-critical'
  if (usage >= 0.7) return 'usage-warning'
  return 'usage-normal'
}

function networkTagType(status: string): TagType {
  const map: Record<string, TagType> = {
    normal: 'success',
    degraded: 'warning',
    down: 'danger',
  }
  return (map[status] || 'info') as TagType
}

function networkLabel(status: string): string {
  const map: Record<string, string> = {
    normal: '正常',
    degraded: '降级',
    down: '中断',
  }
  return map[status] || status
}

function healthTagType(health: string): TagType {
  const map: Record<string, TagType> = {
    healthy: 'success',
    degraded: 'warning',
    unhealthy: 'danger',
  }
  return (map[health] || 'info') as TagType
}

function healthLabel(health: string): string {
  const map: Record<string, string> = {
    healthy: '健康',
    degraded: '降级',
    unhealthy: '异常',
  }
  return map[health] || health
}

// ── Data Loading ────────────────────────────────────────────────────
async function loadData() {
  loading.value = true
  loadFailed.value = false
  try {
    const params: Record<string, any> = {
      page: pagination.page,
      page_size: pagination.pageSize,
    }
    if (filters.keyword) params.keyword = filters.keyword

    const { data } = await monitoringService.stateSnapshots(params)
    if (data.code === 0) {
      tableData.value = data.data?.items || data.data?.list || []
      pagination.total = data.data?.total || 0
    }
  } catch {
    tableData.value = []
    pagination.total = 0
    loadFailed.value = true
    ElMessage.warning('状态快照数据暂不可用，请确认后端监控服务已启动')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  pagination.page = 1
  loadData()
}

function resetFilters() {
  filters.keyword = ''
  pagination.page = 1
  loadData()
}

// ── Lifecycle ───────────────────────────────────────────────────────
onMounted(() => {
  loadData()
})
</script>

<style scoped>
.state-snapshot-page {
  padding: var(--autops-space-xl);
}

.main-card {
  border-radius: var(--autops-radius-md);
}

.filter-form {
  margin-bottom: var(--autops-space-lg);
  padding-bottom: 16px;
  border-bottom: 1px solid var(--autops-bg-4);
}

.filter-form :deep(.el-form-item) {
  margin-bottom: var(--autops-space-md);
}

.snapshot-table {
  width: 100%;
}

.usage-normal {
  color: var(--autops-success);
  font-weight: 500;
}

.usage-warning {
  color: var(--autops-warning);
  font-weight: 500;
}

.usage-critical {
  color: var(--autops-danger);
  font-weight: 600;
}

.text-muted {
  color: var(--autops-text-4);
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: var(--autops-space-lg);
}
</style>
