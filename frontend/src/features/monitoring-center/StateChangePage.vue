<template>
  <div class="state-change-page">
    <!-- ========== Page Header ========== -->
    <div class="autops-page-header">
      <div>
        <div class="autops-page-title">状态变化</div>
        <div class="autops-page-subtitle">状态变更历史、触发来源、证据</div>
      </div>
    </div>

    <!-- ========== Main Card ========== -->
    <div class="autops-card main-card">
      <div class="autops-card-header">
        <span class="autops-card-title">状态变更记录</span>
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
              style="width: 200px"
              @keyup.enter="handleSearch"
            />
          </el-form-item>
          <el-form-item label="变更属性">
            <el-select v-model="filters.attribute" placeholder="全部属性" clearable style="width: 150px">
              <el-option label="状态" value="status" />
              <el-option label="健康度" value="health" />
              <el-option label="IP 地址" value="ip" />
              <el-option label="可达性" value="reachability" />
              <el-option label="配置" value="config" />
            </el-select>
          </el-form-item>
          <el-form-item label="时间范围">
            <el-date-picker
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
          <el-form-item>
            <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
            <el-button :icon="RefreshLeft" @click="resetFilters">重置</el-button>
          </el-form-item>
        </el-form>

        <!-- ========== Table ========== -->
        <el-table
          :data="tableData"
          v-loading="loading"
          stripe
          border
          empty-text="暂无数据"
          class="change-table"
        >
          <el-table-column prop="asset_name" label="资产名" min-width="160" show-overflow-tooltip />
          <el-table-column prop="attribute_name" label="变更属性" width="120" align="center">
            <template #default="{ row }">
              <el-tag size="small" effect="plain">{{ row.attribute_name }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="old_value" label="旧值" min-width="140" show-overflow-tooltip>
            <template #default="{ row }">
              <span class="value-old">{{ row.old_value ?? '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="" width="40" align="center" class-name="arrow-cell">
            <template #default>
              <el-icon><Right /></el-icon>
            </template>
          </el-table-column>
          <el-table-column prop="new_value" label="新值" min-width="140" show-overflow-tooltip>
            <template #default="{ row }">
              <span class="value-new">{{ row.new_value ?? '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="changed_at" label="变更时间" width="175">
            <template #default="{ row }">
              {{ formatTime(row.changed_at) }}
            </template>
          </el-table-column>
          <el-table-column prop="trigger_source" label="触发来源" width="120" show-overflow-tooltip>
            <template #default="{ row }">
              {{ row.trigger_source || '-' }}
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
import { Search, Refresh, RefreshLeft, Right } from '@element-plus/icons-vue'
import client from '@/shared/api/client'
import { API } from '@/shared/api/routes'

// ── State ──────────────────────────────────────────────────────────
const loading = ref(false)
const tableData = ref<any[]>([])

const filters = reactive({
  keyword: '',
  attribute: '',
  dateRange: null as [string, string] | null,
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
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
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
    if (filters.attribute) params.attribute_name = filters.attribute
    if (filters.dateRange && filters.dateRange.length === 2) {
      params.start_time = filters.dateRange[0]
      params.end_time = filters.dateRange[1]
    }

    const { data } = await client.get(API.STATES.ALL_CHANGES, { params })
    if (data.code === 0) {
      tableData.value = data.data?.items || data.data?.list || []
      pagination.total = data.data?.total || 0
    }
  } catch {
    ElMessage.error('加载状态变更记录失败')
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
  filters.attribute = ''
  filters.dateRange = null
  pagination.page = 1
  loadData()
}

// ── Lifecycle ───────────────────────────────────────────────────────
onMounted(() => {
  loadData()
})
</script>

<style scoped>
.state-change-page {
  padding: 20px;
}

.main-card {
  border-radius: 8px;
}

.filter-form {
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #ebeef5;
}

.filter-form :deep(.el-form-item) {
  margin-bottom: 12px;
}

.change-table {
  width: 100%;
}

.arrow-cell {
  text-align: center;
  color: #c0c4cc;
}

.value-old {
  color: #909399;
  text-decoration: line-through;
}

.value-new {
  color: #409eff;
  font-weight: 500;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
