<template>
  <div class="log-source-page">
    <!-- ========== Page Header ========== -->
    <div class="autops-page-header">
      <div>
        <div class="autops-page-title">日志接入</div>
        <div class="autops-page-desc">日志源、解析规则、接入状态</div>
      </div>
    </div>

    <!-- ========== Main Card ========== -->
    <div class="autops-card main-card">
      <div class="autops-card-header">
        <span class="autops-card-title">日志源列表</span>
        <el-button :icon="Refresh" circle size="small" @click="loadData" />
      </div>
      <div class="autops-card-body">
        <!-- ========== Filters ========== -->
        <el-form :inline="true" class="autops-toolbar filter-form" @submit.prevent="handleSearch">
          <el-form-item label="关键词">
            <el-input
              v-model="filters.keyword"
              placeholder="搜索日志源名称"
              clearable
              :prefix-icon="Search"
              style="width: 200px"
              @keyup.enter="handleSearch"
            />
          </el-form-item>
          <el-form-item label="类型">
            <el-select v-model="filters.type" placeholder="全部类型" clearable style="width: 130px">
              <el-option label="Syslog" value="syslog" />
              <el-option label="文件" value="file" />
              <el-option label="API" value="api" />
            </el-select>
          </el-form-item>
          <el-form-item label="状态">
            <el-select v-model="filters.status" placeholder="全部状态" clearable style="width: 130px">
              <el-option label="活跃" value="active" />
              <el-option label="停止" value="inactive" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
            <el-button :icon="RefreshLeft" @click="resetFilters">重置</el-button>
          </el-form-item>
        </el-form>

        <!-- ========== Table ========== -->
        <el-table stripe
 :data="tableData"
 v-loading="loading"border
 empty-text="暂无数据"
 class="log-source-table"
 >
          <el-table-column prop="name" label="名称" min-width="180" show-overflow-tooltip />
          <el-table-column prop="type" label="类型" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="typeTagType(row.type)" size="small" effect="plain">
                {{ typeLabel(row.type) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="protocol" label="协议" width="100" align="center">
            <template #default="{ row }">
              {{ row.protocol || '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small" effect="light">
                {{ row.status === 'active' ? '活跃' : '停止' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="daily_volume" label="日志量/天" width="110" align="right">
            <template #default="{ row }">
              {{ row.daily_volume != null ? formatNumber(row.daily_volume) : '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="parser_rule" label="解析规则" min-width="160" show-overflow-tooltip>
            <template #default="{ row }">
              {{ row.parser_rule || '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="last_received_at" label="最后接收时间" width="175">
            <template #default="{ row }">
              {{ formatTime(row.last_received_at) }}
            </template>
          </el-table-column>
          <el-table-column prop="sample" label="样例日志" min-width="200" show-overflow-tooltip>
            <template #default="{ row }">
              {{ row.sample || '-' }}
            </template>
          </el-table-column>
        </el-table>

        <!-- ========== Pagination ========== -->
        <div class="pagination-wrapper">
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
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh, RefreshLeft } from '@element-plus/icons-vue'
import { monitoringService } from '@/shared/api'

// ── State ──────────────────────────────────────────────────────────
const loading = ref(false)
const tableData = ref<any[]>([])

const filters = reactive({
  keyword: '',
  type: '',
  status: '',
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

function formatNumber(num: number): string {
  if (num >= 1_000_000) return (num / 1_000_000).toFixed(1) + 'M'
  if (num >= 1_000) return (num / 1_000).toFixed(1) + 'K'
  return String(num)
}

function typeTagType(type: string): '' | 'success' | 'warning' | 'info' | 'danger' {
  const map: Record<string, '' | 'success' | 'warning' | 'info' | 'danger'> = {
    syslog: 'success',
    file: 'warning',
    api: '',
  }
  return map[type] || 'info'
}

function typeLabel(type: string): string {
  const map: Record<string, string> = {
    syslog: 'Syslog',
    file: '文件',
    api: 'API',
  }
  return map[type] || type
}

// ── Data Loading ────────────────────────────────────────────────────
async function loadData() {
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: pagination.page,
      page_size: pagination.pageSize,
    }
    if (filters.keyword) params.keyword = filters.keyword
    if (filters.type) params.type = filters.type
    if (filters.status) params.status = filters.status

    const { data } = await monitoringService.logSources(params)
    if (data.code === 0) {
      tableData.value = data.data?.items || data.data?.list || []
      pagination.total = data.data?.total || 0
    }
  } catch {
    ElMessage.error('加载日志源列表失败')
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
  filters.type = ''
  filters.status = ''
  pagination.page = 1
  loadData()
}

// ── Lifecycle ───────────────────────────────────────────────────────
onMounted(() => {
  loadData()
})
</script>

<style scoped>
.log-source-page {
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

.log-source-table {
  width: 100%;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: var(--autops-space-lg);
}
</style>
