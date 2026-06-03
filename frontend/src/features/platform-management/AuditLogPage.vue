     1|<template>
     2|  <div class="page-container">
     3|    <div class="autops-page-header">
     4|      <div>
     5|        <div class="autops-page-title">审计日志</div>
     6|        <div class="autops-page-desc">查看系统操作审计日志</div>
     7|      </div>
     8|    </div>
     9|
    10|    <div class="autops-card">
    11|      
    12|        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px">
    13|          <span style="font-size:18px;font-weight:600">审计日志</span>
    14|          <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
    15|            <el-radio-group v-model="viewMode" size="small">
    16|              <el-radio-button value="table">表格</el-radio-button>
    17|              <el-radio-button value="timeline">时间线</el-radio-button>
    18|            </el-radio-group>
    19|            <el-button @click="exportLogs" :loading="exporting" size="small">
    20|              <el-icon><Download /></el-icon>
    21|              导出
    22|            </el-button>
    23|          </div>
    24|        </div>
    25|      
    26|
    27|      <!-- Advanced Filters -->
    28|      <div class="autops-toolbar">
    29|        <el-date-picker
    30|          v-model="dateRange"
    31|          type="datetimerange"
    32|          range-separator="至"
    33|          start-placeholder="开始时间"
    34|          end-placeholder="结束时间"
    35|          style="width: 360px"
    36|          @change="loadLogs"
    37|        />
    38|        <el-select v-model="filters.action" placeholder="操作类型" clearable style="width: 140px" @change="loadLogs">
    39|          <el-option v-for="a in actionTypes" :key="a" :label="a" :value="a" />
    40|        </el-select>
    41|        <el-input v-model="filters.user" placeholder="用户" style="width: 130px" clearable @change="loadLogs" />
    42|        <el-select v-model="filters.resource_type" placeholder="资源类型" clearable style="width: 140px" @change="loadLogs">
    43|          <el-option v-for="rt in resourceTypes" :key="rt" :label="rt" :value="rt" />
    44|        </el-select>
    45|        <el-button type="primary" @click="loadLogs">查询</el-button>
    46|        <el-button @click="resetFilters">重置</el-button>
    47|      </div>
    48|
    49|      <!-- Table View -->
    50|      <template v-if="viewMode === 'table'">
    51|        <el-table stripe :data="logs" v-loading="loading"@row-click="openDetail" style="cursor:pointer">
    52|          <el-table-column prop="action" label="操作" width="180">
    53|            <template #default="{ row }">
    54|              <el-tag :type="getActionTagType(row.action)" size="small">{{ row.action }}</el-tag>
    55|            </template>
    56|          </el-table-column>
    57|          <el-table-column prop="resource_type" label="资源类型" width="120" />
    58|          <el-table-column prop="resource_id" label="资源ID" width="160" show-overflow-tooltip />
    59|          <el-table-column prop="user_id" label="用户" width="120" />
    60|          <el-table-column prop="detail" label="详情" min-width="250" show-overflow-tooltip />
    61|          <el-table-column prop="ip_address" label="IP" width="130" />
    62|          <el-table-column prop="trace_id" label="TraceID" width="140" show-overflow-tooltip />
    63|          <el-table-column prop="created_at" label="时间" width="170" sortable>
    64|            <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
    65|          </el-table-column>
    66|        </el-table>
    67|      </template>
    68|
    69|      <!-- Timeline View -->
    70|      <template v-if="viewMode === 'timeline'">
    71|        <div class="timeline-wrapper" v-loading="loading">
    72|          <el-timeline v-if="logs.length">
    73|            <el-timeline-item
    74|              v-for="log in logs"
    75|              :key="log.id"
    76|              :timestamp="formatTime(log.created_at)"
    77|              placement="top"
    78|              :type="getTimelineColor(log.action)"
    79|              @click="openDetail(log)"
    80|              style="cursor:pointer"
    81|            >
    82|              <div class="autops-card timeline-card">
    83|                <div class="timeline-header">
    84|                  <el-tag :type="getActionTagType(log.action)" size="small">{{ log.action }}</el-tag>
    85|                  <span class="timeline-user">{{ log.user_id }}</span>
    86|                  <span class="timeline-resource">{{ log.resource_type }} / {{ log.resource_id }}</span>
    87|                </div>
    88|                <div class="timeline-detail">{{ log.detail || '—' }}</div>
    89|                <div class="timeline-meta">
    90|                  <span>IP: {{ log.ip_address || '—' }}</span>
    91|                  <span v-if="log.trace_id">Trace: {{ log.trace_id }}</span>
    92|                </div>
    93|              </div>
    94|            </el-timeline-item>
    95|          </el-timeline>
    96|          <el-empty v-else description="暂无审计日志" />
    97|        </div>
    98|      </template>
    99|
   100|      <el-pagination
   101|        v-model:current-page="page"
   102|        v-model:page-size="pageSize"
   103|        :page-sizes="[20, 50, 100]"
   104|        :total="total"
   105|        layout="total, sizes, prev, pager, next"
   106|        @change="loadLogs"
   107|        style="margin-top: 16px; justify-content: flex-end"
   108|      />
   109|    </div>
   110|
   111|    <!-- Detail Drawer -->
   112|    <el-drawer v-model="drawerVisible" title="审计日志详情" size="520px">
   113|      <template v-if="detailEntry">
   114|        <el-descriptions :column="1" border size="default">
   115|          <el-descriptions-item label="操作">
   116|            <el-tag :type="getActionTagType(detailEntry.action)">{{ detailEntry.action }}</el-tag>
   117|          </el-descriptions-item>
   118|          <el-descriptions-item label="资源类型">{{ detailEntry.resource_type }}</el-descriptions-item>
   119|          <el-descriptions-item label="资源ID">{{ detailEntry.resource_id }}</el-descriptions-item>
   120|          <el-descriptions-item label="用户">{{ detailEntry.user_id }}</el-descriptions-item>
   121|          <el-descriptions-item label="IP 地址">{{ detailEntry.ip_address }}</el-descriptions-item>
   122|          <el-descriptions-item label="TraceID">{{ detailEntry.trace_id }}</el-descriptions-item>
   123|          <el-descriptions-item label="时间">{{ formatTime(detailEntry.created_at) }}</el-descriptions-item>
   124|          <el-descriptions-item label="详情">
   125|            <div class="detail-json">
   126|              <pre>{{ formatDetail(detailEntry.detail) }}</pre>
   127|            </div>
   128|          </el-descriptions-item>
   129|        </el-descriptions>
   130|      </template>
   131|    </el-drawer>
   132|  </div>
   133|</template>
   134|
   135|<script setup lang="ts">
   136|import { ref, reactive, onMounted } from 'vue'
   137|import { ElMessage } from 'element-plus'
   138|import { Download } from '@element-plus/icons-vue'
   139|import api from '@/shared/api/client'
   140|import { API as R } from '@/shared/api/routes'
   141|
   142|const loading = ref(false)
   143|const exporting = ref(false)
   144|const logs = ref<any[]>([])
   145|const page = ref(1)
   146|const pageSize = ref(20)
   147|const total = ref(0)
   148|const dateRange = ref<any>(null)
   149|const viewMode = ref<'table' | 'timeline'>('table')
   150|
   151|const filters = reactive({ user: '', action: '', resource_type: '' })
   152|
   153|// Filter options
   154|const actionTypes = ['create', 'update', 'delete', 'login', 'logout', 'execute', 'import', 'export', 'config_change']
   155|const resourceTypes = ['user', 'role', 'asset', 'policy', 'script', 'alert', 'api_key', 'config', 'execution']
   156|
   157|// Detail drawer
   158|const drawerVisible = ref(false)
   159|const detailEntry = ref<any>(null)
   160|
   161|function formatTime(t: string) { return t ? new Date(t).toLocaleString('zh-CN') : '' }
   162|
   163|function formatDetail(detail: any) {
   164|  if (!detail) return ''
   165|  if (typeof detail === 'string') {
   166|    try { return JSON.stringify(JSON.parse(detail), null, 2) } catch { return detail }
   167|  }
   168|  return JSON.stringify(detail, null, 2)
   169|}
   170|
   171|function getActionTagType(action: string): '' | 'success' | 'warning' | 'danger' | 'info' {
   172|  if (!action) return 'info'
   173|  const a = action.toLowerCase()
   174|  if (a.includes('delete') || a.includes('remove')) return 'danger'
   175|  if (a.includes('create') || a.includes('add')) return 'success'
   176|  if (a.includes('update') || a.includes('edit') || a.includes('change')) return 'warning'
   177|  if (a.includes('login')) return ''
   178|  return 'info'
   179|}
   180|
   181|function getTimelineColor(action: string): '' | 'success' | 'warning' | 'danger' | 'info' | 'primary' {
   182|  if (!action) return 'info'
   183|  const a = action.toLowerCase()
   184|  if (a.includes('delete')) return 'danger'
   185|  if (a.includes('create')) return 'success'
   186|  if (a.includes('update')) return 'warning'
   187|  if (a.includes('login')) return 'primary'
   188|  return 'info'
   189|}
   190|
   191|function openDetail(row: any) {
   192|  detailEntry.value = row
   193|  drawerVisible.value = true
   194|}
   195|
   196|function resetFilters() {
   197|  filters.user = ''
   198|  filters.action = ''
   199|  filters.resource_type = ''
   200|  dateRange.value = null
   201|  page.value = 1
   202|  loadLogs()
   203|}
   204|
   205|async function loadLogs() {
   206|  loading.value = true
   207|  try {
   208|    const params: any = { page: page.value, page_size: pageSize.value }
   209|    if (filters.user) params.username = filters.user
   210|    if (filters.action) params.action = filters.action
   211|    if (filters.resource_type) params.resource_type = filters.resource_type
   212|    if (dateRange.value && dateRange.value.length === 2) {
   213|      params.start_time = dateRange.value[0].toISOString()
   214|      params.end_time = dateRange.value[1].toISOString()
   215|    }
   216|    const { data } = await api.get(R.AUDIT, { params })
   217|    if (data.code === 0) {
   218|      logs.value = data.data.items || []
   219|      total.value = data.data.total || 0
   220|    }
   221|  } finally {
   222|    loading.value = false
   223|  }
   224|}
   225|
   226|async function exportLogs() {
   227|  exporting.value = true
   228|  try {
   229|    const params: any = { page: 1, page_size: 100, export: true }
   230|    if (filters.user) params.username = filters.user
   231|    if (filters.action) params.action = filters.action
   232|    if (filters.resource_type) params.resource_type = filters.resource_type
   233|    if (dateRange.value && dateRange.value.length === 2) {
   234|      params.start_time = dateRange.value[0].toISOString()
   235|      params.end_time = dateRange.value[1].toISOString()
   236|    }
   237|    const { data } = await api.get(R.AUDIT, { params, responseType: 'blob' })
   238|    // If API returns JSON array instead of blob, handle that too
   239|    let csvContent: string
   240|    if (data instanceof Blob) {
   241|      const url = window.URL.createObjectURL(data)
   242|      const a = document.createElement('a')
   243|      a.href = url
   244|      a.download = `audit-logs-${new Date().toISOString().slice(0, 10)}.csv`
   245|      a.click()
   246|      window.URL.revokeObjectURL(url)
   247|      ElMessage.success('导出成功')
   248|      exporting.value = false
   249|      return
   250|    }
   251|    // Fallback: build CSV from JSON
   252|    const items = data.data?.items || data.data || data || []
   253|    if (!Array.isArray(items) || items.length === 0) {
   254|      ElMessage.warning('无数据可导出')
   255|      exporting.value = false
   256|      return
   257|    }
   258|    const headers = ['action', 'resource_type', 'resource_id', 'user_id', 'detail', 'ip_address', 'trace_id', 'created_at']
   259|    const rows = items.map((item: any) => headers.map(h => {
   260|      const val = item[h] ?? ''
   261|      return typeof val === 'object' ? JSON.stringify(val) : String(val)
   262|    }).join(','))
   263|    csvContent = [headers.join(','), ...rows].join('\n')
   264|    const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' })
   265|    const url = window.URL.createObjectURL(blob)
   266|    const a = document.createElement('a')
   267|    a.href = url
   268|    a.download = `audit-logs-${new Date().toISOString().slice(0, 10)}.csv`
   269|    a.click()
   270|    window.URL.revokeObjectURL(url)
   271|    ElMessage.success('导出成功')
   272|  } catch (e: any) {
   273|    ElMessage.error('导出失败')
   274|  } finally {
   275|    exporting.value = false
   276|  }
   277|}
   278|
   279|onMounted(() => loadLogs())
   280|</script>
   281|
   282|<style scoped>
   283|
   284|
   285|.filter-bar {
   286|  display: flex;
   287|  align-items: center;
   288|  gap: 8px;
   289|  flex-wrap: wrap;
   290|  margin-bottom: 16px;
   291|  padding: 12px 16px;
   292|  background: #f7f8fa;
   293|  border-radius: 6px;
   294|}
   295|
   296|.timeline-wrapper { padding: 8px 0; max-height: 600px; overflow-y: auto; }
   297|
   298|.timeline-card { cursor: pointer; }
   299|.timeline-card :deep(.el-card__body) { padding: 12px 16px; }
   300|.timeline-header { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
   301|.timeline-user { color: #4e5969; font-weight: 500; }
   302|.timeline-resource { color: #86909c; font-size: 13px; }
   303|.timeline-detail { color: #1d2129; font-size: 13px; margin-bottom: 6px; }
   304|.timeline-meta { color: #86909c; font-size: 12px; display: flex; gap: 16px; }
   305|
   306|.detail-json pre {
   307|  margin: 0;
   308|  white-space: pre-wrap;
   309|  word-break: break-all;
   310|  font-size: 13px;
   311|  background: #f7f8fa;
   312|  padding: 8px;
   313|  border-radius: 4px;
   314|  max-height: 300px;
   315|  overflow-y: auto;
   316|}
   317|</style>
   318|