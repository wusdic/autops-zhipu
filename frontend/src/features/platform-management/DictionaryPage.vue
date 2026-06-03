     1|<template>
     2|  <div class="page-container">
     3|    <div class="autops-page-header">
     4|      <div>
     5|        <div class="autops-page-title">数据字典</div>
     6|        <div class="autops-page-desc">管理系统字典分类与字典项</div>
     7|      </div>
     8|    </div>
     9|
    10|    <div class="dict-layout">
    11|      <!-- ── Left Panel: Dictionary Groups ────────────────── -->
    12|      <div class="dict-left">
    13|        <div class="panel-header">
    14|          <span class="panel-title">字典分类</span>
    15|          <el-input
    16|            v-model="groupSearch"
    17|            placeholder="搜索分类..."
    18|            size="small"
    19|            clearable
    20|            prefix-icon="Search"
    21|            style="width: 140px"
    22|          />
    23|        </div>
    24|        <div class="group-list">
    25|          <div
    26|            v-for="group in filteredGroups"
    27|            :key="group"
    28|            class="group-item"
    29|            :class="{ active: selectedGroup === group }"
    30|            @click="selectGroup(group)"
    31|          >
    32|            <el-icon size="16" style="margin-right: 6px"><Folder /></el-icon>
    33|            <span class="group-name">{{ group }}</span>
    34|            <el-tag size="small" type="info" class="group-count">{{ groupItemCount(group) }}</el-tag>
    35|          </div>
    36|          <el-empty v-if="filteredGroups.length === 0" description="暂无分类" :image-size="60" />
    37|        </div>
    38|      </div>
    39|
    40|      <!-- ── Right Panel: Dictionary Items Table ──────────── -->
    41|      <div class="dict-right">
    42|        <div class="right-toolbar">
    43|          <div class="toolbar-left">
    44|            <el-input
    45|              v-model="keyword"
    46|              placeholder="搜索键/值/显示名..."
    47|              clearable
    48|              prefix-icon="Search"
    49|              style="width: 240px"
    50|              @keyup.enter="loadItems"
    51|            />
    52|            <el-button @click="loadItems" :loading="loading">查询</el-button>
    53|          </div>
    54|          <el-button type="primary" @click="openCreateDialog">
    55|            <el-icon><Plus /></el-icon> 新增字典项
    56|          </el-button>
    57|        </div>
    58|
    59|        <el-table stripe
 60| :data="items"
 61| v-loading="loading"
 62|63| border
 64| row-key="id"
 65| empty-text="暂无字典项"
 66| style="width: 100%"
 67| >
    68|          <el-table-column prop="category" label="分类" width="150" show-overflow-tooltip />
    69|          <el-table-column prop="key" label="键" min-width="150" show-overflow-tooltip />
    70|          <el-table-column prop="value" label="值" min-width="150" show-overflow-tooltip />
    71|          <el-table-column prop="label" label="显示名" min-width="130" show-overflow-tooltip />
    72|          <el-table-column prop="sort_order" label="排序" width="70" align="center" />
    73|          <el-table-column prop="is_active" label="启用" width="70" align="center">
    74|            <template #default="{ row }">
    75|              <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
    76|                {{ row.is_active ? '是' : '否' }}
    77|              </el-tag>
    78|            </template>
    79|          </el-table-column>
    80|          <el-table-column prop="remark" label="备注" min-width="150" show-overflow-tooltip />
    81|          <el-table-column label="操作" width="180" fixed="right" align="center">
    82|            <template #default="{ row }">
    83|              <el-button text type="primary" size="small" @click="openEditDialog(row)">编辑</el-button>
    84|              <el-button text type="danger" size="small" @click="deleteItem(row)">删除</el-button>
    85|            </template>
    86|          </el-table-column>
    87|        </el-table>
    88|
    89|        <div class="pagination-wrap" v-if="total > pageSize">
    90|          <el-pagination
    91|            v-model:current-page="currentPage"
    92|            :page-size="pageSize"
    93|            :total="total"
    94|            layout="total, prev, pager, next"
    95|            @current-change="loadItems"
    96|          />
    97|        </div>
    98|      </div>
    99|    </div>
   100|
   101|    <!-- ── Create / Edit Dialog ───────────────────────────── -->
   102|    <el-dialog
   103|      v-model="dialogVisible"
   104|      :title="isEditing ? '编辑字典项' : '新增字典项'"
   105|      width="600px"
   106|      destroy-on-close
   107|    >
   108|      <el-form
   109|        ref="formRef"
   110|        :model="form"
   111|        :rules="formRules"
   112|        label-width="80px"
   113|        label-position="right"
   114|      >
   115|        <el-form-item label="分类" prop="category">
   116|          <el-select
   117|            v-model="form.category"
   118|            filterable
   119|            allow-create
   120|            default-first-option
   121|            placeholder="选择或输入分类"
   122|            style="width: 100%"
   123|          >
   124|            <el-option
   125|              v-for="g in allGroups"
   126|              :key="g"
   127|              :label="g"
   128|              :value="g"
   129|            />
   130|          </el-select>
   131|        </el-form-item>
   132|        <el-form-item label="键" prop="key">
   133|          <el-input v-model="form.key" placeholder="字典键，如 high / tcp" />
   134|        </el-form-item>
   135|        <el-form-item label="值" prop="value">
   136|          <el-input v-model="form.value" placeholder="字典值" />
   137|        </el-form-item>
   138|        <el-form-item label="显示名" prop="label">
   139|          <el-input v-model="form.label" placeholder="前端显示名称" />
   140|        </el-form-item>
   141|        <el-form-item label="排序">
   142|          <el-input-number v-model="form.sort_order" :min="0" :max="9999" />
   143|        </el-form-item>
   144|        <el-form-item label="启用">
   145|          <el-switch v-model="form.is_active" />
   146|        </el-form-item>
   147|        <el-form-item label="备注">
   148|          <el-input v-model="form.remark" type="textarea" :rows="2" placeholder="可选备注" />
   149|        </el-form-item>
   150|      </el-form>
   151|      <template #footer>
   152|        <el-button @click="dialogVisible = false">取消</el-button>
   153|        <el-button type="primary" :loading="submitting" @click="submitForm">确定</el-button>
   154|      </template>
   155|    </el-dialog>
   156|  </div>
   157|</template>
   158|
   159|<script setup lang="ts">
   160|import { ref, reactive, computed, onMounted } from 'vue'
   161|import { ElMessage, ElMessageBox } from 'element-plus'
   162|import type { FormInstance, FormRules } from 'element-plus'
   163|import { Plus, Folder } from '@element-plus/icons-vue'
   164|import { platformService } from '@/shared/api'
   165|
   166|// ── State ────────────────────────────────────────────────
   167|const loading = ref(false)
   168|const submitting = ref(false)
   169|const items = ref<any[]>([])
   170|const total = ref(0)
   171|const currentPage = ref(1)
   172|const pageSize = 20
   173|
   174|const selectedGroup = ref('')
   175|const keyword = ref('')
   176|const groupSearch = ref('')
   177|
   178|const dialogVisible = ref(false)
   179|const isEditing = ref(false)
   180|const editingId = ref('')
   181|const formRef = ref<FormInstance>()
   182|
   183|const form = reactive({
   184|  category: '',
   185|  key: '',
   186|  value: '',
   187|  label: '',
   188|  sort_order: 0,
   189|  is_active: true,
   190|  remark: '',
   191|})
   192|
   193|const formRules: FormRules = {
   194|  category: [{ required: true, message: '请选择或输入分类', trigger: 'change' }],
   195|  key: [{ required: true, message: '请输入字典键', trigger: 'blur' }],
   196|  value: [{ required: true, message: '请输入字典值', trigger: 'blur' }],
   197|}
   198|
   199|// ── Computed ─────────────────────────────────────────────
   200|const allGroups = computed(() => {
   201|  const groups = new Set<string>()
   202|  items.value.forEach((item) => groups.add(item.category))
   203|  return Array.from(groups).sort()
   204|})
   205|
   206|const filteredGroups = computed(() => {
   207|  if (!groupSearch.value) return allGroups.value
   208|  const q = groupSearch.value.toLowerCase()
   209|  return allGroups.value.filter((g) => g.toLowerCase().includes(q))
   210|})
   211|
   212|function groupItemCount(group: string): number {
   213|  return items.value.filter((i) => i.category === group).length
   214|}
   215|
   216|// ── Data Loading ─────────────────────────────────────────
   217|async function loadItems() {
   218|  loading.value = true
   219|  try {
   220|    const params: Record<string, any> = {
   221|      page: currentPage.value,
   222|      page_size: pageSize,
   223|    }
   224|    if (selectedGroup.value) params.category = selectedGroup.value
   225|    if (keyword.value) params.keyword = keyword.value
   226|
   227|    const res = await platformService.dictionaries(params)
   228|    const data = res.data?.data ?? res.data
   229|    if (Array.isArray(data)) {
   230|      items.value = data
   231|      total.value = data.length
   232|    } else {
   233|      items.value = data?.items ?? data?.list ?? []
   234|      total.value = data?.total ?? items.value.length
   235|    }
   236|  } catch (err: any) {
   237|    ElMessage.error(err.message || '加载字典失败')
   238|  } finally {
   239|    loading.value = false
   240|  }
   241|}
   242|
   243|// ── Group Selection ──────────────────────────────────────
   244|function selectGroup(group: string) {
   245|  selectedGroup.value = selectedGroup.value === group ? '' : group
   246|  currentPage.value = 1
   247|  loadItems()
   248|}
   249|
   250|// ── Dialog ───────────────────────────────────────────────
   251|function resetForm() {
   252|  form.category = selectedGroup.value || ''
   253|  form.key = ''
   254|  form.value = ''
   255|  form.label = ''
   256|  form.sort_order = 0
   257|  form.is_active = true
   258|  form.remark = ''
   259|}
   260|
   261|function openCreateDialog() {
   262|  isEditing.value = false
   263|  editingId.value = ''
   264|  resetForm()
   265|  dialogVisible.value = true
   266|}
   267|
   268|function openEditDialog(row: any) {
   269|  isEditing.value = true
   270|  editingId.value = row.id
   271|  Object.assign(form, {
   272|    category: row.category,
   273|    key: row.key,
   274|    value: row.value,
   275|    label: row.label,
   276|    sort_order: row.sort_order ?? 0,
   277|    is_active: row.is_active ?? true,
   278|    remark: row.remark ?? '',
   279|  })
   280|  dialogVisible.value = true
   281|}
   282|
   283|async function submitForm() {
   284|  if (!formRef.value) return
   285|  const valid = await formRef.value.validate().catch(() => false)
   286|  if (!valid) return
   287|
   288|  submitting.value = true
   289|  try {
   290|    const payload = { ...form }
   291|    if (isEditing.value) {
   292|      await platformService.dictionaryUpdate(editingId.value, payload)
   293|      ElMessage.success('字典项已更新')
   294|    } else {
   295|      await platformService.dictionaryCreate(payload)
   296|      ElMessage.success('字典项已创建')
   297|    }
   298|    dialogVisible.value = false
   299|    loadItems()
   300|  } catch (err: any) {
   301|    ElMessage.error(err.message || '操作失败')
   302|  } finally {
   303|    submitting.value = false
   304|  }
   305|}
   306|
   307|// ── Delete ───────────────────────────────────────────────
   308|async function deleteItem(row: any) {
   309|  try {
   310|    await ElMessageBox.confirm(
   311|      `确定删除字典项「${row.label || row.key}」吗？`,
   312|      '删除确认',
   313|      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' },
   314|    )
   315|    await platformService.dictionaryDelete(row.id)
   316|    ElMessage.success('已删除')
   317|    loadItems()
   318|  } catch {
   319|    // cancelled or API error handled globally
   320|  }
   321|}
   322|
   323|// ── Init ─────────────────────────────────────────────────
   324|onMounted(() => {
   325|  loadItems()
   326|})
   327|</script>
   328|
   329|<style scoped>
   330|
   333|.autops-page-header {
   334|  display: flex;
   335|  justify-content: space-between;
   336|  align-items: center;
   337|  margin-bottom: 16px;
   338|}
   339|.autops-page-title {
   340|  font-size: 18px;
   341|  font-weight: 600;
   342|  color: #1d2129;
   343|}
   344|
   345|/* Layout */
   346|.dict-layout {
   347|  display: flex;
   348|  gap: 16px;
   349|}
   350|.dict-left {
   351|  width: 240px;
   352|  min-width: 200px;
   353|  flex-shrink: 0;
   354|  background: #fff;
   355|  border: 1px solid #e5e6eb;
   356|  border-radius: 8px;
   357|  display: flex;
   358|  flex-direction: column;
   359|}
   360|.dict-right {
   361|  flex: 1;
   362|  min-width: 0;
   363|}
   364|
   365|/* Panel */
   366|.panel-header {
   367|  display: flex;
   368|  justify-content: space-between;
   369|  align-items: center;
   370|  padding: 12px;
   371|  border-bottom: 1px solid #f2f3f5;
   372|}
   373|.panel-title {
   374|  font-weight: 600;
   375|  font-size: 14px;
   376|  color: #1d2129;
   377|}
   378|.group-list {
   379|  flex: 1;
   380|  overflow-y: auto;
   381|  padding: 4px 0;
   382|}
   383|.group-item {
   384|  display: flex;
   385|  align-items: center;
   386|  padding: 10px 12px;
   387|  cursor: pointer;
   388|  transition: background 0.15s;
   389|  border-left: 3px solid transparent;
   390|}
   391|.group-item:hover {
   392|  background: #f7f8fa;
   393|}
   394|.group-item.active {
   395|  background: #e8f3ff;
   396|  border-left-color: #165dff;
   397|}
   398|.group-name {
   399|  flex: 1;
   400|  font-size: 13px;
   401|  color: #4e5969;
   402|  overflow: hidden;
   403|  text-overflow: ellipsis;
   404|  white-space: nowrap;
   405|}
   406|.group-count {
   407|  margin-left: 4px;
   408|}
   409|
   410|/* Right toolbar */
   411|.right-toolbar {
   412|  display: flex;
   413|  justify-content: space-between;
   414|  align-items: center;
   415|  margin-bottom: 12px;
   416|}
   417|.toolbar-left {
   418|  display: flex;
   419|  gap: 8px;
   420|}
   421|
   422|/* Pagination */
   423|.pagination-wrap {
   424|  display: flex;
   425|  justify-content: flex-end;
   426|  margin-top: 12px;
   427|}
   428|</style>
   429|