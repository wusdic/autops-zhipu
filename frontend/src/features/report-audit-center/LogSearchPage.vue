<template>
  <div class="log-search-page">
    <div class="autops-page-header">
      <div class="autops-page-title">日志搜索</div>
      <div class="autops-page-desc">搜索和查询系统操作日志</div>
    </div>
    <!-- 搜索筛选区 -->
    <el-card class="filter-card" shadow="never">
      <el-form :model="queryParams" inline @submit.prevent="handleSearch">
        <el-form-item label="关键词">
          <el-input
            v-model="queryParams.keyword"
            placeholder="搜索日志关键词"
            clearable
            style="width: 220px"
            @keyup.enter="handleSearch"
          />
        </el-form-item>

        <el-form-item label="日志级别">
          <el-select
            v-model="queryParams.level"
            placeholder="全部级别"
            clearable
            style="width: 140px"
          >
            <el-option label="DEBUG" value="debug">
              <el-tag type="info" size="small">DEBUG</el-tag>
            </el-option>
            <el-option label="INFO" value="info">
              <el-tag type="success" size="small">INFO</el-tag>
            </el-option>
            <el-option label="WARN" value="warn">
              <el-tag type="warning" size="small">WARN</el-tag>
            </el-option>
            <el-option label="ERROR" value="error">
              <el-tag type="danger" size="small">ERROR</el-tag>
            </el-option>
          </el-select>
        </el-form-item>

        <el-form-item label="时间范围">
          <el-date-picker
            v-model="queryParams.dateRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            value-format="YYYY-MM-DD HH:mm:ss"
            style="width: 380px"
          />
        </el-form-item>

        <el-form-item label="来源">
          <el-input
            v-model="queryParams.source"
            placeholder="日志来源"
            clearable
            style="width: 180px"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
          <el-button type="success" :icon="Download" @click="handleExport">导出</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 日志表格区 -->
    <el-card class="table-card" shadow="never">
      <template #header>
        <span style="font-weight:600;font-size:15px">搜索结果</span>
      </template>
      <el-table stripe
 v-loading="loading"
 :data="logList"border
 style="width: 100%"
 @sort-change="handleSortChange"
 >
        <el-table-column prop="timestamp" label="时间" width="180" sortable="custom" align="center">
          <template #default="{ row }">
            {{ formatTime(row.timestamp) }}
          </template>
        </el-table-column>

        <el-table-column prop="level" label="级别" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="(levelTagType(row.level)) as TagType" size="small" effect="dark">
              {{ row.level?.toUpperCase() }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="source" label="来源" width="180" show-overflow-tooltip />

        <el-table-column prop="message" label="消息" min-width="480px" show-overflow-tooltip />

        <el-table-column label="操作" width="100" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" plain size="small" @click="handleViewDetail(row)">
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="queryParams.page"
          v-model:page-size="queryParams.pageSize"
          :page-sizes="[20, 50, 100, 200]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          background
          @size-change="fetchLogList"
          @current-change="fetchLogList"
        />
      </div>
    </el-card>

    <!-- 日志详情弹窗 -->
    <el-dialog v-model="detailVisible" title="日志详情" width="780px" destroy-on-close>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="时间">{{ formatTime(currentLog?.timestamp) }}</el-descriptions-item>
        <el-descriptions-item label="级别">
          <el-tag :type="(levelTagType(currentLog?.level)) as TagType" size="small" effect="dark">
            {{ currentLog?.level?.toUpperCase() }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="来源" :span="2">{{ currentLog?.source }}</el-descriptions-item>
        <el-descriptions-item label="消息" :span="2">
          <div class="log-message-detail">{{ currentLog?.message }}</div>
        </el-descriptions-item>
        <el-descriptions-item v-if="currentLog?.stack_trace" label="堆栈跟踪" :span="2">
          <pre class="stack-trace">{{ currentLog?.stack_trace }}</pre>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import type { TagType } from '@/shared/types'
import { ref, reactive, onMounted } from 'vue'
import { Search, Refresh, Download } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { API } from '@/shared/api/routes'
import client from '@/shared/api/client'
import type { AxiosResponse } from 'axios'

// ---------- 类型定义 ----------
interface LogEntry {
  id: string | number
  timestamp: string
  level: string
  source: string
  message: string
  stack_trace?: string
  [key: string]: unknown
}

interface QueryParams {
  keyword: string
  level: string
  dateRange: string[] | null
  source: string
  page: number
  pageSize: number
  orderBy: string
  orderDir: string
}

// ---------- 状态 ----------
const loading = ref(false)
const logList = ref<LogEntry[]>([])
const total = ref(0)
const detailVisible = ref(false)
const currentLog = ref<LogEntry | null>(null)

const queryParams = reactive<QueryParams>({
  keyword: 'primary',
  level: 'primary',
  dateRange: null,
  source: 'primary',
  page: 1,
  pageSize: 50,
  orderBy: 'timestamp',
  orderDir: 'desc',
})

// ---------- 工具函数 ----------
const levelTagType = (level?: string): TagType => {
  const map: Record<string, TagType> = {
    debug: 'info',
    info: 'success',
    warn: 'warning',
    error: 'danger',
  }
  return (map[level?.toLowerCase() || ''] || 'info') as TagType
}

const formatTime = (ts?: string): string => {
  if (!ts) return '-'
  const d = new Date(ts)
  if (isNaN(d.getTime())) return ts
  return d.toLocaleString('zh-CN', { hour12: false })
}

// ---------- 数据请求 ----------
const buildParams = (): Record<string, unknown> => {
  const params: Record<string, unknown> = {
    page: queryParams.page,
    page_size: queryParams.pageSize,
    ordering: queryParams.orderDir === 'desc' ? '-' + queryParams.orderBy : queryParams.orderBy,
  }
  if (queryParams.keyword) params.keyword = queryParams.keyword
  if (queryParams.level) params.level = queryParams.level
  if (queryParams.source) params.source = queryParams.source
  if (queryParams.dateRange && queryParams.dateRange.length === 2) {
    params.start_time = queryParams.dateRange[0]
    params.end_time = queryParams.dateRange[1]
  }
  return params
}

const fetchLogList = async () => {
  loading.value = true
  try {
    const res: AxiosResponse = await client.get(API.AUDIT, { params: buildParams() })
    const data = res.data?.data ?? res.data
    logList.value = data?.items ?? data?.results ?? data?.list ?? []
    total.value = data?.total ?? data?.count ?? 0
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : '请求日志列表失败'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}

// ---------- 事件处理 ----------
const handleSearch = () => {
  queryParams.page = 1
  fetchLogList()
}

const handleReset = () => {
  queryParams.keyword = ''
  queryParams.level = ''
  queryParams.dateRange = null
  queryParams.source = ''
  queryParams.page = 1
  queryParams.pageSize = 50
  queryParams.orderBy = 'timestamp'
  queryParams.orderDir = 'desc'
  fetchLogList()
}

const handleSortChange = ({ prop, order }: { prop: string | null; order: string | null }) => {
  queryParams.orderBy = prop || 'timestamp'
  queryParams.orderDir = order === 'ascending' ? 'asc' : 'desc'
  fetchLogList()
}

const handleViewDetail = (row: any) => {
  currentLog.value = row
  detailVisible.value = true
}

const handleExport = async () => {
  try {
    await ElMessageBox.confirm('确定导出当前筛选条件下的日志吗？', '导出确认', {
      type: 'warning',
      confirmButtonText: '导出',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }

  try {
    const params = { ...buildParams(), export: true }
    const res: AxiosResponse = await client.get(API.AUDIT, {
      params,
      responseType: 'blob',
    })
    const blob = new Blob([res.data], { type: 'text/csv;charset=utf-8;' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', 'audit_logs_' + Date.now() + '.csv')
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch {
    ElMessage.error('导出失败')
  }
}

// ---------- 初始化 ----------
onMounted(() => {
  fetchLogList()
})
</script>

<style scoped lang="scss">
.log-search-page {
  padding: var(--autops-space-lg);

  .filter-card {
    margin-bottom: var(--autops-space-lg);
  }

  .table-card {
    .pagination-wrapper {
      display: flex;
      justify-content: flex-end;
      margin-top: var(--autops-space-lg);
    }
  }

  .log-message-detail {
    max-height: 300px;
    overflow-y: auto;
    white-space: pre-wrap;
    word-break: break-all;
    font-family: 'Courier New', Courier, monospace;
    font-size: var(--autops-font-13);
    line-height: 1.6;
  }

  .stack-trace {
    max-height: 300px;
    overflow-y: auto;
    white-space: pre-wrap;
    word-break: break-all;
    font-size: var(--autops-font-12);
    line-height: 1.5;
    background: var(--autops-bg-2);
    padding: var(--autops-space-sm);
    border-radius: var(--autops-radius-sm);
    margin: 0;
  }
}
</style>
