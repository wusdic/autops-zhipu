     1|<template>
     2|  <div class="page-container">
     3|    <!-- 页面头部 -->
     4|    <div class="autops-page-header">
     5|      <div class="autops-page-title">巡检模板</div>
     6|      <div class="autops-page-desc">管理巡检模板，定义检查项和规则</div>
     7|    </div>
     8|    <div style="display: flex; justify-content: flex-end; margin-bottom: 16px">
     9|      <el-button type="primary" @click="handleCreate">
    10|        <el-icon><Plus /></el-icon> 新建模板
    11|      </el-button>
    12|    </div>
    13|
    14|    <!-- 搜索栏 -->
    15|    <div class="page-toolbar">
    16|      <el-input
    17|        v-model="searchQuery"
    18|        placeholder="搜索模板名称..."
    19|        clearable
    20|        style="width: 260px"
    21|        @keyup.enter="fetchList"
    22|        @clear="fetchList"
    23|      >
    24|        <template #prefix><el-icon><Search /></el-icon></template>
    25|      </el-input>
    26|      <el-button type="default" @click="fetchList">
    27|        <el-icon><Refresh /></el-icon> 刷新
    28|      </el-button>
    29|    </div>
    30|
    31|    <!-- 数据表格 -->
    32|    <el-table stripe :data="templates" v-loading="loading"empty-text="暂无巡检模板">
    33|      <el-table-column prop="name" label="模板名称" min-width="180" show-overflow-tooltip />
    34|      <el-table-column prop="check_type" label="检查类型" width="120">
    35|        <template #default="{ row }">
    36|          <el-tag size="small">{{ checkTypeLabel(row.check_type) }}</el-tag>
    37|        </template>
    38|      </el-table-column>
    39|      <el-table-column prop="asset_type" label="资产类型" width="120">
    40|        <template #default="{ row }">
    41|          <el-tag type="info" size="small">{{ assetTypeLabel(row.asset_type) }}</el-tag>
    42|        </template>
    43|      </el-table-column>
    44|      <el-table-column prop="check_items" label="检查项数" width="100" align="center">
    45|        <template #default="{ row }">
    46|          <span class="check-item-count">{{ row.check_items ?? 0 }}</span>
    47|        </template>
    48|      </el-table-column>
    49|      <el-table-column prop="created_at" label="创建时间" width="170">
    50|        <template #default="{ row }">
    51|          <span class="text-tertiary">{{ formatTime(row.created_at) }}</span>
    52|        </template>
    53|      </el-table-column>
    54|      <el-table-column prop="description" label="描述" min-width="160" show-overflow-tooltip />
    55|      <el-table-column label="操作" width="180" fixed="right">
    56|        <template #default="{ row }">
    57|          <el-button text type="primary" size="small" @click="handleEdit(row)">编辑</el-button>
    58|          <el-button text type="danger" size="small" @click="handleDelete(row)">删除</el-button>
    59|        </template>
    60|      </el-table-column>
    61|    </el-table>
    62|
    63|    <!-- 分页 -->
    64|    <div class="page-pagination">
    65|      <el-pagination
    66|        v-model:current-page="pagination.page"
    67|        v-model:page-size="pagination.page_size"
    68|        :total="pagination.total"
    69|        :page-sizes="[10, 20, 50, 100]"
    70|        layout="total, sizes, prev, pager, next, jumper"
    71|        background
    72|        @size-change="fetchList"
    73|        @current-change="fetchList"
    74|      />
    75|    </div>
    76|
    77|    <!-- 新建/编辑弹窗 -->
    78|    <el-dialog
    79|      v-model="dialogVisible"
    80|      :title="isEditing ? '编辑模板' : '新建模板'"
    81|      width="600px"
    82|      :close-on-click-modal="false"
    83|      @closed="resetForm"
    84|    >
    85|      <el-form
    86|        ref="formRef"
    87|        :model="form"
    88|        :rules="formRules"
    89|        label-width="90px"
    90|        label-position="right"
    91|      >
    92|        <el-form-item label="模板名称" prop="name">
    93|          <el-input v-model="form.name" placeholder="请输入模板名称" maxlength="100" show-word-limit />
    94|        </el-form-item>
    95|        <el-form-item label="检查类型" prop="check_type">
    96|          <el-select v-model="form.check_type" placeholder="请选择检查类型" style="width: 100%">
    97|            <el-option label="基础巡检" value="basic" />
    98|            <el-option label="指标采集" value="metrics" />
    99|            <el-option label="日志巡检" value="logs" />
   100|            <el-option label="配置巡检" value="config" />
   101|            <el-option label="页面巡检" value="page" />
   102|            <el-option label="基线巡检" value="baseline" />
   103|            <el-option label="证书检查" value="certificate" />
   104|            <el-option label="综合巡检" value="comprehensive" />
   105|          </el-select>
   106|        </el-form-item>
   107|        <el-form-item label="资产类型" prop="asset_type">
   108|          <el-select v-model="form.asset_type" placeholder="请选择资产类型" style="width: 100%">
   109|            <el-option label="Linux 服务器" value="linux_server" />
   110|            <el-option label="Windows 服务器" value="windows_server" />
   111|            <el-option label="数据库" value="database" />
   112|            <el-option label="Web 服务" value="web_service" />
   113|            <el-option label="网络设备" value="network_device" />
   114|            <el-option label="中间件" value="middleware" />
   115|          </el-select>
   116|        </el-form-item>
   117|        <el-form-item label="描述" prop="description">
   118|          <el-input
   119|            v-model="form.description"
   120|            type="textarea"
   121|            :rows="4"
   122|            placeholder="请输入模板描述"
   123|            maxlength="500"
   124|            show-word-limit
   125|          />
   126|        </el-form-item>
   127|      </el-form>
   128|      <template #footer>
   129|        <el-button @click="dialogVisible = false">取消</el-button>
   130|        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">确定</el-button>
   131|      </template>
   132|    </el-dialog>
   133|  </div>
   134|</template>
   135|
   136|<script setup lang="ts">
   137|import { ref, reactive, onMounted } from 'vue'
   138|import { ElMessage, ElMessageBox } from 'element-plus'
   139|import type { FormInstance, FormRules } from 'element-plus'
   140|import { Plus, Search, Refresh } from '@element-plus/icons-vue'
   141|import { inspectionService } from '@/shared/api'
   142|
   143|// ---------- 状态 ----------
   144|const loading = ref(false)
   145|const submitLoading = ref(false)
   146|const dialogVisible = ref(false)
   147|const isEditing = ref(false)
   148|const editingId = ref<string>('')
   149|const templates = ref<any[]>([])
   150|const searchQuery = ref('')
   151|const formRef = ref<FormInstance>()
   152|
   153|const pagination = reactive({
   154|  page: 1,
   155|  page_size: 20,
   156|  total: 0,
   157|})
   158|
   159|const form = reactive({
   160|  name: '',
   161|  check_type: '',
   162|  asset_type: '',
   163|  description: '',
   164|})
   165|
   166|const formRules: FormRules = {
   167|  name: [{ required: true, message: '请输入模板名称', trigger: 'blur' }],
   168|  check_type: [{ required: true, message: '请选择检查类型', trigger: 'change' }],
   169|  asset_type: [{ required: true, message: '请选择资产类型', trigger: 'change' }],
   170|}
   171|
   172|// ---------- 映射 ----------
   173|const checkTypeMap: Record<string, string> = {
   174|  basic: '基础巡检',
   175|  metrics: '指标采集',
   176|  logs: '日志巡检',
   177|  config: '配置巡检',
   178|  page: '页面巡检',
   179|  baseline: '基线巡检',
   180|  certificate: '证书检查',
   181|  comprehensive: '综合巡检',
   182|}
   183|
   184|const assetTypeMap: Record<string, string> = {
   185|  linux_server: 'Linux 服务器',
   186|  windows_server: 'Windows 服务器',
   187|  database: '数据库',
   188|  web_service: 'Web 服务',
   189|  network_device: '网络设备',
   190|  middleware: '中间件',
   191|}
   192|
   193|function checkTypeLabel(val: string) {
   194|  return checkTypeMap[val] || val || '-'
   195|}
   196|
   197|function assetTypeLabel(val: string) {
   198|  return assetTypeMap[val] || val || '-'
   199|}
   200|
   201|function formatTime(val: string) {
   202|  if (!val) return '-'
   203|  return val
   204|}
   205|
   206|// ---------- API ----------
   207|async function fetchList() {
   208|  loading.value = true
   209|  try {
   210|    const params: Record<string, any> = {
   211|      page: pagination.page,
   212|      page_size: pagination.page_size,
   213|    }
   214|    if (searchQuery.value.trim()) {
   215|      params.name = searchQuery.value.trim()
   216|    }
   217|    const res = await inspectionService.listTemplates(params)
   218|    const data = res.data?.data ?? res.data
   219|    templates.value = data?.items ?? data ?? []
   220|    pagination.total = data?.total ?? templates.value.length
   221|  } catch (err: any) {
   222|    ElMessage.error(err.message || '获取模板列表失败')
   223|  } finally {
   224|    loading.value = false
   225|  }
   226|}
   227|
   228|async function createTemplate(data: Record<string, any>) {
   229|  return inspectionService.createTemplate(data)
   230|}
   231|
   232|async function updateTemplate(id: string, data: Record<string, any>) {
   233|  return inspectionService.updateTemplate(id, data)
   234|}
   235|
   236|async function deleteTemplate(id: string) {
   237|  return inspectionService.deleteTemplate(id)
   238|}
   239|
   240|// ---------- 操作 ----------
   241|function handleCreate() {
   242|  isEditing.value = false
   243|  editingId.value = ''
   244|  dialogVisible.value = true
   245|}
   246|
   247|function handleEdit(row: any) {
   248|  isEditing.value = true
   249|  editingId.value = row.id
   250|  form.name = row.name || ''
   251|  form.check_type = row.check_type || ''
   252|  form.asset_type = row.asset_type || ''
   253|  form.description = row.description || ''
   254|  dialogVisible.value = true
   255|}
   256|
   257|async function handleSubmit() {
   258|  if (!formRef.value) return
   259|  const valid = await formRef.value.validate().catch(() => false)
   260|  if (!valid) return
   261|
   262|  submitLoading.value = true
   263|  try {
   264|    const payload = {
   265|      name: form.name,
   266|      check_type: form.check_type,
   267|      asset_type: form.asset_type,
   268|      description: form.description,
   269|    }
   270|    if (isEditing.value) {
   271|      await updateTemplate(editingId.value, payload)
   272|      ElMessage.success('模板更新成功')
   273|    } else {
   274|      await createTemplate(payload)
   275|      ElMessage.success('模板创建成功')
   276|    }
   277|    dialogVisible.value = false
   278|    fetchList()
   279|  } catch (err: any) {
   280|    ElMessage.error(err.message || '操作失败')
   281|  } finally {
   282|    submitLoading.value = false
   283|  }
   284|}
   285|
   286|async function handleDelete(row: any) {
   287|  try {
   288|    await ElMessageBox.confirm(
   289|      `确定要删除模板「${row.name}」吗？此操作不可恢复。`,
   290|      '删除确认',
   291|      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }
   292|    )
   293|    await deleteTemplate(row.id)
   294|    ElMessage.success('模板已删除')
   295|    fetchList()
   296|  } catch (err: any) {
   297|    if (err !== 'cancel') {
   298|      ElMessage.error(err.message || '删除失败')
   299|    }
   300|  }
   301|}
   302|
   303|function resetForm() {
   304|  form.name = ''
   305|  form.check_type = ''
   306|  form.asset_type = ''
   307|  form.description = ''
   308|  isEditing.value = false
   309|  editingId.value = ''
   310|  formRef.value?.resetFields()
   311|}
   312|
   313|// ---------- 初始化 ----------
   314|onMounted(() => {
   315|  fetchList()
   316|})
   317|</script>
   318|
   319|<style scoped>
   320|
   323|.page-header {
   324|  display: flex;
   325|  justify-content: space-between;
   326|  align-items: center;
   327|  margin-bottom: 16px;
   328|}
   329|.page-title {
   330|  font-size: 18px;
   331|  font-weight: 600;
   332|  color: #1d2129;
   333|  margin: 0;
   334|}
   335|.page-toolbar {
   336|  display: flex;
   337|  align-items: center;
   338|  gap: 12px;
   339|  margin-bottom: 16px;
   340|}
   341|.page-pagination {
   342|  display: flex;
   343|  justify-content: flex-end;
   344|  margin-top: 16px;
   345|}
   346|.text-tertiary {
   347|  color: #86909c;
   348|  font-size: 13px;
   349|}
   350|.check-item-count {
   351|  font-weight: 600;
   352|  color: #165dff;
   353|}
   354|</style>
   355|