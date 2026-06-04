<template>
  <div class="page-container">
    <div class="autops-page-header">
      <div>
        <div class="autops-page-title">审计日志</div>
        <div class="autops-page-desc">查看系统操作审计日志</div>
      </div>
    </div>

    <div class="autops-card">
      
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px">
          <span style="font-size:18px;font-weight:600">审计日志</span>
          <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
            <el-radio-group v-model="viewMode" size="small">
              <el-radio-button value="table">表格</el-radio-button>
              <el-radio-button value="timeline">时间线</el-radio-button>
            </el-radio-group>
            <el-button @click="exportLogs" :loading="exporting" size="small">
              <el-icon><Download /></el-icon>
              导出
            </el-button>
          </div>
        </div>
      

      <!-- Advanced Filters -->
      <div class="autops-toolbar">
        <el-date-picker
          v-model="dateRange"
          type="datetimerange"
          range-separator="至"
          start-placeholder="开始时间"
          end-placeholder="结束时间"
          style="width: 360px"
          @change="loadLogs"
        />
        <el-select v-model="filters.action" placeholder="操作类型" clearable style="width: 140px" @change="loadLogs">
          <el-option v-for="a in actionTypes" :key="a" :label="a" :value="a" />
        </el-select>
        <el-input v-model="filters.user" placeholder="用户" style="width: 130px" clearable @change="loadLogs" />
        <el-select v-model="filters.resource_type" placeholder="资源类型" clearable style="width: 140px" @change="loadLogs">
          <el-option v-for="rt in resourceTypes" :key="rt" :label="rt" :value="rt" />
        </el-select>
        <el-button type="primary" @click="loadLogs">查询</el-button>
        <el-button @click="resetFilters">重置</el-button>
      </div>

      <!-- Table View -->
      <template v-if="viewMode === 'table'">
        <el-table stripe :data="logs" v-loading="loading"@row-click="openDetail" style="cursor:pointer">
          <el-table-column prop="action" label="操作" width="180">
            <template #default="{ row }">
              <el-tag :type="getActionTagType(row.action)" size="small">{{ row.action }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="resource_type" label="资源类型" width="120" />
          <el-table-column prop="resource_id" label="资源ID" width="160" show-overflow-tooltip />
          <el-table-column prop="user_id" label="用户" width="120" />
          <el-table-column prop="detail" label="详情" min-width="250" show-overflow-tooltip />
          <el-table-column prop="ip_address" label="IP" width="130" />
          <el-table-column prop="trace_id" label="TraceID" width="140" show-overflow-tooltip />
          <el-table-column prop="created_at" label="时间" width="170" sortable>
            <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
          </el-table-column>
        </el-table>
      </template>

      <!-- Timeline View -->
      <template v-if="viewMode === 'timeline'">
        <div class="timeline-wrapper" v-loading="loading">
          <el-timeline v-if="logs.length">
            <el-timeline-item
              v-for="log in logs"
              :key="log.id"
              :timestamp="formatTime(log.created_at)"
              placement="top"
              :type="getTimelineColor(log.action)"
              @click="openDetail(log)"
              style="cursor:pointer"
            >
              <div class="autops-card timeline-card">
                <div class="timeline-header">
                  <el-tag :type="getActionTagType(log.action)" size="small">{{ log.action }}</el-tag>
                  <span class="timeline-user">{{ log.user_id }}</span>
                  <span class="timeline-resource">{{ log.resource_type }} / {{ log.resource_id }}</span>
                </div>
                <div class="timeline-detail">{{ log.detail || '—' }}</div>
                <div class="timeline-meta">
                  <span>IP: {{ log.ip_address || '—' }}</span>
                  <span v-if="log.trace_id">Trace: {{ log.trace_id }}</span>
                </div>
              </div>
            </el-timeline-item>
          </el-timeline>
          <el-empty v-else description="暂无审计日志" />
        </div>
      </template>

      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :page-sizes="[20, 50, 100]"
        :total="total"
        layout="total, sizes, prev, pager, next"
        @change="loadLogs"
        style="margin-top: 16px; justify-content: flex-end"
      />
    </div>

    <!-- Detail Drawer -->
    <el-drawer v-model="drawerVisible" title="审计日志详情" size="520px">
      <template v-if="detailEntry">
        <el-descriptions :column="1" border size="default">
          <el-descriptions-item label="操作">
            <el-tag :type="getActionTagType(detailEntry.action)">{{ detailEntry.action }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="资源类型">{{ detailEntry.resource_type }}</el-descriptions-item>
          <el-descriptions-item label="资源ID">{{ detailEntry.resource_id }}</el-descriptions-item>
          <el-descriptions-item label="用户">{{ detailEntry.user_id }}</el-descriptions-item>
          <el-descriptions-item label="IP 地址">{{ detailEntry.ip_address }}</el-descriptions-item>
          <el-descriptions-item label="TraceID">{{ detailEntry.trace_id }}</el-descriptions-item>
          <el-descriptions-item label="时间">{{ formatTime(detailEntry.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="详情">
            <div class="detail-json">
              <pre>{{ formatDetail(detailEntry.detail) }}</pre>
            </div>
          </el-descriptions-item>
        </el-descriptions>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Download } from '@element-plus/icons-vue'
import api from '@/shared/api/client'
import { API as R } from '@/shared/api/routes'

const loading = ref(false)
const exporting = ref(false)
const logs = ref<any[]>([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const dateRange = ref<any>(null)
const viewMode = ref<'table' | 'timeline'>('table')

const filters = reactive({ user: '', action: '', resource_type: '' })

// Filter options
const actionTypes = ['create', 'update', 'delete', 'login', 'logout', 'execute', 'import', 'export', 'config_change']
const resourceTypes = ['user', 'role', 'asset', 'policy', 'script', 'alert', 'api_key', 'config', 'execution']

// Detail drawer
const drawerVisible = ref(false)
const detailEntry = ref<any>(null)

function formatTime(t: string) { return t ? new Date(t).toLocaleString('zh-CN') : '' }

function formatDetail(detail: any) {
  if (!detail) return ''
  if (typeof detail === 'string') {
    try { return JSON.stringify(JSON.parse(detail), null, 2) } catch { return detail }
  }
  return JSON.stringify(detail, null, 2)
}

function getActionTagType(action: string): '' | 'success' | 'warning' | 'danger' | 'info' {
  if (!action) return 'info'
  const a = action.toLowerCase()
  if (a.includes('delete') || a.includes('remove')) return 'danger'
  if (a.includes('create') || a.includes('add')) return 'success'
  if (a.includes('update') || a.includes('edit') || a.includes('change')) return 'warning'
  if (a.includes('login')) return ''
  return 'info'
}

function getTimelineColor(action: string): '' | 'success' | 'warning' | 'danger' | 'info' | 'primary' {
  if (!action) return 'info'
  const a = action.toLowerCase()
  if (a.includes('delete')) return 'danger'
  if (a.includes('create')) return 'success'
  if (a.includes('update')) return 'warning'
  if (a.includes('login')) return 'primary'
  return 'info'
}

function openDetail(row: any) {
  detailEntry.value = row
  drawerVisible.value = true
}

function resetFilters() {
  filters.user = ''
  filters.action = ''
  filters.resource_type = ''
  dateRange.value = null
  page.value = 1
  loadLogs()
}

async function loadLogs() {
  loading.value = true
  try {
    const params: any = { page: page.value, page_size: pageSize.value }
    if (filters.user) params.username = filters.user
    if (filters.action) params.action = filters.action
    if (filters.resource_type) params.resource_type = filters.resource_type
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_time = dateRange.value[0].toISOString()
      params.end_time = dateRange.value[1].toISOString()
    }
    const { data } = await api.get(R.AUDIT, { params })
    if (data.code === 0) {
      logs.value = data.data.items || []
      total.value = data.data.total || 0
    }
  } finally {
    loading.value = false
  }
}

async function exportLogs() {
  exporting.value = true
  try {
    const params: any = { page: 1, page_size: 100, export: true }
    if (filters.user) params.username = filters.user
    if (filters.action) params.action = filters.action
    if (filters.resource_type) params.resource_type = filters.resource_type
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_time = dateRange.value[0].toISOString()
      params.end_time = dateRange.value[1].toISOString()
    }
    const { data } = await api.get(R.AUDIT, { params, responseType: 'blob' })
    // If API returns JSON array instead of blob, handle that too
    let csvContent: string
    if (data instanceof Blob) {
      const url = window.URL.createObjectURL(data)
      const a = document.createElement('a')
      a.href = url
      a.download = 'audit-logs-' + new Date().toISOString().slice(0, 10) + '.csv'
      a.click()
      window.URL.revokeObjectURL(url)
      ElMessage.success('导出成功')
      exporting.value = false
      return
    }
    // Fallback: build CSV from JSON
    const items = data.data?.items || data.data || data || []
    if (!Array.isArray(items) || items.length === 0) {
      ElMessage.warning('无数据可导出')
      exporting.value = false
      return
    }
    const headers = ['action', 'resource_type', 'resource_id', 'user_id', 'detail', 'ip_address', 'trace_id', 'created_at']
    const rows = items.map((item: any) => headers.map(h => {
      const val = item[h] ?? ''
      return typeof val === 'object' ? JSON.stringify(val) : String(val)
    }).join(','))
    csvContent = [headers.join(','), ...rows].join('\n')
    const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'audit-logs-' + new Date().toISOString().slice(0, 10) + '.csv'
    a.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (e: any) {
    ElMessage.error('导出失败')
  } finally {
    exporting.value = false
  }
}

onMounted(() => loadLogs())
</script>

<style scoped>


.filter-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 16px;
  padding: 12px 16px;
  background: #f7f8fa;
  border-radius: 6px;
}

.timeline-wrapper { padding: 8px 0; max-height: 600px; overflow-y: auto; }

.timeline-card { cursor: pointer; }
.timeline-card :deep(.el-card__body) { padding: 12px 16px; }
.timeline-header { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.timeline-user { color: #4e5969; font-weight: 500; }
.timeline-resource { color: #86909c; font-size: 13px; }
.timeline-detail { color: #1d2129; font-size: 13px; margin-bottom: 6px; }
.timeline-meta { color: #86909c; font-size: 12px; display: flex; gap: 16px; }

.detail-json pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
  font-size: 13px;
  background: #f7f8fa;
  padding: 8px;
  border-radius: 4px;
  max-height: 300px;
  overflow-y: auto;
}
</style>
