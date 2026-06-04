<template>
  <div class="closure-verification-page">
    <!-- Tabs & Search -->
    <el-card shadow="never" class="filter-card">
      <div class="filter-header">
        <el-tabs v-model="activeTab" @tab-change="handleTabChange">
          <el-tab-pane label="待验证" name="pending" />
          <el-tab-pane label="已通过" name="verified" />
          <el-tab-pane label="未通过" name="failed" />
          <el-tab-pane label="全部" name="all" />
        </el-tabs>
        <el-form :inline="true" :model="queryForm" @submit.prevent="handleSearch">
          <el-form-item label="工单标题">
            <el-input v-model="queryForm.title" placeholder="搜索工单标题" clearable style="width: 200px" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSearch">
              <el-icon><Search /></el-icon>查询
            </el-button>
            <el-button @click="handleReset">
              <el-icon><Refresh /></el-icon>重置
            </el-button>
          </el-form-item>
        </el-form>
      </div>
    </el-card>

    <!-- Data Table -->
    <el-card shadow="never" class="table-card">
      <el-table stripe v-loading="loading" :data="tableData"border style="width: 100%">
        <el-table-column prop="title" label="工单标题" min-width="200" show-overflow-tooltip />
        <el-table-column prop="alert_name" label="关联告警" min-width="160" show-overflow-tooltip>
          <template #default="{ row }">
            <el-tag v-if="row.alert_name" size="small" type="warning">{{ row.alert_name }}</el-tag>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="verification_status" label="验证状态" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.verification_status)" effect="dark" size="small">
              {{ statusLabel(row.verification_status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="verifier" label="验证人" width="120" align="center">
          <template #default="{ row }">
            {{ row.verifier || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="verification_time" label="验证时间" width="180" align="center">
          <template #default="{ row }">
            {{ formatTime(row.verification_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="resolved_by" label="处理人" width="120" align="center">
          <template #default="{ row }">
            {{ row.resolved_by || row.assignee || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="resolved_at" label="解决时间" width="180" align="center">
          <template #default="{ row }">
            {{ formatTime(row.resolved_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" align="center" fixed="right">
          <template #default="{ row }">
            <template v-if="row.verification_status === 'pending' || !row.verification_status">
              <el-button type="success" plain size="small" @click="handleVerify(row, 'verified')">
                通过
              </el-button>
              <el-button type="danger" plain size="small" @click="handleVerify(row, 'failed')">
                不通过
              </el-button>
            </template>
            <el-button type="primary" plain size="small" @click="handleDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- Pagination -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          background
          @size-change="fetchData"
          @current-change="fetchData"
        />
      </div>
    </el-card>

    <!-- Detail Drawer -->
    <el-drawer v-model="drawerVisible" title="工单验证详情" size="560px">
      <template v-if="currentRow">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="工单标题">{{ currentRow.title }}</el-descriptions-item>
          <el-descriptions-item label="关联告警">{{ currentRow.alert_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="验证状态">
            <el-tag :type="statusTagType(currentRow.verification_status)" effect="dark">
              {{ statusLabel(currentRow.verification_status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="验证人">{{ currentRow.verifier || '-' }}</el-descriptions-item>
          <el-descriptions-item label="验证时间">{{ formatTime(currentRow.verification_time) }}</el-descriptions-item>
          <el-descriptions-item label="处理人">{{ currentRow.resolved_by || currentRow.assignee || '-' }}</el-descriptions-item>
          <el-descriptions-item label="解决时间">{{ formatTime(currentRow.resolved_at) }}</el-descriptions-item>
          <el-descriptions-item label="工单描述">{{ currentRow.description || '-' }}</el-descriptions-item>
          <el-descriptions-item v-if="currentRow.verification_remark" label="验证备注">
            {{ currentRow.verification_remark }}
          </el-descriptions-item>
        </el-descriptions>

        <div v-if="!currentRow.verification_status || currentRow.verification_status === 'pending'" class="drawer-actions">
          <el-input
            v-model="verifyRemark"
            type="textarea"
            :rows="3"
            placeholder="验证备注（可选）"
            style="margin-bottom: 12px"
          />
          <div style="display: flex; gap: 8px">
            <el-button type="success" @click="handleVerify(currentRow, 'verified')">验证通过</el-button>
            <el-button type="danger" @click="handleVerify(currentRow, 'failed')">验证不通过</el-button>
          </div>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { Search, Refresh } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import client from '@/shared/api/client'
import { API } from '@/shared/api/routes'

interface TicketRecord {
  id: string | number
  title: string
  alert_name: string
  verification_status: 'pending' | 'verified' | 'failed' | ''
  verifier: string
  verification_time: string
  verification_remark: string
  resolved_by: string
  assignee: string
  resolved_at: string
  description: string
}

const loading = ref(false)
const tableData = ref<TicketRecord[]>([])
const drawerVisible = ref(false)
const currentRow = ref<TicketRecord | null>(null)
const activeTab = ref('pending')
const verifyRemark = ref('')

const queryForm = reactive({
  title: '',
})

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0,
})

// Local verification tracking
const verificationMap = reactive<Record<string | number, { status: string; verifier: string; time: string; remark: string }>>({})

function statusTagType(status: string): '' | 'success' | 'danger' | 'warning' {
  const map: Record<string, '' | 'success' | 'danger' | 'warning'> = {
    pending: 'warning',
    verified: 'success',
    failed: 'danger',
  }
  return map[status] || ''
}

function statusLabel(status: string): string {
  const map: Record<string, string> = {
    pending: '待验证',
    verified: '已通过',
    failed: '未通过',
  }
  return map[status] || '待验证'
}

function formatTime(t: string | undefined): string {
  if (!t) return '-'
  return new Date(t).toLocaleString('zh-CN')
}

function getEffectiveStatus(row: TicketRecord): string {
  const local = verificationMap[row.id]
  if (local) return local.status
  return row.verification_status || 'pending'
}

function buildParams() {
  const params: Record<string, any> = {
    page: pagination.page,
    page_size: pagination.page_size,
    status: 'resolved',
    title: queryForm.title || undefined,
  }
  if (activeTab.value !== 'all') {
    params.verification_status = activeTab.value
  }
  return params
}

async function fetchData() {
  loading.value = true
  try {
    const res = await client.get(API.TICKETS, { params: buildParams() })
    const data = res.data?.data ?? res.data ?? {}
    let items = data.items ?? data.records ?? data.list ?? []
    // Merge local verification state
    items = items.map((row: TicketRecord) => {
      const local = verificationMap[row.id]
      if (local) {
        return { ...row, verification_status: local.status, verifier: local.verifier, verification_time: local.time, verification_remark: local.remark }
      }
      return { ...row, verification_status: row.verification_status || 'pending' }
    })
    // Client-side filter by tab
    if (activeTab.value !== 'all') {
      items = items.filter((r: TicketRecord) => getEffectiveStatus(r) === activeTab.value)
    }
    tableData.value = items
    pagination.total = data.total ?? items.length
  } catch (e: any) {
    ElMessage.error('获取工单数据失败: ' + (e.message ?? '未知错误'))
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  pagination.page = 1
  fetchData()
}

function handleReset() {
  queryForm.title = ''
  handleSearch()
}

function handleTabChange() {
  pagination.page = 1
  fetchData()
}

function handleDetail(row: TicketRecord) {
  currentRow.value = row
  verifyRemark.value = row.verification_remark || ''
  drawerVisible.value = true
}

function handleVerify(row: TicketRecord, status: 'verified' | 'failed') {
  const action = status === 'verified' ? '通过' : '不通过'
  ElMessageBox.confirm(
    `确认将工单「${row.title}」标记为验证${action}？`,
    '验证确认',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: status === 'verified' ? 'success' : 'warning',
    },
  ).then(() => {
    const currentUser = '当前用户' // TODO: get from auth store
    verificationMap[row.id] = {
      status,
      verifier: currentUser,
      time: new Date().toISOString(),
      remark: verifyRemark.value,
    }
    // Update in table
    const idx = tableData.value.findIndex((r) => r.id === row.id)
    if (idx !== -1) {
      tableData.value[idx] = {
        ...tableData.value[idx],
        verification_status: status,
        verifier: currentUser,
        verification_time: new Date().toISOString(),
        verification_remark: verifyRemark.value,
      }
    }
    if (currentRow.value && currentRow.value.id === row.id) {
      currentRow.value = { ...currentRow.value, verification_status: status, verifier: currentUser, verification_time: new Date().toISOString() }
    }
    ElMessage.success(`工单已标记为验证${action}`)
  }).catch(() => {
    // cancelled
  })
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.closure-verification-page {
  padding: 16px;
}
.filter-card {
  margin-bottom: 16px;
}
.filter-header {
  display: flex;
  flex-direction: column;
}
.filter-header :deep(.el-tabs) {
  margin-bottom: -16px;
}
.table-card {
  margin-bottom: 16px;
}
.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
.text-muted {
  color: #c9cdd4;
}
.drawer-actions {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #e5e6eb;
}
</style>
