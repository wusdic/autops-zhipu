<template>
  <div class="evidence-archive-page">
    <!-- Search -->
    <el-card shadow="never" class="filter-card">
      <el-form :inline="true" :model="queryForm" @submit.prevent="handleSearch">
        <el-form-item label="告警ID">
          <el-input v-model="queryForm.alert_id" placeholder="输入告警ID查询证据链" clearable style="width: 240px" />
        </el-form-item>
        <el-form-item label="证据类型">
          <el-select v-model="queryForm.evidence_type" placeholder="全部" clearable style="width: 140px">
            <el-option label="日志" value="log" />
            <el-option label="指标" value="metric" />
            <el-option label="事件" value="event" />
            <el-option label="配置" value="config" />
          </el-select>
        </el-form-item>
        <el-form-item label="来源资产">
          <el-input v-model="queryForm.source_asset" placeholder="搜索来源资产" clearable style="width: 200px" />
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
        <el-descriptions-item label="告警名称">{{ alertInfo.name || alertInfo.alert_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="告警等级">
          <el-tag :type="severityTagType(alertInfo.severity)" size="small">{{ alertInfo.severity || '-' }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="告警时间">{{ formatTime(alertInfo.created_at || alertInfo.time) }}</el-descriptions-item>
        <el-descriptions-item label="来源资产">{{ alertInfo.source_asset || alertInfo.asset_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="alertInfo.status === 'resolved' ? 'success' : 'warning'" size="small">
            {{ alertInfo.status || '-' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="证据数量">
          <el-tag type="info" size="small">{{ tableData.length }}</el-tag>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- Data Table -->
    <el-card shadow="never" class="table-card">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center">
          <span>证据归档列表</span>
          <el-tag v-if="queryForm.alert_id" type="info" size="small">
            告警: {{ queryForm.alert_id }}
          </el-tag>
        </div>
      </template>

      <el-table stripe v-loading="loading" :data="filteredData"border style="width: 100%">
        <el-table-column type="index" label="#" width="50" align="center" />
        <el-table-column prop="evidence_type" label="证据类型" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="evidenceTagType(row.evidence_type)" size="small" effect="plain">
              <el-icon v-if="row.evidence_type === 'log'" style="margin-right: 4px"><Document /></el-icon>
              <el-icon v-else-if="row.evidence_type === 'metric'" style="margin-right: 4px"><TrendCharts /></el-icon>
              <el-icon v-else-if="row.evidence_type === 'event'" style="margin-right: 4px"><Bell /></el-icon>
              <el-icon v-else style="margin-right: 4px"><Setting /></el-icon>
              {{ evidenceLabel(row.evidence_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="source_asset" label="来源资产" min-width="160" show-overflow-tooltip />
        <el-table-column prop="timestamp" label="时间" width="180" align="center">
          <template #default="{ row }">
            {{ formatTime(row.timestamp) }}
          </template>
        </el-table-column>
        <el-table-column prop="summary" label="内容摘要" min-width="280" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.summary || row.content?.substring(0, 120) || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="collected_by" label="采集方式" width="100" align="center">
          <template #default="{ row }">
            {{ row.collected_by || '-' }}
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
          <el-descriptions-item label="证据类型">
            <el-tag :type="evidenceTagType(currentRow.evidence_type)" size="small">
              {{ evidenceLabel(currentRow.evidence_type) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="来源资产">{{ currentRow.source_asset || '-' }}</el-descriptions-item>
          <el-descriptions-item label="时间">{{ formatTime(currentRow.timestamp) }}</el-descriptions-item>
          <el-descriptions-item label="采集方式">{{ currentRow.collected_by || '-' }}</el-descriptions-item>
          <el-descriptions-item label="关联告警ID">{{ currentRow.alert_id || '-' }}</el-descriptions-item>
        </el-descriptions>

        <div class="detail-content-section">
          <h4>内容摘要</h4>
          <div class="summary-box">{{ currentRow.summary || '-' }}</div>
        </div>

        <div v-if="currentRow.content" class="detail-content-section">
          <h4>原始内容</h4>
          <pre class="raw-content">{{ formatContent(currentRow.content) }}</pre>
        </div>

        <div v-if="currentRow.metadata" class="detail-content-section">
          <h4>元数据</h4>
          <pre class="raw-content">{{ formatMetadata(currentRow.metadata) }}</pre>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { Search, Refresh, Document, TrendCharts, Bell, Setting } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import client from '@/shared/api/client'
import { API } from '@/shared/api/routes'

interface EvidenceRecord {
  id: string | number
  alert_id: string | number
  evidence_type: 'log' | 'metric' | 'event' | 'config'
  source_asset: string
  timestamp: string
  summary: string
  content: string
  collected_by: string
  metadata: Record<string, any>
}

interface AlertInfo {
  id: string | number
  name: string
  alert_name: string
  severity: string
  created_at: string
  time: string
  source_asset: string
  asset_name: string
  status: string
}

const loading = ref(false)
const tableData = ref<EvidenceRecord[]>([])
const alertInfo = ref<AlertInfo | null>(null)
const drawerVisible = ref(false)
const currentRow = ref<EvidenceRecord | null>(null)

const queryForm = reactive({
  alert_id: '',
  evidence_type: '',
  source_asset: '',
})

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0,
})

const filteredData = computed(() => {
  let data = tableData.value
  if (queryForm.evidence_type) {
    data = data.filter((r) => r.evidence_type === queryForm.evidence_type)
  }
  if (queryForm.source_asset) {
    data = data.filter((r) => r.source_asset?.includes(queryForm.source_asset))
  }
  return data
})

function evidenceTagType(type: string): '' | 'success' | 'warning' | 'danger' | 'info' {
  const map: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    log: '',
    metric: 'success',
    event: 'warning',
    config: 'info',
  }
  return map[type] || ''
}

function evidenceLabel(type: string): string {
  const map: Record<string, string> = {
    log: '日志',
    metric: '指标',
    event: '事件',
    config: '配置',
  }
  return map[type] || type || '-'
}

function severityTagType(severity: string): '' | 'success' | 'warning' | 'danger' | 'info' {
  const map: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    critical: 'danger',
    high: 'danger',
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

function formatContent(content: string): string {
  try {
    const parsed = JSON.parse(content)
    return JSON.stringify(parsed, null, 2)
  } catch {
    return content
  }
}

function formatMetadata(metadata: Record<string, any>): string {
  try {
    return JSON.stringify(metadata, null, 2)
  } catch {
    return String(metadata)
  }
}

async function fetchData() {
  loading.value = true
  alertInfo.value = null

  try {
    if (queryForm.alert_id) {
      // Fetch evidence chain for specific alert
      try {
        const evidenceRes = await client.get(API.ALERT_EVIDENCE_CHAIN(queryForm.alert_id))
        const data = evidenceRes.data?.data ?? evidenceRes.data ?? {}
        tableData.value = Array.isArray(data) ? data : (data.items ?? data.records ?? data.list ?? [])
        // Try to get alert info from evidence
        if (tableData.value.length > 0 && tableData.value[0].alert_id) {
          try {
            const alertRes = await client.get(`${API.ALERTS}/${queryForm.alert_id}`)
            alertInfo.value = alertRes.data?.data ?? alertRes.data ?? null
          } catch {
            // Alert info not available, that's okay
          }
        }
      } catch {
        // Fallback: search alerts and extract evidence
        const alertRes = await client.get(API.ALERTS, {
          params: { id: queryForm.alert_id, page: 1, page_size: 1 },
        })
        const alertData = alertRes.data?.data ?? alertRes.data ?? {}
        const alerts = alertData.items ?? alertData.records ?? alertData.list ?? []
        if (alerts.length > 0) {
          alertInfo.value = alerts[0]
          tableData.value = alerts[0].evidence_chain ?? alerts[0].evidences ?? []
        } else {
          tableData.value = []
        }
      }
    } else {
      // Fetch all alerts and aggregate evidence
      const res = await client.get(API.ALERTS, {
        params: {
          page: pagination.page,
          page_size: pagination.page_size,
        },
      })
      const data = res.data?.data ?? res.data ?? {}
      const alerts = data.items ?? data.records ?? data.list ?? []
      // Flatten evidence from all alerts
      const allEvidence: EvidenceRecord[] = []
      alerts.forEach((alert: any) => {
        const evidences = alert.evidence_chain ?? alert.evidences ?? []
        evidences.forEach((e: EvidenceRecord) => {
          allEvidence.push({ ...e, alert_id: alert.id })
        })
      })
      tableData.value = allEvidence
      pagination.total = data.total ?? allEvidence.length
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
  queryForm.source_asset = ''
  pagination.page = 1
  fetchData()
}

function handleViewDetail(row: EvidenceRecord) {
  currentRow.value = row
  drawerVisible.value = true
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.evidence-archive-page {
  padding: 16px;
}
.filter-card {
  margin-bottom: 16px;
}
.alert-info-card {
  margin-bottom: 16px;
}
.table-card {
  margin-bottom: 16px;
}
.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
.detail-content-section {
  margin-top: 20px;
}
.detail-content-section h4 {
  margin-bottom: 8px;
  color: #1d2129;
  font-size: 14px;
}
.summary-box {
  background: #f7f8fa;
  border: 1px solid #e5e6eb;
  border-radius: 4px;
  padding: 12px;
  font-size: 13px;
  line-height: 1.6;
  color: #4e5969;
  word-break: break-all;
}
.raw-content {
  background: #1e1e1e;
  color: #c9cdd4;
  border-radius: 4px;
  padding: 12px;
  font-size: 12px;
  line-height: 1.5;
  max-height: 400px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-all;
  font-family: 'Courier New', Courier, monospace;
}
</style>
