     1|<template>
     2|  <div class="page-container">
     3|    <div class="autops-page-header">
     4|      <h2>巡检详情</h2>
     5|      <div>
     6|        <el-button @click="goBack"><el-icon><ArrowLeft /></el-icon> 返回</el-button>
     7|        <el-button type="primary" @click="rerunInspection" :loading="rerunning"><el-icon><Refresh /></el-icon> 重新巡检</el-button>
     8|      </div>
     9|    </div>
    10|
    11|    <div v-loading="loading">
    12|      <!-- 基本信息 -->
    13|      <div class="autops-card" style="margin-bottom: 16px">
    14|        <el-descriptions :column="3" border>
    15|          <el-descriptions-item label="巡检任务ID">{{ taskDetail?.id?.slice(0, 8) || '-' }}</el-descriptions-item>
    16|          <el-descriptions-item label="巡检模板">{{ taskDetail?.template_name || taskDetail?.inspection_type || '-' }}</el-descriptions-item>
    17|          <el-descriptions-item label="状态">
    18|            <el-tag :type="statusTag(taskDetail?.status)" effect="dark">{{ statusLabel(taskDetail?.status) }}</el-tag>
    19|          </el-descriptions-item>
    20|          <el-descriptions-item label="资产数量">{{ taskDetail?.asset_count || taskDetail?.target_assets?.length || 0 }}</el-descriptions-item>
    21|          <el-descriptions-item label="开始时间">{{ formatTime(taskDetail?.started_at) }}</el-descriptions-item>
    22|          <el-descriptions-item label="完成时间">{{ formatTime(taskDetail?.completed_at) }}</el-descriptions-item>
    23|          <el-descriptions-item label="巡检类型">{{ typeLabel(taskDetail?.inspection_type) }}</el-descriptions-item>
    24|          <el-descriptions-item label="创建人">{{ taskDetail?.created_by || 'system' }}</el-descriptions-item>
    25|          <el-descriptions-item label="耗时">{{ taskDetail?.duration || '-' }}</el-descriptions-item>
    26|        </el-descriptions>
    27|      </div>
    28|
    29|      <!-- 结果概要 -->
    30|      <el-row :gutter="16" style="margin-bottom: 16px">
    31|        <el-col :xs="12" :sm="6" v-for="stat in resultStats" :key="stat.label">
    32|          <div class="autops-metric-card">
    33|            <div class="metric-label">{{ stat.label }}</div>
    34|            <div class="metric-value" :style="{ color: stat.color }">{{ stat.value }}</div>
    35|          </div>
    36|        </el-col>
    37|      </el-row>
    38|
    39|      <!-- 巡检项明细 -->
    40|      <div class="autops-card" style="margin-bottom: 16px">
    41|        <div class="autops-card-header">
    42|          <div class="autops-card-title">巡检项明细</div>
    43|          <div>
    44|            <el-select v-model="resultFilter" placeholder="结果筛选" style="width: 120px" clearable>
    45|              <el-option label="通过" value="pass" />
    46|              <el-option label="失败" value="fail" />
    47|              <el-option label="警告" value="warning" />
    48|              <el-option label="跳过" value="skip" />
    49|            </el-select>
    50|          </div>
    51|        </div>
    52|        <el-table stripe :data="filteredResults"class="autops-table" @expand-change="handleExpand">
    53|          <el-table-column type="expand">
    54|            <template #default="{ row }">
    55|              <div style="padding: 12px 24px">
    56|                <h4>详细结果</h4>
    57|                <el-descriptions :column="2" border size="small">
    58|                  <el-descriptions-item label="检查项">{{ row.check_item }}</el-descriptions-item>
    59|                  <el-descriptions-item label="实际值">{{ row.actual_value || '-' }}</el-descriptions-item>
    60|                  <el-descriptions-item label="期望值">{{ row.expected_value || '-' }}</el-descriptions-item>
    61|                  <el-descriptions-item label="差异说明">{{ row.diff_description || '-' }}</el-descriptions-item>
    62|                </el-descriptions>
    63|                <div v-if="row.recommendation" style="margin-top: 8px">
    64|                  <el-alert type="info" :closable="false"><strong>建议:</strong> {{ row.recommendation }}</el-alert>
    65|                </div>
    66|              </div>
    67|            </template>
    68|          </el-table-column>
    69|          <el-table-column prop="asset_name" label="资产" min-width="140" show-overflow-tooltip />
    70|          <el-table-column prop="check_item" label="检查项" min-width="160" show-overflow-tooltip />
    71|          <el-table-column prop="module" label="模块" width="100">
    72|            <template #default="{ row }">
    73|              <el-tag size="small">{{ row.module || '-' }}</el-tag>
    74|            </template>
    75|          </el-table-column>
    76|          <el-table-column prop="result" label="结果" width="80">
    77|            <template #default="{ row }">
    78|              <el-tag :type="resultTag(row.result)" size="small">{{ resultLabel(row.result) }}</el-tag>
    79|            </template>
    80|          </el-table-column>
    81|          <el-table-column prop="severity" label="严重度" width="80">
    82|            <template #default="{ row }">
    83|              <el-tag v-if="row.result === 'fail'" :type="severityTag(row.severity)" size="small">{{ row.severity || '-' }}</el-tag>
    84|              <span v-else>-</span>
    85|            </template>
    86|          </el-table-column>
    87|          <el-table-column prop="message" label="信息" min-width="200" show-overflow-tooltip />
    88|          <el-table-column label="操作" width="100" fixed="right">
    89|            <template #default="{ row }">
    90|              <el-button v-if="row.result === 'fail'" link type="warning" @click="navToAnomalyFromInspection(taskDetail?.id)">报异常</el-button>
    91|            </template>
    92|          </el-table-column>
    93|        </el-table>
    94|      </div>
    95|
    96|      <!-- 工作流操作 -->
    97|      <div class="autops-card">
    98|        <div class="autops-card-header"><div class="autops-card-title">后续操作</div></div>
    99|        <div style="display: flex; gap: 8px; padding: 12px">
   100|          <el-button type="warning" @click="navToAnomalyFromInspection(taskDetail?.id)">
   101|            <el-icon><Warning /></el-icon> 查看异常项
   102|          </el-button>
   103|          <el-button type="primary" @click="navToReportFromInspection(taskDetail?.id)">
   104|            <el-icon><Document /></el-icon> 生成报告
   105|          </el-button>
   106|        </div>
   107|      </div>
   108|    </div>
   109|  </div>
   110|</template>
   111|
   112|<script setup lang="ts">
   113|import { ref, computed, onMounted } from 'vue'
   114|import { useRoute, useRouter } from 'vue-router'
   115|import { ArrowLeft, Refresh, Warning, Document } from '@element-plus/icons-vue'
   116|import { ElMessage } from 'element-plus'
   117|import api from '@/shared/api'
   118|import { routes as API } from '@/shared/api/routes'
   119|import { useWorkflowNav } from '@/shared/composables/useWorkflowNav'
   120|
   121|const route = useRoute()
   122|const router = useRouter()
   123|const { navToAnomalyFromInspection, navToReportFromInspection } = useWorkflowNav()
   124|
   125|const loading = ref(false)
   126|const rerunning = ref(false)
   127|const taskDetail = ref<any>(null)
   128|const checkResults = ref<any[]>([])
   129|const resultFilter = ref('')
   130|
   131|const taskId = computed(() => route.params.id as string || route.query.task_id as string)
   132|
   133|const resultStats = computed(() => {
   134|  const all = checkResults.value
   135|  return [
   136|    { label: '检查项总数', value: all.length, color: '#165dff' },
   137|    { label: '通过', value: all.filter(r => r.result === 'pass').length, color: '#00b42a' },
   138|    { label: '失败', value: all.filter(r => r.result === 'fail').length, color: '#f53f3f' },
   139|    { label: '警告', value: all.filter(r => r.result === 'warning').length, color: '#ff7d00' },
   140|  ]
   141|})
   142|
   143|const filteredResults = computed(() => {
   144|  if (!resultFilter.value) return checkResults.value
   145|  return checkResults.value.filter(r => r.result === resultFilter.value)
   146|})
   147|
   148|async function fetchDetail() {
   149|  if (!taskId.value) return
   150|  loading.value = true
   151|  try {
   152|    const res = await api.get(`${API.INSPECTION_TASKS}/${taskId.value}`)
   153|    const data = res.data
   154|    if (data?.code === 0) {
   155|      taskDetail.value = data.data
   156|      // Build check results from task detail
   157|      const items = data.data?.items || data.data?.check_results || []
   158|      checkResults.value = items.map((r: any) => ({
   159|        ...r,
   160|        asset_name: r.asset_name || r.asset?.name || '-',
   161|        check_item: r.check_item || r.name || r.item_name || '-',
   162|        result: r.result || r.status || 'pass',
   163|        message: r.message || r.description || '',
   164|        module: r.module || r.category || '-',
   165|      }))
   166|    }
   167|  } catch (e) {
   168|    ElMessage.error('获取巡检详情失败')
   169|  } finally {
   170|    loading.value = false
   171|  }
   172|}
   173|
   174|async function rerunInspection() {
   175|  rerunning.value = true
   176|  try {
   177|    await api.post(API.INSPECTION_TASKS, { template_id: taskDetail.value?.template_id, asset_ids: taskDetail.value?.target_assets })
   178|    ElMessage.success('已触发重新巡检')
   179|  } catch (e) {
   180|    ElMessage.error('触发失败')
   181|  } finally {
   182|    rerunning.value = false
   183|  }
   184|}
   185|
   186|function handleExpand(row: any) { /* expanded */ }
   187|
   188|function goBack() { router.back() }
   189|
   190|function statusTag(s: string) {
   191|  const map: Record<string, string> = { running: 'warning', completed: 'success', failed: 'danger', pending: 'info' }
   192|  return map[s] || 'info'
   193|}
   194|function statusLabel(s: string) {
   195|  const map: Record<string, string> = { running: '执行中', completed: '已完成', failed: '失败', pending: '待执行' }
   196|  return map[s] || s || '-'
   197|}
   198|function resultTag(r: string) {
   199|  const map: Record<string, string> = { pass: 'success', fail: 'danger', warning: 'warning', skip: 'info' }
   200|  return map[r] || 'info'
   201|}
   202|function resultLabel(r: string) {
   203|  const map: Record<string, string> = { pass: '通过', fail: '失败', warning: '警告', skip: '跳过' }
   204|  return map[r] || r || '-'
   205|}
   206|function severityTag(s: string) {
   207|  const map: Record<string, string> = { critical: 'danger', high: 'danger', medium: 'warning', low: 'info' }
   208|  return map[s] || 'info'
   209|}
   210|function typeLabel(t: string) {
   211|  const map: Record<string, string> = { page: '页面巡检', log: '日志巡检', config: '配置巡检', performance: '性能巡检', security: '安全巡检', baseline: '基线巡检' }
   212|  return map[t] || t || '-'
   213|}
   214|function formatTime(t: string) {
   215|  return t ? new Date(t).toLocaleString('zh-CN') : '-'
   216|}
   217|
   218|onMounted(fetchDetail)
   219|</script>
   220|
   221|<style scoped>
   222|
   223|
   224|
   225|
   226|</style>
   227|