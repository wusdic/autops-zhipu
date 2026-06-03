     1|<template>
     2|  <div class="page-container">
     3|    <!-- Page Header -->
     4|    <div class="autops-page-header">
     5|      <div class="autops-page-title-row">
     6|        <el-button link @click="router.back()"><el-icon><ArrowLeft /></el-icon> 返回</el-button>
     7|        <span class="autops-page-title">Dry-run 预演</span>
     8|      </div>
     9|      <div class="autops-page-desc">模拟自动化策略执行，预览执行计划与影响分析</div>
    10|    </div>
    11|
    12|    <!-- Alert -->
    13|    <el-alert
    14|      type="info"
    15|      title="Dry-run 模式：仅预演执行计划，不实际修改系统"
    16|      show-icon
    17|      :closable="false"
    18|      style="margin-bottom: 16px;"
    19|    />
    20|
    21|    <!-- Two-column layout: List + Detail -->
    22|    <el-row :gutter="16">
    23|      <!-- Left: Dry-run List -->
    24|      <el-col :span="showDetail ? 10 : 24">
    25|        <el-card shadow="never" class="table-card">
    26|          <template #header>
    27|            <div class="card-header">
    28|              <span class="card-title">预演记录</span>
    29|            </div>
    30|          </template>
    31|
    32|          <!-- Filter -->
    33|          <el-row :gutter="12" style="margin-bottom: 12px;">
    34|            <el-col :span="8">
    35|              <el-input
    36|                v-model="searchKeyword"
    37|                placeholder="搜索名称..."
    38|                clearable
    39|                size="small"
    40|                @keyup.enter="handleSearch"
    41|                @clear="handleSearch"
    42|              >
    43|                <template #prefix>
    44|                  <el-icon><Search /></el-icon>
    45|                </template>
    46|              </el-input>
    47|            </el-col>
    48|            <el-col :span="5">
    49|              <el-select v-model="filterStatus" placeholder="状态" clearable size="small" @change="handleSearch">
    50|                <el-option label="运行中" value="running" />
    51|                <el-option label="成功" value="success" />
    52|                <el-option label="失败" value="failed" />
    53|                <el-option label="已取消" value="cancelled" />
    54|              </el-select>
    55|            </el-col>
    56|            <el-col :span="4">
    57|              <el-button size="small" type="primary" @click="handleSearch">查询</el-button>
    58|              <el-button size="small" @click="resetFilters">重置</el-button>
    59|            </el-col>
    60|          </el-row>
    61|
    62|          <!-- Table -->
    63|          <el-table stripe
 64| :data="dryRuns"
 65|66| v-loading="loading"
 67| empty-text="暂无预演记录"
 68| highlight-current-row
 69| @current-change="handleRowSelect"
 70| size="small"
 71| >
    72|            <el-table-column prop="name" label="名称" min-width="150" show-overflow-tooltip>
    73|              <template #default="{ row }">
    74|                <span class="dryrun-name" @click="loadDetail(row)">{{ row.name || '-' }}</span>
    75|              </template>
    76|            </el-table-column>
    77|            <el-table-column prop="policy_name" label="关联策略" width="130" show-overflow-tooltip>
    78|              <template #default="{ row }">
    79|                <span class="text-tertiary">{{ row.policy_name || row.policy_id || '-' }}</span>
    80|              </template>
    81|            </el-table-column>
    82|            <el-table-column prop="status" label="状态" width="90" align="center">
    83|              <template #default="{ row }">
    84|                <el-tag :type="dryRunStatusTag(row.status)" size="small" effect="light">
    85|                  {{ dryRunStatusLabel(row.status) }}
    86|                </el-tag>
    87|              </template>
    88|            </el-table-column>
    89|            <el-table-column prop="triggered_at" label="触发时间" width="160">
    90|              <template #default="{ row }">
    91|                <span class="text-tertiary">{{ formatTime(row.triggered_at || row.created_at) }}</span>
    92|              </template>
    93|            </el-table-column>
    94|            <el-table-column label="操作" width="180" fixed="right" align="center">
    95|              <template #default="{ row }">
    96|                <el-button text type="primary" size="small" @click="loadDetail(row)">查看</el-button>
    97|                <el-button text type="danger" size="small" @click="handleDelete(row)">删除</el-button>
    98|              </template>
    99|            </el-table-column>
   100|          </el-table>
   101|
   102|          <!-- Pagination -->
   103|          <div class="pagination-wrap">
   104|            <el-pagination
   105|              v-model:current-page="pagination.page"
   106|              v-model:page-size="pagination.page_size"
   107|              :total="pagination.total"
   108|              :page-sizes="[10, 20, 50]"
   109|              layout="total, sizes, prev, pager, next"
   110|              background
   111|              small
   112|              @size-change="fetchDryRuns"
   113|              @current-change="fetchDryRuns"
   114|            />
   115|          </div>
   116|        </el-card>
   117|      </el-col>
   118|
   119|      <!-- Right: Detail View -->
   120|      <el-col :span="14" v-if="showDetail">
   121|        <el-card shadow="never" class="detail-card">
   122|          <template #header>
   123|            <div class="card-header">
   124|              <span class="card-title">预演详情</span>
   125|              <el-button text type="primary" size="small" @click="showDetail = false; detail = null">
   126|                <el-icon><Close /></el-icon> 关闭
   127|              </el-button>
   128|            </div>
   129|          </template>
   130|
   131|          <div v-loading="detailLoading">
   132|            <template v-if="detail">
   133|              <!-- Basic Info -->
   134|              <el-descriptions :column="2" border size="small" style="margin-bottom: 20px;">
   135|                <el-descriptions-item label="名称">{{ detail.name || '-' }}</el-descriptions-item>
   136|                <el-descriptions-item label="关联策略">{{ detail.policy_name || detail.policy_id || '-' }}</el-descriptions-item>
   137|                <el-descriptions-item label="状态">
   138|                  <el-tag :type="dryRunStatusTag(detail.status)" size="small">
   139|                    {{ dryRunStatusLabel(detail.status) }}
   140|                  </el-tag>
   141|                </el-descriptions-item>
   142|                <el-descriptions-item label="触发时间">{{ formatTime(detail.triggered_at || detail.created_at) }}</el-descriptions-item>
   143|                <el-descriptions-item label="完成时间" v-if="detail.completed_at">
   144|                  {{ formatTime(detail.completed_at) }}
   145|                </el-descriptions-item>
   146|                <el-descriptions-item label="耗时" v-if="detail.duration">
   147|                  {{ detail.duration }}s
   148|                </el-descriptions-item>
   149|              </el-descriptions>
   150|
   151|              <!-- Step-by-step Execution Plan -->
   152|              <div class="section-title">执行计划模拟</div>
   153|              <div v-if="detail.steps && detail.steps.length" class="steps-container">
   154|                <div
   155|                  v-for="(step, index) in detail.steps"
   156|                  :key="index"
   157|                  class="step-item"
   158|                  :class="{ 'step-success': step.status === 'success', 'step-failed': step.status === 'failed', 'step-running': step.status === 'running', 'step-pending': step.status === 'pending' }"
   159|                >
   160|                  <div class="step-header">
   161|                    <div class="step-index">{{ index + 1 }}</div>
   162|                    <div class="step-info">
   163|                      <div class="step-name">{{ step.name || `步骤 ${index + 1}` }}</div>
   164|                      <div class="step-desc">{{ step.description || '-' }}</div>
   165|                    </div>
   166|                    <el-tag
   167|                      :type="dryRunStatusTag(step.status)"
   168|                      size="small"
   169|                      effect="light"
   170|                      style="margin-left: auto;"
   171|                    >
   172|                      {{ dryRunStatusLabel(step.status) }}
   173|                    </el-tag>
   174|                  </div>
   175|                  <div v-if="step.action" class="step-detail">
   176|                    <div class="step-detail-row">
   177|                      <span class="step-label">动作:</span>
   178|                      <span>{{ step.action }}</span>
   179|                    </div>
   180|                    <div v-if="step.target" class="step-detail-row">
   181|                      <span class="step-label">目标:</span>
   182|                      <span>{{ step.target }}</span>
   183|                    </div>
   184|                    <div v-if="step.result" class="step-detail-row">
   185|                      <span class="step-label">模拟结果:</span>
   186|                      <el-tag size="small" type="info">{{ step.result }}</el-tag>
   187|                    </div>
   188|                    <div v-if="step.message" class="step-detail-row">
   189|                      <span class="step-label">消息:</span>
   190|                      <span class="text-tertiary">{{ step.message }}</span>
   191|                    </div>
   192|                  </div>
   193|                </div>
   194|              </div>
   195|              <el-empty v-else description="暂无执行步骤数据" :image-size="60" />
   196|
   197|              <!-- Impact Analysis -->
   198|              <div class="section-title" style="margin-top: 20px;">影响分析</div>
   199|              <el-descriptions v-if="detail.impact" :column="1" border size="small">
   200|                <el-descriptions-item label="目标资源">
   201|                  {{ detail.impact.target || '-' }}
   202|                </el-descriptions-item>
   203|                <el-descriptions-item label="影响范围">
   204|                  <el-tag size="small" type="warning">{{ detail.impact.scope || '-' }}</el-tag>
   205|                </el-descriptions-item>
   206|                <el-descriptions-item label="风险等级">
   207|                  <el-tag :type="riskTagType(detail.impact.risk_level)" size="small">
   208|                    {{ riskLabel(detail.impact.risk_level) }}
   209|                  </el-tag>
   210|                </el-descriptions-item>
   211|                <el-descriptions-item label="预计变更">
   212|                  {{ detail.impact.changes || '-' }}
   213|                </el-descriptions-item>
   214|                <el-descriptions-item label="影响资产数" v-if="detail.impact.affected_count">
   215|                  {{ detail.impact.affected_count }}
   216|                </el-descriptions-item>
   217|              </el-descriptions>
   218|              <el-empty v-else description="暂无影响分析数据" :image-size="60" />
   219|
   220|              <!-- Error Info -->
   221|              <div v-if="detail.error" style="margin-top: 20px;">
   222|                <div class="section-title" style="color: #f53f3f;">错误信息</div>
   223|                <el-alert type="error" :title="detail.error" show-icon :closable="false" />
   224|              </div>
   225|            </template>
   226|          </div>
   227|        </el-card>
   228|      </el-col>
   229|    </el-row>
   230|  </div>
   231|</template>
   232|
   233|<script setup lang="ts">
   234|import { ref, reactive, onMounted } from 'vue'
   235|import { useRouter } from 'vue-router'
   236|import { ElMessage, ElMessageBox } from 'element-plus'
   237|import { ArrowLeft, Refresh, Search, Close } from '@element-plus/icons-vue'
   238|import { automationService } from '@/shared/api'
   239|import client from '@/shared/api/client'
   240|import { API } from '@/shared/api/routes'
   241|
   242|const router = useRouter()
   243|
   244|// ---------- Types ----------
   245|interface DryRunStep {
   246|  name?: string
   247|  description?: string
   248|  status: 'pending' | 'running' | 'success' | 'failed' | 'skipped'
   249|  action?: string
   250|  target?: string
   251|  result?: string
   252|  message?: string
   253|}
   254|
   255|interface DryRunImpact {
   256|  target?: string
   257|  scope?: string
   258|  risk_level?: 'high' | 'medium' | 'low'
   259|  changes?: string
   260|  affected_count?: number
   261|}
   262|
   263|interface DryRun {
   264|  id: string
   265|  name: string
   266|  policy_id?: string
   267|  policy_name?: string
   268|  status: 'pending' | 'running' | 'success' | 'failed' | 'cancelled'
   269|  triggered_at?: string
   270|  created_at?: string
   271|  completed_at?: string
   272|  duration?: number
   273|  steps?: DryRunStep[]
   274|  impact?: DryRunImpact
   275|  error?: string
   276|}
   277|
   278|// ---------- State ----------
   279|const loading = ref(false)
   280|const detailLoading = ref(false)
   281|const dryRuns = ref<DryRun[]>([])
   282|const detail = ref<DryRun | null>(null)
   283|const showDetail = ref(false)
   284|
   285|const searchKeyword = ref('')
   286|const filterStatus = ref('')
   287|
   288|const pagination = reactive({
   289|  page: 1,
   290|  page_size: 20,
   291|  total: 0,
   292|})
   293|
   294|// ---------- Helpers ----------
   295|function dryRunStatusTag(status?: string) {
   296|  const map: Record<string, string> = {
   297|    pending: 'info',
   298|    running: '',
   299|    success: 'success',
   300|    failed: 'danger',
   301|    cancelled: 'info',
   302|    skipped: 'warning',
   303|  }
   304|  return map[status || ''] || 'info'
   305|}
   306|
   307|function dryRunStatusLabel(status?: string) {
   308|  const map: Record<string, string> = {
   309|    pending: '等待中',
   310|    running: '运行中',
   311|    success: '成功',
   312|    failed: '失败',
   313|    cancelled: '已取消',
   314|    skipped: '已跳过',
   315|  }
   316|  return map[status || ''] || '未知'
   317|}
   318|
   319|function riskTagType(level?: string) {
   320|  const map: Record<string, string> = { high: 'danger', medium: 'warning', low: 'success' }
   321|  return map[level || ''] || 'info'
   322|}
   323|
   324|function riskLabel(level?: string) {
   325|  const map: Record<string, string> = { high: '高风险', medium: '中风险', low: '低风险' }
   326|  return map[level || ''] || '未知'
   327|}
   328|
   329|function formatTime(val?: string) {
   330|  if (!val) return '-'
   331|  return val.replace('T', ' ').substring(0, 19)
   332|}
   333|
   334|// ---------- Data Fetching ----------
   335|async function fetchDryRuns() {
   336|  loading.value = true
   337|  try {
   338|    const params: Record<string, any> = {
   339|      page: pagination.page,
   340|      page_size: pagination.page_size,
   341|    }
   342|    if (searchKeyword.value) params.keyword = searchKeyword.value
   343|    if (filterStatus.value) params.status = filterStatus.value
   344|
   345|    // Use direct API call since automationService doesn't have listDryRuns
   346|    const res = await client.get(API.AUTOMATION.DRY_RUN, { params })
   347|    const data = res.data?.data ?? res.data
   348|    if (Array.isArray(data?.items)) {
   349|      dryRuns.value = data.items
   350|      pagination.total = data.total ?? data.items.length
   351|    } else if (Array.isArray(data)) {
   352|      dryRuns.value = data
   353|      pagination.total = data.length
   354|    }
   355|  } catch (e: any) {
   356|    ElMessage.error(e.message || '获取预演列表失败')
   357|  } finally {
   358|    loading.value = false
   359|  }
   360|}
   361|
   362|// ---------- Search & Filter ----------
   363|function handleSearch() {
   364|  pagination.page = 1
   365|  fetchDryRuns()
   366|}
   367|
   368|function resetFilters() {
   369|  searchKeyword.value = ''
   370|  filterStatus.value = ''
   371|  handleSearch()
   372|}
   373|
   374|// ---------- Detail ----------
   375|function handleRowSelect(row: DryRun | null) {
   376|  if (row) loadDetail(row)
   377|}
   378|
   379|async function loadDetail(row: DryRun) {
   380|  detailLoading.value = true
   381|  showDetail.value = true
   382|  try {
   383|    const res = await automationService.getDryRunDetail(row.id)
   384|    const data = res.data?.data ?? res.data
   385|    detail.value = data && typeof data === 'object' ? data : row
   386|  } catch (e: any) {
   387|    // Fallback: use row data if API fails
   388|    detail.value = row
   389|    ElMessage.warning(e.message || '获取详情失败，显示本地数据')
   390|  } finally {
   391|    detailLoading.value = false
   392|  }
   393|}
   394|
   395|// ---------- Actions ----------
   396|async function handleDelete(row: DryRun) {
   397|  try {
   398|    await ElMessageBox.confirm(
   399|      `确认删除预演记录「${row.name}」？此操作不可撤销。`,
   400|      '删除确认',
   401|      { type: 'warning', confirmButtonText: '确定', cancelButtonText: '取消' }
   402|    )
   403|    await client.delete(API.AUTOMATION.DRY_RUN_DETAIL(row.id))
   404|    ElMessage.success('删除成功')
   405|    if (detail.value?.id === row.id) {
   406|      detail.value = null
   407|      showDetail.value = false
   408|    }
   409|    fetchDryRuns()
   410|  } catch (e: any) {
   411|    if (e !== 'cancel') {
   412|      ElMessage.error(e.message || '删除失败')
   413|    }
   414|  }
   415|}
   416|
   417|// ---------- Init ----------
   418|onMounted(() => {
   419|  fetchDryRuns()
   420|})
   421|</script>
   422|
   423|<style scoped>
   424|
   427|
   428|
   433|
   434|
   439|
   440|.table-card :deep(.el-card__body) {
   441|  padding: 16px;
   442|}
   443|
   444|.detail-card :deep(.el-card__body) {
   445|  padding: 16px;
   446|}
   447|
   448|.dryrun-name {
   449|  color: #165dff;
   450|  cursor: pointer;
   451|  font-weight: 500;
   452|}
   453|
   454|.dryrun-name:hover {
   455|  text-decoration: underline;
   456|}
   457|
   458|.text-tertiary {
   459|  color: #86909c;
   460|  font-size: 13px;
   461|}
   462|
   463|.pagination-wrap {
   464|  display: flex;
   465|  justify-content: flex-end;
   466|  padding: 12px 0 0;
   467|}
   468|
   469|.section-title {
   470|  font-size: 14px;
   471|  font-weight: 600;
   472|  color: #1d2129;
   473|  margin-bottom: 12px;
   474|}
   475|
   476|/* Step Items */
   477|.steps-container {
   478|  display: flex;
   479|  flex-direction: column;
   480|  gap: 8px;
   481|}
   482|
   483|.step-item {
   484|  border: 1px solid #e5e6eb;
   485|  border-radius: 6px;
   486|  padding: 12px;
   487|  transition: border-color 0.2s;
   488|}
   489|
   490|.step-item.step-success {
   491|  border-left: 3px solid #00b42a;
   492|}
   493|
   494|.step-item.step-failed {
   495|  border-left: 3px solid #f53f3f;
   496|}
   497|
   498|.step-item.step-running {
   499|  border-left: 3px solid #165dff;
   500|}
   501|