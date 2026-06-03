     1|<template>
     2|  <div class="page-container">
     3|    <!-- ========== Page Header ========== -->
     4|    <div class="autops-page-header">
     5|      <div>
     6|        <div class="autops-page-title">告警规则</div>
     7|        <div class="autops-page-desc">配置指标阈值与触发条件，实现自动化告警</div>
     8|      </div>
     9|    </div>
    10|
    11|    <el-row :gutter="16" class="stat-row mb-lg">
    12|      <el-col :span="6"><div class="autops-card stat-card"><div class="autops-card-body"><div class="stat-value">{{ stats.total }}</div><div class="stat-label">规则总数</div></div></div></el-col>
    13|      <el-col :span="6"><div class="autops-card stat-card success"><div class="autops-card-body"><div class="stat-value">{{ stats.active }}</div><div class="stat-label">已启用</div></div></div></el-col>
    14|      <el-col :span="6"><div class="autops-card stat-card warning"><div class="autops-card-body"><div class="stat-value">{{ stats.triggeredToday }}</div><div class="stat-label">今日触发</div></div></div></el-col>
    15|      <el-col :span="6"><div class="autops-card stat-card primary"><div class="autops-card-body"><div class="stat-value">{{ stats.mostTriggered || '-' }}</div><div class="stat-label">最常触发</div></div></div></el-col>
    16|    </el-row>
    17|
    18|    <div class="autops-toolbar">
    19|      <el-input v-model="filters.keyword" placeholder="搜索规则" clearable style="width:200px;" @clear="load" @keyup.enter="load" />
    20|      <el-select v-model="filters.severity" placeholder="严重度" clearable style="width:120px;margin-right:8px">
    21|        <el-option label="严重" value="critical" /><el-option label="警告" value="warning" /><el-option label="信息" value="info" />
    22|      </el-select>
    23|      <el-select v-model="filters.status" placeholder="状态" clearable style="width:120px;margin-right:8px">
    24|        <el-option label="启用" value="active" /><el-option label="停用" value="inactive" />
    25|      </el-select>
    26|      <el-select v-model="filters.metric" placeholder="指标类型" clearable style="width:140px;margin-right:8px">
    27|        <el-option label="CPU" value="cpu_usage" /><el-option label="内存" value="memory_usage" /><el-option label="磁盘" value="disk_usage" />
    28|        <el-option label="网络入" value="network_in" /><el-option label="网络出" value="network_out" /><el-option label="响应时间" value="response_time" />
    29|        <el-option label="状态检查" value="status_check" /><el-option label="自定义" value="custom" />
    30|      </el-select>
    31|      <el-button type="primary" @click="load"><el-icon><Search /></el-icon> 搜索</el-button>
    32|      <el-button @click="resetFilters">重置</el-button>
    33|      <div style="flex:1" />
    34|      <el-button type="primary" @click="openCreate"><el-icon><Plus /></el-icon> 新建规则</el-button>
    35|    </div>
    36|
    37|    <el-table stripe :data="items" v-loading="loading">
    38|      <el-table-column prop="name" label="规则名称" min-width="160">
    39|        <template #default="{ row }"><el-link type="primary" @click="viewDetail(row)">{{ row.name }}</el-link></template>
    40|      </el-table-column>
    41|      <el-table-column label="指标" width="120">
    42|        <template #default="{ row }"><el-tag size="small">{{ metricLabel(row.metric) }}</el-tag></template>
    43|      </el-table-column>
    44|      <el-table-column label="条件" min-width="180">
    45|        <template #default="{ row }">
    46|          <span v-if="row.conditions?.length">
    47|            <span v-for="(c,i) in row.conditions.slice(0,2)" :key="i">
    48|              {{ c.field }} {{ c.operator }} {{ c.value }}{{ c.unit||'' }}
    49|              <span v-if="i < Math.min(row.conditions.length,2)-1" style="color:#86909c">{{ row.condition_logic||'AND' }} </span>
    50|            </span>
    51|            <span v-if="row.conditions.length > 2" style="color:#86909c">+{{ row.conditions.length-2 }}</span>
    52|          </span>
    53|          <span v-else>-</span>
    54|        </template>
    55|      </el-table-column>
    56|      <el-table-column prop="severity" label="严重度" width="90">
    57|        <template #default="{ row }"><el-tag :type="severityType(row.severity)" size="small">{{ row.severity }}</el-tag></template>
    58|      </el-table-column>
    59|      <el-table-column label="状态" width="80">
    60|        <template #default="{ row }">
    61|          <el-switch v-model="row._active" size="small" @change="toggleRule(row)" />
    62|        </template>
    63|      </el-table-column>
    64|      <el-table-column prop="trigger_count" label="触发次数" width="90" align="center" />
    65|      <el-table-column prop="created_at" label="创建时间" width="170">
    66|        <template #default="{ row }">{{ fmt(row.created_at) }}</template>
    67|      </el-table-column>
    68|      <el-table-column label="操作" width="180" fixed="right">
    69|        <template #default="{ row }">
    70|          <el-button size="small" @click="viewDetail(row)">详情</el-button>
    71|          <el-button size="small" type="primary" @click="openEdit(row)">编辑</el-button>
    72|          <el-button size="small" @click="testRule(row)">测试</el-button>
    73|          <el-button size="small" @click="duplicateRule(row)">复制</el-button>
    74|        </template>
    75|      </el-table-column>
    76|    </el-table>
    77|    <el-pagination v-if="total > pageSize" class="pagination" :current-page="page" :page-size="pageSize" :total="total" @current-change="(p:number)=>{page=p;load()}" layout="total, prev, pager, next" />
    78|
    79|    <!-- 创建/编辑对话框 -->
    80|    <el-dialog v-model="showDialog" :title="editing?'编辑规则':'新建规则'" width="780px" top="5vh">
    81|      <el-form :model="form" label-width="100px">
    82|        <el-row :gutter="16">
    83|          <el-col :span="12"><el-form-item label="规则名称" required><el-input v-model="form.name" placeholder="例如: CPU使用率过高" /></el-form-item></el-col>
    84|          <el-col :span="12"><el-form-item label="严重度">
    85|            <el-select v-model="form.severity" style="width:100%">
    86|              <el-option label="严重" value="critical" /><el-option label="警告" value="warning" /><el-option label="信息" value="info" />
    87|            </el-select>
    88|          </el-form-item></el-col>
    89|        </el-row>
    90|        <el-form-item label="描述"><el-input v-model="form.description" type="textarea" :rows="2" /></el-form-item>
    91|
    92|        <!-- 条件可视化编辑器 -->
    93|        <el-divider content-position="left">告警条件</el-divider>
    94|        <div class="condition-editor">
    95|          <el-radio-group v-model="form.condition_logic" size="small" style="margin-bottom:8px">
    96|            <el-radio-button value="AND">全部满足(AND)</el-radio-button>
    97|            <el-radio-button value="OR">任一满足(OR)</el-radio-button>
    98|          </el-radio-group>
    99|          <div v-for="(cond, idx) in form.conditions" :key="idx" class="cond-row">
   100|            <el-select v-model="cond.metric" placeholder="指标" style="width:160px" size="small">
   101|              <el-option label="CPU使用率" value="cpu_usage" /><el-option label="内存使用率" value="memory_usage" />
   102|              <el-option label="磁盘使用率" value="disk_usage" /><el-option label="网络入流量" value="network_in" />
   103|              <el-option label="网络出流量" value="network_out" /><el-option label="响应时间" value="response_time" />
   104|              <el-option label="状态码" value="status_code" /><el-option label="连接数" value="connection_count" />
   105|              <el-option label="进程数" value="process_count" /><el-option label="自定义" value="custom" />
   106|            </el-select>
   107|            <el-select v-model="cond.operator" style="width:90px" size="small">
   108|              <el-option label=">" value=">" /><el-option label=">=" value=">=" />
   109|              <el-option label="<" value="<" /><el-option label="<=" value="<=" />
   110|              <el-option label="=" value="=" /><el-option label="!=" value="!=" />
   111|            </el-select>
   112|            <el-input-number v-model="cond.value" :min="0" placeholder="阈值" style="width:130px" size="small" />
   113|            <el-select v-model="cond.unit" style="width:80px" size="small" placeholder="单位">
   114|              <el-option label="%" value="%" /><el-option label="ms" value="ms" />
   115|              <el-option label="MB" value="MB" /><el-option label="GB" value="GB" />
   116|              <el-option label="次" value="次" /><el-option label="" value="" />
   117|            </el-select>
   118|            <el-select v-model="cond.duration" style="width:120px" size="small" placeholder="持续时间">
   119|              <el-option label="即时" value="" /><el-option label="30秒" value="30s" />
   120|              <el-option label="1分钟" value="1m" /><el-option label="5分钟" value="5m" />
   121|              <el-option label="15分钟" value="15m" /><el-option label="30分钟" value="30m" />
   122|              <el-option label="1小时" value="1h" />
   123|            </el-select>
   124|            <el-button size="small" type="danger" @click="form.conditions.splice(idx,1)"><el-icon><Delete /></el-icon></el-button>
   125|          </div>
   126|          <el-button type="primary" plain size="small" @click="addCondition" style="margin-top:4px"><el-icon><Plus /></el-icon> 添加条件</el-button>
   127|        </div>
   128|
   129|        <el-row :gutter="16" style="margin-top:16px">
   130|          <el-col :span="8"><el-form-item label="通知方式"><el-select v-model="form.notify_type" style="width:100%">
   131|            <el-option label="站内通知" value="internal" /><el-option label="邮件" value="email" /><el-option label="全部" value="all" />
   132|          </el-select></el-form-item></el-col>
   133|          <el-col :span="8"><el-form-item label="重复间隔"><el-select v-model="form.repeat_interval" style="width:100%">
   134|            <el-option label="不重复" value="" /><el-option label="5分钟" value="5m" /><el-option label="15分钟" value="15m" />
   135|            <el-option label="1小时" value="1h" /><el-option label="24小时" value="24h" />
   136|          </el-select></el-form-item></el-col>
   137|          <el-col :span="8"><el-form-item label="状态"><el-switch v-model="form.active" active-text="启用" inactive-text="停用" /></el-form-item></el-col>
   138|        </el-row>
   139|      </el-form>
   140|      <template #footer>
   141|        <el-button @click="showDialog=false">取消</el-button>
   142|        <el-button type="primary" @click="save">保存</el-button>
   143|      </template>
   144|    </el-dialog>
   145|
   146|    <!-- 详情抽屉 -->
   147|    <el-drawer v-model="showDetail" :title="detail?.name || '规则详情'" size="560px">
   148|      <template v-if="detail">
   149|        <el-descriptions :column="2" border>
   150|          <el-descriptions-item label="名称">{{ detail.name }}</el-descriptions-item>
   151|          <el-descriptions-item label="严重度"><el-tag :type="severityType(detail.severity)" size="small">{{ detail.severity }}</el-tag></el-descriptions-item>
   152|          <el-descriptions-item label="状态">{{ detail.active !== false ? '启用' : '停用' }}</el-descriptions-item>
   153|          <el-descriptions-item label="触发次数">{{ detail.trigger_count || 0 }}</el-descriptions-item>
   154|          <el-descriptions-item label="描述" :span="2">{{ detail.description || '-' }}</el-descriptions-item>
   155|        </el-descriptions>
   156|
   157|        <h4 style="margin:16px 0 8px">条件详情</h4>
   158|        <div v-if="detail.conditions?.length">
   159|          <div v-for="(c,i) in detail.conditions" :key="i" style="margin-bottom:6px">
   160|            <el-tag size="small">{{ metricLabel(c.metric) }}</el-tag>
   161|            <strong style="margin:0 4px">{{ c.operator }}</strong>
   162|            <el-tag size="small" type="warning">{{ c.value }}{{ c.unit||'' }}</el-tag>
   163|            <span v-if="c.duration" style="color:#165dff;margin-left:4px">持续 {{ c.duration }}</span>
   164|          </div>
   165|          <p style="color:#86909c;font-size:13px;margin-top:4px">逻辑: {{ detail.condition_logic || 'AND' }}</p>
   166|        </div>
   167|
   168|        <h4 style="margin:16px 0 8px">近期触发记录</h4>
   169|        <el-table stripe :data="triggerHistory"size="small">
   170|          <el-table-column prop="triggered_at" label="时间" width="170">
   171|            <template #default="{ row }">{{ fmt(row.triggered_at) }}</template>
   172|          </el-table-column>
   173|          <el-table-column prop="asset_name" label="资产" min-width="120" />
   174|          <el-table-column prop="actual_value" label="实际值" width="100" />
   175|        </el-table>
   176|      </template>
   177|    </el-drawer>
   178|  </div>
   179|</template>
   180|
   181|<script setup lang="ts">
   182|import { ref, reactive, onMounted } from 'vue'
   183|import { ElMessage } from 'element-plus'
   184|import { Plus, Search, Delete } from '@element-plus/icons-vue'
   185|import api from '@/shared/api/client'
   186|import { API } from '@/shared/api/routes'
   187|
   188|const stats = reactive({ total: 0, active: 0, triggeredToday: 0, mostTriggered: '' })
   189|const filters = reactive({ keyword: '', severity: '', status: '', metric: '' })
   190|const items = ref<any[]>([])
   191|const loading = ref(false)
   192|const page = ref(1)
   193|const pageSize = 20
   194|const total = ref(0)
   195|
   196|const showDialog = ref(false)
   197|const editing = ref(false)
   198|const editId = ref('')
   199|const form = reactive({
   200|  name: '', description: '', severity: 'warning', condition_logic: 'AND',
   201|  conditions: [] as any[], notify_type: 'internal', repeat_interval: '', active: true,
   202|})
   203|
   204|const showDetail = ref(false)
   205|const detail = ref<any>(null)
   206|const triggerHistory = ref<any[]>([])
   207|
   208|function resetFilters() { Object.assign(filters, { keyword:'', severity:'', status:'', metric:'' }); load() }
   209|
   210|async function load() {
   211|  loading.value = true
   212|  try {
   213|    const params: any = { page: page.value, page_size: pageSize }
   214|    if (filters.keyword) params.keyword = filters.keyword
   215|    if (filters.severity) params.severity = filters.severity
   216|    if (filters.status) params.status = filters.status === 'active'
   217|    if (filters.metric) params.metric = filters.metric
   218|    const res = await api.get(API.ALERT_RULES, { params })
   219|    if (res.data?.code === 0) {
   220|      items.value = (res.data.data?.items || res.data.data || []).map((r: any) => ({ ...r, _active: r.active !== false }))
   221|      total.value = res.data.data?.total || items.value.length
   222|    }
   223|    computeStats()
   224|  } catch { ElMessage.error('加载失败') }
   225|  finally { loading.value = false }
   226|}
   227|
   228|function computeStats() {
   229|  stats.total = items.value.length
   230|  stats.active = items.value.filter(i => i._active).length
   231|  stats.triggeredToday = items.value.reduce((a: number, i: any) => a + (i.trigger_count || 0), 0)
   232|  const sorted = [...items.value].sort((a: any, b: any) => (b.trigger_count||0) - (a.trigger_count||0))
   233|  stats.mostTriggered = sorted[0]?.name || ''
   234|}
   235|
   236|function addCondition() { form.conditions.push({ metric: 'cpu_usage', operator: '>', value: 90, unit: '%', duration: '' }) }
   237|
   238|function openCreate() {
   239|  editing.value = false; editId.value = ''
   240|  Object.assign(form, { name:'', description:'', severity:'warning', condition_logic:'AND', conditions:[], notify_type:'internal', repeat_interval:'', active:true })
   241|  addCondition()
   242|  showDialog.value = true
   243|}
   244|
   245|function openEdit(row: any) {
   246|  editing.value = true; editId.value = row.id
   247|  Object.assign(form, {
   248|    name: row.name, description: row.description||'', severity: row.severity||'warning',
   249|    condition_logic: row.condition_logic||'AND', conditions: row.conditions?.length ? [...row.conditions] : [],
   250|    notify_type: row.notify_type||'internal', repeat_interval: row.repeat_interval||'', active: row.active !== false,
   251|  })
   252|  if (!form.conditions.length) addCondition()
   253|  showDialog.value = true
   254|}
   255|
   256|async function save() {
   257|  if (!form.name) return ElMessage.warning('请输入名称')
   258|  try {
   259|    const payload = { ...form, active: form.active }
   260|    if (editing.value) await api.put(`${API.ALERT_RULES}/${editId.value}`, payload)
   261|    else await api.post(API.ALERT_RULES, payload)
   262|    ElMessage.success('保存成功'); showDialog.value = false; load()
   263|  } catch (e: any) { ElMessage.error(e?.message || '保存失败') }
   264|}
   265|
   266|async function viewDetail(row: any) {
   267|  try {
   268|    const res = await api.get(`${API.ALERT_RULES}/${row.id}`)
   269|    if (res.data?.code === 0) detail.value = res.data.data
   270|    else detail.value = row
   271|  } catch { detail.value = row }
   272|  triggerHistory.value = []
   273|  showDetail.value = true
   274|}
   275|
   276|async function toggleRule(row: any) {
   277|  try {
   278|    await api.patch(`${API.ALERT_RULES}/${row.id}`, { active: row._active })
   279|    ElMessage.success(row._active ? '已启用' : '已停用')
   280|  } catch { row._active = !row._active; ElMessage.error('操作失败') }
   281|}
   282|
   283|async function testRule(row: any) {
   284|  try {
   285|    const res = await api.post(`${API.ALERT_RULES}/${row.id}/test`)
   286|    ElMessage.success(res.data?.data?.matched ? '规则命中! 条件满足' : '规则未命中，条件不满足')
   287|  } catch { ElMessage.warning('测试功能暂不可用') }
   288|}
   289|
   290|async function duplicateRule(row: any) {
   291|  try {
   292|    await api.post(API.ALERT_RULES, { ...row, name: `${row.name} (副本)`, active: false, id: undefined })
   293|    ElMessage.success('复制成功'); load()
   294|  } catch { ElMessage.error('复制失败') }
   295|}
   296|
   297|function metricLabel(m: string) {
   298|  return ({ cpu_usage:'CPU使用率', memory_usage:'内存使用率', disk_usage:'磁盘使用率', network_in:'网络入', network_out:'网络出', response_time:'响应时间', status_check:'状态检查', status_code:'状态码', connection_count:'连接数', process_count:'进程数', custom:'自定义' })[m] || m
   299|}
   300|function severityType(s: string) { return ({ critical:'danger', warning:'warning', info:'info' })[s] || 'info' }
   301|function fmt(t: string) { return t ? new Date(t).toLocaleString('zh-CN') : '-' }
   302|
   303|onMounted(() => { load() })
   304|</script>
   305|
   306|<style scoped>
   307|
   308|.stat-row { margin-bottom: 20px; }
   309|
   310|.stat-card 
   311|.stat-card.success .stat-value { color: #00b42a; }
   312|.stat-card.warning .stat-value { color: #ff7d00; }
   313|.stat-card.primary .stat-value { color: #165dff; font-size: 16px; }
   314|.stat-card 
   315|.toolbar { margin-bottom: 16px; display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
   316|.pagination { margin-top: 16px; display: flex; justify-content: flex-end; }
   317|.condition-editor { background: #f7f8fa; padding: 12px; border-radius: 4px; }
   318|.cond-row { display: flex; gap: 6px; align-items: center; margin-bottom: 6px; }
   319|</style>
   320|