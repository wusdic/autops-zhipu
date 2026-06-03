     1|<template>
     2|  <div class="page-container">
     3|    <div class="autops-page-header">
     4|      <div class="autops-page-title">通知规则</div>
     5|      <div class="autops-page-desc">配置告警和事件的通知规则和发送渠道</div>
     6|    </div>
     7|    <div style="display: flex; justify-content: flex-end; margin-bottom: 16px">
     8|      <el-button type="primary" @click="openCreateDialog">
     9|        <el-icon><Plus /></el-icon> 新建规则
    10|      </el-button>
    11|    </div>
    12|
    13|    <!-- Filters -->
    14|    <el-card class="mb-md">
    15|      <el-row :gutter="16">
    16|        <el-col :span="8">
    17|          <el-select v-model="filters.event_type" placeholder="事件类型" clearable @change="fetchData">
    18|            <el-option v-for="e in eventTypes" :key="e" :label="e" :value="e" />
    19|          </el-select>
    20|        </el-col>
    21|        <el-col :span="8">
    22|          <el-select v-model="filters.target_type" placeholder="目标类型" clearable @change="fetchData">
    23|            <el-option label="用户" value="user" />
    24|            <el-option label="角色" value="role" />
    25|            <el-option label="渠道" value="channel" />
    26|          </el-select>
    27|        </el-col>
    28|        <el-col :span="8">
    29|          <el-select v-model="filters.enabled" placeholder="状态" clearable @change="fetchData">
    30|            <el-option label="启用" :value="true" />
    31|            <el-option label="禁用" :value="false" />
    32|          </el-select>
    33|        </el-col>
    34|      </el-row>
    35|    </el-card>
    36|
    37|    <!-- Table -->
    38|    <el-card v-loading="loading">
    39|      <el-table stripe :data="items"empty-text="暂无通知规则" style="width: 100%">
    40|        <el-table-column prop="name" label="规则名称" min-width="160" show-overflow-tooltip />
    41|        <el-table-column prop="event_type" label="事件类型" width="180" show-overflow-tooltip />
    42|        <el-table-column prop="target_type" label="目标类型" width="100">
    43|          <template #default="{ row }">
    44|            <el-tag size="small" :type="row.target_type === 'user' ? '' : row.target_type === 'role' ? 'warning' : 'info'">
    45|              {{ targetText(row.target_type) }}
    46|            </el-tag>
    47|          </template>
    48|        </el-table-column>
    49|        <el-table-column label="通知渠道" width="200">
    50|          <template #default="{ row }">
    51|            <template v-if="row.channels">
    52|              <el-tag v-for="ch in parseJSON(row.channels)" :key="ch" size="small" type="info" style="margin: 2px">{{ ch }}</el-tag>
    53|            </template>
    54|          </template>
    55|        </el-table-column>
    56|        <el-table-column prop="severity_filter" label="严重级别过滤" width="140">
    57|          <template #default="{ row }">{{ row.severity_filter || '全部' }}</template>
    58|        </el-table-column>
    59|        <el-table-column label="静默时段" width="140">
    60|          <template #default="{ row }">
    61|            {{ row.quiet_hours_start && row.quiet_hours_end ? row.quiet_hours_start + '-' + row.quiet_hours_end : '无' }}
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
    95|          <el-input v-model="formData.name" placeholder="如：严重告警通知" />
    96|        </el-form-item>
    97|        <el-form-item label="事件类型" required>
    98|          <el-select v-model="formData.event_type" placeholder="选择事件类型" style="width: 100%" filterable>
    99|            <el-option v-for="e in eventTypes" :key="e" :label="e" :value="e" />
   100|          </el-select>
   101|        </el-form-item>
   102|        <el-form-item label="目标类型" required>
   103|          <el-radio-group v-model="formData.target_type">
   104|            <el-radio value="user">用户</el-radio>
   105|            <el-radio value="role">角色</el-radio>
   106|            <el-radio value="channel">渠道</el-radio>
   107|          </el-radio-group>
   108|        </el-form-item>
   109|        <el-form-item label="目标ID" required>
   110|          <el-input v-model="formData.target_ids" placeholder='如：["user-id-1","user-id-2"]' />
   111|        </el-form-item>
   112|        <el-form-item label="通知渠道" required>
   113|          <el-checkbox-group v-model="selectedChannels">
   114|            <el-checkbox value="in_app">站内</el-checkbox>
   115|            <el-checkbox value="email">邮件</el-checkbox>
   116|            <el-checkbox value="sms">短信</el-checkbox>
   117|            <el-checkbox value="webhook">Webhook</el-checkbox>
   118|          </el-checkbox-group>
   119|        </el-form-item>
   120|        <el-form-item label="严重级别过滤">
   121|          <el-input v-model="formData.severity_filter" placeholder='如：["critical","high"] 留空=全部' />
   122|        </el-form-item>
   123|        <el-row :gutter="16">
   124|          <el-col :span="12">
   125|            <el-form-item label="静默开始">
   126|              <el-time-select v-model="formData.quiet_hours_start" start="00:00" step="00:30" end="23:30" placeholder="开始时间" />
   127|            </el-form-item>
   128|          </el-col>
   129|          <el-col :span="12">
   130|            <el-form-item label="静默结束">
   131|              <el-time-select v-model="formData.quiet_hours_end" start="00:00" step="00:30" end="23:30" placeholder="结束时间" />
   132|            </el-form-item>
   133|          </el-col>
   134|        </el-row>
   135|        <el-form-item label="描述">
   136|          <el-input v-model="formData.description" type="textarea" :rows="2" />
   137|        </el-form-item>
   138|      </el-form>
   139|      <template #footer>
   140|        <el-button @click="dialogVisible = false">取消</el-button>
   141|        <el-button type="primary" :loading="submitting" @click="submitForm">确定</el-button>
   142|      </template>
   143|    </el-dialog>
   144|  </div>
   145|</template>
   146|
   147|<script setup lang="ts">
   148|import { ref, reactive, onMounted } from 'vue'
   149|import { ElMessage } from 'element-plus'
   150|import { Plus } from '@element-plus/icons-vue'
   151|import { notificationRuleService } from '@/shared/api'
   152|
   153|const loading = ref(false)
   154|const items = ref<any[]>([])
   155|const total = ref(0)
   156|const currentPage = ref(1)
   157|const pageSize = 20
   158|
   159|const filters = reactive({ event_type: '', target_type: '', enabled: null as boolean | null })
   160|
   161|const eventTypes = [
   162|  'alert.created', 'alert.escalated', 'alert.resolved',
   163|  'execution.completed', 'execution.failed', 'execution.approval_required',
   164|  'ticket.created', 'ticket.assigned', 'ticket.closed',
   165|  'anomaly.detected', 'inspection.completed', 'inspection.failed',
   166|  'discovery.completed', 'knowledge.created',
   167|]
   168|
   169|async function fetchData() {
   170|  loading.value = true
   171|  try {
   172|    const params: Record<string, any> = { page: currentPage.value, page_size: pageSize }
   173|    if (filters.event_type) params.event_type = filters.event_type
   174|    if (filters.target_type) params.target_type = filters.target_type
   175|    if (filters.enabled !== null) params.enabled = filters.enabled
   176|
   177|    const resp = await notificationRuleService.list(params)
   178|    if (resp.data?.code === 0) {
   179|      items.value = resp.data.data?.items || []
   180|      total.value = resp.data.data?.total || 0
   181|    }
   182|  } catch (e) {
   183|    console.error('Failed to fetch notification rules:', e)
   184|  } finally {
   185|    loading.value = false
   186|  }
   187|}
   188|
   189|const dialogVisible = ref(false)
   190|const editingRule = ref<any>(null)
   191|const submitting = ref(false)
   192|const selectedChannels = ref<string[]>(['in_app'])
   193|const formData = reactive({
   194|  name: '', event_type: '', target_type: 'user', target_ids: '[]',
   195|  channels: '["in_app"]', severity_filter: '', quiet_hours_start: '', quiet_hours_end: '', description: '',
   196|})
   197|
   198|function openCreateDialog() {
   199|  editingRule.value = null
   200|  Object.assign(formData, { name: '', event_type: '', target_type: 'user', target_ids: '[]', channels: '["in_app"]', severity_filter: '', quiet_hours_start: '', quiet_hours_end: '', description: '' })
   201|  selectedChannels.value = ['in_app']
   202|  dialogVisible.value = true
   203|}
   204|
   205|function openEditDialog(row: any) {
   206|  editingRule.value = row
   207|  Object.assign(formData, { name: row.name, event_type: row.event_type, target_type: row.target_type, target_ids: row.target_ids, channels: row.channels, severity_filter: row.severity_filter || '', quiet_hours_start: row.quiet_hours_start || '', quiet_hours_end: row.quiet_hours_end || '', description: row.description || '' })
   208|  selectedChannels.value = parseJSON(row.channels)
   209|  dialogVisible.value = true
   210|}
   211|
   212|async function submitForm() {
   213|  if (!formData.name || !formData.event_type) {
   214|    ElMessage.warning('请填写必填项')
   215|    return
   216|  }
   217|  submitting.value = true
   218|  try {
   219|    const data = { ...formData, channels: JSON.stringify(selectedChannels.value) }
   220|    if (editingRule.value) {
   221|      await notificationRuleService.update(editingRule.value.id, data)
   222|      ElMessage.success('规则已更新')
   223|    } else {
   224|      await notificationRuleService.create(data)
   225|      ElMessage.success('规则已创建')
   226|    }
   227|    dialogVisible.value = false
   228|    fetchData()
   229|  } catch (e) {
   230|    console.error('Submit failed:', e)
   231|    ElMessage.error('操作失败')
   232|  } finally {
   233|    submitting.value = false
   234|  }
   235|}
   236|
   237|async function toggleRule(row: any) {
   238|  try {
   239|    await notificationRuleService.toggle(row.id)
   240|    fetchData()
   241|  } catch { ElMessage.error('操作失败') }
   242|}
   243|
   244|async function deleteRule(row: any) {
   245|  try {
   246|    await notificationRuleService.delete(row.id)
   247|    ElMessage.success('已删除')
   248|    fetchData()
   249|  } catch { ElMessage.error('删除失败') }
   250|}
   251|
   252|function targetText(t: string) {
   253|  const map: Record<string, string> = { user: '用户', role: '角色', channel: '渠道' }
   254|  return map[t] || t
   255|}
   256|
   257|function parseJSON(s: string): string[] {
   258|  try { return JSON.parse(s) } catch { return [] }
   259|}
   260|
   261|onMounted(fetchData)
   262|</script>
   263|
   264|<style scoped>
   265|
   266|.mb-md { margin-bottom: 16px; }
   267|</style>
   268|