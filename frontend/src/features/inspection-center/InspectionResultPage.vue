<template>
  <div class="autops-page-container">
    <PageHeader title="巡检结果" desc="查看详细的巡检检测项结果" />

    <!-- 搜索筛选区 -->
    <el-card class="filter-card" shadow="never">
      <el-form :model="queryParams" inline @submit.prevent="handleSearch">
        <el-form-item label="关键词">
          <el-input
            v-model="queryParams.keyword"
            placeholder="搜索资产名/检查项"
            clearable
            style="width: 220px"
            @keyup.enter="handleSearch"
          />
        </el-form-item>

        <el-form-item label="状态">
          <el-select v-model="queryParams.status" placeholder="全部状态" clearable style="width: 140px">
            <el-option label="通过" value="pass">
              <el-tag type="success" size="small">PASS</el-tag>
            </el-option>
            <el-option label="失败" value="fail">
              <el-tag type="danger" size="small">FAIL</el-tag>
            </el-option>
            <el-option label="警告" value="warn">
              <el-tag type="warning" size="small">WARN</el-tag>
            </el-option>
          </el-select>
        </el-form-item>

        <el-form-item label="检查类型">
          <el-select v-model="queryParams.check_type" placeholder="全部类型" clearable style="width: 160px">
            <el-option v-for="ct in checkTypes" :key="ct.value" :label="ct.label" :value="ct.value" />
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

        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
          <el-button type="success" :icon="Download" @click="handleExport">导出</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 统计概览 -->
    <el-row :gutter="16" class="stat-row">
      <el-col :xs="12" :sm="6">
        <div class="autops-metric-card">
          <div class="metric-icon bg-brand"><el-icon size="20"><Document /></el-icon></div>
          <div class="metric-label">检查总数</div>
          <div class="metric-value">{{ total }}</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="autops-metric-card">
          <div class="metric-icon bg-success"><el-icon size="20"><CircleCheckFilled /></el-icon></div>
          <div class="metric-label">通过</div>
          <div class="metric-value">{{ passCount }}</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="autops-metric-card">
          <div class="metric-icon bg-warning"><el-icon size="20"><Warning /></el-icon></div>
          <div class="metric-label">警告</div>
          <div class="metric-value">{{ warnCount }}</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="autops-metric-card">
          <div class="metric-icon bg-danger"><el-icon size="20"><CircleCloseFilled /></el-icon></div>
          <div class="metric-label">失败</div>
          <div class="metric-value">{{ failCount }}</div>
        </div>
      </el-col>
    </el-row>

    <!-- 检查结果表格 -->
    <el-card class="table-card" shadow="never">
      <template #header>
        <div class="autops-card-header">
          <span>巡检结果</span>
          <div class="header-actions">
            <el-button-group>
              <el-button
                :type="viewMode === 'table' ? 'primary' : 'default'"
                size="small"
                @click="viewMode = 'table'"
              >
                表格
              </el-button>
              <el-button
                :type="viewMode === 'group' ? 'primary' : 'default'"
                size="small"
                @click="viewMode = 'group'"
              >
                按资产分组
              </el-button>
            </el-button-group>
          </div>
        </div>
      </template>

      <!-- 表格视图 -->
      <el-table stripe
 v-if="viewMode === 'table'"
 v-loading="loading"
 :data="resultList"border
 style="width: 100%"
 @sort-change="handleSortChange"
 >
        <el-table-column prop="asset_name" label="资产名" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">
            <div class="asset-cell">
              <el-icon><Monitor /></el-icon>
              <span>{{ row.asset_name || row.asset?.name || '-' }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="check_type" label="检查类型" width="140" align="center">
          <template #default="{ row }">
            <el-tag size="small" type="info">{{ checkTypeLabel(row.check_type) }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <StatusBadge :status="row.status" />
          </template>
        </el-table-column>

        <el-table-column prop="check_item" label="检查项" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.check_item || row.item_name || '-' }}
          </template>
        </el-table-column>

        <el-table-column prop="detail" label="详情" min-width="260" show-overflow-tooltip>
          <template #default="{ row }">
            <span :class="{ 'text-danger': row.status === 'fail', 'text-warning': row.status === 'warn' }">
              {{ row.detail || row.message || row.description || '-' }}
            </span>
          </template>
        </el-table-column>

        <el-table-column prop="checked_at" label="检查时间" width="170" align="center" sortable="custom">
          <template #default="{ row }">
            {{ formatTime(row.checked_at || row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="180" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" plain size="small" @click="handleViewDetail(row)">
              详情
            </el-button>
            <el-button
              type="warning" plain
              size="small"
              @click="handleCreateTicket(row)"
            >
              工单
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分组视图 -->
      <div v-else v-loading="loading">
        <div v-for="group in groupedResults" :key="group.asset" class="asset-group">
          <div class="group-header">
            <el-icon><Monitor /></el-icon>
            <span class="group-name">{{ group.asset }}</span>
            <el-tag
              v-for="stat in group.stats"
              :key="stat.label"
              :type="(stat.type as TagType)"
              size="small"
              style="margin-left: 8px"
            >
              {{ stat.label }}: {{ stat.count }}
            </el-tag>
          </div>
          <el-table stripe  :data="group.items" border size="small" class="mb-lg">
            <el-table-column prop="check_type" label="检查类型" width="140" align="center">
              <template #default="{ row }">
                <el-tag size="small" type="info">{{ checkTypeLabel(row.check_type) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100" align="center">
              <template #default="{ row }">
                <StatusBadge :status="row.status" />
              </template>
            </el-table-column>
            <el-table-column prop="check_item" label="检查项" min-width="200" show-overflow-tooltip />
            <el-table-column prop="detail" label="详情" min-width="260" show-overflow-tooltip />
            <el-table-column prop="checked_at" label="检查时间" width="170" align="center">
              <template #default="{ row }">
                {{ formatTime(row.checked_at || row.created_at) }}
              </template>
            </el-table-column>
          </el-table>
        </div>
        <el-empty v-if="!groupedResults.length" description="暂无数据" />
      </div>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="queryParams.page"
          v-model:page-size="queryParams.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          background
          @size-change="fetchResultList"
          @current-change="fetchResultList"
        />
      </div>
    </el-card>

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailVisible" title="巡检结果详情" width="780px" destroy-on-close>
      <el-descriptions v-if="currentResult" :column="2" border>
        <el-descriptions-item label="资产名">{{ currentResult.asset_name || currentResult.asset?.name }}</el-descriptions-item>
        <el-descriptions-item label="资产IP">{{ currentResult.asset_ip || currentResult.asset?.ip || '-' }}</el-descriptions-item>
        <el-descriptions-item label="检查类型">
          <el-tag size="small" type="info">{{ checkTypeLabel(currentResult.check_type) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <StatusBadge :status="currentResult.status" />
        </el-descriptions-item>
        <el-descriptions-item label="检查项" :span="2">{{ currentResult.check_item || currentResult.item_name }}</el-descriptions-item>
        <el-descriptions-item label="详情" :span="2">
          <div class="detail-message">{{ currentResult.detail || currentResult.message || '-' }}</div>
        </el-descriptions-item>
        <el-descriptions-item label="期望值">{{ currentResult.expected || '-' }}</el-descriptions-item>
        <el-descriptions-item label="实际值">{{ currentResult.actual || '-' }}</el-descriptions-item>
        <el-descriptions-item label="检查时间">{{ formatTime(currentResult.checked_at || currentResult.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="任务ID">{{ currentResult.task_id || '-' }}</el-descriptions-item>
       <el-descriptions-item v-if="currentResult.suggestion" label="建议" :span="2">
         <div class="detail-message">{{ currentResult.suggestion }}</div>
       </el-descriptions-item>
     </el-descriptions>
     <template #footer>
       <el-button @click="detailVisible = false">关闭</el-button>
       <el-button
         type="warning"
         @click="navToAnomalyFromInspection(currentResult?.task_id ?? '')"
       >
         <el-icon><Warning /></el-icon> 查看异常
       </el-button>
       <el-button
         type="primary"
         @click="navToReportFromInspection(currentResult?.task_id ?? '')"
       >
         <el-icon><Document /></el-icon> 生成报告
       </el-button>
     </template>
   </el-dialog>
  </div>
</template>

<script setup lang="ts">
import type { TagType } from '@/shared/types'
import { ref, reactive, computed, onMounted } from 'vue'
import { Search, Refresh, Download, Monitor } from '@element-plus/icons-vue'
import PageHeader from '@/shared/components/PageHeader.vue'
import StatusBadge from '@/shared/components/StatusBadge.vue'
import { Warning, Document, CircleCheckFilled, CircleCloseFilled } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { API } from '@/shared/api/routes'
import client from '@/shared/api/client'
import type { AxiosResponse } from 'axios'
import { useWorkflowNav } from '@/shared/composables/useWorkflowNav'

// ---------- 类型定义 ----------
interface InspectionResult {
  id: string | number
  asset_name?: string
  asset?: { name: string; ip?: string }
  asset_ip?: string
  check_type: string
  status: 'pass' | 'fail' | 'warn'
  check_item?: string
  item_name?: string
  detail?: string
  message?: string
  description?: string
  expected?: string
  actual?: string
  checked_at?: string
  created_at?: string
  task_id?: string
  suggestion?: string
  [key: string]: unknown
}

interface QueryParams {
  keyword: string
  status: string
  check_type: string
  dateRange: string[] | null
  page: number
  pageSize: number
  orderBy: string
  orderDir: string
}

interface GroupResult {
  asset: string
  items: InspectionResult[]
  stats: Array<{ label: string; count: number; type: string }>
}

// ---------- 常量 ----------
const checkTypes = [
  { label: '系统基线', value: 'baseline' },
  { label: '安全漏洞', value: 'vulnerability' },
  { label: '配置合规', value: 'compliance' },
  { label: '性能检查', value: 'performance' },
  { label: '网络连通', value: 'network' },
  { label: '服务状态', value: 'service' },
  { label: '磁盘空间', value: 'disk' },
  { label: '证书有效期', value: 'certificate' },
]

// ---------- 状态 ----------
const loading = ref(false)
const resultList = ref<InspectionResult[]>([])
const total = ref(0)
const detailVisible = ref(false)
const currentResult = ref<InspectionResult | null>(null)
const viewMode = ref<'table' | 'group'>('table')
const { navToAnomalyFromInspection, navToReportFromInspection } = useWorkflowNav()

const queryParams = reactive<QueryParams>({
  keyword: '',
  status: '',
  check_type: '',
  dateRange: null,
  page: 1,
  pageSize: 20,
  orderBy: 'checked_at',
  orderDir: 'desc',
})

// ---------- 计算属性 ----------
const passCount = computed(() => resultList.value.filter(r => r.status === 'pass').length)
const warnCount = computed(() => resultList.value.filter(r => r.status === 'warn').length)
const failCount = computed(() => resultList.value.filter(r => r.status === 'fail').length)

const groupedResults = computed((): GroupResult[] => {
  const map = new Map<string, InspectionResult[]>()
  for (const item of resultList.value) {
    const key = item.asset_name || item.asset?.name || '未知资产'
    if (!map.has(key)) map.set(key, [])
    map.get(key)!.push(item)
  }
  return Array.from(map.entries()).map(([asset, items]) => ({
    asset,
    items,
    stats: [
      { label: '通过', count: items.filter(i => i.status === 'pass').length, type: 'success' },
      { label: '警告', count: items.filter(i => i.status === 'warn').length, type: 'warning' },
      { label: '失败', count: items.filter(i => i.status === 'fail').length, type: 'danger' },
    ],
  }))
})

// ---------- 工具函数 ----------
const formatTime = (ts?: string): string => {
  if (!ts) return '-'
  const d = new Date(ts)
  if (isNaN(d.getTime())) return ts
  return d.toLocaleString('zh-CN', { hour12: false })
}

const statusTagType = (status?: string): TagType => {
  const map: Record<string, TagType> = {
    pass: 'success',
    fail: 'danger',
    warn: 'warning',
  }
  return (map[status || ''] || 'warning') as TagType
}

const statusLabel = (status?: string): string => {
  const map: Record<string, string> = { pass: '通过', fail: '失败', warn: '警告' }
  return map[status || ''] || status || '-'
}

const checkTypeLabel = (type?: string): string => {
  const found = checkTypes.find(ct => ct.value === type)
  return found?.label || type || '-'
}

// ---------- 数据请求 ----------
const buildParams = (): Record<string, unknown> => {
  const params: Record<string, unknown> = {
    page: queryParams.page,
    page_size: queryParams.pageSize,
    ordering: queryParams.orderDir === 'desc' ? '-' + queryParams.orderBy : queryParams.orderBy,
  }
  if (queryParams.keyword) params.keyword = queryParams.keyword
  if (queryParams.status) params.status = queryParams.status
  if (queryParams.check_type) params.check_type = queryParams.check_type
  if (queryParams.dateRange && queryParams.dateRange.length === 2) {
    params.start_time = queryParams.dateRange[0]
    params.end_time = queryParams.dateRange[1]
  }
  return params
}

const fetchResultList = async () => {
  loading.value = true
  try {
    const res: AxiosResponse = await client.get(API.INSPECTION.RESULTS, { params: buildParams() })
    const data = res.data?.data ?? res.data
    resultList.value = data?.items ?? data?.results ?? data?.list ?? []
    total.value = data?.total ?? data?.count ?? 0
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : '获取巡检结果失败'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}

// ---------- 事件处理 ----------
const handleSearch = () => {
  queryParams.page = 1
  fetchResultList()
}

const handleReset = () => {
  queryParams.keyword = ''
  queryParams.status = ''
  queryParams.check_type = ''
  queryParams.dateRange = null
  queryParams.page = 1
  queryParams.pageSize = 20
  queryParams.orderBy = 'checked_at'
  queryParams.orderDir = 'desc'
  fetchResultList()
}

const handleSortChange = ({ prop, order }: { prop: string | null; order: string | null }) => {
  queryParams.orderBy = prop || 'checked_at'
  queryParams.orderDir = order === 'ascending' ? 'asc' : 'desc'
  fetchResultList()
}

const handleViewDetail = (row: any) => {
  currentResult.value = row
  detailVisible.value = true
}

const handleCreateTicket = (row: any) => {
  ElMessage.info('创建工单: ' + row.check_item || row.item_name + ' - ' + row.asset_name || row.asset?.name)
}

const handleExport = async () => {
  try {
    await ElMessageBox.confirm('确定导出当前筛选条件下的巡检结果吗？', '导出确认', {
      type: 'warning',
      confirmButtonText: '导出',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }

  try {
    const params = { ...buildParams(), export: true }
    const res: AxiosResponse = await client.get(API.INSPECTION.RESULTS, {
      params,
      responseType: 'blob',
    })
    const blob = new Blob([res.data], { type: 'text/csv;charset=utf-8;' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', 'inspection_results_' + Date.now() + '.csv')
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch {
    ElMessage.error('导出失败')
  }
}

// ---------- 生命周期 ----------
onMounted(() => {
  fetchResultList()
})
</script>

<style scoped lang="scss">
.inspection-result-page {
  padding: var(--autops-space-lg);

  .filter-card {
    margin-bottom: var(--autops-space-lg);
  }

  .stat-row {
    margin-bottom: var(--autops-space-lg);
  }

  .table-card {
    
    .asset-cell {
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .pagination-wrapper {
      display: flex;
      justify-content: flex-end;
      margin-top: var(--autops-space-lg);
    }
  }

  .asset-group {
    .group-header {
      display: flex;
      align-items: center;
      padding: var(--autops-space-sm) 0;
      font-size: var(--autops-font-14);
      font-weight: 600;

      .group-name {
        margin-left: 6px;
      }
    }
  }

  
  
  .detail-message {
    max-height: 200px;
    overflow-y: auto;
    white-space: pre-wrap;
    word-break: break-all;
    line-height: 1.6;
  }
}
</style>
