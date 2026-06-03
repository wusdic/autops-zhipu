     1|<template>
     2|  <div class="page-container">
     3|    <div class="autops-page-header">
     4|      <div>
     5|        <div class="autops-page-title">策略管理</div>
     6|        <div class="autops-page-desc">配置自动化触发策略</div>
     7|      </div>
     8|    </div>
     9|
    10|    <el-row :gutter="16" class="stat-row">
    11|      <el-col :span="6"><div class="autops-card stat-card"><div class="stat-value">{{ stats.total }}</div><div class="stat-label">策略总数</div></div></el-col>
    12|      <el-col :span="6"><div class="autops-card stat-card success"><div class="stat-value">{{ stats.active }}</div><div class="stat-label">已激活</div></div></el-col>
    13|      <el-col :span="6"><div class="autops-card stat-card danger"><div class="stat-value">{{ stats.highRisk }}</div><div class="stat-label">高风险</div></div></el-col>
    14|      <el-col :span="6"><div class="autops-card stat-card warning"><div class="stat-value">{{ stats.pendingApproval }}</div><div class="stat-label">待审批</div></div></el-col>
    15|    </el-row>
    16|
    17|    <div class="autops-toolbar">
    18|      <el-input v-model="filters.keyword" placeholder="搜索策略" clearable style="width:200px;margin-right:8px" @clear="load" @keyup.enter="load" />
    19|      <el-select v-model="filters.status" placeholder="状态" clearable style="width:120px;margin-right:8px">
    20|        <el-option label="草稿" value="draft" /><el-option label="已激活" value="active" /><el-option label="已废弃" value="deprecated" />
    21|      </el-select>
    22|      <el-select v-model="filters.risk_level" placeholder="风险等级" clearable style="width:120px;margin-right:8px">
    23|        <el-option label="低" value="low" /><el-option label="中" value="medium" /><el-option label="高" value="high" /><el-option label="严重" value="critical" />
    24|      </el-select>
    25|      <el-select v-model="filters.trigger_source" placeholder="触发源" clearable style="width:130px;margin-right:8px">
    26|        <el-option label="事件" value="event" /><el-option label="告警" value="alert" /><el-option label="状态变更" value="state_change" /><el-option label="手动" value="manual" /><el-option label="定时" value="schedule" />
    27|      </el-select>
    28|      <el-button type="primary" @click="load"><el-icon><Search /></el-icon> 搜索</el-button>
    29|      <el-button @click="resetFilters">重置</el-button>
    30|      <div style="flex:1" />
    31|      <el-button type="primary" @click="openCreate"><el-icon><Plus /></el-icon> 新建策略</el-button>
    32|    </div>
    33|
    34|    <el-table stripe :data="items" v-loading="loading">
    35|      <el-table-column prop="name" label="名称" min-width="160">
    36|        <template #default="{ row }"><el-link type="primary" @click="viewDetail(row)">{{ row.name }}</el-link></template>
    37|      </el-table-column>
    38|      <el-table-column prop="trigger_type" label="触发类型" width="100">
    39|        <template #default="{ row }"><el-tag size="small">{{ triggerLabel(row.trigger_type) }}</el-tag></template>
    40|      </el-table-column>
    41|      <el-table-column prop="risk_level" label="风险" width="80">
    42|        <template #default="{ row }"><el-tag :type="riskType(row.risk_level)" size="small">{{ row.risk_level }}</el-tag></template>
    43|      </el-table-column>
    44|      <el-table-column prop="status" label="状态" width="90">
    45|        <template #default="{ row }"><el-tag :type="row.status==='active'?'success':'info'" size="small">{{ statusLabel(row.status) }}</el-tag></template>
    46|      </el-table-column>
    47|      <el-table-column label="范围" min-width="140" show-overflow-tooltip>
    48|        <template #default="{ row }">{{ row.scope_description || '-' }}</template>
    49|      </el-table-column>
    50|      <el-table-column label="动作数" width="80" align="center">
    51|        <template #default="{ row }">{{ row.action_chain?.length || 0 }}</template>
    52|      </el-table-column>
    53|      <el-table-column prop="created_at" label="创建时间" width="170">
    54|        <template #default="{ row }">{{ fmt(row.created_at) }}</template>
    55|      </el-table-column>
    56|      <el-table-column label="操作" width="240" fixed="right">
    57|        <template #default="{ row }">
    58|          <el-button size="small" @click="viewDetail(row)">详情</el-button>
    59|          <el-button size="small" type="primary" @click="openEdit(row)">编辑</el-button>
    60|          <el-button size="small" type="warning" @click="simulate(row)">模拟</el-button>
    61|          <el-button size="small" @click="duplicate(row)">复制</el-button>
    62|          <el-button size="small" :type="row.status==='active'?'info':'success'" @click="toggleStatus(row)">{{ row.status==='active'?'停用':'激活' }}</el-button>
    63|        </template>
    64|      </el-table-column>
    65|    </el-table>
    66|    <el-pagination v-if="total > pageSize" class="pagination" :current-page="page" :page-size="pageSize" :total="total" @current-change="(p:number)=>{page=p;load()}" layout="total, prev, pager, next" />
    67|
    68|    <!-- 创建/编辑对话框 -->
    69|    <el-dialog v-model="showDialog" :title="editing?'编辑策略':'新建策略'" width="780px" top="5vh">
    70|      <el-form :model="form" label-width="110px">
    71|        <el-row :gutter="16">
    72|          <el-col :span="12"><el-form-item label="策略名称" required><el-input v-model="form.name" /></el-form-item></el-col>
    73|          <el-col :span="12"><el-form-item label="触发源">
    74|            <el-select v-model="form.trigger_source" style="width:100%">
    75|              <el-option label="事件" value="event" /><el-option label="告警" value="alert" /><el-option label="状态变更" value="state_change" /><el-option label="手动" value="manual" /><el-option label="定时" value="schedule" />
    76|            </el-select>
    77|          </el-form-item></el-col>
    78|        </el-row>
    79|        <el-form-item label="描述"><el-input v-model="form.description" type="textarea" :rows="2" /></el-form-item>
    80|
    81|        <!-- 触发条件可视化编辑 -->
    82|        <el-divider content-position="left">触发条件</el-divider>
    83|        <div class="condition-builder">
    84|          <el-radio-group v-model="form.condition_logic" size="small" style="margin-bottom:8px">
    85|            <el-radio-button value="AND">全部满足(AND)</el-radio-button>
    86|            <el-radio-button value="OR">任一满足(OR)</el-radio-button>
    87|          </el-radio-group>
    88|          <div v-for="(cond, idx) in form.conditions" :key="idx" class="condition-row">
    89|            <el-select v-model="cond.field" placeholder="字段" style="width:180px" size="small">
    90|              <el-option label="CPU使用率" value="cpu_usage" /><el-option label="内存使用率" value="memory_usage" />
    91|              <el-option label="磁盘使用率" value="disk_usage" /><el-option label="响应时间" value="response_time" />
    92|              <el-option label="状态码" value="status_code" /><el-option label="事件类型" value="event_type" />
    93|              <el-option label="告警级别" value="alert_severity" /><el-option label="端口状态" value="port_status" />
    94|              <el-option label="进程状态" value="process_status" /><el-option label="自定义" value="custom" />
    95|            </el-select>
    96|            <el-select v-model="cond.operator" style="width:100px" size="small">
    97|              <el-option label=">" value="gt" /><el-option label=">=" value="gte" />
    98|              <el-option label="<" value="lt" /><el-option label="<=" value="lte" />
    99|              <el-option label="=" value="eq" /><el-option label="!=" value="neq" />
   100|              <el-option label="包含" value="contains" /><el-option label="匹配" value="matches" />
   101|            </el-select>
   102|            <el-input v-model="cond.value" placeholder="值" style="width:150px" size="small" />
   103|            <el-input v-model="cond.duration" placeholder="持续时间(可选)" style="width:130px" size="small" />
   104|            <el-button size="small" type="danger" @click="form.conditions.splice(idx,1)"><el-icon><Delete /></el-icon></el-button>
   105|          </div>
   106|          <el-button type="primary" plain size="small" @click="addCondition" style="margin-top:4px"><el-icon><Plus /></el-icon> 添加条件</el-button>
   107|        </div>
   108|
   109|        <!-- 适用范围 -->
   110|        <el-divider content-position="left">适用范围</el-divider>
   111|        <el-row :gutter="16">
   112|          <el-col :span="12">
   113|            <el-form-item label="资产分组">
   114|              <el-select v-model="form.scope_groups" multiple placeholder="选择分组" style="width:100%">
   115|                <el-option v-for="g in groups" :key="g.id" :label="g.name" :value="g.id" />
   116|              </el-select>
   117|            </el-form-item>
   118|          </el-col>
   119|          <el-col :span="12">
   120|            <el-form-item label="资产类型">
   121|              <el-select v-model="form.scope_asset_types" multiple placeholder="类型筛选" style="width:100%">
   122|                <el-option label="Linux" value="linux_server" /><el-option label="Windows" value="windows_server" />
   123|                <el-option label="网络设备" value="network_device" /><el-option label="数据库" value="database" />
   124|                <el-option label="Web服务" value="web_service" />
   125|              </el-select>
   126|            </el-form-item>
   127|          </el-col>
   128|        </el-row>
   129|
   130|        <!-- 动作链 -->
   131|        <el-divider content-position="left">动作链</el-divider>
   132|        <div class="action-chain">
   133|          <div v-for="(act, idx) in form.actions" :key="idx" class="action-item">
   134|            <span class="action-num">{{ idx+1 }}</span>
   135|            <el-select v-model="act.type" style="width:130px" size="small">
   136|              <el-option label="执行脚本" value="script" /><el-option label="执行Playbook" value="playbook" />
   137|              <el-option label="发送通知" value="notification" /><el-option label="创建工单" value="ticket" />
   138|              <el-option label="抑制告警" value="suppress" />
   139|            </el-select>
   140|            <el-input v-model="act.target" placeholder="目标(脚本/Playbook ID)" style="width:200px" size="small" />
   141|            <el-input v-model="act.params_json" placeholder="参数 JSON" style="width:200px" size="small" />
   142|            <el-button size="small" type="danger" @click="form.actions.splice(idx,1)"><el-icon><Delete /></el-icon></el-button>
   143|          </div>
   144|          <el-button type="primary" plain size="small" @click="addAction"><el-icon><Plus /></el-icon> 添加动作</el-button>
   145|        </div>
   146|
   147|        <el-row :gutter="16" style="margin-top:16px">
   148|          <el-col :span="8"><el-form-item label="风险等级"><el-select v-model="form.risk_level" style="width:100%">
   149|            <el-option label="低" value="low" /><el-option label="中" value="medium" /><el-option label="高" value="high" /><el-option label="严重" value="critical" />
   150|          </el-select></el-form-item></el-col>
   151|          <el-col :span="8"><el-form-item label="需要审批"><el-switch v-model="form.requires_approval" /></el-form-item></el-col>
   152|          <el-col :span="8"><el-form-item label="最大影响面"><el-input-number v-model="form.max_impact" :min="1" :max="1000" style="width:100%" /></el-form-item></el-col>
   153|        </el-row>
   154|      </el-form>
   155|      <template #footer>
   156|        <el-button @click="showDialog=false">取消</el-button>
   157|        <el-button type="primary" @click="save">保存</el-button>
   158|      </template>
   159|    </el-dialog>
   160|
   161|    <!-- 详情抽屉 -->
   162|    <el-drawer v-model="showDetail" :title="detail?.name || '策略详情'" size="620px">
   163|      <template v-if="detail">
   164|        <el-descriptions :column="2" border>
   165|          <el-descriptions-item label="名称">{{ detail.name }}</el-descriptions-item>
   166|          <el-descriptions-item label="触发源"><el-tag size="small">{{ triggerLabel(detail.trigger_source) }}</el-tag></el-descriptions-item>
   167|          <el-descriptions-item label="风险等级"><el-tag :type="riskType(detail.risk_level)" size="small">{{ detail.risk_level }}</el-tag></el-descriptions-item>
   168|          <el-descriptions-item label="状态"><el-tag :type="detail.status==='active'?'success':'info'" size="small">{{ statusLabel(detail.status) }}</el-tag></el-descriptions-item>
   169|          <el-descriptions-item label="需要审批">{{ detail.requires_approval ? '是' : '否' }}</el-descriptions-item>
   170|          <el-descriptions-item label="最大影响面">{{ detail.max_impact || '-' }}</el-descriptions-item>
   171|          <el-descriptions-item label="描述" :span="2">{{ detail.description || '-' }}</el-descriptions-item>
   172|        </el-descriptions>
   173|
   174|        <h4 style="margin:16px 0 8px">触发条件</h4>
   175|        <div v-if="detail.conditions?.length">
   176|          <div v-for="(c,i) in detail.conditions" :key="i" class="cond-display">
   177|            <el-tag size="small" type="info">{{ c.field }}</el-tag>
   178|            <span class="cond-op">{{ c.operator }}</span>
   179|            <el-tag size="small">{{ c.value }}</el-tag>
   180|            <span v-if="c.duration" class="cond-dur">持续 {{ c.duration }}</span>
   181|          </div>
   182|          <div class="cond-logic">逻辑: <strong>{{ detail.condition_logic || 'AND' }}</strong></div>
   183|        </div>
   184|        <el-empty v-else description="无条件" :image-size="40" />
   185|
   186|        <h4 style="margin:16px 0 8px">适用范围</h4>
   187|        <el-tag v-for="g in detail.scope_groups" :key="g" style="margin-right:4px">{{ getGroupName(g) }}</el-tag>
   188|        <el-tag v-for="t in detail.scope_asset_types" :key="t" type="info" style="margin-right:4px">{{ t }}</el-tag>
   189|
   190|        <h4 style="margin:16px 0 8px">动作链</h4>
   191|        <el-timeline v-if="detail.actions?.length">
   192|          <el-timeline-item v-for="(a,i) in detail.actions" :key="i" :timestamp="`步骤 ${i+1}`" placement="top">
   193|            <el-tag>{{ actionTypeLabel(a.type) }}</el-tag> → {{ a.target || '-' }}
   194|          </el-timeline-item>
   195|        </el-timeline>
   196|        <el-empty v-else description="无动作" :image-size="40" />
   197|
   198|        <div style="margin-top:16px;display:flex;gap:8px">
   199|          <el-button type="primary" @click="openEdit(detail);showDetail=false">编辑</el-button>
   200|          <el-button type="warning" @click="simulate(detail);showDetail=false">模拟执行</el-button>
   201|          <el-button @click="duplicate(detail);showDetail=false">复制</el-button>
   202|        </div>
   203|      </template>
   204|    </el-drawer>
   205|  </div>
   206|</template>
   207|
   208|<script setup lang="ts">
   209|import { ref, reactive, onMounted } from 'vue'
   210|import { useRouter } from 'vue-router'
   211|import { ElMessage, ElMessageBox } from 'element-plus'
   212|import { Plus, Search, Delete } from '@element-plus/icons-vue'
   213|import api from '@/shared/api/client'
   214|import { API } from '@/shared/api/routes'
   215|
   216|const router = useRouter()
   217|const stats = reactive({ total: 0, active: 0, highRisk: 0, pendingApproval: 0 })
   218|const filters = reactive({ keyword: '', status: '', risk_level: '', trigger_source: '' })
   219|const items = ref<any[]>([])
   220|const loading = ref(false)
   221|const page = ref(1)
   222|const pageSize = 20
   223|const total = ref(0)
   224|const groups = ref<any[]>([])
   225|
   226|const showDialog = ref(false)
   227|const editing = ref(false)
   228|const editId = ref('')
   229|const form = reactive({
   230|  name: '', description: '', trigger_source: 'event', condition_logic: 'AND',
   231|  conditions: [] as any[], scope_groups: [] as string[], scope_asset_types: [] as string[],
   232|  actions: [] as any[], risk_level: 'low', requires_approval: false, max_impact: 10,
   233|})
   234|
   235|const showDetail = ref(false)
   236|const detail = ref<any>(null)
   237|
   238|function resetFilters() { Object.assign(filters, { keyword:'', status:'', risk_level:'', trigger_source:'' }); load() }
   239|
   240|async function load() {
   241|  loading.value = true
   242|  try {
   243|    const params: any = { page: page.value, page_size: pageSize }
   244|    if (filters.keyword) params.keyword = filters.keyword
   245|    if (filters.status) params.status = filters.status
   246|    if (filters.risk_level) params.risk_level = filters.risk_level
   247|    if (filters.trigger_source) params.trigger_source = filters.trigger_source
   248|    const res = await api.get(API.POLICIES, { params })
   249|    if (res.data?.code === 0) {
   250|      items.value = res.data.data?.items || res.data.data || []
   251|      total.value = res.data.data?.total || items.value.length
   252|    }
   253|    computeStats()
   254|  } catch { ElMessage.error('加载失败') }
   255|  finally { loading.value = false }
   256|}
   257|
   258|function computeStats() {
   259|  stats.total = items.value.length
   260|  stats.active = items.value.filter(i => i.status === 'active').length
   261|  stats.highRisk = items.value.filter(i => ['high','critical'].includes(i.risk_level)).length
   262|  stats.pendingApproval = items.value.filter(i => i.requires_approval && i.status === 'draft').length
   263|}
   264|
   265|async function loadGroups() {
   266|  try {
   267|    const res = await api.get(API.ASSET_GROUPS, { params: { page_size: 100 } })
   268|    if (res.data?.code === 0) groups.value = res.data.data?.items || res.data.data || []
   269|  } catch {}
   270|}
   271|
   272|function addCondition() { form.conditions.push({ field: '', operator: 'gt', value: '', duration: '' }) }
   273|function addAction() { form.actions.push({ type: 'script', target: '', params_json: '' }) }
   274|
   275|function openCreate() {
   276|  editing.value = false; editId.value = ''
   277|  Object.assign(form, { name:'', description:'', trigger_source:'event', condition_logic:'AND', conditions:[], scope_groups:[], scope_asset_types:[], actions:[], risk_level:'low', requires_approval:false, max_impact:10 })
   278|  showDialog.value = true
   279|}
   280|
   281|function openEdit(row: any) {
   282|  editing.value = true; editId.value = row.id
   283|  Object.assign(form, {
   284|    name: row.name, description: row.description||'', trigger_source: row.trigger_source||'event',
   285|    condition_logic: row.condition_logic||'AND', conditions: row.conditions?.length ? [...row.conditions] : [],
   286|    scope_groups: row.scope_groups||[], scope_asset_types: row.scope_asset_types||[],
   287|    actions: row.actions?.length ? [...row.actions] : [], risk_level: row.risk_level||'low',
   288|    requires_approval: !!row.requires_approval, max_impact: row.max_impact||10,
   289|  })
   290|  showDialog.value = true
   291|}
   292|
   293|async function save() {
   294|  if (!form.name) return ElMessage.warning('请输入名称')
   295|  try {
   296|    if (editing.value) await api.put(API.POLICY_DETAIL(editId.value), form)
   297|    else await api.post(API.POLICIES, form)
   298|    ElMessage.success('保存成功'); showDialog.value = false; load()
   299|  } catch (e: any) { ElMessage.error(e?.message || '保存失败') }
   300|}
   301|
   302|async function viewDetail(row: any) {
   303|  try {
   304|    const res = await api.get(API.POLICY_DETAIL(row.id))
   305|    if (res.data?.code === 0) detail.value = res.data.data
   306|    else detail.value = row
   307|  } catch { detail.value = row }
   308|  showDetail.value = true
   309|}
   310|
   311|function simulate(row: any) { router.push(`/policies/${row.id}/simulate`) }
   312|
   313|async function duplicate(row: any) {
   314|  try {
   315|    const payload = { ...row, name: `${row.name} (副本)`, status: 'draft', id: undefined }
   316|    await api.post(API.POLICIES, payload)
   317|    ElMessage.success('复制成功'); load()
   318|  } catch { ElMessage.error('复制失败') }
   319|}
   320|
   321|async function toggleStatus(row: any) {
   322|  const newStatus = row.status === 'active' ? 'draft' : 'active'
   323|  try {
   324|    await api.patch(API.POLICY_DETAIL(row.id), { status: newStatus })
   325|    ElMessage.success(newStatus === 'active' ? '已激活' : '已停用'); load()
   326|  } catch { ElMessage.error('操作失败') }
   327|}
   328|
   329|function getGroupName(id: string) { return groups.value.find(g => g.id === id)?.name || id }
   330|function triggerLabel(s: string) { return ({ event:'事件', alert:'告警', state_change:'状态变更', manual:'手动', schedule:'定时' })[s] || s }
   331|function actionTypeLabel(t: string) { return ({ script:'脚本', playbook:'Playbook', notification:'通知', ticket:'工单', suppress:'抑制' })[t] || t }
   332|function statusLabel(s: string) { return ({ draft:'草稿', active:'已激活', deprecated:'已废弃' })[s] || s }
   333|function riskType(r: string) { return ({ low:'info', medium:'warning', high:'danger', critical:'danger' })[r] || 'info' }
   334|function fmt(t: string) { return t ? new Date(t).toLocaleString('zh-CN') : '-' }
   335|
   336|onMounted(() => { load(); loadGroups() })
   337|</script>
   338|
   339|<style scoped>
   340|
   341|.stat-row { margin-bottom: 20px; }
   342|
   343|.stat-card 
   344|.stat-card.success .stat-value { color: #00b42a; }
   345|.stat-card.danger .stat-value { color: #f53f3f; }
   346|.stat-card.warning .stat-value { color: #ff7d00; }
   347|.stat-card 
   348|.toolbar { margin-bottom: 16px; display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
   349|.pagination { margin-top: 16px; display: flex; justify-content: flex-end; }
   350|.condition-builder { background: #f7f8fa; padding: 12px; border-radius: 4px; }
   351|.condition-row { display: flex; gap: 6px; align-items: center; margin-bottom: 6px; }
   352|.action-chain { background: #f7f8fa; padding: 12px; border-radius: 4px; }
   353|.action-item { display: flex; gap: 6px; align-items: center; margin-bottom: 6px; }
   354|.action-num { width: 22px; height: 22px; background: #ff7d00; color: #fff; border-radius: 50%; text-align: center; line-height: 22px; font-size: 11px; }
   355|.cond-display { display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }
   356|.cond-op { color: #86909c; font-weight: bold; }
   357|.cond-dur { color: #165dff; font-size: 12px; }
   358|.cond-logic { margin-top: 6px; color: #4e5969; font-size: 13px; }
   359|</style>
   360|