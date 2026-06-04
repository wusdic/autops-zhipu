<template>
  <div class="discovery-result-page">
    <!-- 搜索与筛选栏 -->
    <el-card shadow="never" class="filter-card">
      <el-form :inline="true" :model="filterForm" @submit.prevent="handleSearch">
        <el-form-item label="关键词">
          <el-input
            v-model="filterForm.keyword"
            placeholder="搜索 IP / 主机名"
            clearable
            style="width: 220px"
            @clear="handleSearch"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select
            v-model="filterForm.status"
            placeholder="全部状态"
            clearable
            style="width: 150px"
            @change="handleSearch"
          >
            <el-option label="新增" value="new" />
            <el-option label="已忽略" value="ignored" />
            <el-option label="已导入" value="imported" />
          </el-select>
        </el-form-item>
        <el-form-item label="资产类型">
          <el-select
            v-model="filterForm.asset_type"
            placeholder="全部类型"
            clearable
            style="width: 150px"
            @change="handleSearch"
          >
            <el-option label="服务器" value="server" />
            <el-option label="网络设备" value="network" />
            <el-option label="安全设备" value="security" />
            <el-option label="数据库" value="database" />
            <el-option label="中间件" value="middleware" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 操作栏 -->
    <el-card shadow="never" class="table-card">
      <template #header>
        <div class="card-header">
          <span class="title">发现结果列表</span>
          <div class="actions">
          <el-button
             type="primary"
             :icon="Download"
             :disabled="!selectedRows.length"
             @click="handleBatchImport"
           >
             批量导入 ({{ selectedRows.length }})
           </el-button>
           <el-button
             type="success"
             :disabled="!selectedRows.length"
             @click="handleManageToAssets"
           >
             <el-icon><Plus /></el-icon> 纳管到资产
           </el-button>
           <el-button
              :icon="RefreshRight"
              :loading="loading"
              @click="fetchData"
            >
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <!-- 数据表格 -->
      <el-table stripe
 v-loading="loading"
 :data="tableData"
 border@selection-change="handleSelectionChange"
 @sort-change="handleSortChange"
 >
        <el-table-column type="selection" width="50" align="center" />
        <el-table-column prop="ip" label="IP 地址" min-width="140" sortable="custom" show-overflow-tooltip />
        <el-table-column prop="hostname" label="主机名" min-width="150" show-overflow-tooltip />
        <el-table-column prop="asset_type" label="资产类型" min-width="110">
          <template #default="{ row }">
            <el-tag :type="assetTypeTagMap[row.asset_type] || 'info'" size="small">
              {{ assetTypeLabelMap[row.asset_type] || row.asset_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="port" label="端口" min-width="100">
          <template #default="{ row }">
            <span>{{ row.ports?.join(', ') || row.port || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" min-width="100">
          <template #default="{ row }">
            <el-tag :type="statusTagMap[row.status]" size="small" effect="dark">
              {{ statusLabelMap[row.status] || row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="discovered_at" label="发现时间" min-width="170" sortable="custom">
          <template #default="{ row }">
            {{ formatTime(row.discovered_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="os_info" label="操作系统" min-width="140" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.os_info || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" align="center" fixed="right">
          <template #default="{ row }">
            <template v-if="row.status === 'new'">
              <el-button type="primary" plain size="small" @click="handleImport(row)">
                导入
              </el-button>
              <el-button type="warning" plain size="small" @click="handleIgnore(row)">
                忽略
              </el-button>
            </template>
            <template v-else-if="row.status === 'ignored'">
              <el-button type="primary" plain size="small" @click="handleImport(row)">
                导入
              </el-button>
            </template>
            <template v-else>
              <el-tag type="success" size="small">已导入</el-tag>
            </template>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          background
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 导入确认弹窗 -->
    <el-dialog v-model="importDialogVisible" title="导入资产确认" width="600px" destroy-on-close>
      <el-descriptions :column="1" border>
        <el-descriptions-item label="IP 地址">{{ currentRow?.ip }}</el-descriptions-item>
        <el-descriptions-item label="主机名">{{ currentRow?.hostname || '-' }}</el-descriptions-item>
        <el-descriptions-item label="资产类型">
          {{ assetTypeLabelMap[currentRow?.asset_type] || currentRow?.asset_type }}
        </el-descriptions-item>
        <el-descriptions-item label="端口">{{ currentRow?.ports?.join(', ') || currentRow?.port || '-' }}</el-descriptions-item>
      </el-descriptions>
      <el-form :model="importForm" label-width="100px" style="margin-top: 20px">
        <el-form-item label="资产分组">
          <el-select v-model="importForm.group_id" placeholder="选择分组（可选）" clearable style="width: 100%">
            <el-option label="默认分组" :value="0" />
            <el-option label="服务器组" :value="1" />
            <el-option label="网络设备组" :value="2" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="importForm.remark" type="textarea" :rows="2" placeholder="备注信息（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="importDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="importLoading" @click="confirmImport">确认导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, RefreshRight, Download } from '@element-plus/icons-vue'
import { Plus } from '@element-plus/icons-vue'
import client from '@/shared/api/client'
import { API } from '@/shared/api/routes'
import { useWorkflowNav } from '@/shared/composables/useWorkflowNav'

// ─── 类型定义 ────────────────────────────────────────
interface DiscoveryResult {
  id: number | string
  ip: string
  hostname: string
  asset_type: string
  ports: string[]
  port?: string
  status: 'new' | 'ignored' | 'imported'
  discovered_at: string
  os_info?: string
  [key: string]: unknown
}

// ─── 响应式状态 ──────────────────────────────────────
const loading = ref(false)
const importLoading = ref(false)
const importDialogVisible = ref(false)
const tableData = ref<DiscoveryResult[]>([])
const selectedRows = ref<DiscoveryResult[]>([])
const currentRow = ref<DiscoveryResult | null>(null)
const { navToAssetFromDiscovery } = useWorkflowNav()

const filterForm = reactive({
  keyword: '',
  status: '',
  asset_type: '',
})

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0,
})

const sortInfo = reactive({
  sort_by: '',
  sort_order: '',
})

const importForm = reactive({
  group_id: undefined as number | undefined,
  remark: '',
})

// ─── 映射表 ──────────────────────────────────────────
const statusTagMap: Record<string, string> = {
  new: 'danger',
  ignored: 'warning',
  imported: 'success',
}

const statusLabelMap: Record<string, string> = {
  new: '新增',
  ignored: '已忽略',
  imported: '已导入',
}

const assetTypeTagMap: Record<string, string> = {
  server: '',
  network: 'success',
  security: 'danger',
  database: 'warning',
  middleware: 'info',
}

const assetTypeLabelMap: Record<string, string> = {
  server: '服务器',
  network: '网络设备',
  security: '安全设备',
  database: '数据库',
  middleware: '中间件',
}

// ─── 数据获取 ────────────────────────────────────────
async function fetchData() {
  loading.value = true
  try {
    const params: Record<string, unknown> = {
      page: pagination.page,
      page_size: pagination.page_size,
    }
    if (filterForm.keyword) params.keyword = filterForm.keyword
    if (filterForm.status) params.status = filterForm.status
    if (filterForm.asset_type) params.asset_type = filterForm.asset_type
    if (sortInfo.sort_by) {
      params.sort_by = sortInfo.sort_by
      params.sort_order = sortInfo.sort_order
    }
    const res = await client.get(API.DISCOVERY_RESULTS, { params })
    const data = res.data?.data ?? res.data
    if (Array.isArray(data)) {
      tableData.value = data
      pagination.total = data.length
    } else {
      tableData.value = data?.items ?? data?.results ?? data?.list ?? []
      pagination.total = data?.total ?? tableData.value.length
    }
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : '获取发现结果失败'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}

// ─── 搜索与筛选 ──────────────────────────────────────
function handleSearch() {
  pagination.page = 1
  fetchData()
}

function handleReset() {
  filterForm.keyword = ''
  filterForm.status = ''
  filterForm.asset_type = ''
  sortInfo.sort_by = ''
  sortInfo.sort_order = ''
  pagination.page = 1
  fetchData()
}

// ─── 排序 ────────────────────────────────────────────
function handleSortChange({ prop, order }: { prop: string; order: string | null }) {
  sortInfo.sort_by = order ? prop : ''
  sortInfo.sort_order = order === 'ascending' ? 'asc' : order === 'descending' ? 'desc' : ''
  fetchData()
}

// ─── 分页 ────────────────────────────────────────────
function handleSizeChange(size: number) {
  pagination.page_size = size
  pagination.page = 1
  fetchData()
}

function handlePageChange(page: number) {
  pagination.page = page
  fetchData()
}

// ─── 多选 ────────────────────────────────────────────
function handleSelectionChange(rows: DiscoveryResult[]) {
 selectedRows.value = rows
}
// ─── 纳管到资产工作流 ────────────────────────────────
const handleManageToAssets = () => {
  if (selectedRows.value.length > 0) {
    const ids = selectedRows.value.map(r => String(r.id))
    navToAssetFromDiscovery(ids)
  }
}

// ─── 导入 ────────────────────────────────────────────
function handleImport(row: DiscoveryResult) {
  currentRow.value = row
  importForm.group_id = undefined
  importForm.remark = ''
  importDialogVisible.value = true
}

async function confirmImport() {
  if (!currentRow.value) return
  importLoading.value = true
  try {
    const payload = {
      ...currentRow.value,
      group_id: importForm.group_id,
      remark: importForm.remark,
    }
    await client.post(API.ASSET_IMPORT, payload)
    ElMessage.success('导入成功')
    importDialogVisible.value = false
    fetchData()
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : '导入失败'
    ElMessage.error(msg)
  } finally {
    importLoading.value = false
  }
}

async function handleBatchImport() {
  const importable = selectedRows.value.filter(r => r.status !== 'imported')
  if (!importable.length) {
    ElMessage.warning('没有可导入的记录')
    return
  }
  try {
    await ElMessageBox.confirm(
      `确定批量导入选中的 ${importable.length} 条记录？`,
      '批量导入确认',
      { type: 'info' }
    )
    loading.value = true
    await client.post(API.ASSET_IMPORT, { items: importable })
    ElMessage.success(`成功导入 ${importable.length} 条记录`)
    fetchData()
  } catch (err: unknown) {
    if (err !== 'cancel') {
      const msg = err instanceof Error ? err.message : '批量导入失败'
      ElMessage.error(msg)
    }
  } finally {
    loading.value = false
  }
}

// ─── 忽略 ────────────────────────────────────────────
async function handleIgnore(row: DiscoveryResult) {
  try {
    await ElMessageBox.confirm(
      `确定忽略 ${row.ip} 的发现结果？`,
      '忽略确认',
      { type: 'warning' }
    )
    await client.patch(`${API.DISCOVERY_RESULTS}/${row.id}/ignore`, {})
    ElMessage.success('已忽略')
    fetchData()
  } catch (err: unknown) {
    if (err !== 'cancel') {
      const msg = err instanceof Error ? err.message : '操作失败'
      ElMessage.error(msg)
    }
  }
}

// ─── 工具函数 ────────────────────────────────────────
function formatTime(time: string): string {
  if (!time) return '-'
  try {
    return new Date(time).toLocaleString('zh-CN', { hour12: false })
  } catch {
    return time
  }
}

// ─── 初始化 ──────────────────────────────────────────
onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.discovery-result-page {
  padding: 20px;
}

.filter-card {
  margin-bottom: 16px;
}

.filter-card :deep(.el-card__body) {
  padding-bottom: 2px;
}

.table-card 
.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
  padding: 4px 0;
}
</style>
