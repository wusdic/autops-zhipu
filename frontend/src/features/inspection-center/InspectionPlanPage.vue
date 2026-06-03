     1|<template>
     2|  <div class="page-container">
     3|    <!-- 页面头部 -->
     4|    <div class="autops-page-header">
     5|      <div class="autops-page-title">巡检计划</div>
     6|      <div class="autops-page-desc">创建和管理巡检计划，设置调度周期</div>
     7|    </div>
     8|    <div style="display: flex; justify-content: flex-end; margin-bottom: 16px">
     9|      <el-button type="primary" @click="handleCreate">
    10|        <el-icon><Plus /></el-icon> 新建计划
    11|      </el-button>
    12|    </div>
    13|
    14|    <!-- 搜索栏 -->
    15|    <div class="page-toolbar">
    16|      <el-input
    17|        v-model="searchQuery"
    18|        placeholder="搜索计划名称..."
    19|        clearable
    20|        style="width: 260px"
    21|        @keyup.enter="fetchPlans"
    22|        @clear="fetchPlans"
    23|      >
    24|        <template #prefix><el-icon><Search /></el-icon></template>
    25|      </el-input>
    26|      <el-select v-model="enabledFilter" placeholder="状态筛选" clearable style="width: 130px" @change="fetchPlans">
    27|        <el-option label="已启用" :value="true" />
    28|        <el-option label="已禁用" :value="false" />
    29|      </el-select>
    30|      <el-button type="default" @click="fetchPlans">
    31|        <el-icon><Refresh /></el-icon> 刷新
    32|      </el-button>
    33|    </div>
    34|
    35|    <!-- 数据表格 -->
    36|    <el-table stripe :data="plans" v-loading="loading"empty-text="暂无巡检计划">
    37|      <el-table-column prop="name" label="计划名称" min-width="180" show-overflow-tooltip />
    38|      <el-table-column prop="template_name" label="关联模板" width="160" show-overflow-tooltip>
    39|        <template #default="{ row }">
    40|          <span>{{ row.template_name || getTemplateName(row.template_id) }}</span>
    41|        </template>
    42|      </el-table-column>
    43|      <el-table-column prop="cron" label="执行周期" width="140">
    44|        <template #default="{ row }">
    45|          <span class="cron-text">{{ row.cron }}</span>
    46|        </template>
    47|      </el-table-column>
    48|      <el-table-column prop="cron_description" label="周期说明" width="130">
    49|        <template #default="{ row }">
    50|          <span class="text-tertiary">{{ row.cron_description || parseCron(row.cron) }}</span>
    51|        </template>
    52|      </el-table-column>
    53|      <el-table-column prop="next_run" label="下次执行" width="170">
    54|        <template #default="{ row }">
    55|          <span class="text-tertiary">{{ row.next_run || '-' }}</span>
    56|        </template>
    57|      </el-table-column>
    58|      <el-table-column prop="enabled" label="状态" width="90" align="center">
    59|        <template #default="{ row }">
    60|          <el-tag :type="row.enabled ? 'success' : 'info'" size="small">
    61|            {{ row.enabled ? '已启用' : '已禁用' }}
    62|          </el-tag>
    63|        </template>
    64|      </el-table-column>
    65|      <el-table-column prop="created_at" label="创建时间" width="170">
    66|        <template #default="{ row }">
    67|          <span class="text-tertiary">{{ row.created_at || '-' }}</span>
    68|        </template>
    69|      </el-table-column>
    70|      <el-table-column label="操作" width="180" fixed="right">
    71|        <template #default="{ row }">
    72|          <el-button text type="primary" size="small" @click="handleEdit(row)">编辑</el-button>
    73|          <el-button text type="danger" size="small" @click="handleDelete(row)">删除</el-button>
    74|        </template>
    75|      </el-table-column>
    76|    </el-table>
    77|
    78|    <!-- 分页 -->
    79|    <div class="page-pagination">
    80|      <el-pagination
    81|        v-model:current-page="pagination.page"
    82|        v-model:page-size="pagination.page_size"
    83|        :total="pagination.total"
    84|        :page-sizes="[10, 20, 50, 100]"
    85|        layout="total, sizes, prev, pager, next, jumper"
    86|        background
    87|        @size-change="fetchPlans"
    88|        @current-change="fetchPlans"
    89|      />
    90|    </div>
    91|
    92|    <!-- 新建/编辑弹窗 -->
    93|    <el-dialog
    94|      v-model="dialogVisible"
    95|      :title="isEditing ? '编辑计划' : '新建计划'"
    96|      width="600px"
    97|      :close-on-click-modal="false"
    98|      @closed="resetForm"
    99|    >
   100|      <el-form
   101|        ref="formRef"
   102|        :model="form"
   103|        :rules="formRules"
   104|        label-width="100px"
   105|        label-position="right"
   106|      >
   107|        <el-form-item label="计划名称" prop="name">
   108|          <el-input v-model="form.name" placeholder="请输入计划名称" maxlength="100" show-word-limit />
   109|        </el-form-item>
   110|        <el-form-item label="关联模板" prop="template_id">
   111|          <el-select
   112|            v-model="form.template_id"
   113|            placeholder="请选择巡检模板"
   114|            style="width: 100%"
   115|            filterable
   116|            :loading="templateLoading"
   117|          >
   118|            <el-option
   119|              v-for="tpl in templateOptions"
   120|              :key="tpl.id"
   121|              :label="tpl.name"
   122|              :value="tpl.id"
   123|            />
   124|          </el-select>
   125|        </el-form-item>
   126|        <el-form-item label="执行周期" prop="cron">
   127|          <el-input v-model="form.cron" placeholder="Cron 表达式，如: 0 8 * * *">
   128|            <template #append>
   129|              <el-tooltip content="Cron 表达式格式: 分 时 日 月 周&#10;示例:&#10;0 8 * * * 每天 8:00&#10;0 */2 * * * 每 2 小时&#10;0 0 * * 1 每周一 0:00" placement="top">
   130|                <el-icon><QuestionFilled /></el-icon>
   131|              </el-tooltip>
   132|            </template>
   133|          </el-input>
   134|        </el-form-item>
   135|        <el-form-item label="周期预览">
   136|          <span class="cron-preview">{{ parseCron(form.cron) || '请输入 Cron 表达式' }}</span>
   137|        </el-form-item>
   138|        <el-form-item label="是否启用" prop="enabled">
   139|          <el-switch v-model="form.enabled" active-text="启用" inactive-text="禁用" />
   140|        </el-form-item>
   141|        <el-form-item label="描述">
   142|          <el-input
   143|            v-model="form.description"
   144|            type="textarea"
   145|            :rows="3"
   146|            placeholder="请输入计划描述（可选）"
   147|            maxlength="500"
   148|            show-word-limit
   149|          />
   150|        </el-form-item>
   151|      </el-form>
   152|      <template #footer>
   153|        <el-button @click="dialogVisible = false">取消</el-button>
   154|        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">确定</el-button>
   155|      </template>
   156|    </el-dialog>
   157|  </div>
   158|</template>
   159|
   160|<script setup lang="ts">
   161|import { ref, reactive, onMounted } from 'vue'
   162|import { ElMessage, ElMessageBox } from 'element-plus'
   163|import type { FormInstance, FormRules } from 'element-plus'
   164|import { Plus, Search, Refresh, QuestionFilled } from '@element-plus/icons-vue'
   165|import { inspectionService } from '@/shared/api'
   166|
   167|// ---------- 状态 ----------
   168|const loading = ref(false)
   169|const submitLoading = ref(false)
   170|const templateLoading = ref(false)
   171|const dialogVisible = ref(false)
   172|const isEditing = ref(false)
   173|const editingId = ref<string>('')
   174|const plans = ref<any[]>([])
   175|const searchQuery = ref('')
   176|const enabledFilter = ref<boolean | string>('')
   177|const templateOptions = ref<any[]>([])
   178|const formRef = ref<FormInstance>()
   179|
   180|const pagination = reactive({
   181|  page: 1,
   182|  page_size: 20,
   183|  total: 0,
   184|})
   185|
   186|const form = reactive({
   187|  name: '',
   188|  template_id: '',
   189|  cron: '0 8 * * *',
   190|  enabled: true,
   191|  description: '',
   192|})
   193|
   194|const formRules: FormRules = {
   195|  name: [{ required: true, message: '请输入计划名称', trigger: 'blur' }],
   196|  template_id: [{ required: true, message: '请选择关联模板', trigger: 'change' }],
   197|  cron: [{ required: true, message: '请输入 Cron 表达式', trigger: 'blur' }],
   198|}
   199|
   200|// ---------- 工具函数 ----------
   201|function getTemplateName(templateId: string) {
   202|  if (!templateId) return '-'
   203|  const tpl = templateOptions.value.find(t => t.id === templateId)
   204|  return tpl ? tpl.name : templateId
   205|}
   206|
   207|function parseCron(cron: string) {
   208|  if (!cron) return ''
   209|  const parts = cron.trim().split(/\s+/)
   210|  if (parts.length < 5) return '无效表达式'
   211|
   212|  const [minute, hour, dayOfMonth, month, dayOfWeek] = parts
   213|
   214|  // 每天
   215|  if (dayOfMonth === '*' && month === '*' && dayOfWeek === '*') {
   216|    if (hour.startsWith('*/')) {
   217|      return `每 ${hour.slice(2)} 小时执行`
   218|    }
   219|    return `每天 ${hour}:${minute.padStart(2, '0')} 执行`
   220|  }
   221|  // 每周
   222|  if (dayOfWeek !== '*' && dayOfMonth === '*' && month === '*') {
   223|    const weekDayMap: Record<string, string> = {
   224|      '0': '周日', '1': '周一', '2': '周二', '3': '周三',
   225|      '4': '周四', '5': '周五', '6': '周六', '7': '周日',
   226|    }
   227|    return `每${weekDayMap[dayOfWeek] || '周' + dayOfWeek} ${hour}:${minute.padStart(2, '0')} 执行`
   228|  }
   229|  // 每月
   230|  if (dayOfMonth !== '*' && month === '*' && dayOfWeek === '*') {
   231|    return `每月 ${dayOfMonth} 日 ${hour}:${minute.padStart(2, '0')} 执行`
   232|  }
   233|  return `Cron: ${cron}`
   234|}
   235|
   236|// ---------- API ----------
   237|async function fetchPlans() {
   238|  loading.value = true
   239|  try {
   240|    const params: Record<string, any> = {
   241|      page: pagination.page,
   242|      page_size: pagination.page_size,
   243|    }
   244|    if (searchQuery.value.trim()) {
   245|      params.name = searchQuery.value.trim()
   246|    }
   247|    if (enabledFilter.value !== '' && enabledFilter.value !== null) {
   248|      params.enabled = enabledFilter.value
   249|    }
   250|    const res = await inspectionService.listPlans(params)
   251|    const data = res.data?.data ?? res.data
   252|    plans.value = data?.items ?? data ?? []
   253|    pagination.total = data?.total ?? plans.value.length
   254|  } catch (err: any) {
   255|    ElMessage.error(err.message || '获取计划列表失败')
   256|  } finally {
   257|    loading.value = false
   258|  }
   259|}
   260|
   261|async function fetchTemplates() {
   262|  templateLoading.value = true
   263|  try {
   264|    const res = await inspectionService.listTemplates({ page_size: 200 })
   265|    const data = res.data?.data ?? res.data
   266|    templateOptions.value = data?.items ?? data ?? []
   267|  } catch {
   268|    templateOptions.value = []
   269|  } finally {
   270|    templateLoading.value = false
   271|  }
   272|}
   273|
   274|async function createPlan(data: Record<string, any>) {
   275|  return inspectionService.createPlan(data)
   276|}
   277|
   278|async function updatePlan(id: string, data: Record<string, any>) {
   279|  return inspectionService.updatePlan(id, data)
   280|}
   281|
   282|async function deletePlan(id: string) {
   283|  return inspectionService.deletePlan(id)
   284|}
   285|
   286|// ---------- 操作 ----------
   287|function handleCreate() {
   288|  isEditing.value = false
   289|  editingId.value = ''
   290|  form.enabled = true
   291|  form.cron = '0 8 * * *'
   292|  dialogVisible.value = true
   293|}
   294|
   295|function handleEdit(row: any) {
   296|  isEditing.value = true
   297|  editingId.value = row.id
   298|  form.name = row.name || ''
   299|  form.template_id = row.template_id || ''
   300|  form.cron = row.cron || '0 8 * * *'
   301|  form.enabled = row.enabled !== false
   302|  form.description = row.description || ''
   303|  dialogVisible.value = true
   304|}
   305|
   306|async function handleSubmit() {
   307|  if (!formRef.value) return
   308|  const valid = await formRef.value.validate().catch(() => false)
   309|  if (!valid) return
   310|
   311|  submitLoading.value = true
   312|  try {
   313|    const payload = {
   314|      name: form.name,
   315|      template_id: form.template_id,
   316|      cron: form.cron,
   317|      enabled: form.enabled,
   318|      description: form.description,
   319|    }
   320|    if (isEditing.value) {
   321|      await updatePlan(editingId.value, payload)
   322|      ElMessage.success('计划更新成功')
   323|    } else {
   324|      await createPlan(payload)
   325|      ElMessage.success('计划创建成功')
   326|    }
   327|    dialogVisible.value = false
   328|    fetchPlans()
   329|  } catch (err: any) {
   330|    ElMessage.error(err.message || '操作失败')
   331|  } finally {
   332|    submitLoading.value = false
   333|  }
   334|}
   335|
   336|async function handleDelete(row: any) {
   337|  try {
   338|    await ElMessageBox.confirm(
   339|      `确定要删除计划「${row.name}」吗？此操作不可恢复。`,
   340|      '删除确认',
   341|      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }
   342|    )
   343|    await deletePlan(row.id)
   344|    ElMessage.success('计划已删除')
   345|    fetchPlans()
   346|  } catch (err: any) {
   347|    if (err !== 'cancel') {
   348|      ElMessage.error(err.message || '删除失败')
   349|    }
   350|  }
   351|}
   352|
   353|function resetForm() {
   354|  form.name = ''
   355|  form.template_id = ''
   356|  form.cron = '0 8 * * *'
   357|  form.enabled = true
   358|  form.description = ''
   359|  isEditing.value = false
   360|  editingId.value = ''
   361|  formRef.value?.resetFields()
   362|}
   363|
   364|// ---------- 初始化 ----------
   365|onMounted(() => {
   366|  fetchPlans()
   367|  fetchTemplates()
   368|})
   369|</script>
   370|
   371|<style scoped>
   372|
   375|.page-header {
   376|  display: flex;
   377|  justify-content: space-between;
   378|  align-items: center;
   379|  margin-bottom: 16px;
   380|}
   381|.page-title {
   382|  font-size: 18px;
   383|  font-weight: 600;
   384|  color: #1d2129;
   385|  margin: 0;
   386|}
   387|.page-toolbar {
   388|  display: flex;
   389|  align-items: center;
   390|  gap: 12px;
   391|  margin-bottom: 16px;
   392|}
   393|.page-pagination {
   394|  display: flex;
   395|  justify-content: flex-end;
   396|  margin-top: 16px;
   397|}
   398|.text-tertiary {
   399|  color: #86909c;
   400|  font-size: 13px;
   401|}
   402|.cron-text {
   403|  font-family: 'Courier New', Courier, monospace;
   404|  font-size: 13px;
   405|  background: #f2f3f5;
   406|  padding: 2px 6px;
   407|  border-radius: 4px;
   408|}
   409|.cron-preview {
   410|  color: #86909c;
   411|  font-size: 13px;
   412|}
   413|</style>
   414|