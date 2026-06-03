     1|<template>
     2|  <div class="page-container">
     3|    <div class="autops-page-header">
     4|      <div>
     5|        <div class="autops-page-title">Playbook 管理</div>
     6|        <div class="autops-page-desc">编排自动化步骤流程</div>
     7|      </div>
     8|    </div>
     9|
    10|    <el-row :gutter="16" class="stat-row">
    11|      <el-col :span="6"><div class="autops-card stat-card"><div class="stat-value">{{ stats.total }}</div><div class="stat-label">Playbook 总数</div></div></el-col>
    12|      <el-col :span="6"><div class="autops-card stat-card success"><div class="stat-value">{{ stats.active }}</div><div class="stat-label">已激活</div></div></el-col>
    13|      <el-col :span="6"><div class="autops-card stat-card primary"><div class="stat-value">{{ stats.withScripts }}</div><div class="stat-label">关联脚本</div></div></el-col>
    14|      <el-col :span="6"><div class="autops-card stat-card warning"><div class="stat-value">{{ stats.avgSteps }}</div><div class="stat-label">平均步骤数</div></div></el-col>
    15|    </el-row>
    16|
    17|    <div class="autops-toolbar">
    18|      <el-input v-model="filters.keyword" placeholder="搜索名称/描述" clearable style="width:220px;margin-right:8px" @clear="load" @keyup.enter="load" />
    19|      <el-select v-model="filters.status" placeholder="状态" clearable style="width:130px;margin-right:8px">
    20|        <el-option label="草稿" value="draft" /><el-option label="已激活" value="active" /><el-option label="已废弃" value="deprecated" />
    21|      </el-select>
    22|      <el-select v-model="filters.risk_level" placeholder="风险等级" clearable style="width:130px;margin-right:8px">
    23|        <el-option label="低" value="low" /><el-option label="中" value="medium" /><el-option label="高" value="high" /><el-option label="严重" value="critical" />
    24|      </el-select>
    25|      <el-button type="primary" @click="load"><el-icon><Search /></el-icon> 搜索</el-button>
    26|      <el-button @click="resetFilters">重置</el-button>
    27|      <div style="flex:1" />
    28|      <el-button type="primary" @click="openCreate"><el-icon><Plus /></el-icon> 新建 Playbook</el-button>
    29|    </div>
    30|
    31|    <el-table stripe :data="items" v-loading="loading">
    32|      <el-table-column prop="name" label="名称" min-width="160">
    33|        <template #default="{ row }"><el-link type="primary" @click="viewDetail(row)">{{ row.name }}</el-link></template>
    34|      </el-table-column>
    35|      <el-table-column prop="description" label="描述" min-width="180" show-overflow-tooltip />
    36|      <el-table-column label="步骤数" width="90" align="center">
    37|        <template #default="{ row }"><el-tag size="small">{{ row.steps?.length || 0 }}</el-tag></template>
    38|      </el-table-column>
    39|      <el-table-column prop="status" label="状态" width="100">
    40|        <template #default="{ row }"><el-tag :type="row.status==='active'?'success':row.status==='draft'?'info':'warning'" size="small">{{ statusLabel(row.status) }}</el-tag></template>
    41|      </el-table-column>
    42|      <el-table-column prop="risk_level" label="风险" width="90">
    43|        <template #default="{ row }"><el-tag :type="riskType(row.risk_level)" size="small">{{ row.risk_level || 'low' }}</el-tag></template>
    44|      </el-table-column>
    45|      <el-table-column label="关联策略" width="90" align="center">
    46|        <template #default="{ row }">{{ row.policy_count || 0 }}</template>
    47|      </el-table-column>
    48|      <el-table-column prop="created_at" label="创建时间" width="170">
    49|        <template #default="{ row }">{{ fmt(row.created_at) }}</template>
    50|      </el-table-column>
    51|      <el-table-column label="操作" width="240" fixed="right">
    52|        <template #default="{ row }">
    53|          <el-button size="small" @click="viewDetail(row)">详情</el-button>
    54|          <el-button size="small" type="primary" @click="openEdit(row)">编辑</el-button>
    55|          <el-button size="small" @click="duplicate(row)">复制</el-button>
    56|          <el-button size="small" type="success" @click="quickExec(row)">执行</el-button>
    57|          <el-button size="small" type="danger" @click="remove(row)">删除</el-button>
    58|        </template>
    59|      </el-table-column>
    60|    </el-table>
    61|    <el-pagination v-if="total > pageSize" class="pagination" :current-page="page" :page-size="pageSize" :total="total" @current-change="(p:number)=>{page=p;load()}" layout="total, prev, pager, next" />
    62|
    63|    <!-- 创建/编辑对话框 -->
    64|    <el-dialog v-model="showDialog" :title="editing?'编辑 Playbook':'新建 Playbook'" width="780px" top="5vh">
    65|      <el-form :model="form" label-width="100px">
    66|        <el-row :gutter="16">
    67|          <el-col :span="12"><el-form-item label="名称" required><el-input v-model="form.name" placeholder="Playbook 名称" /></el-form-item></el-col>
    68|          <el-col :span="12"><el-form-item label="风险等级"><el-select v-model="form.risk_level" style="width:100%">
    69|            <el-option label="低" value="low" /><el-option label="中" value="medium" /><el-option label="高" value="high" /><el-option label="严重" value="critical" />
    70|          </el-select></el-form-item></el-col>
    71|        </el-row>
    72|        <el-form-item label="描述"><el-input v-model="form.description" type="textarea" :rows="2" /></el-form-item>
    73|        <el-form-item label="状态"><el-select v-model="form.status" style="width:200px">
    74|          <el-option label="草稿" value="draft" /><el-option label="已激活" value="active" /><el-option label="已废弃" value="deprecated" />
    75|        </el-select></el-form-item>
    76|
    77|        <!-- 步骤编排器 -->
    78|        <el-divider content-position="left">步骤编排</el-divider>
    79|        <div class="step-orchestrator">
    80|          <div v-for="(step, idx) in form.steps" :key="idx" class="step-item">
    81|            <div class="step-header">
    82|              <span class="step-number">{{ idx + 1 }}</span>
    83|              <el-input v-model="step.name" placeholder="步骤名称" style="width:180px" size="small" />
    84|              <el-select v-model="step.script_id" placeholder="选择脚本" style="width:200px" size="small" filterable>
    85|                <el-option v-for="s in scripts" :key="s.id" :label="s.name" :value="s.id" />
    86|              </el-select>
    87|              <el-input-number v-model="step.timeout" :min="10" :max="3600" placeholder="超时" size="small" style="width:120px" />
    88|              <el-select v-model="step.on_failure" style="width:120px" size="small">
    89|                <el-option label="继续" value="continue" /><el-option label="停止" value="stop" /><el-option label="回滚" value="rollback" />
    90|              </el-select>
    91|              <el-button-group>
    92|                <el-button size="small" :disabled="idx===0" @click="moveStep(idx,-1)">↑</el-button>
    93|                <el-button size="small" :disabled="idx===form.steps.length-1" @click="moveStep(idx,1)">↓</el-button>
    94|              </el-button-group>
    95|              <el-button size="small" type="danger" @click="form.steps.splice(idx,1)"><el-icon><Delete /></el-icon></el-button>
    96|            </div>
    97|            <div class="step-params">
    98|              <el-input v-model="step.params_json" placeholder="参数 JSON (可选)" style="width:400px" size="small" />
    99|              <el-input v-model="step.condition" placeholder="条件表达式 (可选)" style="width:300px;margin-left:8px" size="small" />
   100|            </div>
   101|          </div>
   102|          <el-button type="primary" plain @click="addStep" style="margin-top:8px"><el-icon><Plus /></el-icon> 添加步骤</el-button>
   103|        </div>
   104|
   105|        <!-- 步骤流程预览 -->
   106|        <el-divider content-position="left">流程预览</el-divider>
   107|        <div class="flow-preview" v-if="form.steps.length">
   108|          <div v-for="(step, idx) in form.steps" :key="idx" class="flow-node">
   109|            <div class="flow-box">{{ idx+1 }}. {{ step.name || '(未命名)' }}</div>
   110|            <div v-if="idx < form.steps.length - 1" class="flow-arrow">→</div>
   111|          </div>
   112|        </div>
   113|        <el-empty v-else description="请添加步骤" :image-size="60" />
   114|      </el-form>
   115|      <template #footer>
   116|        <el-button @click="showDialog=false">取消</el-button>
   117|        <el-button type="primary" @click="save">保存</el-button>
   118|      </template>
   119|    </el-dialog>
   120|
   121|    <!-- 详情抽屉 -->
   122|    <el-drawer v-model="showDetail" :title="detail?.name || 'Playbook 详情'" size="600px">
   123|      <template v-if="detail">
   124|        <el-descriptions :column="2" border>
   125|          <el-descriptions-item label="名称">{{ detail.name }}</el-descriptions-item>
   126|          <el-descriptions-item label="状态"><el-tag :type="detail.status==='active'?'success':'info'" size="small">{{ statusLabel(detail.status) }}</el-tag></el-descriptions-item>
   127|          <el-descriptions-item label="风险等级"><el-tag :type="riskType(detail.risk_level)" size="small">{{ detail.risk_level }}</el-tag></el-descriptions-item>
   128|          <el-descriptions-item label="步骤数">{{ detail.steps?.length || 0 }}</el-descriptions-item>
   129|          <el-descriptions-item label="描述" :span="2">{{ detail.description || '-' }}</el-descriptions-item>
   130|          <el-descriptions-item label="创建时间">{{ fmt(detail.created_at) }}</el-descriptions-item>
   131|          <el-descriptions-item label="更新时间">{{ fmt(detail.updated_at) }}</el-descriptions-item>
   132|        </el-descriptions>
   133|
   134|        <h4 style="margin:16px 0 8px">步骤详情</h4>
   135|        <el-table stripe :data="detail.steps || []"size="small">
   136|          <el-table-column prop="name" label="步骤名" min-width="120" />
   137|          <el-table-column label="脚本" min-width="120">
   138|            <template #default="{ row }">{{ getScriptName(row.script_id) }}</template>
   139|          </el-table-column>
   140|          <el-table-column prop="timeout" label="超时(s)" width="80" />
   141|          <el-table-column prop="on_failure" label="失败处理" width="90" />
   142|          <el-table-column prop="condition" label="条件" min-width="120" show-overflow-tooltip />
   143|        </el-table>
   144|
   145|        <h4 style="margin:16px 0 8px">执行历史</h4>
   146|        <el-table stripe :data="execHistory"size="small" v-loading="execLoading">
   147|          <el-table-column label="序号" type="index" width="60" align="center" />
   148|          <el-table-column prop="status" label="状态" width="90">
   149|            <template #default="{ row }"><el-tag :type="row.status==='success'?'success':'danger'" size="small">{{ row.status }}</el-tag></template>
   150|          </el-table-column>
   151|          <el-table-column prop="started_at" label="时间" min-width="160">
   152|            <template #default="{ row }">{{ fmt(row.started_at) }}</template>
   153|          </el-table-column>
   154|        </el-table>
   155|
   156|        <div style="margin-top:16px;display:flex;gap:8px">
   157|          <el-button type="primary" @click="openEdit(detail);showDetail=false">编辑</el-button>
   158|          <el-button @click="duplicate(detail);showDetail=false">复制</el-button>
   159|          <el-button type="success" @click="quickExec(detail);showDetail=false">执行</el-button>
   160|        </div>
   161|      </template>
   162|    </el-drawer>
   163|  </div>
   164|</template>
   165|
   166|<script setup lang="ts">
   167|import { ref, reactive, onMounted } from 'vue'
   168|import { useRouter } from 'vue-router'
   169|import { ElMessage, ElMessageBox } from 'element-plus'
   170|import { Plus, Search, Delete } from '@element-plus/icons-vue'
   171|import api from '@/shared/api/client'
   172|import { API } from '@/shared/api/routes'
   173|
   174|const router = useRouter()
   175|
   176|const stats = reactive({ total: 0, active: 0, withScripts: 0, avgSteps: 0 })
   177|const filters = reactive({ keyword: '', status: '', risk_level: '' })
   178|const items = ref<any[]>([])
   179|const loading = ref(false)
   180|const page = ref(1)
   181|const pageSize = 20
   182|const total = ref(0)
   183|
   184|const scripts = ref<any[]>([])
   185|const showDialog = ref(false)
   186|const editing = ref(false)
   187|const editId = ref('')
   188|const form = reactive({ name: '', description: '', status: 'draft', risk_level: 'low', steps: [] as any[] })
   189|
   190|const showDetail = ref(false)
   191|const detail = ref<any>(null)
   192|const execHistory = ref<any[]>([])
   193|const execLoading = ref(false)
   194|
   195|function resetFilters() { filters.keyword=''; filters.status=''; filters.risk_level=''; load() }
   196|
   197|async function load() {
   198|  loading.value = true
   199|  try {
   200|    const params: any = { page: page.value, page_size: pageSize }
   201|    if (filters.keyword) params.keyword = filters.keyword
   202|    if (filters.status) params.status = filters.status
   203|    if (filters.risk_level) params.risk_level = filters.risk_level
   204|    const res = await api.get(API.PLAYBOOKS, { params })
   205|    if (res.data?.code === 0) {
   206|      items.value = res.data.data?.items || res.data.data || []
   207|      total.value = res.data.data?.total || items.value.length
   208|    }
   209|    computeStats()
   210|  } catch { ElMessage.error('加载失败') }
   211|  finally { loading.value = false }
   212|}
   213|
   214|function computeStats() {
   215|  stats.total = items.value.length
   216|  stats.active = items.value.filter(i => i.status === 'active').length
   217|  stats.withScripts = items.value.filter(i => i.steps?.some((s: any) => s.script_id)).length
   218|  const steps = items.value.map(i => i.steps?.length || 0)
   219|  stats.avgSteps = items.value.length ? Math.round(steps.reduce((a: number, b: number) => a + b, 0) / items.value.length) : 0
   220|}
   221|
   222|async function loadScripts() {
   223|  try {
   224|    const res = await api.get(API.SCRIPTS, { params: { page_size: 100 } })
   225|    if (res.data?.code === 0) scripts.value = res.data.data?.items || res.data.data || []
   226|  } catch {}
   227|}
   228|
   229|function addStep() {
   230|  form.steps.push({ name: '', script_id: '', timeout: 300, on_failure: 'stop', params_json: '', condition: '' })
   231|}
   232|
   233|function moveStep(idx: number, dir: number) {
   234|  const arr = form.steps
   235|  const t = arr[idx]; arr[idx] = arr[idx + dir]; arr[idx + dir] = t
   236|  form.steps = [...arr]
   237|}
   238|
   239|function openCreate() {
   240|  editing.value = false; editId.value = ''
   241|  form.name = ''; form.description = ''; form.status = 'draft'; form.risk_level = 'low'; form.steps = []
   242|  showDialog.value = true
   243|}
   244|
   245|function openEdit(row: any) {
   246|  editing.value = true; editId.value = row.id
   247|  form.name = row.name; form.description = row.description || ''; form.status = row.status || 'draft'
   248|  form.risk_level = row.risk_level || 'low'
   249|  form.steps = (row.steps || []).map((s: any) => ({ ...s, params_json: typeof s.params === 'object' ? JSON.stringify(s.params) : (s.params_json || '') }))
   250|  showDialog.value = true
   251|}
   252|
   253|async function save() {
   254|  if (!form.name) return ElMessage.warning('请输入名称')
   255|  try {
   256|    const payload = { ...form, steps: form.steps.map(s => ({ ...s, params: s.params_json ? JSON.parse(s.params_json) : {} })) }
   257|    if (editing.value) await api.put(`${API.PLAYBOOKS}/${editId.value}`, payload)
   258|    else await api.post(API.PLAYBOOKS, payload)
   259|    ElMessage.success('保存成功'); showDialog.value = false; load()
   260|  } catch (e: any) { ElMessage.error(e?.message || '保存失败') }
   261|}
   262|
   263|async function viewDetail(row: any) {
   264|  try {
   265|    const res = await api.get(`${API.PLAYBOOKS}/${row.id}`)
   266|    if (res.data?.code === 0) detail.value = res.data.data
   267|    else detail.value = row
   268|  } catch { detail.value = row }
   269|  showDetail.value = true
   270|  loadExecHistory(row.id)
   271|}
   272|
   273|async function loadExecHistory(playbookId: string) {
   274|  execLoading.value = true
   275|  try {
   276|    const res = await api.get(API.EXECUTIONS, { params: { playbook_id: playbookId, page_size: 10 } })
   277|    if (res.data?.code === 0) execHistory.value = res.data.data?.items || res.data.data || []
   278|  } catch { execHistory.value = [] }
   279|  finally { execLoading.value = false }
   280|}
   281|
   282|async function duplicate(row: any) {
   283|  try {
   284|    const payload = { ...row, name: `${row.name} (副本)`, status: 'draft', id: undefined, created_at: undefined, updated_at: undefined }
   285|    await api.post(API.PLAYBOOKS, payload)
   286|    ElMessage.success('复制成功'); load()
   287|  } catch { ElMessage.error('复制失败') }
   288|}
   289|
   290|function quickExec(row: any) {
   291|  router.push({ path: '/executions', query: { playbook_id: row.id, playbook_name: row.name } })
   292|}
   293|
   294|async function remove(row: any) {
   295|  try {
   296|    await ElMessageBox.confirm('确定删除此 Playbook？关联策略将失效。', '确认删除', { type: 'warning' })
   297|    await api.delete(`${API.PLAYBOOKS}/${row.id}`)
   298|    ElMessage.success('已删除'); load()
   299|  } catch {}
   300|}
   301|
   302|function getScriptName(id: string) { return scripts.value.find(s => s.id === id)?.name || id || '-' }
   303|function statusLabel(s: string) { return ({ draft:'草稿', active:'已激活', deprecated:'已废弃' })[s] || s }
   304|function riskType(r: string) { return ({ low:'info', medium:'warning', high:'danger', critical:'danger' })[r] || 'info' }
   305|function fmt(t: string) { return t ? new Date(t).toLocaleString('zh-CN') : '-' }
   306|
   307|onMounted(() => { load(); loadScripts() })
   308|</script>
   309|
   310|<style scoped>
   311|
   312|.stat-row { margin-bottom: 20px; }
   313|
   314|.stat-card 
   315|.stat-card.success .stat-value { color: #00b42a; }
   316|.stat-card.primary .stat-value { color: #165dff; }
   317|.stat-card.warning .stat-value { color: #ff7d00; }
   318|.stat-card 
   319|.toolbar { margin-bottom: 16px; display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
   320|.pagination { margin-top: 16px; display: flex; justify-content: flex-end; }
   321|.step-orchestrator { background: #f7f8fa; padding: 12px; border-radius: 4px; }
   322|.step-item { background: #fff; border: 1px solid #e5e6eb; border-radius: 4px; padding: 10px; margin-bottom: 8px; }
   323|.step-header { display: flex; gap: 6px; align-items: center; }
   324|.step-number { width: 24px; height: 24px; background: #165dff; color: #fff; border-radius: 50%; text-align: center; line-height: 24px; font-size: 12px; flex-shrink: 0; }
   325|.step-params { display: flex; margin-top: 8px; padding-left: 30px; }
   326|.flow-preview { display: flex; align-items: center; gap: 4px; flex-wrap: wrap; padding: 8px; background: #fafafa; border-radius: 4px; }
   327|.flow-box { background: #165dff; color: #fff; padding: 4px 12px; border-radius: 4px; font-size: 12px; }
   328|.flow-arrow { color: #86909c; font-size: 16px; }
   329|</style>
   330|