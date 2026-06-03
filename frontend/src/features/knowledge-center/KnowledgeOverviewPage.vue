     1|<template>
     2|  <div class="page-container">
     3|    <!-- Page Header -->
     4|    <div class="autops-page-header">
     5|      <div class="autops-page-title">知识总览</div>
     6|      <div class="autops-page-desc">查看知识库整体情况，快速访问核心功能</div>
     7|    </div>
     8|
     9|    <!-- Stat Cards -->
    10|    <el-row :gutter="16" class="stat-row">
    11|      <el-col :span="6" v-for="stat in statCards" :key="stat.label">
    12|        <el-card shadow="hover" class="stat-card" v-loading="statsLoading">
    13|          <div class="stat-card-inner">
    14|            <div class="stat-icon-wrap" :style="{ background: stat.bgColor }">
    15|              <el-icon :size="24" :style="{ color: stat.color }">
    16|                <component :is="stat.icon" />
    17|              </el-icon>
    18|            </div>
    19|            <div class="stat-info">
    20|              <el-statistic :title="stat.label" :value="stat.value" />
    21|            </div>
    22|          </div>
    23|        </el-card>
    24|      </el-col>
    25|    </el-row>
    26|
    27|    <!-- Recent Knowledge Table -->
    28|    <el-card class="main-card" shadow="never">
    29|      <template #header>
    30|        <div class="card-header">
    31|          <span class="card-title">最近更新的知识</span>
    32|          <el-button type="primary" text @click="router.push({ name: 'knowledge' })">
    33|            查看全部 <el-icon class="el-icon--right"><ArrowRight /></el-icon>
    34|          </el-button>
    35|        </div>
    36|      </template>
    37|      <el-table stripe
 38| :data="recentItems"
 39|40| v-loading="tableLoading"
 41| empty-text="暂无知识"
 42| style="width: 100%"
 43| >
    44|        <el-table-column prop="title" label="标题" min-width="220" show-overflow-tooltip>
    45|          <template #default="{ row }">
    46|            <el-link type="primary" @click="router.push(`/knowledge/${row.id}`)">
    47|              {{ row.title }}
    48|            </el-link>
    49|          </template>
    50|        </el-table-column>
    51|        <el-table-column prop="category" label="分类" width="120">
    52|          <template #default="{ row }">
    53|            <el-tag size="small" :type="getCategoryTagType(row.category)">
    54|              {{ row.category || '未分类' }}
    55|            </el-tag>
    56|          </template>
    57|        </el-table-column>
    58|        <el-table-column prop="status" label="状态" width="100">
    59|          <template #default="{ row }">
    60|            <el-tag size="small" :type="getStatusTagType(row.status)">
    61|              {{ getStatusLabel(row.status) }}
    62|            </el-tag>
    63|          </template>
    64|        </el-table-column>
    65|        <el-table-column prop="created_by" label="创建者" width="120">
    66|          <template #default="{ row }">
    67|            <span>{{ row.created_by || row.author || '-' }}</span>
    68|          </template>
    69|        </el-table-column>
    70|        <el-table-column prop="updated_at" label="更新时间" width="180">
    71|          <template #default="{ row }">
    72|            <span class="text-muted">{{ formatTime(row.updated_at) }}</span>
    73|          </template>
    74|        </el-table-column>
    75|      </el-table>
    76|    </el-card>
    77|
    78|    <!-- Quick Links + Category Stats -->
    79|    <el-row :gutter="16" class="bottom-row">
    80|      <!-- Category Distribution -->
    81|      <el-col :span="12">
    82|        <el-card class="main-card" shadow="never">
    83|          <template #header>
    84|            <div class="card-header">
    85|              <span class="card-title">知识分类统计</span>
    86|            </div>
    87|          </template>
    88|          <div class="category-list" v-loading="statsLoading">
    89|            <div v-for="cat in categories" :key="cat.name" class="category-row">
    90|              <span class="category-name">{{ cat.name }}</span>
    91|              <el-progress
    92|                :percentage="cat.percentage"
    93|                :stroke-width="12"
    94|                :color="cat.color"
    95|                style="flex: 1; margin: 0 16px"
    96|              />
    97|              <span class="category-count">{{ cat.count }} 篇</span>
    98|            </div>
    99|            <el-empty v-if="categories.length === 0 && !statsLoading" description="暂无分类数据" :image-size="60" />
   100|          </div>
   101|        </el-card>
   102|      </el-col>
   103|
   104|      <!-- Quick Links -->
   105|      <el-col :span="12">
   106|        <el-card class="main-card" shadow="never">
   107|          <template #header>
   108|            <div class="card-header">
   109|              <span class="card-title">快速访问</span>
   110|            </div>
   111|          </template>
   112|          <div class="quick-links">
   113|            <div
   114|              v-for="link in quickLinks"
   115|              :key="link.name"
   116|              class="quick-link-item"
   117|              @click="router.push(link.route)"
   118|            >
   119|              <div class="quick-link-icon" :style="{ background: link.bgColor, color: link.color }">
   120|                <el-icon :size="22"><component :is="link.icon" /></el-icon>
   121|              </div>
   122|              <div class="quick-link-info">
   123|                <div class="quick-link-title">{{ link.title }}</div>
   124|                <div class="quick-link-desc">{{ link.description }}</div>
   125|              </div>
   126|              <el-icon class="quick-link-arrow"><ArrowRight /></el-icon>
   127|            </div>
   128|          </div>
   129|        </el-card>
   130|      </el-col>
   131|    </el-row>
   132|  </div>
   133|</template>
   134|
   135|<script setup lang="ts">
   136|import { ref, reactive, onMounted } from 'vue'
   137|import { useRouter } from 'vue-router'
   138|import { ElMessage } from 'element-plus'
   139|import { Document, Checked, EditPen, StarFilled, ArrowRight, Upload, List, View as Review, Notebook } from '@element-plus/icons-vue'
   140|import { knowledgeService } from '@/shared/api'
   141|
   142|const router = useRouter()
   143|
   144|// --- State ---
   145|const statsLoading = ref(false)
   146|const tableLoading = ref(false)
   147|const recentItems = ref<any[]>([])
   148|
   149|const statCards = reactive([
   150|  { label: '知识总数', value: 0, icon: Document, color: '#165dff', bgColor: '#e8f3ff' },
   151|  { label: '已发布', value: 0, icon: Checked, color: '#00b42a', bgColor: '#e8ffea' },
   152|  { label: '草稿', value: 0, icon: EditPen, color: '#ff7d00', bgColor: '#fff7e8' },
   153|  { label: '平均评分', value: 0, icon: StarFilled, color: '#722ed1', bgColor: '#f5e8ff' },
   154|])
   155|
   156|const categories = ref<{ name: string; count: number; percentage: number; color: string }[]>([])
   157|
   158|const quickLinks = [
   159|  {
   160|    name: 'knowledge-list',
   161|    title: '知识列表',
   162|    description: '浏览和管理所有知识条目',
   163|    icon: List,
   164|    color: '#165dff',
   165|    bgColor: '#e8f3ff',
   166|    route: { name: 'knowledge' },
   167|  },
   168|  {
   169|    name: 'knowledge-import',
   170|    title: '知识导入',
   171|    description: '批量导入外部知识文档',
   172|    icon: Upload,
   173|    color: '#00b42a',
   174|    bgColor: '#e8ffea',
   175|    route: { name: 'knowledge-import' },
   176|  },
   177|  {
   178|    name: 'knowledge-review',
   179|    title: '知识审核',
   180|    description: '审核待发布的知识内容',
   181|    icon: Review,
   182|    color: '#ff7d00',
   183|    bgColor: '#fff7e8',
   184|    route: { name: 'knowledge-review' },
   185|  },
   186|  {
   187|    name: 'prompt-templates',
   188|    title: 'Prompt 模板',
   189|    description: '管理 AI 提示词模板',
   190|    icon: Notebook,
   191|    color: '#722ed1',
   192|    bgColor: '#f5e8ff',
   193|    route: { name: 'prompt-templates' },
   194|  },
   195|]
   196|
   197|// --- Helpers ---
   198|function formatTime(val: string | number | null | undefined): string {
   199|  if (!val) return '-'
   200|  const d = new Date(val)
   201|  if (isNaN(d.getTime())) return '-'
   202|  const pad = (n: number) => String(n).padStart(2, '0')
   203|  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
   204|}
   205|
   206|function getStatusTagType(status: string): '' | 'success' | 'warning' | 'danger' | 'info' {
   207|  const map: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
   208|    published: 'success',
   209|    draft: 'warning',
   210|    review: '',
   211|    rejected: 'danger',
   212|    archived: 'info',
   213|  }
   214|  return map[status] || 'info'
   215|}
   216|
   217|function getStatusLabel(status: string): string {
   218|  const map: Record<string, string> = {
   219|    published: '已发布',
   220|    draft: '草稿',
   221|    review: '审核中',
   222|    rejected: '已拒绝',
   223|    archived: '已归档',
   224|  }
   225|  return map[status] || status || '未知'
   226|}
   227|
   228|function getCategoryTagType(category: string): '' | 'success' | 'warning' | 'danger' | 'info' {
   229|  const map: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
   230|    故障处理: 'danger',
   231|    标准方案: 'success',
   232|    经验沉淀: 'warning',
   233|    操作指南: '',
   234|    FAQ: 'info',
   235|  }
   236|  return map[category] || 'info'
   237|}
   238|
   239|// --- Data Fetching ---
   240|async function fetchStats() {
   241|  statsLoading.value = true
   242|  try {
   243|    const res = await knowledgeService.stats()
   244|    // /api/v1/knowledge/stats returns: { total, published, draft }
   245|    // Response is wrapped: { code: 0, data: { total, published, draft } }
   246|    const raw = res.data ?? {}
   247|    const data = raw.data ?? raw
   248|    statCards[0].value = data.total ?? 0
   249|    statCards[1].value = data.published ?? 0
   250|    statCards[2].value = data.draft ?? 0
   251|    statCards[3].value = data.avg_score ?? data.average_rating ?? 0
   252|
   253|    // Build category distribution
   254|    if (data.categories && Array.isArray(data.categories)) {
   255|      var catTotal = data.categories.reduce(function (s: number, c: any) { return s + (c.count || 0) }, 0) || 1
   256|      var colors = ['#165dff', '#00b42a', '#ff7d00', '#722ed1', '#f53f3f', '#0fc6c2', '#f77234', '#3491fa']
   257|      categories.value = data.categories.map(function (c: any, i: number) {
   258|        return {
   259|          name: c.name || c.category || '未分类',
   260|          count: c.count || 0,
   261|          percentage: Math.round(((c.count || 0) / catTotal) * 100),
   262|          color: colors[i % colors.length],
   263|        }
   264|      })
   265|    }
   266|  } catch (err: any) {
   267|    console.error('Failed to fetch knowledge stats:', err)
   268|    ElMessage.error('获取知识统计信息失败')
   269|  } finally {
   270|    statsLoading.value = false
   271|  }
   272|}
   273|
   274|async function fetchRecentItems() {
   275|  tableLoading.value = true
   276|  try {
   277|    const res = await knowledgeService.list({ page: 1, page_size: 10 })
   278|    const data = res.data?.data ?? res.data ?? {}
   279|    recentItems.value = data.items ?? data.list ?? []
   280|  } catch (err: any) {
   281|    console.error('Failed to fetch recent knowledge:', err)
   282|    ElMessage.error('获取最近知识列表失败')
   283|  } finally {
   284|    tableLoading.value = false
   285|  }
   286|}
   287|
   288|// --- Lifecycle ---
   289|onMounted(() => {
   290|  fetchStats()
   291|  fetchRecentItems()
   292|})
   293|</script>
   294|
   295|<style scoped>
   296|
   301|
   302|.stat-row {
   303|  margin-bottom: 16px;
   304|}
   305|
   306|
   309|
   310|.stat-card-inner {
   311|  display: flex;
   312|  align-items: center;
   313|  gap: 16px;
   314|}
   315|
   316|.stat-icon-wrap {
   317|  width: 48px;
   318|  height: 48px;
   319|  border-radius: 12px;
   320|  display: flex;
   321|  align-items: center;
   322|  justify-content: center;
   323|  flex-shrink: 0;
   324|}
   325|
   326|.stat-info {
   327|  flex: 1;
   328|}
   329|
   330|.main-card {
   331|  margin-bottom: 16px;
   332|  border-radius: 8px;
   333|}
   334|
   335|
   340|
   341|
   346|
   347|.bottom-row {
   348|  margin-top: 0;
   349|}
   350|
   351|/* Category Distribution */
   352|.category-list {
   353|  min-height: 200px;
   354|}
   355|
   356|.category-row {
   357|  display: flex;
   358|  align-items: center;
   359|  margin-bottom: 16px;
   360|}
   361|
   362|.category-row:last-child {
   363|  margin-bottom: 0;
   364|}
   365|
   366|.category-name {
   367|  width: 80px;
   368|  font-size: 14px;
   369|  color: #4e5969;
   370|  flex-shrink: 0;
   371|}
   372|
   373|.category-count {
   374|  font-size: 13px;
   375|  color: #86909c;
   376|  flex-shrink: 0;
   377|  width: 50px;
   378|  text-align: right;
   379|}
   380|
   381|/* Quick Links */
   382|.quick-links {
   383|  display: flex;
   384|  flex-direction: column;
   385|  gap: 4px;
   386|}
   387|
   388|.quick-link-item {
   389|  display: flex;
   390|  align-items: center;
   391|  padding: 14px 16px;
   392|  border-radius: 8px;
   393|  cursor: pointer;
   394|  transition: background-color 0.2s;
   395|}
   396|
   397|.quick-link-item:hover {
   398|  background-color: #f2f3f5;
   399|}
   400|
   401|.quick-link-icon {
   402|  width: 44px;
   403|  height: 44px;
   404|  border-radius: 10px;
   405|  display: flex;
   406|  align-items: center;
   407|  justify-content: center;
   408|  flex-shrink: 0;
   409|  margin-right: 14px;
   410|}
   411|
   412|.quick-link-info {
   413|  flex: 1;
   414|}
   415|
   416|.quick-link-title {
   417|  font-size: 14px;
   418|  font-weight: 500;
   419|  color: #1d2129;
   420|  margin-bottom: 2px;
   421|}
   422|
   423|.quick-link-desc {
   424|  font-size: 12px;
   425|  color: #86909c;
   426|}
   427|
   428|.quick-link-arrow {
   429|  color: #c9cdd4;
   430|  font-size: 14px;
   431|}
   432|
   433|.text-muted {
   434|  color: #86909c;
   435|  font-size: 13px;
   436|}
   437|</style>
   438|