<template>
  <div class="state-change-page">
    <!-- ========== Page Header ========== -->
    <div class="autops-page-header">
      <div>
        <div class="autops-page-title">状态变化</div>
        <div class="autops-page-desc">状态变更历史、触发来源、证据</div>
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
        <el-table stripe
 :data="tableData"
 v-loading="loading"border
 class="change-table"
 >
          <el-table-column prop="asset_name" label="资产名" min-width="160" show-overflow-tooltip>
            <template #default="{ row }">
              {{ row.asset_name || row.asset_id || '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="attribute_name" label="变更属性" width="140" align="center">
            <template #default="{ row }">
              <el-tag size="small" effect="plain">{{ attributeLabel(row.attribute_name) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="old_value" label="旧值" min-width="140" show-overflow-tooltip>
            <template #default="{ row }">
              <span class="value-old">{{ formatValue(row.attribute_name, row.old_value) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="" width="40" align="center" class-name="arrow-cell">
            <template #default>
              <el-icon><Right /></el-icon>
            </template>
          </el-table-column>
          <el-table-column prop="new_value" label="新值" min-width="140" show-overflow-tooltip>
            <template #default="{ row }">
              <span class="value-new">{{ formatValue(row.attribute_name, row.new_value) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="changed_at" label="变更时间" width="175">
            <template #default="{ row }">
              {{ formatTime(row.changed_at) }}
            </template>
          </el-table-column>
          <el-table-column prop="trigger_source" label="触发来源" width="120" show-overflow-tooltip>
            <template #default="{ row }">
              <el-tag size="small" :type="triggerSourceType(row.trigger_source)" effect="plain">{{ triggerSourceLabel(row.trigger_source) }}</el-tag>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-if="!loading && tableData.length === 0" description="暂无状态变更记录">
          <p style="color:#86909c;font-size:13px;margin-top:4px">当资产状态发生变化时，变更记录将在此展示</p>
        </el-empty>

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
var ATTRIBUTE_LABEL_MAP: Record<string, string> = {
  status: '运行状态',
  health: '健康度',
  health_score: '健康分数',
  ip: 'IP 地址',
  reachability: '可达性',
  config: '配置',
  cpu_usage: 'CPU使用率',
  memory_usage: '内存使用率',
  disk_usage: '磁盘使用率',
  network_in: '网络入流量',
  network_out: '网络出流量',
  load_1m: '负载(1分钟)',
  load_5m: '负载(5分钟)',
  load_15m: '负载(15分钟)',
  process_count: '进程数',
  connection_count: '连接数',
  response_time: '响应时间',
  uptime: '运行时间',
  os_version: '系统版本',
  agent_version: 'Agent版本',
  port: '端口',
  service_status: '服务状态',
  temperature: '温度',
}

var PERCENT_ATTRIBUTES = ['cpu_usage', 'memory_usage', 'disk_usage', 'health_score']
var BYTE_ATTRIBUTES = ['network_in', 'network_out']

function attributeLabel(name: string): string {
  return ATTRIBUTE_LABEL_MAP[name] || name || '-'
}

function formatValue(attrName: string | null | undefined, value: any): string {
  if (value === null || value === undefined || value === '') return '-'
  if (!attrName) return String(value)
  if (PERCENT_ATTRIBUTES.indexOf(attrName) >= 0) {
    var num = parseFloat(value)
    if (!isNaN(num)) {
      if (num > 1) return num.toFixed(1) + '%'
      return (num * 100).toFixed(1) + '%'
    }
  }
  if (BYTE_ATTRIBUTES.indexOf(attrName) >= 0) {
    var bytes = parseFloat(value)
    if (!isNaN(bytes)) return formatBytes(bytes)
  }
  if (attrName === 'temperature') {
    var temp = parseFloat(value)
    if (!isNaN(temp)) return temp.toFixed(1) + '°C'
  }
  if (attrName === 'response_time') {
    var ms = parseFloat(value)
    if (!isNaN(ms)) {
      if (ms >= 1000) return (ms / 1000).toFixed(2) + 's'
      return ms.toFixed(0) + 'ms'
    }
  }
  if (attrName === 'status' || attrName === 'service_status') {
    return statusValueLabel(String(value))
  }
  if (attrName === 'reachability') {
    return String(value) === 'true' || value === true ? '可达' : '不可达'
  }
  return String(value)
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return bytes.toFixed(0) + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB'
}

function statusValueLabel(val: string): string {
  var map: Record<string, string> = {
    online: '在线',
    offline: '离线',
    running: '运行中',
    stopped: '已停止',
    warning: '警告',
    critical: '严重',
    healthy: '健康',
    unhealthy: '不健康',
    unknown: '未知',
    active: '活跃',
    inactive: '不活跃',
  }
  return map[val] || val
}

var TRIGGER_SOURCE_MAP: Record<string, string> = {
  collector: '采集器',
  monitoring: '监控',
  agent: 'Agent',
  manual: '手动',
  system: '系统',
  policy: '策略',
  alert: '告警',
  api: 'API',
  schedule: '定时任务',
  discovery: '自动发现',
  execution: '自动化执行',
}

function triggerSourceLabel(source: string | null | undefined): string {
  return TRIGGER_SOURCE_MAP[source || ''] || source || '-'
}

function triggerSourceType(source: string | null | undefined): string {
  var map: Record<string, string> = {
    collector: '', monitoring: '', agent: '',
    manual: 'warning', system: 'info', policy: 'success',
    alert: 'danger', api: 'info', schedule: '',
    discovery: 'success', execution: '',
  }
  return map[source || ''] || 'info'
}

function formatTime(val: string | null | undefined): string {
  if (!val) return '-'
  const d = new Date(val)
  if (isNaN(d.getTime())) return '-'
  const pad = (n: number) => String(n).padStart(2, '0')
  return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()) + ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes()) + ':' + pad(d.getSeconds())
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
  border-bottom: 1px solid #e5e6eb;
}

.filter-form :deep(.el-form-item) {
  margin-bottom: 12px;
}

.change-table {
  width: 100%;
}

.arrow-cell {
  text-align: center;
  color: #c9cdd4;
}

.value-old {
  color: #86909c;
  text-decoration: line-through;
}

.value-new {
  color: #165dff;
  font-weight: 500;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
