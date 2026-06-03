     1|<template>
     2|  <div class="page-container">
     3|    <!-- Page Header -->
     4|    <div class="autops-page-header">
     5|      <div class="autops-page-title">审批中心</div>
     6|      <div class="autops-page-desc">审批自动化执行请求，管控操作风险</div>
     7|    </div>
     8|
     9|    <!-- Status Tabs -->
    10|    <el-card shadow="never" class="tabs-card">
    11|      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
    12|        <el-tab-pane label="全部" name="all" />
    13|        <el-tab-pane name="pending">
    14|          <template #label>
    15|            <span>待审批 <el-badge v-if="pendingCount > 0" :value="pendingCount" class="tab-badge" /></span>
    16|          </template>
    17|        </el-tab-pane>
    18|        <el-tab-pane label="已批准" name="approved" />
    19|        <el-tab-pane label="已拒绝" name="rejected" />
    20|      </el-tabs>
    21|
    22|      <!-- Filter Row -->
    23|      <el-row :gutter="16" align="middle" style="margin-bottom: 16px;">
    24|        <el-col :span="6">
    25|          <el-input
    26|            v-model="searchKeyword"
    27|            placeholder="搜索请求名称、请求人..."
    28|            clearable
    29|            @keyup.enter="handleSearch"
    30|            @clear="handleSearch"
    31|          >
    32|            <template #prefix>
    33|              <el-icon><Search /></el-icon>
    34|            </template>
    35|          </el-input>
    36|        </el-col>
    37|        <el-col :span="4">
    38|          <el-select v-model="filterRisk" placeholder="风险等级" clearable @change="handleSearch">
    39|            <el-option label="高风险" value="high" />
    40|            <el-option label="中风险" value="medium" />
    41|            <el-option label="低风险" value="low" />
    42|          </el-select>
    43|        </el-col>
    44|        <el-col :span="4">
    45|          <el-select v-model="filterType" placeholder="请求类型" clearable @change="handleSearch">
    46|            <el-option label="脚本执行" value="script" />
    47|            <el-option label="Playbook 执行" value="playbook" />
    48|            <el-option label="配置变更" value="config" />
    49|            <el-option label="巡检任务" value="inspection" />
    50|          </el-select>
    51|        </el-col>
    52|        <el-col :span="4">
    53|          <el-button type="primary" @click="handleSearch">查询</el-button>
    54|          <el-button @click="resetFilters">重置</el-button>
    55|        </el-col>
    56|      </el-row>
    57|
    58|      <!-- Data Table -->
    59|      <el-table stripe
 60| :data="approvals"
 61|62| v-loading="loading"
 63| empty-text="暂无审批记录"
 64| @sort-change="handleSortChange"
 65| >
    66|        <el-table-column prop="name" label="请求名称" min-width="180" show-overflow-tooltip>
    67|          <template #default="{ row }">
    68|            <span class="request-name" @click="viewDetail(row)">{{ row.name || row.title || '-' }}</span>
    69|          </template>
    70|        </el-table-column>
    71|        <el-table-column prop="type" label="类型" width="120">
    72|          <template #default="{ row }">
    73|            <el-tag size="small" effect="plain">{{ typeLabel(row.type || row.execution_type) }}</el-tag>
    74|          </template>
    75|        </el-table-column>
    76|        <el-table-column prop="risk_level" label="风险等级" width="100" align="center">
    77|          <template #default="{ row }">
    78|            <el-tag :type="riskTagType(row.risk_level)" size="small" effect="light">
    79|              {{ riskLabel(row.risk_level) }}
    80|            </el-tag>
    81|          </template>
    82|        </el-table-column>
    83|        <el-table-column prop="requester" label="请求人" width="110">
    84|          <template #default="{ row }">
    85|            {{ row.requester || row.applicant || row.created_by || '-' }}
    86|          </template>
    87|        </el-table-column>
    88|        <el-table-column prop="reason" label="原因" min-width="160" show-overflow-tooltip>
    89|          <template #default="{ row }">
    90|            <span class="text-tertiary">{{ row.reason || row.description || '-' }}</span>
    91|          </template>
    92|        </el-table-column>
    93|        <el-table-column prop="created_at" label="请求时间" width="170" sortable="custom">
    94|          <template #default="{ row }">
    95|            <span class="text-tertiary">{{ formatTime(row.created_at) }}</span>
    96|          </template>
    97|        </el-table-column>
    98|        <el-table-column prop="status" label="状态" width="100" align="center">
    99|          <template #default="{ row }">
   100|            <el-tag :type="statusTagType(row.status)" size="small" effect="light">
   101|              {{ statusLabel(row.status) }}
   102|            </el-tag>
   103|          </template>
   104|        </el-table-column>
   105|        <el-table-column label="操作" width="180" fixed="right" align="center">
   106|          <template #default="{ row }">
   107|            <template v-if="row.status === 'pending'">
   108|              <el-button text type="success" size="small" @click="openActionDialog(row, 'approve')">
   109|                批准
   110|              </el-button>
   111|              <el-button text type="danger" size="small" @click="openActionDialog(row, 'reject')">
   112|                拒绝
   113|              </el-button>
   114|            </template>
   115|            <template v-else>
   116|              <el-button text type="primary" size="small" @click="viewDetail(row)">查看</el-button>
   117|            </template>
   118|          </template>
   119|        </el-table-column>
   120|      </el-table>
   121|
   122|      <!-- Pagination -->
   123|      <div class="pagination-wrap">
   124|        <el-pagination
   125|          v-model:current-page="pagination.page"
   126|          v-model:page-size="pagination.page_size"
   127|          :total="pagination.total"
   128|          :page-sizes="[10, 20, 50, 100]"
   129|          layout="total, sizes, prev, pager, next, jumper"
   130|          background
   131|          @size-change="fetchApprovals"
   132|          @current-change="fetchApprovals"
   133|        />
   134|      </div>
   135|    </el-card>
   136|
   137|    <!-- Approve / Reject Dialog -->
   138|    <el-dialog
   139|      v-model="actionDialogVisible"
   140|      :title="actionType === 'approve' ? '批准请求' : '拒绝请求'"
   141|      width="600px"
   142|      :close-on-click-modal="false"
   143|      @closed="resetActionForm"
   144|    >
   145|      <div class="action-dialog-content">
   146|        <el-descriptions :column="1" border size="small" style="margin-bottom: 16px;">
   147|          <el-descriptions-item label="请求名称">{{ currentAction?.name || currentAction?.title || '-' }}</el-descriptions-item>
   148|          <el-descriptions-item label="类型">{{ typeLabel(currentAction?.type || currentAction?.execution_type) }}</el-descriptions-item>
   149|          <el-descriptions-item label="风险等级">
   150|            <el-tag :type="riskTagType(currentAction?.risk_level)" size="small">
   151|              {{ riskLabel(currentAction?.risk_level) }}
   152|            </el-tag>
   153|          </el-descriptions-item>
   154|          <el-descriptions-item label="请求人">{{ currentAction?.requester || currentAction?.applicant || '-' }}</el-descriptions-item>
   155|        </el-descriptions>
   156|
   157|        <el-form label-position="top">
   158|          <el-form-item :label="actionType === 'approve' ? '批准备注（可选）' : '拒绝原因'">
   159|            <el-input
   160|              v-model="actionComment"
   161|              type="textarea"
   162|              :rows="4"
   163|              :placeholder="actionType === 'approve' ? '请输入批准备注...' : '请输入拒绝原因...'"
   164|              maxlength="256"
   165|              show-word-limit
   166|            />
   167|          </el-form-item>
   168|        </el-form>
   169|      </div>
   170|
   171|      <template #footer>
   172|        <el-button @click="actionDialogVisible = false">取消</el-button>
   173|        <el-button
   174|          :type="actionType === 'approve' ? 'success' : 'danger'"
   175|          :loading="actionSubmitting"
   176|          @click="submitAction"
   177|        >
   178|          {{ actionType === 'approve' ? '确认批准' : '确认拒绝' }}
   179|        </el-button>
   180|      </template>
   181|    </el-dialog>
   182|
   183|    <!-- Detail Drawer -->
   184|    <el-drawer v-model="drawerVisible" title="审批详情" size="520px">
   185|      <template v-if="currentDetail">
   186|        <el-descriptions :column="1" border>
   187|          <el-descriptions-item label="请求名称">{{ currentDetail.name || currentDetail.title || '-' }}</el-descriptions-item>
   188|          <el-descriptions-item label="类型">{{ typeLabel(currentDetail.type || currentDetail.execution_type) }}</el-descriptions-item>
   189|          <el-descriptions-item label="风险等级">
   190|            <el-tag :type="riskTagType(currentDetail.risk_level)" size="small">
   191|              {{ riskLabel(currentDetail.risk_level) }}
   192|            </el-tag>
   193|          </el-descriptions-item>
   194|          <el-descriptions-item label="状态">
   195|            <el-tag :type="statusTagType(currentDetail.status)" size="small">
   196|              {{ statusLabel(currentDetail.status) }}
   197|            </el-tag>
   198|          </el-descriptions-item>
   199|          <el-descriptions-item label="请求人">{{ currentDetail.requester || currentDetail.applicant || '-' }}</el-descriptions-item>
   200|          <el-descriptions-item label="请求时间">{{ formatTime(currentDetail.created_at) }}</el-descriptions-item>
   201|          <el-descriptions-item label="原因/说明">{{ currentDetail.reason || currentDetail.description || '-' }}</el-descriptions-item>
   202|          <el-descriptions-item label="审批人" v-if="currentDetail.reviewer">{{ currentDetail.reviewer }}</el-descriptions-item>
   203|          <el-descriptions-item label="审批时间" v-if="currentDetail.reviewed_at">{{ formatTime(currentDetail.reviewed_at) }}</el-descriptions-item>
   204|          <el-descriptions-item label="审批备注" v-if="currentDetail.comment">{{ currentDetail.comment }}</el-descriptions-item>
   205|        </el-descriptions>
   206|
   207|        <!-- Execution Targets -->
   208|        <div v-if="currentDetail.targets && currentDetail.targets.length" style="margin-top: 20px;">
   209|          <div class="section-title">执行目标</div>
   210|          <el-table stripe  :data="currentDetail.targets" size="small" border>
   211|            <el-table-column prop="name" label="名称" min-width="120" />
   212|            <el-table-column prop="type" label="类型" width="100" />
   213|            <el-table-column prop="action" label="操作" width="180" />
   214|          </el-table>
   215|        </div>
   216|
   217|        <!-- Quick Actions for Pending -->
   218|        <div v-if="currentDetail.status === 'pending'" style="margin-top: 24px; display: flex; gap: 12px;">
   219|          <el-button type="success" @click="openActionDialog(currentDetail, 'approve'); drawerVisible = false">
   220|            批准
   221|          </el-button>
   222|          <el-button type="danger" @click="openActionDialog(currentDetail, 'reject'); drawerVisible = false">
   223|            拒绝
   224|          </el-button>
   225|        </div>
   226|      </template>
   227|    </el-drawer>
   228|  </div>
   229|</template>
   230|
   231|<script setup lang="ts">
   232|import { ref, reactive, computed, onMounted } from 'vue'
   233|import { ElMessage } from 'element-plus'
   234|import { Search } from '@element-plus/icons-vue'
   235|import { automationService } from '@/shared/api'
   236|
   237|// ---------- Types ----------
   238|interface Approval {
   239|  id: string
   240|  name?: string
   241|  title?: string
   242|  type?: string
   243|  execution_type?: string
   244|  risk_level: 'high' | 'medium' | 'low'
   245|  status: 'pending' | 'approved' | 'rejected'
   246|  requester?: string
   247|  applicant?: string
   248|  created_by?: string
   249|  reason?: string
   250|  description?: string
   251|  created_at: string
   252|  reviewed_at?: string
   253|  reviewer?: string
   254|  comment?: string
   255|  targets?: Array<{ name: string; type: string; action: string }>
   256|}
   257|
   258|// ---------- State ----------
   259|const loading = ref(false)
   260|const actionSubmitting = ref(false)
   261|const approvals = ref<Approval[]>([])
   262|const activeTab = ref('all')
   263|
   264|const drawerVisible = ref(false)
   265|const currentDetail = ref<Approval | null>(null)
   266|
   267|const actionDialogVisible = ref(false)
   268|const actionType = ref<'approve' | 'reject'>('approve')
   269|const currentAction = ref<Approval | null>(null)
   270|const actionComment = ref('')
   271|
   272|const searchKeyword = ref('')
   273|const filterRisk = ref('')
   274|const filterType = ref('')
   275|const sortField = ref('')
   276|const sortOrder = ref('')
   277|
   278|const pagination = reactive({
   279|  page: 1,
   280|  page_size: 20,
   281|  total: 0,
   282|})
   283|
   284|// ---------- Computed ----------
   285|const pendingCount = computed(() => approvals.value.filter(a => a.status === 'pending').length)
   286|
   287|// ---------- Label Helpers ----------
   288|function typeLabel(type?: string) {
   289|  const map: Record<string, string> = {
   290|    script: '脚本执行',
   291|    playbook: 'Playbook 执行',
   292|    config: '配置变更',
   293|    inspection: '巡检任务',
   294|  }
   295|  return map[type || ''] || type || '-'
   296|}
   297|
   298|function riskTagType(level?: string) {
   299|  const map: Record<string, string> = { high: 'danger', medium: 'warning', low: 'success' }
   300|  return map[level || ''] || 'info'
   301|}
   302|
   303|function riskLabel(level?: string) {
   304|  const map: Record<string, string> = { high: '高风险', medium: '中风险', low: '低风险' }
   305|  return map[level || ''] || '未知'
   306|}
   307|
   308|function statusTagType(status?: string) {
   309|  const map: Record<string, string> = { pending: 'warning', approved: 'success', rejected: 'danger' }
   310|  return map[status || ''] || 'info'
   311|}
   312|
   313|function statusLabel(status?: string) {
   314|  const map: Record<string, string> = { pending: '待审批', approved: '已批准', rejected: '已拒绝' }
   315|  return map[status || ''] || '未知'
   316|}
   317|
   318|function formatTime(val?: string) {
   319|  if (!val) return '-'
   320|  return val.replace('T', ' ').substring(0, 19)
   321|}
   322|
   323|// ---------- Data Fetching ----------
   324|async function fetchApprovals() {
   325|  loading.value = true
   326|  try {
   327|    const params: Record<string, any> = {
   328|      page: pagination.page,
   329|      page_size: pagination.page_size,
   330|    }
   331|    if (activeTab.value !== 'all') params.status = activeTab.value
   332|    if (searchKeyword.value) params.keyword = searchKeyword.value
   333|    if (filterRisk.value) params.risk_level = filterRisk.value
   334|    if (filterType.value) params.type = filterType.value
   335|    if (sortField.value) {
   336|      params.sort_by = sortField.value
   337|      params.sort_order = sortOrder.value
   338|    }
   339|
   340|    const res = await automationService.listApprovals(params)
   341|    const data = res.data?.data ?? res.data
   342|    if (Array.isArray(data?.items)) {
   343|      approvals.value = data.items
   344|      pagination.total = data.total ?? data.items.length
   345|    } else if (Array.isArray(data)) {
   346|      approvals.value = data
   347|      pagination.total = data.length
   348|    }
   349|  } catch (e: any) {
   350|    ElMessage.error(e.message || '获取审批列表失败')
   351|  } finally {
   352|    loading.value = false
   353|  }
   354|}
   355|
   356|// ---------- Search & Filter ----------
   357|function handleTabChange() {
   358|  pagination.page = 1
   359|  fetchApprovals()
   360|}
   361|
   362|function handleSearch() {
   363|  pagination.page = 1
   364|  fetchApprovals()
   365|}
   366|
   367|function resetFilters() {
   368|  searchKeyword.value = ''
   369|  filterRisk.value = ''
   370|  filterType.value = ''
   371|  sortField.value = ''
   372|  sortOrder.value = ''
   373|  handleSearch()
   374|}
   375|
   376|function handleSortChange({ prop, order }: any) {
   377|  sortField.value = prop || ''
   378|  sortOrder.value = order === 'ascending' ? 'asc' : order === 'descending' ? 'desc' : ''
   379|  fetchApprovals()
   380|}
   381|
   382|// ---------- Detail ----------
   383|function viewDetail(row: Approval) {
   384|  currentDetail.value = row
   385|  drawerVisible.value = true
   386|}
   387|
   388|// ---------- Approve / Reject ----------
   389|function openActionDialog(row: Approval, type: 'approve' | 'reject') {
   390|  currentAction.value = row
   391|  actionType.value = type
   392|  actionComment.value = ''
   393|  actionDialogVisible.value = true
   394|}
   395|
   396|function resetActionForm() {
   397|  actionComment.value = ''
   398|  currentAction.value = null
   399|}
   400|
   401|async function submitAction() {
   402|  if (!currentAction.value) return
   403|
   404|  if (actionType.value === 'reject' && !actionComment.value.trim()) {
   405|    ElMessage.warning('请填写拒绝原因')
   406|    return
   407|  }
   408|
   409|  actionSubmitting.value = true
   410|  try {
   411|    if (actionType.value === 'approve') {
   412|      await automationService.approve(currentAction.value.id, {
   413|        approved: true,
   414|        comment: actionComment.value,
   415|      })
   416|      ElMessage.success('已批准')
   417|    } else {
   418|      await automationService.reject(currentAction.value.id, {
   419|        comment: actionComment.value,
   420|      })
   421|      ElMessage.success('已拒绝')
   422|    }
   423|    actionDialogVisible.value = false
   424|    fetchApprovals()
   425|  } catch (e: any) {
   426|    ElMessage.error(e.message || '操作失败')
   427|  } finally {
   428|    actionSubmitting.value = false
   429|  }
   430|}
   431|
   432|// ---------- Init ----------
   433|onMounted(() => {
   434|  fetchApprovals()
   435|})
   436|</script>
   437|
   438|<style scoped>
   439|
   442|
   443|.tabs-card :deep(.el-card__body) {
   444|  padding: 16px 20px;
   445|}
   446|
   447|.request-name {
   448|  color: #165dff;
   449|  cursor: pointer;
   450|  font-weight: 500;
   451|}
   452|
   453|.request-name:hover {
   454|  text-decoration: underline;
   455|}
   456|
   457|.text-tertiary {
   458|  color: #86909c;
   459|  font-size: 13px;
   460|}
   461|
   462|.pagination-wrap {
   463|  display: flex;
   464|  justify-content: flex-end;
   465|  padding: 16px 0 0;
   466|}
   467|
   468|.tab-badge {
   469|  margin-left: 4px;
   470|}
   471|
   472|.tab-badge :deep(.el-badge__content) {
   473|  top: -2px;
   474|}
   475|
   476|.action-dialog-content {
   477|  padding: 0 4px;
   478|}
   479|
   480|.section-title {
   481|  font-size: 14px;
   482|  font-weight: 600;
   483|  color: #1d2129;
   484|  margin-bottom: 12px;
   485|}
   486|</style>
   487|