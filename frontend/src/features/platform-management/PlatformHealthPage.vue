     1|<template>
     2|  <div class="page-container">
     3|    <div class="autops-page-header">
     4|      <div>
     5|        <div class="autops-page-title">平台状态</div>
     6|        <div class="autops-page-desc">查看平台运行指标与健康度</div>
     7|      </div>
     8|      <div class="top-actions" style="display:flex;align-items:center;gap:12px">
     9|        <div class="auto-refresh-control">
    10|          <el-switch v-model="autoRefresh" active-text="自动刷新" @change="toggleAutoRefresh" />
    11|          <span v-if="autoRefresh" class="refresh-countdown">{{ countdown }}s</span>
    12|        </div>
    13|        <el-button type="primary" @click="runSelfCheck" :loading="selfChecking">
    14|          <el-icon><CircleCheck /></el-icon>
    15|          自检
    16|        </el-button>
    17|        <el-button @click="loadStatus" :loading="loading">
    18|          <el-icon><Refresh /></el-icon>
    19|          刷新
    20|        </el-button>
    21|      </div>
    22|    </div>
    23|
    24|    <!-- Overall Health Summary -->
    25|    <el-alert
    26|      v-if="overallStatus"
    27|      :title="overallStatus.title"
    28|      :type="overallStatus.type"
    29|      :description="overallStatus.desc"
    30|      show-icon
    31|      :closable="false"
    32|      style="margin-bottom: 16px"
    33|    />
    34|
    35|    <!-- Component Health Cards -->
    36|    <div class="status-grid" v-loading="loading">
    37|      <div class="autops-card status-card" v-for="comp in components" :key="comp.key" :class="{ 'status-card-unhealthy': comp.status === 'unhealthy' }">
    38|        <div class="card-header">
    39|          <span class="card-icon">{{ comp.icon }}</span>
    40|          <span class="card-title">{{ comp.label }}</span>
    41|          <el-tag :type="getTagType(comp.status)" size="small" effect="dark">
    42|            {{ statusLabels[comp.status] || comp.status || '未知' }}
    43|          </el-tag>
    44|        </div>
    45|        <div class="card-body" v-if="comp.detail">
    46|          <div class="detail-row" v-for="(val, key) in comp.detail" :key="key">
    47|            <span class="detail-key">{{ key }}</span>
    48|            <span class="detail-val">{{ val }}</span>
    49|          </div>
    50|        </div>
    51|        <div class="card-body" v-else>
    52|          <span class="text-muted">暂无详情</span>
    53|        </div>
    54|        <div class="card-footer" v-if="comp.latency !== undefined">
    55|          <span class="latency-label">延迟</span>
    56|          <span class="latency-value" :class="{ 'latency-warn': comp.latency > 500 }">
    57|            {{ comp.latency }}ms
    58|          </span>
    59|        </div>
    60|      </div>
    61|    </div>
    62|
    63|    <!-- Health Check History Chart -->
    64|    <div class="autops-card" style="margin-top: 20px">
    65|      <div class="autops-card-header">
    66|                <span style="font-weight:600">健康检查历史</span>
    67|      </div>
    68|      <div class="chart-container">
    69|        <div class="chart-placeholder" v-if="!historyData.length">
    70|          <span class="text-muted">暂无历史数据，点击「自检」开始记录</span>
    71|        </div>
    72|        <div class="history-timeline" v-else>
    73|          <div class="history-row" v-for="(entry, idx) in historyData" :key="idx">
    74|            <span class="history-time">{{ entry.time }}</span>
    75|            <div class="history-dots">
    76|              <span
    77|                v-for="comp in entry.components"
    78|                :key="comp.key"
    79|                class="history-dot"
    80|                :class="'dot-' + comp.status"
    81|                :title="comp.label + ': ' + (statusLabels[comp.status] || comp.status)"
    82|              />
    83|            </div>
    84|            <el-tag :type="entry.overall === 'healthy' ? 'success' : entry.overall === 'degraded' ? 'warning' : 'danger'" size="small">
    85|              {{ statusLabels[entry.overall] || entry.overall }}
    86|            </el-tag>
    87|          </div>
    88|        </div>
    89|      </div>
    90|    </div>
    91|
    92|    <!-- Self-check Result Drawer -->
    93|    <el-drawer v-model="selfCheckVisible" title="自检结果" size="520px">
    94|      <div v-if="selfCheckResult">
    95|        <el-result
    96|          :icon="selfCheckResult.healthy ? 'success' : 'error'"
    97|          :title="selfCheckResult.healthy ? '所有组件正常' : '部分组件异常'"
    98|          :sub-title="`检查时间: ${selfCheckResult.time}`"
    99|        />
   100|        <el-descriptions :column="1" border style="margin-top: 16px">
   101|          <el-descriptions-item v-for="item in selfCheckResult.items" :key="item.key" :label="item.label">
   102|            <div style="display:flex;align-items:center;gap:8px">
   103|              <el-tag :type="getTagType(item.status)" size="small">{{ statusLabels[item.status] || item.status }}</el-tag>
   104|              <span style="color:#86909c;font-size:13px">{{ item.message || '' }}</span>
   105|            </div>
   106|          </el-descriptions-item>
   107|        </el-descriptions>
   108|      </div>
   109|    </el-drawer>
   110|  </div>
   111|</template>
   112|
   113|<script setup lang="ts">
   114|import { ref, computed, onMounted, onUnmounted } from 'vue'
   115|import { ElMessage } from 'element-plus'
   116|import { Refresh, CircleCheck } from '@element-plus/icons-vue'
   117|import api from '@/shared/api/client'
   118|import { API as R } from '@/shared/api/routes'
   119|
   120|interface StatusComponent {
   121|  key: string
   122|  label: string
   123|  icon: string
   124|  status: string
   125|  detail: Record<string, string> | null
   126|  latency?: number
   127|}
   128|
   129|interface HistoryEntry {
   130|  time: string
   131|  overall: string
   132|  components: { key: string; label: string; status: string }[]
   133|}
   134|
   135|const statusLabels: Record<string, string> = {
   136|  healthy: '正常',
   137|  degraded: '降级',
   138|  unhealthy: '异常',
   139|  unknown: '未知',
   140|}
   141|
   142|const loading = ref(false)
   143|const selfChecking = ref(false)
   144|const selfCheckVisible = ref(false)
   145|const selfCheckResult = ref<any>(null)
   146|
   147|const components = ref<StatusComponent[]>([
   148|  { key: 'api', label: 'API 服务', icon: '🌐', status: 'unknown', detail: null },
   149|  { key: 'database', label: '数据库', icon: '🗄️', status: 'unknown', detail: null },
   150|  { key: 'redis', label: 'Redis', icon: '⚡', status: 'unknown', detail: null },
   151|  { key: 'llm', label: 'LLM 服务', icon: '🤖', status: 'unknown', detail: null },
   152|  { key: 'collector', label: '采集器', icon: '📡', status: 'unknown', detail: null },
   153|])
   154|
   155|const historyData = ref<HistoryEntry[]>([])
   156|
   157|// Auto-refresh
   158|const autoRefresh = ref(false)
   159|const countdown = ref(30)
   160|let refreshTimer: ReturnType<typeof setInterval> | null = null
   161|let countdownTimer: ReturnType<typeof setInterval> | null = null
   162|
   163|function toggleAutoRefresh(val: boolean) {
   164|  if (val) {
   165|    startAutoRefresh()
   166|  } else {
   167|    stopAutoRefresh()
   168|  }
   169|}
   170|
   171|function startAutoRefresh() {
   172|  countdown.value = 30
   173|  countdownTimer = setInterval(() => {
   174|    countdown.value--
   175|    if (countdown.value <= 0) {
   176|      countdown.value = 30
   177|      loadStatus()
   178|    }
   179|  }, 1000)
   180|}
   181|
   182|function stopAutoRefresh() {
   183|  if (refreshTimer) { clearInterval(refreshTimer); refreshTimer = null }
   184|  if (countdownTimer) { clearInterval(countdownTimer); countdownTimer = null }
   185|}
   186|
   187|// Overall status
   188|const overallStatus = computed(() => {
   189|  const comps = components.value.filter(c => c.key !== 'frontend')
   190|  const unhealthy = comps.some(c => c.status === 'unhealthy')
   191|  const degraded = comps.some(c => c.status === 'degraded')
   192|  const allHealthy = comps.every(c => c.status === 'healthy')
   193|  if (unhealthy) {
   194|    return { title: '平台存在异常', type: 'error' as const, desc: '部分组件运行异常，请检查详情' }
   195|  }
   196|  if (degraded) {
   197|    return { title: '平台运行降级', type: 'warning' as const, desc: '部分组件处于降级状态' }
   198|  }
   199|  if (allHealthy) {
   200|    return { title: '平台运行正常', type: 'success' as const, desc: '所有组件状态正常' }
   201|  }
   202|  return null
   203|})
   204|
   205|function getTagType(status: string): 'success' | 'warning' | 'danger' | 'info' {
   206|  switch (status) {
   207|    case 'healthy': return 'success'
   208|    case 'degraded': return 'warning'
   209|    case 'unhealthy': return 'danger'
   210|    default: return 'info'
   211|  }
   212|}
   213|
   214|function addHistoryEntry() {
   215|  const entry: HistoryEntry = {
   216|    time: new Date().toLocaleString('zh-CN'),
   217|    overall: components.value.every(c => c.status === 'healthy') ? 'healthy'
   218|      : components.value.some(c => c.status === 'unhealthy') ? 'unhealthy' : 'degraded',
   219|    components: components.value.map(c => ({ key: c.key, label: c.label, status: c.status })),
   220|  }
   221|  historyData.value.unshift(entry)
   222|  // Keep last 20 entries
   223|  if (historyData.value.length > 20) historyData.value.pop()
   224|}
   225|
   226|async function loadStatus() {
   227|  loading.value = true
   228|  try {
   229|    const { data } = await api.get(R.PLATFORM_STATUS)
   230|    if (data.code === 0) {
   231|      const result = data.data || data
   232|      const statusData = result.components || result
   233|      components.value.forEach(comp => {
   234|        const info = statusData[comp.key]
   235|        if (info) {
   236|          // Normalize 'ok' → 'healthy'
   237|          let s = info.status || 'unknown'
   238|          if (s === 'ok' || s === 'UP' || s === 'up') s = 'healthy'
   239|          comp.status = s
   240|          comp.detail = info.detail || null
   241|          comp.latency = info.latency
   242|        } else {
   243|          // Component not reported by backend - check type
   244|          if (comp.key === 'api') {
   245|            comp.status = 'healthy'
   246|            comp.detail = { '版本': result.version || '1.0.0', '状态': '运行中' }
   247|          } else if (comp.key === 'llm') {
   248|            comp.status = 'degraded'
   249|            comp.detail = { '状态': '未配置或不可用' }
   250|          } else if (comp.key === 'collector') {
   251|            comp.status = 'healthy'
   252|            comp.detail = { '内置采集器': '运行中' }
   253|          }
   254|        }
   255|      })
   256|      addHistoryEntry()
   257|    }
   258|  } catch (e: any) {
   259|    ElMessage.error('加载平台状态失败')
   260|  } finally {
   261|    loading.value = false
   262|  }
   263|}
   264|
   265|async function runSelfCheck() {
   266|  selfChecking.value = true
   267|  try {
   268|    const { data } = await api.post(R.PLATFORM_STATUS + '/self-check')
   269|    if (data.code === 0) {
   270|      const result = data.data || data
   271|      selfCheckResult.value = {
   272|        healthy: result.healthy !== false,
   273|        time: new Date().toLocaleString('zh-CN'),
   274|        items: components.value.map(comp => {
   275|          const info = result.components?.[comp.key]
   276|          return {
   277|            key: comp.key,
   278|            label: comp.label,
   279|            status: info?.status || comp.status,
   280|            message: info?.message || '',
   281|          }
   282|        }),
   283|      }
   284|      selfCheckVisible.value = true
   285|      // Also refresh status
   286|      await loadStatus()
   287|    }
   288|  } catch (e: any) {
   289|    ElMessage.error('自检请求失败')
   290|  } finally {
   291|    selfChecking.value = false
   292|  }
   293|}
   294|
   295|onMounted(() => { loadStatus() })
   296|onUnmounted(() => { stopAutoRefresh() })
   297|</script>
   298|
   299|<style scoped>
   300|
   301|.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 8px; }
   302|.page-header h2 { margin: 0; font-size: 20px; color: #1d2129; }
   303|
   304|.auto-refresh-control {
   305|  display: flex;
   306|  align-items: center;
   307|  gap: 6px;
   308|}
   309|.refresh-countdown {
   310|  font-size: 12px;
   311|  color: #86909c;
   312|  min-width: 28px;
   313|}
   314|
   315|.status-grid {
   316|  display: grid;
   317|  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
   318|  gap: 16px;
   319|}
   320|
   321|.status-card {
   322|  border-radius: 8px;
   323|  transition: border-color 0.3s;
   324|}
   325|.status-card-unhealthy {
   326|  border-color: #f53f3f;
   327|}
   328|.status-card :deep(.el-card__body) {
   329|  padding: 16px 20px;
   330|}
   331|
   332|.card-header {
   333|  display: flex;
   334|  align-items: center;
   335|  gap: 8px;
   336|  margin-bottom: 12px;
   337|  font-size: 15px;
   338|  font-weight: 600;
   339|}
   340|.card-icon { font-size: 22px; }
   341|
   342|
   343|.card-body { font-size: 13px; }
   344|.detail-row {
   345|  display: flex;
   346|  justify-content: space-between;
   347|  padding: 4px 0;
   348|  border-bottom: 1px solid #f0f0f0;
   349|}
   350|.detail-row:last-child { border-bottom: none; }
   351|.detail-key { color: #86909c; }
   352|.detail-val { color: #1d2129; font-weight: 500; }
   353|
   354|.card-footer {
   355|  display: flex;
   356|  justify-content: space-between;
   357|  align-items: center;
   358|  margin-top: 10px;
   359|  padding-top: 8px;
   360|  border-top: 1px solid #f0f0f0;
   361|  font-size: 13px;
   362|}
   363|.latency-label { color: #86909c; }
   364|.latency-value { color: #00b42a; font-weight: 600; }
   365|.latency-warn { color: #ff7d00; }
   366|
   367|.text-muted { color: #86909c; font-size: 13px; }
   368|
   369|.chart-container { min-height: 80px; }
   370|.chart-placeholder {
   371|  display: flex;
   372|  align-items: center;
   373|  justify-content: center;
   374|  height: 80px;
   375|}
   376|
   377|.history-timeline { max-height: 300px; overflow-y: auto; }
   378|.history-row {
   379|  display: flex;
   380|  align-items: center;
   381|  gap: 12px;
   382|  padding: 8px 0;
   383|  border-bottom: 1px solid #f5f5f5;
   384|}
   385|.history-row:last-child { border-bottom: none; }
   386|.history-time {
   387|  font-size: 13px;
   388|  color: #4e5969;
   389|  white-space: nowrap;
   390|  min-width: 160px;
   391|}
   392|.history-dots { display: flex; gap: 6px; flex: 1; }
   393|.history-dot {
   394|  width: 14px;
   395|  height: 14px;
   396|  border-radius: 50%;
   397|  display: inline-block;
   398|  cursor: default;
   399|}
   400|.dot-healthy { background-color: #00b42a; }
   401|.dot-degraded { background-color: #ff7d00; }
   402|.dot-unhealthy { background-color: #f53f3f; }
   403|.dot-unknown { background-color: #c9cdd4; }
   404|</style>
   405|