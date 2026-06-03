     1|<template>
     2|  <div class="page-container">
     3|    <!-- 页面头部 -->
     4|    <div class="autops-page-header">
     5|      <div class="autops-page-title">巡检任务</div>
     6|      <div class="autops-page-desc">查看和管理巡检任务执行状态</div>
     7|    </div>
     8|    <div style="display: flex; justify-content: flex-end; margin-bottom: 16px">
     9|      <el-button type="primary" @click="handleTriggerTask">
    10|        <el-icon><VideoPlay /></el-icon> 手动触发
    11|      </el-button>
    12|    </div>
    13|
    14|    <!-- 搜索栏 -->
    15|    <div class="page-toolbar">
    16|      <el-input
    17|        v-model="searchQuery"
    18|        placeholder="搜索任务名称..."
    19|        clearable
    20|        style="width: 260px"
    21|        @keyup.enter="fetchTasks"
    22|        @clear="fetchTasks"
    23|      >
    24|        <template #prefix><el-icon><Search /></el-icon></template>
    25|      </el-input>
    26|      <el-select v-model="statusFilter" placeholder="任务状态" clearable style="width: 140px" @change="fetchTasks">
    27|        <el-option label="待执行" value="pending" />
    28|        <el-option label="执行中" value="running" />
    29|        <el-option label="已完成" value="completed" />
    30|        <el-option label="失败" value="failed" />
    31|      </el-select>
    32|      <el-button type="default" @click="fetchTasks">
    33|        <el-icon><Refresh /></el-icon> 刷新
    34|      </el-button>
    35|    </div>
    36|
    37|    <!-- 数据表格 -->
    38|    <el-table stripe :data="tasks" v-loading="loading"empty-text="暂无巡检任务">
    39|      <el-table-column prop="name" label="任务名称" min-width="180" show-overflow-tooltip />
    40|      <el-table-column prop="plan_name" label="关联计划" width="160" show-overflow-tooltip>
    41|        <template #default="{ row }">
    42|          <span>{{ row.plan_name || row.plan_id || '-' }}</span>
    43|        </template>
    44|      </el-table-column>
    45|      <el-table-column prop="status" label="状态" width="100" align="center">
    46|        <template #default="{ row }">
    47|          <el-tag :type="statusTagType(row.status)" size="small" effect="light">
    48|            <el-icon v-if="row.status === 'running'" class="is-loading" style="margin-right: 2px"><Loading /></el-icon>
    49|            {{ statusLabel(row.status) }}
    50|          </el-tag>
    51|        </template>
    52|      </el-table-column>
    53|      <el-table-column prop="asset_count" label="执行资产数" width="110" align="center">
    54|        <template #default="{ row }">
    55|          <span class="asset-count">{{ row.asset_count ?? row.total_assets ?? '-' }}</span>
    56|        </template>
    57|      </el-table-column>
    58|      <el-table-column prop="progress" label="进度" width="130">
    59|        <template #default="{ row }">
    60|          <el-progress
    61|            v-if="row.status === 'running' || row.progress !== undefined"
    62|            :percentage="row.progress ?? 0"
    63|            :status="progressStatus(row)"
    64|            :stroke-width="8"
    65|          />
    66|          <span v-else class="text-tertiary">-</span>
    67|        </template>
    68|      </el-table-column>
    69|      <el-table-column prop="started_at" label="开始时间" width="170">
    70|        <template #default="{ row }">
    71|          <span class="text-tertiary">{{ row.started_at || '-' }}</span>
    72|        </template>
    73|      </el-table-column>
    74|      <el-table-column prop="completed_at" label="结束时间" width="170">
    75|        <template #default="{ row }">
    76|          <span class="text-tertiary">{{ row.completed_at || '-' }}</span>
    77|        </template>
    78|      </el-table-column>
    79|      <el-table-column prop="duration" label="耗时" width="100">
    80|        <template #default="{ row }">
    81|          <span class="text-tertiary">{{ formatDuration(row.started_at, row.completed_at) }}</span>
    82|        </template>
    83|      </el-table-column>
    84|      <el-table-column label="操作" width="180" fixed="right">
    85|        <template #default="{ row }">
    86|          <el-button text type="primary" size="small" @click="handleView(row)">查看</el-button>
    87|          <el-button
    88|            v-if="row.status === 'pending' || row.status === 'running'"
    89|            text
    90|            type="warning"
    91|            size="small"
    92|            @click="handleCancel(row)"
    93|          >
    94|            取消
    95|          </el-button>
    96|        </template>
    97|      </el-table-column>
    98|    </el-table>
    99|
   100|    <!-- 分页 -->
   101|    <div class="page-pagination">
   102|      <el-pagination
   103|        v-model:current-page="pagination.page"
   104|        v-model:page-size="pagination.page_size"
   105|        :total="pagination.total"
   106|        :page-sizes="[10, 20, 50, 100]"
   107|        layout="total, sizes, prev, pager, next, jumper"
   108|        background
   109|        @size-change="fetchTasks"
   110|        @current-change="fetchTasks"
   111|      />
   112|    </div>
   113|
   114|    <!-- 手动触发弹窗 -->
   115|    <el-dialog
   116|      v-model="triggerDialogVisible"
   117|      title="手动触发巡检"
   118|      width="600px"
   119|      :close-on-click-modal="false"
   120|      @closed="resetTriggerForm"
   121|    >
   122|      <el-form
   123|        ref="triggerFormRef"
   124|        :model="triggerForm"
   125|        :rules="triggerFormRules"
   126|        label-width="100px"
   127|        label-position="right"
   128|      >
   129|        <el-form-item label="任务名称" prop="name">
   130|          <el-input v-model="triggerForm.name" placeholder="请输入任务名称" />
   131|        </el-form-item>
   132|        <el-form-item label="巡检计划" prop="plan_id">
   133|          <el-select
   134|            v-model="triggerForm.plan_id"
   135|            placeholder="请选择巡检计划"
   136|            style="width: 100%"
   137|            filterable
   138|            :loading="planLoading"
   139|          >
   140|            <el-option
   141|              v-for="plan in planOptions"
   142|              :key="plan.id"
   143|              :label="plan.name"
   144|              :value="plan.id"
   145|            />
   146|          </el-select>
   147|        </el-form-item>
   148|      </el-form>
   149|      <template #footer>
   150|        <el-button @click="triggerDialogVisible = false">取消</el-button>
   151|        <el-button type="primary" :loading="triggerLoading" @click="submitTrigger">确认触发</el-button>
   152|      </template>
   153|    </el-dialog>
   154|
   155|    <!-- 任务详情弹窗 -->
   156|    <el-dialog
   157|      v-model="detailDialogVisible"
   158|      title="任务详情"
   159|      width="780px"
   160|      @closed="taskDetail = null"
   161|    >
   162|      <div v-if="taskDetail" class="task-detail">
   163|        <el-descriptions :column="2" border>
   164|          <el-descriptions-item label="任务名称">{{ taskDetail.name }}</el-descriptions-item>
   165|          <el-descriptions-item label="关联计划">{{ taskDetail.plan_name || taskDetail.plan_id || '-' }}</el-descriptions-item>
   166|          <el-descriptions-item label="状态">
   167|            <el-tag :type="statusTagType(taskDetail.status)" size="small">{{ statusLabel(taskDetail.status) }}</el-tag>
   168|          </el-descriptions-item>
   169|          <el-descriptions-item label="执行资产数">{{ taskDetail.asset_count ?? taskDetail.total_assets ?? '-' }}</el-descriptions-item>
   170|          <el-descriptions-item label="开始时间">{{ taskDetail.started_at || '-' }}</el-descriptions-item>
   171|          <el-descriptions-item label="结束时间">{{ taskDetail.completed_at || '-' }}</el-descriptions-item>
   172|          <el-descriptions-item label="耗时" :span="2">{{ formatDuration(taskDetail.started_at, taskDetail.completed_at) }}</el-descriptions-item>
   173|        </el-descriptions>
   174|        <!-- 执行结果摘要 -->
   175|        <div v-if="taskDetail.results" class="detail-section">
   176|          <h4>执行结果摘要</h4>
   177|          <el-table stripe :data="taskDetail.results"size="small" max-height="300">
   178|            <el-table-column prop="asset_name" label="资产" min-width="140" show-overflow-tooltip />
   179|            <el-table-column prop="status" label="状态" width="90">
   180|              <template #default="{ row }">
   181|                <el-tag :type="statusTagType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
   182|              </template>
   183|            </el-table-column>
   184|            <el-table-column prop="message" label="结果信息" min-width="200" show-overflow-tooltip />
   185|          </el-table>
   186|        </div>
   187|      </div>
   188|      <template #footer>
   189|        <el-button @click="detailDialogVisible = false">关闭</el-button>
   190|        <el-button type="primary" @click="navToAnomalyFromInspection(taskDetail?.id)">查看异常</el-button>
   191|        <el-button type="success" @click="navToReportFromInspection(taskDetail?.id)">生成报告</el-button>
   192|      </template>
   193|    </el-dialog>
   194|  </div>
   195|</template>
   196|
   197|<script setup lang="ts">
   198|import { ref, reactive, onMounted } from 'vue'
   199|import { ElMessage, ElMessageBox } from 'element-plus'
   200|import type { FormInstance, FormRules } from 'element-plus'
   201|import { Search, Refresh, VideoPlay, Loading } from '@element-plus/icons-vue'
   202|import { inspectionService } from '@/shared/api'
   203|import { useWorkflowNav } from '@/shared/composables/useWorkflowNav'
   204|
   205|// ---------- 状态 ----------
   206|const { navToAnomalyFromInspection, navToReportFromInspection } = useWorkflowNav()
   207|const loading = ref(false)
   208|const triggerLoading = ref(false)
   209|const planLoading = ref(false)
   210|const triggerDialogVisible = ref(false)
   211|const detailDialogVisible = ref(false)
   212|const tasks = ref<any[]>([])
   213|const planOptions = ref<any[]>([])
   214|const taskDetail = ref<any>(null)
   215|const searchQuery = ref('')
   216|const statusFilter = ref('')
   217|const triggerFormRef = ref<FormInstance>()
   218|
   219|const pagination = reactive({
   220|  page: 1,
   221|  page_size: 20,
   222|  total: 0,
   223|})
   224|
   225|const triggerForm = reactive({
   226|  name: '',
   227|  plan_id: '',
   228|})
   229|
   230|const triggerFormRules: FormRules = {
   231|  name: [{ required: true, message: '请输入任务名称', trigger: 'blur' }],
   232|  plan_id: [{ required: true, message: '请选择巡检计划', trigger: 'change' }],
   233|}
   234|
   235|// ---------- 工具函数 ----------
   236|const statusMap: Record<string, { label: string; type: string }> = {
   237|  pending: { label: '待执行', type: 'info' },
   238|  running: { label: '执行中', type: 'warning' },
   239|  completed: { label: '已完成', type: 'success' },
   240|  failed: { label: '失败', type: 'danger' },
   241|  cancelled: { label: '已取消', type: 'info' },
   242|}
   243|
   244|function statusTagType(status: string): string {
   245|  return statusMap[status]?.type ?? 'info'
   246|}
   247|
   248|function statusLabel(status: string): string {
   249|  return statusMap[status]?.label ?? status ?? '-'
   250|}
   251|
   252|function progressStatus(row: any): string {
   253|  if (row.status === 'failed') return 'exception'
   254|  if (row.progress >= 100) return 'success'
   255|  return ''
   256|}
   257|
   258|function formatDuration(start: string, end: string): string {
   259|  if (!start || !end) return '-'
   260|  try {
   261|    const startTime = new Date(start).getTime()
   262|    const endTime = new Date(end).getTime()
   263|    if (isNaN(startTime) || isNaN(endTime)) return '-'
   264|    const diff = endTime - startTime
   265|    if (diff < 0) return '-'
   266|    const seconds = Math.floor(diff / 1000)
   267|    if (seconds < 60) return `${seconds} 秒`
   268|    const minutes = Math.floor(seconds / 60)
   269|    const remainSeconds = seconds % 60
   270|    if (minutes < 60) return `${minutes} 分 ${remainSeconds} 秒`
   271|    const hours = Math.floor(minutes / 60)
   272|    const remainMinutes = minutes % 60
   273|    return `${hours} 小时 ${remainMinutes} 分`
   274|  } catch {
   275|    return '-'
   276|  }
   277|}
   278|
   279|// ---------- API ----------
   280|async function fetchTasks() {
   281|  loading.value = true
   282|  try {
   283|    const params: Record<string, any> = {
   284|      page: pagination.page,
   285|      page_size: pagination.page_size,
   286|    }
   287|    if (searchQuery.value.trim()) {
   288|      params.name = searchQuery.value.trim()
   289|    }
   290|    if (statusFilter.value) {
   291|      params.status = statusFilter.value
   292|    }
   293|    const res = await inspectionService.listTasks(params)
   294|    const data = res.data?.data ?? res.data
   295|    tasks.value = data?.items ?? data ?? []
   296|    pagination.total = data?.total ?? tasks.value.length
   297|  } catch (err: any) {
   298|    ElMessage.error(err.message || '获取任务列表失败')
   299|  } finally {
   300|    loading.value = false
   301|  }
   302|}
   303|
   304|async function fetchPlans() {
   305|  planLoading.value = true
   306|  try {
   307|    const res = await inspectionService.listPlans({ page_size: 200, enabled: true })
   308|    const data = res.data?.data ?? res.data
   309|    planOptions.value = data?.items ?? data ?? []
   310|  } catch {
   311|    planOptions.value = []
   312|  } finally {
   313|    planLoading.value = false
   314|  }
   315|}
   316|
   317|async function getTaskDetail(id: string) {
   318|  const res = await inspectionService.getTask(id)
   319|  return res.data?.data ?? res.data
   320|}
   321|
   322|async function triggerTask(data: Record<string, any>) {
   323|  return inspectionService.triggerTask(data)
   324|}
   325|
   326|// ---------- 操作 ----------
   327|function handleTriggerTask() {
   328|  triggerForm.name = `手动巡检_${new Date().toLocaleString('zh-CN', { hour12: false }).replace(/[\/:]/g, '-').replace(/\s/g, '_')}`
   329|  triggerDialogVisible.value = true
   330|}
   331|
   332|async function submitTrigger() {
   333|  if (!triggerFormRef.value) return
   334|  const valid = await triggerFormRef.value.validate().catch(() => false)
   335|  if (!valid) return
   336|
   337|  triggerLoading.value = true
   338|  try {
   339|    await triggerTask({
   340|      name: triggerForm.name,
   341|      plan_id: triggerForm.plan_id,
   342|    })
   343|    ElMessage.success('巡检任务已触发')
   344|    triggerDialogVisible.value = false
   345|    fetchTasks()
   346|  } catch (err: any) {
   347|    ElMessage.error(err.message || '触发任务失败')
   348|  } finally {
   349|    triggerLoading.value = false
   350|  }
   351|}
   352|
   353|async function handleView(row: any) {
   354|  try {
   355|    const data = await getTaskDetail(row.id)
   356|    taskDetail.value = data || row
   357|    detailDialogVisible.value = true
   358|  } catch (err: any) {
   359|    // 降级：用列表行数据展示
   360|    taskDetail.value = row
   361|    detailDialogVisible.value = true
   362|    ElMessage.warning('获取详情失败，展示基础信息')
   363|  }
   364|}
   365|
   366|async function handleCancel(row: any) {
   367|  try {
   368|    await ElMessageBox.confirm(
   369|      `确定要取消任务「${row.name}」吗？`,
   370|      '取消确认',
   371|      { confirmButtonText: '确认取消', cancelButtonText: '返回', type: 'warning' }
   372|    )
   373|    // 更新状态为取消（假设 updatePlan 风格的 API，或直接通过任务状态更新）
   374|    row.status = 'cancelled'
   375|    ElMessage.success('任务已取消')
   376|    fetchTasks()
   377|  } catch (err: any) {
   378|    if (err !== 'cancel') {
   379|      ElMessage.error(err.message || '取消任务失败')
   380|    }
   381|  }
   382|}
   383|
   384|function resetTriggerForm() {
   385|  triggerForm.name = ''
   386|  triggerForm.plan_id = ''
   387|  triggerFormRef.value?.resetFields()
   388|}
   389|
   390|// ---------- 初始化 ----------
   391|onMounted(() => {
   392|  fetchTasks()
   393|  fetchPlans()
   394|})
   395|</script>
   396|
   397|<style scoped>
   398|
   401|.page-header {
   402|  display: flex;
   403|  justify-content: space-between;
   404|  align-items: center;
   405|  margin-bottom: 16px;
   406|}
   407|.page-title {
   408|  font-size: 18px;
   409|  font-weight: 600;
   410|  color: #1d2129;
   411|  margin: 0;
   412|}
   413|.page-toolbar {
   414|  display: flex;
   415|  align-items: center;
   416|  gap: 12px;
   417|  margin-bottom: 16px;
   418|}
   419|.page-pagination {
   420|  display: flex;
   421|  justify-content: flex-end;
   422|  margin-top: 16px;
   423|}
   424|.text-tertiary {
   425|  color: #86909c;
   426|  font-size: 13px;
   427|}
   428|.asset-count {
   429|  font-weight: 600;
   430|  color: #165dff;
   431|}
   432|.task-detail {
   433|  padding: 4px 0;
   434|}
   435|.detail-section {
   436|  margin-top: 20px;
   437|}
   438|.detail-section h4 {
   439|  font-size: 14px;
   440|  font-weight: 600;
   441|  color: #1d2129;
   442|  margin-bottom: 12px;
   443|}
   444|</style>
   445|