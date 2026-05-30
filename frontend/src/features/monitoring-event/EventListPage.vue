<template>
  <div>
    <el-card>
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span>事件列表</span>
          <div>
            <el-select v-model="filters.event_type" placeholder="事件类型" clearable style="width:160px;margin-right:8px" @change="loadEvents">
              <el-option label="阈值超限" value="threshold_exceeded" />
              <el-option label="服务异常" value="service_down" />
              <el-option label="端口不可达" value="port_unreachable" />
              <el-option label="磁盘告警" value="disk_usage_high" />
              <el-option label="连接失败" value="db_connection_failed" />
              <el-option label="证书过期" value="cert_expiring" />
              <el-option label="采集器离线" value="collector_offline" />
              <el-option label="执行失败" value="automation_failed" />
            </el-select>
            <el-select v-model="filters.severity" placeholder="严重级别" clearable style="width:120px;margin-right:8px" @change="loadEvents">
              <el-option label="Critical" value="critical" />
              <el-option label="Warning" value="warning" />
              <el-option label="Info" value="info" />
            </el-select>
            <el-button @click="loadEvents">刷新</el-button>
          </div>
        </div>
      </template>

      <el-table :data="events" v-loading="loading" stripe @sort-change="handleSort">
        <el-table-column prop="event_type" label="事件类型" width="150">
          <template #default="{ row }">
            <el-tag :type="eventTypeTag(row.event_type)" size="small">{{ row.event_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="severity" label="级别" width="90" sortable>
          <template #default="{ row }">
            <el-tag :type="severityTag(row.severity)" size="small">{{ row.severity }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
        <el-table-column prop="source" label="来源" width="100" />
        <el-table-column prop="asset_id" label="关联资产" width="120" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.status==='resolved'?'success':row.status==='acknowledged'?'warning':'info'" size="small">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="时间" width="170" sortable>
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewEvent(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination v-model:current-page="page" :page-size="pageSize" :total="total"
        :page-sizes="[20,50,100]" layout="total, sizes, prev, pager, next"
        @change="loadEvents" style="margin-top:16px;justify-content:flex-end" />
    </el-card>

    <el-drawer v-model="showDetail" :title="current?.title || '事件详情'" size="550px">
      <template v-if="current">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="事件ID">{{ current.id }}</el-descriptions-item>
          <el-descriptions-item label="类型">{{ current.event_type }}</el-descriptions-item>
          <el-descriptions-item label="级别">{{ current.severity }}</el-descriptions-item>
          <el-descriptions-item label="来源">{{ current.source }}</el-descriptions-item>
          <el-descriptions-item label="状态">{{ current.status }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatTime(current.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="关联资产" :span="2">{{ current.asset_id || '无' }}</el-descriptions-item>
        </el-descriptions>
        <div v-if="current.raw_data" style="margin-top:16px">
          <h4>原始数据</h4>
          <el-input type="textarea" :rows="8" :model-value="formatJson(current.raw_data)" readonly />
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import api from '@/shared/api/client'
import { API as R } from '@/shared/api/routes'

const loading = ref(false)
const events = ref<any[]>([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const showDetail = ref(false)
const current = ref<any>(null)
const filters = reactive({ event_type: '', severity: '' })
const API = R.EVENTS

function eventTypeTag(t: string) {
  const m: Record<string, string> = { threshold_exceeded: 'warning', service_down: 'danger', port_unreachable: 'danger', disk_usage_high: 'warning', collector_offline: 'info' }
  return m[t] || ''
}
function severityTag(s: string) {
  const m: Record<string, string> = { critical: 'danger', warning: 'warning', info: 'info' }
  return m[s] || ''
}
function formatTime(t: string) { return t ? new Date(t).toLocaleString('zh-CN') : '' }
function formatJson(s: string) { try { return JSON.stringify(JSON.parse(s), null, 2) } catch { return s } }
function handleSort() { loadEvents() }

async function loadEvents() {
  loading.value = true
  try {
    const params: any = { page: page.value, page_size: pageSize.value }
    if (filters.event_type) params.event_type = filters.event_type
    if (filters.severity) params.severity = filters.severity
    const { data } = await api.get(API, { params })
    if (data.code === 0) { events.value = data.data.items || []; total.value = data.data.total || 0 }
  } finally { loading.value = false }
}

function viewEvent(row: any) { current.value = row; showDetail.value = true }
onMounted(() => loadEvents())
</script>
