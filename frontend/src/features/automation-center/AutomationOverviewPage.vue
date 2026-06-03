     1|<template>
     2|  <div class="page-container">
     3|    <!-- 页面头部 -->
     4|    <div class="autops-page-header">
     5|      <div class="autops-page-title">自动化总览</div>
     6|      <div class="autops-page-desc">管理自动化脚本、Playbook 与执行记录</div>
     7|    </div>
     8|
     9|    <div style="display: flex; justify-content: flex-end; margin-bottom: 16px;">
    10|      <el-button type="primary" @click="router.push('/scripts')">
    11|        <el-icon><Plus /></el-icon>
    12|        创建脚本
    13|      </el-button>
    14|    </div>
    15|
    16|    <!-- 统计卡片 -->
    17|    <el-row :gutter="16" class="stat-row">
    18|      <el-col :span="6" v-for="stat in statCards" :key="stat.key">
    19|        <el-card
    20|          shadow="hover"
    21|          class="stat-card"
    22|          :class="{ 'stat-card-clickable': stat.route }"
    23|          v-loading="statsLoading"
    24|          @click="stat.route && router.push(stat.route)"
    25|        >
    26|          <div class="stat-card-inner">
    27|            <div class="stat-icon-wrap" :style="{ background: stat.bg, color: stat.color }">
    28|              <el-icon :size="24"><component :is="stat.icon" /></el-icon>
    29|            </div>
    30|            <el-statistic :title="stat.label" :value="stat.value" class="stat-body">
    31|              <template #suffix v-if="stat.suffix">{{ stat.suffix }}</template>
    32|            </el-statistic>
    33|          </div>
    34|        </el-card>
    35|      </el-col>
    36|    </el-row>
    37|
    38|    <!-- 最近执行记录 -->
    39|    <el-card class="main-card">
    40|      <template #header>
    41|        <div class="card-header">
    42|          <span class="card-title">最近执行记录</span>
    43|          <el-button text type="primary" @click="router.push('/executions')">
    44|            查看全部 <el-icon><ArrowRight /></el-icon>
    45|          </el-button>
    46|        </div>
    47|      </template>
    48|      <el-table stripe
 49| :data="recentExecutions"
 50| v-loading="executionsLoading"
 51|52| empty-text="暂无执行记录"
 53| style="width: 100%"
 54| >
    55|        <el-table-column prop="name" label="执行名称" min-width="180" show-overflow-tooltip>
    56|          <template #default="{ row }">
    57|            <el-link type="primary" @click="router.push(`/executions/${row.id}`)">
    58|              {{ row.name || row.playbook_name || row.script_name || '-' }}
    59|            </el-link>
    60|          </template>
    61|        </el-table-column>
    62|        <el-table-column prop="status" label="状态" width="100" align="center">
    63|          <template #default="{ row }">
    64|            <el-tag :type="statusType(row.status)" size="small" effect="light">
    65|              {{ statusLabel(row.status) }}
    66|            </el-tag>
    67|          </template>
    68|        </el-table-column>
    69|        <el-table-column prop="trigger_type" label="触发方式" width="110" align="center">
    70|          <template #default="{ row }">
    71|            <span>{{ triggerLabel(row.trigger_type || row.trigger) }}</span>
    72|          </template>
    73|        </el-table-column>
    74|        <el-table-column prop="started_at" label="开始时间" width="170">
    75|          <template #default="{ row }">
    76|            <span class="text-muted">{{ formatTime(row.started_at || row.created_at) }}</span>
    77|          </template>
    78|        </el-table-column>
    79|        <el-table-column prop="duration" label="耗时" width="100" align="center">
    80|          <template #default="{ row }">
    81|            <span>{{ formatDuration(row) }}</span>
    82|          </template>
    83|        </el-table-column>
    84|        <el-table-column label="操作" width="100" align="center" fixed="right">
    85|          <template #default="{ row }">
    86|            <el-button text type="primary" size="small" @click="router.push(`/executions/${row.id}`)">
    87|              详情
    88|            </el-button>
    89|          </template>
    90|        </el-table-column>
    91|      </el-table>
    92|    </el-card>
    93|
    94|    <!-- 快速导航 -->
    95|    <el-row :gutter="16" class="quick-links-row">
    96|      <el-col :span="6" v-for="link in quickLinks" :key="link.label">
    97|        <el-card
    98|          shadow="hover"
    99|          class="quick-link-card"
   100|          @click="router.push(link.route)"
   101|        >
   102|          <div class="quick-link-inner">
   103|            <el-icon :size="32" :color="link.color"><component :is="link.icon" /></el-icon>
   104|            <div class="quick-link-text">
   105|              <div class="quick-link-label">{{ link.label }}</div>
   106|              <div class="quick-link-desc">{{ link.desc }}</div>
   107|            </div>
   108|          </div>
   109|        </el-card>
   110|      </el-col>
   111|    </el-row>
   112|  </div>
   113|</template>
   114|
   115|<script setup lang="ts">
   116|import { ref, reactive, onMounted } from 'vue'
   117|import { useRouter } from 'vue-router'
   118|import { ElMessage } from 'element-plus'
   119|import {
   120|  Plus,
   121|  ArrowRight,
   122|  Document,
   123|  VideoPlay,
   124|  List,
   125|  CircleCheck,
   126|  Checked,
   127|  Stamp,
   128|} from '@element-plus/icons-vue'
   129|import { automationService } from '@/shared/api'
   130|
   131|const router = useRouter()
   132|
   133|// ── 统计卡片 ──
   134|const statsLoading = ref(false)
   135|const statCards = reactive([
   136|  {
   137|    key: 'scripts',
   138|    label: '脚本数',
   139|    value: 0,
   140|    icon: Document,
   141|    bg: '#e8f3ff',
   142|    color: '#165dff',
   143|    route: '/scripts',
   144|  },
   145|  {
   146|    key: 'playbooks',
   147|    label: 'Playbook数',
   148|    value: 0,
   149|    icon: VideoPlay,
   150|    bg: '#fff7e8',
   151|    color: '#ff7d00',
   152|    route: '/playbooks',
   153|  },
   154|  {
   155|    key: 'executions',
   156|    label: '执行数',
   157|    value: 0,
   158|    icon: List,
   159|    bg: '#e8ffea',
   160|    color: '#00b42a',
   161|    route: '/executions',
   162|  },
   163|  {
   164|    key: 'success_rate',
   165|    label: '成功率',
   166|    value: 0,
   167|    suffix: '%',
   168|    icon: CircleCheck,
   169|    bg: '#f0e8ff',
   170|    color: '#722ed1',
   171|    route: '/executions',
   172|  },
   173|])
   174|
   175|// ── 最近执行记录 ──
   176|const executionsLoading = ref(false)
   177|const recentExecutions = ref<any[]>([])
   178|
   179|// ── 快速导航 ──
   180|const quickLinks = [
   181|  {
   182|    label: '脚本库',
   183|    desc: '管理自动化脚本',
   184|    icon: Document,
   185|    color: '#165dff',
   186|    route: '/scripts',
   187|  },
   188|  {
   189|    label: 'Playbook',
   190|    desc: '编排自动化剧本',
   191|    icon: VideoPlay,
   192|    color: '#ff7d00',
   193|    route: '/playbooks',
   194|  },
   195|  {
   196|    label: '执行历史',
   197|    desc: '查看所有执行记录',
   198|    icon: List,
   199|    color: '#00b42a',
   200|    route: '/executions',
   201|  },
   202|  {
   203|    label: '审批中心',
   204|    desc: '处理待审批任务',
   205|    icon: Stamp,
   206|    color: '#722ed1',
   207|    route: '/approvals',
   208|  },
   209|]
   210|
   211|// ── 状态映射 ──
   212|const statusMap: Record<string, { type: '' | 'success' | 'warning' | 'danger' | 'info'; label: string }> = {
   213|  completed: { type: 'success', label: '已完成' },
   214|  success: { type: 'success', label: '成功' },
   215|  failed: { type: 'danger', label: '失败' },
   216|  running: { type: 'warning', label: '执行中' },
   217|  pending: { type: 'info', label: '待执行' },
   218|  cancelled: { type: 'info', label: '已取消' },
   219|  timeout: { type: 'danger', label: '超时' },
   220|  paused: { type: 'warning', label: '已暂停' },
   221|  waiting_approval: { type: 'warning', label: '待审批' },
   222|  rolled_back: { type: 'info', label: '已回滚' },
   223|}
   224|
   225|function statusType(status: string) {
   226|  return statusMap[status]?.type ?? 'info'
   227|}
   228|
   229|function statusLabel(status: string) {
   230|  return statusMap[status]?.label ?? status
   231|}
   232|
   233|// ── 触发方式映射 ──
   234|const triggerMap: Record<string, string> = {
   235|  manual: '手动触发',
   236|  auto: '自动触发',
   237|  schedule: '定时触发',
   238|  alert: '告警触发',
   239|  event: '事件触发',
   240|  policy: '策略触发',
   241|  api: 'API 触发',
   242|}
   243|
   244|function triggerLabel(trigger: string | undefined): string {
   245|  if (!trigger) return '-'
   246|  return triggerMap[trigger] ?? trigger
   247|}
   248|
   249|// ── 格式化工具 ──
   250|function formatTime(val: string | null | undefined): string {
   251|  if (!val) return '-'
   252|  try {
   253|    const d = new Date(val)
   254|    if (isNaN(d.getTime())) return val
   255|    const pad = (n: number) => String(n).padStart(2, '0')
   256|    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
   257|  } catch {
   258|    return val
   259|  }
   260|}
   261|
   262|function formatDuration(row: any): string {
   263|  if (row.duration !== undefined && row.duration !== null) {
   264|    const sec = Number(row.duration)
   265|    if (isNaN(sec)) return row.duration
   266|    if (sec < 60) return `${sec}s`
   267|    if (sec < 3600) return `${Math.floor(sec / 60)}m ${sec % 60}s`
   268|    return `${Math.floor(sec / 3600)}h ${Math.floor((sec % 3600) / 60)}m`
   269|  }
   270|  if (row.started_at && row.finished_at) {
   271|    const diff = new Date(row.finished_at).getTime() - new Date(row.started_at).getTime()
   272|    if (diff > 0) {
   273|      const sec = Math.round(diff / 1000)
   274|      if (sec < 60) return `${sec}s`
   275|      if (sec < 3600) return `${Math.floor(sec / 60)}m ${sec % 60}s`
   276|      return `${Math.floor(sec / 3600)}h ${Math.floor((sec % 3600) / 60)}m`
   277|    }
   278|  }
   279|  return '-'
   280|}
   281|
   282|// ── 数据获取 ──
   283|async function fetchStats() {
   284|  statsLoading.value = true
   285|  try {
   286|    // 并行请求获取各计数
   287|    const [scriptsRes, playbooksRes, executionsRes] = await Promise.allSettled([
   288|      automationService.listScripts({ page: 1, page_size: 1 }),
   289|      automationService.listPlaybooks({ page: 1, page_size: 1 }),
   290|      automationService.listExecutions({ page: 1, page_size: 1 }),
   291|    ])
   292|
   293|    // 解析脚本总数
   294|    if (scriptsRes.status === 'fulfilled') {
   295|      const data = scriptsRes.value?.data
   296|      statCards[0].value = data?.total ?? data?.count ?? (data?.items?.length ?? 0)
   297|    }
   298|
   299|    // 解析 Playbook 总数
   300|    if (playbooksRes.status === 'fulfilled') {
   301|      const data = playbooksRes.value?.data
   302|      statCards[1].value = data?.total ?? data?.count ?? (data?.items?.length ?? 0)
   303|    }
   304|
   305|    // 解析执行总数 & 成功率
   306|    if (executionsRes.status === 'fulfilled') {
   307|      const data = executionsRes.value?.data
   308|      statCards[2].value = data?.total ?? data?.count ?? 0
   309|
   310|      if (data?.success_rate !== undefined) {
   311|        statCards[3].value = Number(data.success_rate)
   312|      } else if (data?.stats?.success_rate !== undefined) {
   313|        statCards[3].value = Number(data.stats.success_rate)
   314|      }
   315|    }
   316|
   317|    // 尝试获取 overview 统计（补充成功率等）
   318|    try {
   319|      const overviewRes = await automationService.overview()
   320|      // /api/v1/automation/stats returns: { total, completed, failed, pending_approval, running, rolling_back, success_rate }
   321|      const raw = overviewRes?.data
   322|      const od = raw?.data ?? raw ?? {}
   323|      // execution total and success_rate from stats endpoint
   324|      if (od.total !== undefined) statCards[2].value = od.total ?? statCards[2].value
   325|      if (od.success_rate !== undefined) statCards[3].value = Number(od.success_rate)
   326|      // These fields are not returned by the stats endpoint,
   327|      // so we rely on the list endpoints above for script/playbook counts
   328|    } catch {
   329|      // overview 接口可选，忽略错误
   330|    }
   331|  } catch (err: any) {
   332|    console.error('获取自动化统计数据失败:', err)
   333|    ElMessage.error('获取统计数据失败')
   334|  } finally {
   335|    statsLoading.value = false
   336|  }
   337|}
   338|
   339|async function fetchRecentExecutions() {
   340|  executionsLoading.value = true
   341|  try {
   342|    const res = await automationService.listExecutions({ page: 1, page_size: 10 })
   343|    // Backend wraps: { code: 0, data: { items: [...], total, ... } }
   344|    const raw = res?.data ?? {}
   345|    const data = raw.data ?? raw
   346|    if (Array.isArray(data?.items)) {
   347|      recentExecutions.value = data.items
   348|    } else if (Array.isArray(data?.results)) {
   349|      recentExecutions.value = data.results
   350|    } else if (Array.isArray(data)) {
   351|      recentExecutions.value = data
   352|    } else {
   353|      recentExecutions.value = []
   354|    }
   355|  } catch (err: any) {
   356|    console.error('获取最近执行记录失败:', err)
   357|    ElMessage.error('获取执行记录失败')
   358|  } finally {
   359|    executionsLoading.value = false
   360|  }
   361|}
   362|
   363|// ── 生命周期 ──
   364|onMounted(() => {
   365|  fetchStats()
   366|  fetchRecentExecutions()
   367|})
   368|</script>
   369|
   370|<style scoped>
   371|
   376|
   377|.stat-row {
   378|  margin-bottom: 16px;
   379|}
   380|
   381|
   385|
   386|.stat-card-clickable {
   387|  cursor: pointer;
   388|}
   389|
   390|.stat-card-clickable:hover {
   391|  transform: translateY(-2px);
   392|}
   393|
   394|.stat-card-inner {
   395|  display: flex;
   396|  align-items: center;
   397|  gap: 16px;
   398|}
   399|
   400|.stat-icon-wrap {
   401|  width: 48px;
   402|  height: 48px;
   403|  border-radius: 12px;
   404|  display: flex;
   405|  align-items: center;
   406|  justify-content: center;
   407|  flex-shrink: 0;
   408|}
   409|
   410|.stat-body {
   411|  flex: 1;
   412|}
   413|
   414|.stat-body :deep(.el-statistic__head) {
   415|  font-size: 13px;
   416|  color: #86909c;
   417|  margin-bottom: 4px;
   418|}
   419|
   420|.stat-body :deep(.el-statistic__content) {
   421|  font-size: 24px;
   422|  font-weight: 600;
   423|  color: #1d2129;
   424|}
   425|
   426|.main-card {
   427|  margin-bottom: 16px;
   428|}
   429|
   430|
   435|
   436|
   441|
   442|.text-muted {
   443|  color: #86909c;
   444|  font-size: 13px;
   445|}
   446|
   447|/* 快速导航 */
   448|.quick-links-row {
   449|  margin-bottom: 16px;
   450|}
   451|
   452|.quick-link-card {
   453|  cursor: pointer;
   454|  transition: all 0.2s;
   455|}
   456|
   457|.quick-link-card:hover {
   458|  transform: translateY(-2px);
   459|  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
   460|}
   461|
   462|.quick-link-inner {
   463|  display: flex;
   464|  align-items: center;
   465|  gap: 14px;
   466|  padding: 4px 0;
   467|}
   468|
   469|.quick-link-text {
   470|  flex: 1;
   471|}
   472|
   473|.quick-link-label {
   474|  font-size: 15px;
   475|  font-weight: 600;
   476|  color: #1d2129;
   477|  margin-bottom: 2px;
   478|}
   479|
   480|.quick-link-desc {
   481|  font-size: 12px;
   482|  color: #86909c;
   483|}
   484|</style>
   485|