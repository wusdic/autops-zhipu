<template>
  <div class="evidence-archive-page">
    <!-- Search -->
    <el-card shadow="never" class="filter-card">
      <el-form :inline="true" :model="queryForm" @submit.prevent="handleSearch">
        <el-form-item label="告警ID">
          <el-input v-model="queryForm.alert_id" placeholder="输入告警ID查询证据链" clearable style="width: 240px" />
        </el-form-item>
        <el-form-item label="事件类型">
          <el-select v-model="queryForm.evidence_type" placeholder="全部" clearable style="width: 140px">
            <el-option label="告警创建" value="alert_created" />
            <el-option label="状态变更" value="status_change" />
            <el-option label="处置操作" value="action" />
            <el-option label="关联事件" value="event" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="queryForm.keyword" placeholder="搜索标题/内容" clearable style="width: 200px" />
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
    </el-card>

    <!-- Alert Info (when loaded by alert_id) -->
    <el-card v-if="alertInfo" shadow="never" class="alert-info-card">
      <template #header>
        <span>关联告警信息</span>
      </template>
      <el-descriptions :column="3" border size="small">
        <el-descriptions-item label="告警标题">{{ alertInfo.title || '-' }}</el-descriptions-item>
        <el-descriptions-item label="告警等级">
          <el-tag :type="severityTagType(alertInfo.severity)" size="small">{{ alertInfo.severity || '-' }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="alertInfo.status === 'resolved' ? 'success' : 'warning'" size="small">
            {{ alertInfo.status || '-' }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- Data Table -->
    <el-card shadow="never" class="table-card">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center">
          <span>证据时间线</span>
          <el-tag v-if="queryForm.alert_id" type="info" size="small">
            告警: {{ queryForm.alert_id }}
          </el-tag>
        </div>
      </template>

      <el-table stripe v-loading="loading" :data="filteredData" border style="width: 100%">
        <el-table-column type="index" label="#" width="50" align="center" />
        <el-table-column prop="type" label="事件类型" width="130" align="center">
          <template #default="{ row }">
            <el-tag :type="eventTypeTagType(row.type)" size="small" effect="plain">
              {{ eventTypeLabel(row.type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="事件标题" min-width="240" show-overflow-tooltip />
        <el-table-column prop="severity" label="严重程度" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="severityTagType(row.severity)" size="small">{{ row.severity || '-' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="time" label="时间" width="180" align="center">
          <template #default="{ row }">
            {{ formatTime(row.time) }}
          </template>
        </el-table-column>
        <el-table-column label="详情" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.data">{{ formatDataBrief(row.data) }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" plain size="small" @click="handleViewDetail(row)">查看</el-button>
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
    <el-drawer v-model="drawerVisible" title="证据详情" size="600px">
      <template v-if="currentRow">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="事件类型">
            <el-tag :type="eventTypeTagType(currentRow.type)" size="small">
              {{ eventTypeLabel(currentRow.type) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="事件标题">{{ currentRow.title || '-' }}</el-descriptions-item>
          <el-descriptions-item label="严重程度">
            <el-tag :type="severityTagType(currentRow.severity)" size="small">{{ currentRow.severity || '-' }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="时间">{{ formatTime(currentRow.time) }}</el-descriptions-item>
        </el-descriptions>

        <div v-if="currentRow.data" class="detail-content-section">
          <h4>事件数据</h4>
          <pre class="raw-content">{{ formatData(currentRow.data) }}</pre>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { Search, Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import client from '@/shared/api/client'
import { API } from '@/shared/api/routes'

interface TimelineEntry {
  time: string
  type: string
  severity: string
  title: string
  data: Record<string, any>
}

interface AlertInfo {
  id: string
  title: string
  severity: string
  status: string
}

const loading = ref(false)
const tableData = ref<TimelineEntry[]>([])
const alertInfo = ref<AlertInfo | null>(null)
const drawerVisible = ref(false)
const currentRow = ref<TimelineEntry | null>(null)

const queryForm = reactive({
  alert_id: '',
  evidence_type: '',
  keyword: '',
})

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0,
})

const filteredData = computed(() => {
  var data = tableData.value
  if (queryForm.evidence_type) {
    data = data.filter(function(r) { return r.type === queryForm.evidence_type })
  }
  if (queryForm.keyword) {
    var kw = queryForm.keyword.toLowerCase()
    data = data.filter(function(r) {
      return (r.title || '').toLowerCase().indexOf(kw) >= 0
    })
  }
  return data
})

function eventTypeTagType(t: string): string {
  var map: Record<string, string> = {
    alert_created: 'danger',
    status_change: 'warning',
    action: 'primary',
    event: 'info',
  }
  return map[t] || 'info'
}

function eventTypeLabel(t: string): string {
  var map: Record<string, string> = {
    alert_created: '告警创建',
    status_change: '状态变更',
    action: '处置操作',
    event: '关联事件',
    acknowledged: '已确认',
    resolved: '已解决',
    escalated: '已升级',
  }
  return map[t] || t || '-'
}

function severityTagType(severity: string): string {
  var map: Record<string, string> = {
    critical: 'danger',
    high: 'danger',
    warning: 'warning',
    medium: 'warning',
    low: 'info',
    info: 'info',
  }
  return map[severity] || ''
}

function formatTime(t: string | undefined): string {
  if (!t) return '-'
  return new Date(t).toLocaleString('zh-CN')
}

function formatDataBrief(data: Record<string, any>): string {
  if (!data) return '-'
  try {
    var parts: string[] = []
    var keys = Object.keys(data)
    for (var i = 0; i < Math.min(keys.length, 3); i++) {
      parts.push(keys[i] + ': ' + String(data[keys[i]]))
    }
    return parts.join('; ')
  } catch {
    return String(data)
  }
}

function formatData(data: Record<string, any>): string {
  try {
    return JSON.stringify(data, null, 2)
  } catch {
    return String(data)
  }
}

async function fetchData() {
  loading.value = true
  alertInfo.value = null

  try {
    if (queryForm.alert_id) {
      // Fetch evidence chain for specific alert
      var evidenceRes = await client.get(API.ALERT_EVIDENCE_CHAIN(queryForm.alert_id))
      var rawData = evidenceRes.data?.data ?? evidenceRes.data ?? {}

      // API returns { alert, timeline, related_ticket }
      if (rawData.alert) {
        alertInfo.value = rawData.alert
      }
      // timeline is the actual data array
      tableData.value = Array.isArray(rawData.timeline)
        ? rawData.timeline
        : (Array.isArray(rawData) ? rawData : [])
      pagination.total = tableData.value.length
    } else {
      // Fetch all alerts and collect timelines
      var res = await client.get(API.ALERTS, {
        params: {
          page: pagination.page,
          page_size: pagination.page_size,
        },
      })
      var resData = res.data?.data ?? res.data ?? {}
      var alerts = resData.items ?? resData.records ?? resData.list ?? []

      var allEntries: TimelineEntry[] = []
      for (var i = 0; i < alerts.length; i++) {
        var alert = alerts[i]
        // Add alert creation as timeline entry
        allEntries.push({
          time: alert.created_at || '',
          type: 'alert_created',
          severity: alert.severity || 'info',
          title: alert.title || '告警',
          data: { alert_id: alert.id, status: alert.status },
        })
      }
      tableData.value = allEntries
      pagination.total = resData.total ?? allEntries.length
    }
  } catch (e: any) {
    ElMessage.error('获取证据数据失败: ' + (e.message ?? '未知错误'))
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  pagination.page = 1
  fetchData()
}

function handleReset() {
  queryForm.alert_id = ''
  queryForm.evidence_type = ''
  queryForm.keyword = ''
  pagination.page = 1
  fetchData()
}

function handleViewDetail(row: TimelineEntry) {
  currentRow.value = row
  drawerVisible.value = true
}

onMounted(function() {
  fetchData()
})
</script>

<style scoped>
.evidence-archive-page {
  padding: var(--autops-space-lg);
}
.filter-card {
  margin-bottom: var(--autops-space-lg);
}
.alert-info-card {
  margin-bottom: var(--autops-space-lg);
}
.table-card {
  margin-bottom: var(--autops-space-lg);
}
.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: var(--autops-space-lg);
}
.detail-content-section {
  margin-top: var(--autops-space-xl);
}
.detail-content-section h4 {
  margin-bottom: var(--autops-space-sm);
  color: var(--autops-text-1);
  font-size: var(--autops-font-14);
}
.raw-content {
  background: var(--autops-terminal-bg);
  color: var(--autops-text-4);
  border-radius: var(--autops-radius-sm);
  padding: var(--autops-space-md);
  font-size: var(--autops-font-12);
  line-height: 1.5;
  max-height: 400px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-all;
  font-family: 'Courier New', Courier, monospace;
}
</style>
