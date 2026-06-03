     1|<template>
     2|  <div class="page-container">
     3|    <!-- 页面头部 -->
     4|    <div class="autops-page-header">
     5|      <div class="autops-page-title">巡检总览</div>
     6|      <div class="autops-page-desc">管理和配置巡检模板、计划与任务</div>
     7|    </div>
     8|
     9|    <div style="display: flex; justify-content: flex-end; margin-bottom: 16px;">
    10|      <el-button type="primary" @click="router.push('/inspection/templates')">
    11|        <el-icon><Plus /></el-icon>
    12|        创建模板
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
    38|    <!-- 最近巡检任务 -->
    39|    <el-card class="main-card">
    40|      <template #header>
    41|        <div class="card-header">
    42|          <span class="card-title">最近巡检任务</span>
    43|          <el-button text type="primary" @click="router.push('/inspection/tasks')">
    44|            查看全部 <el-icon><ArrowRight /></el-icon>
    45|          </el-button>
    46|        </div>
    47|      </template>
    48|      <el-table stripe
 49| :data="recentTasks"
 50| v-loading="tasksLoading"
 51|52| empty-text="暂无巡检任务"
 53| style="width: 100%"
 54| >
    55|        <el-table-column prop="name" label="任务名称" min-width="180" show-overflow-tooltip>
    56|          <template #default="{ row }">
    57|            <el-link type="primary" @click="router.push(`/inspection/${row.id}`)">
    58|              {{ row.name || row.template_name || '-' }}
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
    69|        <el-table-column prop="asset_names" label="巡检资产" min-width="160" show-overflow-tooltip>
    70|          <template #default="{ row }">
    71|            <span>{{ formatAssets(row) }}</span>
    72|          </template>
    73|        </el-table-column>
    74|        <el-table-column prop="started_at" label="开始时间" width="170">
    75|          <template #default="{ row }">
    76|            <span class="text-muted">{{ formatTime(row.started_at) }}</span>
    77|          </template>
    78|        </el-table-column>
    79|        <el-table-column prop="duration" label="耗时" width="100" align="center">
    80|          <template #default="{ row }">
    81|            <span>{{ formatDuration(row) }}</span>
    82|          </template>
    83|        </el-table-column>
    84|        <el-table-column label="操作" width="100" align="center" fixed="right">
    85|          <template #default="{ row }">
    86|            <el-button text type="primary" size="small" @click="router.push(`/inspection/${row.id}`)">
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
   123|  Calendar,
   124|  List,
   125|  DataAnalysis,
   126|  Tickets,
   127|} from '@element-plus/icons-vue'
   128|import { inspectionService } from '@/shared/api'
   129|
   130|const router = useRouter()
   131|
   132|// ── 统计卡片 ──
   133|const statsLoading = ref(false)
   134|const statCards = reactive([
   135|  {
   136|    key: 'templates',
   137|    label: '模板数',
   138|    value: 0,
   139|    icon: Document,
   140|    bg: '#e8f3ff',
   141|    color: '#165dff',
   142|    route: '/inspection/templates',
   143|  },
   144|  {
   145|    key: 'plans',
   146|    label: '计划数',
   147|    value: 0,
   148|    icon: Calendar,
   149|    bg: '#fff7e8',
   150|    color: '#ff7d00',
   151|    route: '/inspection/plans',
   152|  },
   153|  {
   154|    key: 'tasks',
   155|    label: '任务数',
   156|    value: 0,
   157|    icon: List,
   158|    bg: '#e8ffea',
   159|    color: '#00b42a',
   160|    route: '/inspection/tasks',
   161|  },
   162|  {
   163|    key: 'completion_rate',
   164|    label: '完成率',
   165|    value: 0,
   166|    suffix: '%',
   167|    icon: DataAnalysis,
   168|    bg: '#f0e8ff',
   169|    color: '#722ed1',
   170|    route: '/inspection/results',
   171|  },
   172|])
   173|
   174|// ── 最近任务 ──
   175|const tasksLoading = ref(false)
   176|const recentTasks = ref<any[]>([])
   177|
   178|// ── 快速导航 ──
   179|const quickLinks = [
   180|  {
   181|    label: '巡检模板',
   182|    desc: '管理和配置巡检模板',
   183|    icon: Document,
   184|    color: '#165dff',
   185|    route: '/inspection/templates',
   186|  },
   187|  {
   188|    label: '巡检计划',
   189|    desc: '创建定时巡检计划',
   190|    icon: Calendar,
   191|    color: '#ff7d00',
   192|    route: '/inspection/plans',
   193|  },
   194|  {
   195|    label: '巡检任务',
   196|    desc: '查看所有巡检任务',
   197|    icon: List,
   198|    color: '#00b42a',
   199|    route: '/inspection/tasks',
   200|  },
   201|  {
   202|    label: '巡检报告',
   203|    desc: '查看巡检结果和报告',
   204|    icon: Tickets,
   205|    color: '#722ed1',
   206|    route: '/inspection/reports',
   207|  },
   208|]
   209|
   210|// ── 状态映射 ──
   211|const statusMap: Record<string, { type: '' | 'success' | 'warning' | 'danger' | 'info'; label: string }> = {
   212|  completed: { type: 'success', label: '已完成' },
   213|  success: { type: 'success', label: '已完成' },
   214|  failed: { type: 'danger', label: '失败' },
   215|  running: { type: 'warning', label: '执行中' },
   216|  pending: { type: 'info', label: '待执行' },
   217|  cancelled: { type: 'info', label: '已取消' },
   218|  timeout: { type: 'danger', label: '超时' },
   219|}
   220|
   221|function statusType(status: string) {
   222|  return statusMap[status]?.type ?? 'info'
   223|}
   224|
   225|function statusLabel(status: string) {
   226|  return statusMap[status]?.label ?? status
   227|}
   228|
   229|// ── 格式化工具 ──
   230|function formatTime(val: string | null | undefined): string {
   231|  if (!val) return '-'
   232|  try {
   233|    const d = new Date(val)
   234|    if (isNaN(d.getTime())) return val
   235|    const pad = (n: number) => String(n).padStart(2, '0')
   236|    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
   237|  } catch {
   238|    return val
   239|  }
   240|}
   241|
   242|function formatAssets(row: any): string {
   243|  if (row.asset_names && Array.isArray(row.asset_names)) {
   244|    return row.asset_names.join(', ') || '-'
   245|  }
   246|  if (row.asset_name) return row.asset_name
   247|  if (row.asset_count !== undefined) return `${row.asset_count} 个资产`
   248|  return '-'
   249|}
   250|
   251|function formatDuration(row: any): string {
   252|  if (row.duration !== undefined && row.duration !== null) {
   253|    const sec = Number(row.duration)
   254|    if (isNaN(sec)) return row.duration
   255|    if (sec < 60) return `${sec}s`
   256|    if (sec < 3600) return `${Math.floor(sec / 60)}m ${sec % 60}s`
   257|    return `${Math.floor(sec / 3600)}h ${Math.floor((sec % 3600) / 60)}m`
   258|  }
   259|  // 尝试从 started_at / finished_at 计算
   260|  if (row.started_at && row.finished_at) {
   261|    const diff = new Date(row.finished_at).getTime() - new Date(row.started_at).getTime()
   262|    if (diff > 0) {
   263|      const sec = Math.round(diff / 1000)
   264|      if (sec < 60) return `${sec}s`
   265|      if (sec < 3600) return `${Math.floor(sec / 60)}m ${sec % 60}s`
   266|      return `${Math.floor(sec / 3600)}h ${Math.floor((sec % 3600) / 60)}m`
   267|    }
   268|  }
   269|  return '-'
   270|}
   271|
   272|// ── 数据获取 ──
   273|async function fetchStats() {
   274|  statsLoading.value = true
   275|  try {
   276|    // 并行请求获取各计数
   277|    const [templatesRes, plansRes, tasksRes] = await Promise.allSettled([
   278|      inspectionService.listTemplates({ page: 1, page_size: 1 }),
   279|      inspectionService.listPlans({ page: 1, page_size: 1 }),
   280|      inspectionService.listTasks({ page: 1, page_size: 1 }),
   281|    ])
   282|
   283|    // 解析模板总数
   284|    if (templatesRes.status === 'fulfilled') {
   285|      const data = templatesRes.value?.data
   286|      statCards[0].value = data?.total ?? data?.count ?? (data?.items?.length ?? 0)
   287|    }
   288|
   289|    // 解析计划总数
   290|    if (plansRes.status === 'fulfilled') {
   291|      const data = plansRes.value?.data
   292|      statCards[1].value = data?.total ?? data?.count ?? (data?.items?.length ?? 0)
   293|    }
   294|
   295|    // 解析任务总数 & 完成率
   296|    if (tasksRes.status === 'fulfilled') {
   297|      const data = tasksRes.value?.data
   298|      const total = data?.total ?? data?.count ?? 0
   299|      statCards[2].value = total
   300|
   301|      // 尝试从 overview 获取完成率
   302|      if (data?.completion_rate !== undefined) {
   303|        statCards[3].value = Number(data.completion_rate)
   304|      } else if (data?.stats?.completion_rate !== undefined) {
   305|        statCards[3].value = Number(data.stats.completion_rate)
   306|      }
   307|    }
   308|
   309|    // 尝试获取 overview 统计（补充完成率等）
   310|    try {
   311|      const overviewRes = await inspectionService.overview()
   312|      // /api/v1/inspection/stats returns: { tasks: {...}, templates: {...}, plans: {...}, results: {...} }
   313|      const raw = overviewRes?.data
   314|      const od = raw?.data ?? raw ?? {}
   315|      if (od.templates) statCards[0].value = od.templates.total ?? statCards[0].value
   316|      if (od.plans) statCards[1].value = od.plans.total ?? statCards[1].value
   317|      if (od.tasks) {
   318|        statCards[2].value = od.tasks.total ?? statCards[2].value
   319|        // Compute completion rate from tasks
   320|        var taskTotal = od.tasks.total ?? 0
   321|        var taskCompleted = od.tasks.completed ?? 0
   322|        if (taskTotal > 0) {
   323|          statCards[3].value = Math.round((taskCompleted / taskTotal) * 100)
   324|        }
   325|      }
   326|    } catch {
   327|      // overview 接口可选，忽略错误
   328|    }
   329|  } catch (err: any) {
   330|    console.error('获取巡检统计数据失败:', err)
   331|    ElMessage.error('获取统计数据失败')
   332|  } finally {
   333|    statsLoading.value = false
   334|  }
   335|}
   336|
   337|async function fetchRecentTasks() {
   338|  tasksLoading.value = true
   339|  try {
   340|    const res = await inspectionService.listTasks({ page: 1, page_size: 10 })
   341|    const data = res?.data
   342|    if (Array.isArray(data?.items)) {
   343|      recentTasks.value = data.items
   344|    } else if (Array.isArray(data?.results)) {
   345|      recentTasks.value = data.results
   346|    } else if (Array.isArray(data)) {
   347|      recentTasks.value = data
   348|    } else if (data?.data && Array.isArray(data.data)) {
   349|      recentTasks.value = data.data
   350|    } else {
   351|      recentTasks.value = []
   352|    }
   353|  } catch (err: any) {
   354|    console.error('获取最近巡检任务失败:', err)
   355|    ElMessage.error('获取最近任务失败')
   356|  } finally {
   357|    tasksLoading.value = false
   358|  }
   359|}
   360|
   361|// ── 生命周期 ──
   362|onMounted(() => {
   363|  fetchStats()
   364|  fetchRecentTasks()
   365|})
   366|</script>
   367|
   368|<style scoped>
   369|
   374|
   375|.stat-row {
   376|  margin-bottom: 16px;
   377|}
   378|
   379|
   383|
   384|.stat-card-clickable {
   385|  cursor: pointer;
   386|}
   387|
   388|.stat-card-clickable:hover {
   389|  transform: translateY(-2px);
   390|}
   391|
   392|.stat-card-inner {
   393|  display: flex;
   394|  align-items: center;
   395|  gap: 16px;
   396|}
   397|
   398|.stat-icon-wrap {
   399|  width: 48px;
   400|  height: 48px;
   401|  border-radius: 12px;
   402|  display: flex;
   403|  align-items: center;
   404|  justify-content: center;
   405|  flex-shrink: 0;
   406|}
   407|
   408|.stat-body {
   409|  flex: 1;
   410|}
   411|
   412|.stat-body :deep(.el-statistic__head) {
   413|  font-size: 13px;
   414|  color: #86909c;
   415|  margin-bottom: 4px;
   416|}
   417|
   418|.stat-body :deep(.el-statistic__content) {
   419|  font-size: 24px;
   420|  font-weight: 600;
   421|  color: #1d2129;
   422|}
   423|
   424|.main-card {
   425|  margin-bottom: 16px;
   426|}
   427|
   428|
   433|
   434|
   439|
   440|.text-muted {
   441|  color: #86909c;
   442|  font-size: 13px;
   443|}
   444|
   445|/* 快速导航 */
   446|.quick-links-row {
   447|  margin-bottom: 16px;
   448|}
   449|
   450|.quick-link-card {
   451|  cursor: pointer;
   452|  transition: all 0.2s;
   453|}
   454|
   455|.quick-link-card:hover {
   456|  transform: translateY(-2px);
   457|  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
   458|}
   459|
   460|.quick-link-inner {
   461|  display: flex;
   462|  align-items: center;
   463|  gap: 14px;
   464|  padding: 4px 0;
   465|}
   466|
   467|.quick-link-text {
   468|  flex: 1;
   469|}
   470|
   471|.quick-link-label {
   472|  font-size: 15px;
   473|  font-weight: 600;
   474|  color: #1d2129;
   475|  margin-bottom: 2px;
   476|}
   477|
   478|.quick-link-desc {
   479|  font-size: 12px;
   480|  color: #86909c;
   481|}
   482|</style>
   483|