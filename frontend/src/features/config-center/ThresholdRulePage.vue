     1|<template>
     2|  <div class="page-container">
     3|    <div class="autops-page-header">
     4|      <div class="autops-page-title">阈值规则</div>
     5|      <el-button type="primary" @click="openCreateDialog">
     6|        <el-icon><Plus /></el-icon> 新建规则
     7|      </el-button>
     8|    </div>
     9|
    10|    <!-- Filters -->
    11|    <el-card class="mb-md">
    12|      <el-row :gutter="16">
    13|        <el-col :span="6">
    14|          <el-select v-model="filters.metric_name" placeholder="指标名称" clearable @change="fetchData">
    15|            <el-option v-for="m in metricOptions" :key="m" :label="m" :value="m" />
    16|          </el-select>
    17|        </el-col>
    18|        <el-col :span="6">
    19|          <el-select v-model="filters.severity" placeholder="严重级别" clearable @change="fetchData">
    20|            <el-option label="严重" value="critical" />
    21|            <el-option label="高" value="high" />
    22|            <el-option label="警告" value="warning" />
    23|            <el-option label="信息" value="info" />
    24|          </el-select>
    25|        </el-col>
    26|        <el-col :span="6">
    27|          <el-select v-model="filters.asset_type" placeholder="资产类型" clearable @change="fetchData">
    28|            <el-option label="Linux服务器" value="linux_server" />
    29|            <el-option label="Windows服务器" value="windows_server" />
    30|            <el-option label="数据库" value="database" />
    31|            <el-option label="Web服务" value="web_service" />
    32|          </el-select>
    33|        </el-col>
    34|        <el-col :span="6">
    35|          <el-select v-model="filters.enabled" placeholder="状态" clearable @change="fetchData">
    36|            <el-option label="启用" :value="true" />
    37|            <el-option label="禁用" :value="false" />
    38|          </el-select>
    39|        </el-col>
    40|      </el-row>
    41|    </el-card>
    42|
    43|    <!-- Table -->
    44|    <el-card v-loading="loading">
    45|      <el-table stripe :data="items"empty-text="暂无阈值规则" style="width: 100%">
    46|        <el-table-column prop="name" label="规则名称" min-width="160" show-overflow-tooltip />
    47|        <el-table-column prop="metric_name" label="指标" width="140" />
    48|        <el-table-column prop="asset_type" label="资产类型" width="120">
    49|          <template #default="{ row }">{{ row.asset_type || '全部' }}</template>
    50|        </el-table-column>
    51|        <el-table-column label="条件" width="160">
    52|          <template #default="{ row }">
    53|            {{ conditionText(row.condition) }} {{ row.threshold_value }}{{ metricUnit(row.metric_name) }}
    54|          </template>
    55|        </el-table-column>
    56|        <el-table-column prop="duration_seconds" label="持续时间" width="100">
    57|          <template #default="{ row }">{{ row.duration_seconds > 0 ? row.duration_seconds + '秒' : '即时' }}</template>
    58|        </el-table-column>
    59|        <el-table-column prop="severity" label="严重级别" width="100">
    60|          <template #default="{ row }">
    61|            <el-tag :type="severityTag(row.severity)" size="small">{{ severityText(row.severity) }}</el-tag>
    62|          </template>
    63|        </el-table-column>
    64|        <el-table-column prop="enabled" label="状态" width="80">
    65|          <template #default="{ row }">
    66|            <el-switch :model-value="row.enabled" @change="toggleRule(row)" />
    67|          </template>
    68|        </el-table-column>
    69|        <el-table-column label="操作" width="180" fixed="right">
    70|          <template #default="{ row }">
    71|            <el-button text type="primary" size="small" @click="openEditDialog(row)">编辑</el-button>
    72|            <el-popconfirm title="确定删除此规则？" @confirm="deleteRule(row)">
    73|              <template #reference>
    74|                <el-button text type="danger" size="small">删除</el-button>
    75|              </template>
    76|            </el-popconfirm>
    77|          </template>
    78|        </el-table-column>
    79|      </el-table>
    80|      <el-pagination
    81|        v-if="total > pageSize"
    82|        v-model:current-page="currentPage"
    83|        :page-size="pageSize"
    84|        :total="total"
    85|        layout="total, prev, pager, next"
    86|        style="margin-top: 16px; justify-content: flex-end"
    87|        @current-change="fetchData"
    88|      />
    89|    </el-card>
    90|
    91|    <!-- Create/Edit Dialog -->
    92|    <el-dialog v-model="dialogVisible" :title="editingRule ? '编辑规则' : '新建规则'" width="600px" destroy-on-close>
    93|      <el-form :model="formData" label-width="100px">
    94|        <el-form-item label="规则名称" required>
    95|          <el-input v-model="formData.name" placeholder="如：CPU高负载告警" />
    96|        </el-form-item>
    97|        <el-form-item label="指标名称" required>
    98|          <el-select v-model="formData.metric_name" placeholder="选择指标" style="width: 100%">
    99|            <el-option v-for="m in metricOptions" :key="m" :label="m" :value="m" />
   100|          </el-select>
   101|        </el-form-item>
   102|        <el-form-item label="资产类型">
   103|          <el-select v-model="formData.asset_type" placeholder="全部" clearable style="width: 100%">
   104|            <el-option label="Linux服务器" value="linux_server" />
   105|            <el-option label="Windows服务器" value="windows_server" />
   106|            <el-option label="数据库" value="database" />
   107|            <el-option label="Web服务" value="web_service" />
   108|          </el-select>
   109|        </el-form-item>
   110|        <el-row :gutter="16">
   111|          <el-col :span="12">
   112|            <el-form-item label="条件" required>
   113|              <el-select v-model="formData.condition" style="width: 100%">
   114|                <el-option label="大于 (>)" value="gt" />
   115|                <el-option label="大于等于 (>=)" value="gte" />
   116|                <el-option label="小于 (<)" value="lt" />
   117|                <el-option label="小于等于 (<=)" value="lte" />
   118|                <el-option label="等于 (=)" value="eq" />
   119|              </el-select>
   120|            </el-form-item>
   121|          </el-col>
   122|          <el-col :span="12">
   123|            <el-form-item label="阈值" required>
   124|              <el-input-number v-model="formData.threshold_value" :precision="1" :step="0.1" style="width: 100%" />
   125|            </el-form-item>
   126|          </el-col>
   127|        </el-row>
   128|        <el-form-item label="持续时间">
   129|          <el-input-number v-model="formData.duration_seconds" :min="0" :step="60" style="width: 100%" />
   130|          <div class="text-tertiary font-12" style="margin-top: 4px">0 表示即时触发</div>
   131|        </el-form-item>
   132|        <el-form-item label="严重级别" required>
   133|          <el-select v-model="formData.severity" style="width: 100%">
   134|            <el-option label="严重" value="critical" />
   135|            <el-option label="高" value="high" />
   136|            <el-option label="警告" value="warning" />
   137|            <el-option label="信息" value="info" />
   138|          </el-select>
   139|        </el-form-item>
   140|        <el-form-item label="描述">
   141|          <el-input v-model="formData.description" type="textarea" :rows="2" />
   142|        </el-form-item>
   143|      </el-form>
   144|      <template #footer>
   145|        <el-button @click="dialogVisible = false">取消</el-button>
   146|        <el-button type="primary" :loading="submitting" @click="submitForm">确定</el-button>
   147|      </template>
   148|    </el-dialog>
   149|  </div>
   150|</template>
   151|
   152|<script setup lang="ts">
   153|import { ref, reactive, onMounted } from 'vue'
   154|import { ElMessage } from 'element-plus'
   155|import { Plus } from '@element-plus/icons-vue'
   156|import { thresholdService } from '@/shared/api'
   157|
   158|const loading = ref(false)
   159|const items = ref<any[]>([])
   160|const total = ref(0)
   161|const currentPage = ref(1)
   162|const pageSize = 20
   163|
   164|const filters = reactive({ metric_name: '', severity: '', asset_type: '', enabled: null as boolean | null })
   165|
   166|const metricOptions = ['cpu_usage', 'memory_usage', 'disk_usage', 'disk_io', 'network_in', 'network_out', 'response_time', 'connection_count', 'process_count', 'load_avg']
   167|
   168|async function fetchData() {
   169|  loading.value = true
   170|  try {
   171|    const params: Record<string, any> = { page: currentPage.value, page_size: pageSize }
   172|    if (filters.metric_name) params.metric_name = filters.metric_name
   173|    if (filters.severity) params.severity = filters.severity
   174|    if (filters.asset_type) params.asset_type = filters.asset_type
   175|    if (filters.enabled !== null) params.enabled = filters.enabled
   176|
   177|    const resp = await thresholdService.list(params)
   178|    if (resp.data?.code === 0) {
   179|      items.value = resp.data.data?.items || []
   180|      total.value = resp.data.data?.total || 0
   181|    }
   182|  } catch (e) {
   183|    console.error('Failed to fetch threshold rules:', e)
   184|  } finally {
   185|    loading.value = false
   186|  }
   187|}
   188|
   189|const dialogVisible = ref(false)
   190|const editingRule = ref<any>(null)
   191|const submitting = ref(false)
   192|const formData = reactive({
   193|  name: '', metric_name: '', asset_type: '', condition: 'gt',
   194|  threshold_value: 90, duration_seconds: 0, severity: 'warning', description: '',
   195|})
   196|
   197|function openCreateDialog() {
   198|  editingRule.value = null
   199|  Object.assign(formData, { name: '', metric_name: '', asset_type: '', condition: 'gt', threshold_value: 90, duration_seconds: 0, severity: 'warning', description: '' })
   200|  dialogVisible.value = true
   201|}
   202|
   203|function openEditDialog(row: any) {
   204|  editingRule.value = row
   205|  Object.assign(formData, { name: row.name, metric_name: row.metric_name, asset_type: row.asset_type || '', condition: row.condition, threshold_value: row.threshold_value, duration_seconds: row.duration_seconds, severity: row.severity, description: row.description || '' })
   206|  dialogVisible.value = true
   207|}
   208|
   209|async function submitForm() {
   210|  if (!formData.name || !formData.metric_name) {
   211|    ElMessage.warning('请填写必填项')
   212|    return
   213|  }
   214|  submitting.value = true
   215|  try {
   216|    const data = { ...formData, asset_type: formData.asset_type || null }
   217|    if (editingRule.value) {
   218|      await thresholdService.update(editingRule.value.id, data)
   219|      ElMessage.success('规则已更新')
   220|    } else {
   221|      await thresholdService.create(data)
   222|      ElMessage.success('规则已创建')
   223|    }
   224|    dialogVisible.value = false
   225|    fetchData()
   226|  } catch (e) {
   227|    console.error('Submit failed:', e)
   228|    ElMessage.error('操作失败')
   229|  } finally {
   230|    submitting.value = false
   231|  }
   232|}
   233|
   234|async function toggleRule(row: any) {
   235|  try {
   236|    await thresholdService.toggle(row.id)
   237|    fetchData()
   238|  } catch { ElMessage.error('操作失败') }
   239|}
   240|
   241|async function deleteRule(row: any) {
   242|  try {
   243|    await thresholdService.delete(row.id)
   244|    ElMessage.success('已删除')
   245|    fetchData()
   246|  } catch { ElMessage.error('删除失败') }
   247|}
   248|
   249|function conditionText(c: string) {
   250|  const map: Record<string, string> = { gt: '>', gte: '>=', lt: '<', lte: '<=', eq: '=' }
   251|  return map[c] || c
   252|}
   253|
   254|function metricUnit(m: string) {
   255|  if (m.includes('usage') || m.includes('cpu') || m.includes('memory') || m.includes('disk_usage')) return '%'
   256|  if (m.includes('time')) return 'ms'
   257|  return ''
   258|}
   259|
   260|function severityText(s: string) {
   261|  const map: Record<string, string> = { critical: '严重', high: '高', warning: '警告', info: '信息' }
   262|  return map[s] || s
   263|}
   264|
   265|function severityTag(s: string) {
   266|  const map: Record<string, string> = { critical: 'danger', high: 'warning', warning: '', info: 'info' }
   267|  return map[s] || 'info'
   268|}
   269|
   270|onMounted(fetchData)
   271|</script>
   272|
   273|<style scoped>
   274|
   275|.mb-md { margin-bottom: 16px; }
   276|.text-tertiary { color: #86909c; }
   277|.font-12 { font-size: 12px; }
   278|</style>
   279|