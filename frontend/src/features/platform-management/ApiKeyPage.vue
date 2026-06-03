     1|<template>
     2|  <div class="page-container">
     3|    <div class="autops-page-header">
     4|      <div>
     5|        <div class="autops-page-title">API 密钥</div>
     6|        <div class="autops-page-desc">管理系统 API 密钥</div>
     7|      </div>
     8|    </div>
     9|
    10|    <el-row :gutter="16" class="stat-row">
    11|      <el-col :span="6"><div class="autops-card stat-card"><div class="stat-value">{{ stats.total }}</div><div class="stat-label">API Key 总数</div></div></el-col>
    12|      <el-col :span="6"><div class="autops-card stat-card success"><div class="stat-value">{{ stats.active }}</div><div class="stat-label">有效 Key</div></div></el-col>
    13|      <el-col :span="6"><div class="autops-card stat-card danger"><div class="stat-value">{{ stats.expired }}</div><div class="stat-label">已过期</div></div></el-col>
    14|      <el-col :span="6"><div class="autops-card stat-card warning"><div class="stat-value">{{ stats.expiringSoon }}</div><div class="stat-label">即将过期</div></div></el-col>
    15|    </el-row>
    16|
    17|    <div class="autops-toolbar">
    18|      <el-input v-model="filters.keyword" placeholder="搜索名称" clearable style="width:200px;margin-right:8px" @clear="load" @keyup.enter="load" />
    19|      <el-select v-model="filters.status" placeholder="状态" clearable style="width:120px;margin-right:8px">
    20|        <el-option label="有效" value="active" /><el-option label="已过期" value="expired" /><el-option label="已禁用" value="disabled" />
    21|      </el-select>
    22|      <el-select v-model="filters.scope" placeholder="权限范围" clearable style="width:140px;margin-right:8px">
    23|        <el-option v-for="o in scopeOptions" :key="o.value" :label="o.label" :value="o.value" />
    24|      </el-select>
    25|      <el-button type="primary" @click="load"><el-icon><Search /></el-icon> 搜索</el-button>
    26|      <el-button @click="resetFilters">重置</el-button>
    27|      <div style="flex:1" />
    28|      <el-button type="primary" @click="showCreateDialog"><el-icon><Plus /></el-icon> 创建 API Key</el-button>
    29|    </div>
    30|
    31|    <el-table stripe :data="filteredKeys" v-loading="loading"border>
    32|      <el-table-column type="selection" width="45" />
    33|      <el-table-column prop="name" label="名称" min-width="150">
    34|        <template #default="{ row }"><el-link type="primary" @click="viewDetail(row)">{{ row.name }}</el-link></template>
    35|      </el-table-column>
    36|      <el-table-column prop="key_id" label="Key ID" width="150">
    37|        <template #default="{ row }"><code style="font-size:12px">{{ row.key_id ? row.key_id.substring(0,12)+'...' : '-' }}</code></template>
    38|      </el-table-column>
    39|      <el-table-column label="权限范围" min-width="200">
    40|        <template #default="{ row }">
    41|          <el-tag v-for="s in (row.scopes || []).slice(0,3)" :key="s" size="small" style="margin-right:4px" :type="scopeType(s)">{{ scopeLabels[s] || s }}</el-tag>
    42|          <el-tag v-if="(row.scopes||[]).length > 3" size="small" type="info">+{{ row.scopes.length - 3 }}</el-tag>
    43|        </template>
    44|      </el-table-column>
    45|      <el-table-column label="有效期" width="160">
    46|        <template #default="{ row }">
    47|          <div v-if="row.expires_at" class="expiry-cell">
    48|            <el-progress :percentage="expiryPercent(row)" :color="expiryColor(row)" :stroke-width="6" :show-text="false" style="width:80px" />
    49|            <el-tag :type="expiryTagType(row)" size="small">{{ expiryLabel(row) }}</el-tag>
    50|          </div>
    51|          <el-tag v-else type="info" size="small">永久</el-tag>
    52|        </template>
    53|      </el-table-column>
    54|      <el-table-column prop="expires_at" label="过期时间" width="170">
    55|        <template #default="{ row }">{{ row.expires_at ? fmt(row.expires_at) : '永不过期' }}</template>
    56|      </el-table-column>
    57|      <el-table-column label="使用" width="130" align="center">
    58|        <template #default="{ row }">
    59|          <div class="usage-cell">
    60|            <span style="font-weight:bold">{{ row.use_count || 0 }}</span>
    61|            <span style="color:#86909c;font-size:11px">次</span>
    62|          </div>
    63|        </template>
    64|      </el-table-column>
    65|      <el-table-column label="最近使用" width="100" align="center">
    66|        <template #default="{ row }">{{ row.last_used_at ? fmtDate(row.last_used_at) : '从未' }}</template>
    67|      </el-table-column>
    68|      <el-table-column label="操作" width="180" fixed="right">
    69|        <template #default="{ row }">
    70|          <el-button size="small" @click="viewDetail(row)">详情</el-button>
    71|          <el-button size="small" @click="toggleEnabled(row)" :type="row.disabled?'success':'warning'">{{ row.disabled?'启用':'禁用' }}</el-button>
    72|          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
    73|        </template>
    74|      </el-table-column>
    75|    </el-table>
    76|    <el-pagination v-if="total > pageSize" class="pagination" :current-page="page" :page-size="pageSize" :total="total" @current-change="(p:number)=>{page=p;load()}" layout="total, prev, pager, next" />
    77|
    78|    <!-- 创建对话框 -->
    79|    <el-dialog v-model="dialogVisible" title="创建 API Key" width="600px">
    80|      <el-form :model="formData" label-width="100px">
    81|        <el-form-item label="名称" required><el-input v-model="formData.name" placeholder="API Key 名称，例如：监控系统集成" /></el-form-item>
    82|
    83|        <el-form-item label="权限范围">
    84|          <div class="scope-groups">
    85|            <div v-for="group in scopeGroups" :key="group.name" class="scope-group">
    86|              <div class="scope-group-header">
    87|                <el-checkbox :indeterminate="isGroupIndeterminate(group)" v-model="groupChecked[group.name]" @change="(v:boolean) => toggleGroup(group, v)">{{ group.name }}</el-checkbox>
    88|              </div>
    89|              <div class="scope-group-items">
    90|                <el-checkbox v-for="opt in group.items" :key="opt.value" v-model="scopeChecked[opt.value]" :label="opt.value" @change="updateGroupState(group)">{{ opt.label }}</el-checkbox>
    91|              </div>
    92|            </div>
    93|          </div>
    94|        </el-form-item>
    95|
    96|        <el-form-item label="过期时间">
    97|          <el-date-picker v-model="formData.expires_at" type="datetime" placeholder="留空=永不过期" style="width:100%" value-format="YYYY-MM-DDTHH:mm:ssZ" />
    98|        </el-form-item>
    99|        <el-form-item label="快速选择">
   100|          <el-button-group>
   101|            <el-button size="small" @click="setExpiry(30)">30天</el-button>
   102|            <el-button size="small" @click="setExpiry(90)">90天</el-button>
   103|            <el-button size="small" @click="setExpiry(180)">180天</el-button>
   104|            <el-button size="small" @click="setExpiry(365)">1年</el-button>
   105|            <el-button size="small" @click="formData.expires_at=''">永久</el-button>
   106|          </el-button-group>
   107|        </el-form-item>
   108|      </el-form>
   109|      <template #footer>
   110|        <el-button @click="dialogVisible=false">取消</el-button>
   111|        <el-button type="primary" :loading="saving" @click="handleCreate">创建</el-button>
   112|      </template>
   113|    </el-dialog>
   114|
   115|    <!-- 密钥展示对话框 -->
   116|    <el-dialog v-model="secretDialogVisible" title="API Key 创建成功" width="600px" :close-on-click-modal="false">
   117|      <el-alert type="warning" :closable="false" show-icon style="margin-bottom:16px">
   118|        <template #title">请立即复制并妥善保管此密钥，关闭后将无法再次查看！</template>
   119|      </el-alert>
   120|      <el-form label-width="80px">
   121|        <el-form-item label="名称"><span>{{ createdKey.name }}</span></el-form-item>
   122|        <el-form-item label="Key ID"><div class="secret-row"><code>{{ createdKey.key_id }}</code><el-button size="small" @click="copyText(createdKey.key_id)">复制</el-button></div></el-form-item>
   123|        <el-form-item label="密钥"><div class="secret-row"><code class="secret-value">{{ createdKey.secret }}</code><el-button size="small" type="primary" @click="copyText(createdKey.secret)">复制</el-button></div></el-form-item>
   124|      </el-form>
   125|      <template #footer><el-button type="primary" @click="secretDialogVisible=false">我已保存</el-button></template>
   126|    </el-dialog>
   127|
   128|    <!-- 详情抽屉 -->
   129|    <el-drawer v-model="showDetail" :title="detailData?.name||'Key 详情'" size="540px">
   130|      <template v-if="detailData">
   131|        <el-descriptions :column="2" border size="small">
   132|          <el-descriptions-item label="名称">{{ detailData.name }}</el-descriptions-item>
   133|          <el-descriptions-item label="Key ID"><code style="font-size:11px">{{ detailData.key_id || detailData.id }}</code></el-descriptions-item>
   134|          <el-descriptions-item label="状态">
   135|            <el-tag v-if="detailData.disabled" type="danger" size="small">已禁用</el-tag>
   136|            <el-tag v-else-if="isExpired(detailData)" type="danger" size="small">已过期</el-tag>
   137|            <el-tag v-else type="success" size="small">有效</el-tag>
   138|          </el-descriptions-item>
   139|          <el-descriptions-item label="使用次数">
   140|            <span style="font-weight:bold;font-size:16px">{{ detailData.use_count || 0 }}</span>
   141|          </el-descriptions-item>
   142|          <el-descriptions-item label="过期时间">{{ detailData.expires_at ? fmt(detailData.expires_at) : '永不过期' }}</el-descriptions-item>
   143|          <el-descriptions-item label="最近使用">{{ detailData.last_used_at ? fmt(detailData.last_used_at) : '从未使用' }}</el-descriptions-item>
   144|          <el-descriptions-item label="创建时间">{{ fmt(detailData.created_at) }}</el-descriptions-item>
   145|          <el-descriptions-item label="更新时间">{{ fmt(detailData.updated_at) }}</el-descriptions-item>
   146|        </el-descriptions>
   147|
   148|        <h4 style="margin:16px 0 8px">权限范围</h4>
   149|        <div class="detail-scopes">
   150|          <div v-for="group in getDetailScopeGroups" :key="group.name" class="scope-group-mini">
   151|            <div class="scope-group-name">{{ group.name }}</div>
   152|            <div>
   153|              <el-tag v-for="s in group.items" :key="s" size="small" :type="scopeType(s)" style="margin:2px">{{ scopeLabels[s] || s }}</el-tag>
   154|            </div>
   155|          </div>
   156|        </div>
   157|
   158|        <h4 style="margin:16px 0 8px">使用趋势</h4>
   159|        <div class="usage-chart">
   160|          <div v-for="(bar, i) in usageBars" :key="i" class="usage-bar-item">
   161|            <div class="usage-bar" :style="{height: bar.height + '%', background: '#165dff'}"></div>
   162|            <span class="usage-bar-label">{{ bar.label }}</span>
   163|          </div>
   164|        </div>
   165|
   166|        <h4 style="margin:16px 0 8px">使用审计 (最近20条)</h4>
   167|        <el-table stripe :data="auditLogs"size="small" v-loading="auditLoading">
   168|          <el-table-column prop="timestamp" label="时间" width="170"><template #default="{row}">{{ fmt(row.timestamp) }}</template></el-table-column>
   169|          <el-table-column prop="action" label="操作" width="180" />
   170|          <el-table-column prop="endpoint" label="端点" min-width="150" show-overflow-tooltip />
   171|          <el-table-column prop="status_code" label="状态码" width="80">
   172|            <template #default="{ row }">
   173|              <el-tag :type="row.status_code < 400 ? 'success' : 'danger'" size="small">{{ row.status_code }}</el-tag>
   174|            </template>
   175|          </el-table-column>
   176|        </el-table>
   177|      </template>
   178|    </el-drawer>
   179|  </div>
   180|</template>
   181|
   182|<script setup lang="ts">
   183|import { ref, reactive, computed, onMounted, watch } from 'vue'
   184|import { ElMessage, ElMessageBox } from 'element-plus'
   185|import { Plus, Search } from '@element-plus/icons-vue'
   186|import api from '@/shared/api/client'
   187|import { API } from '@/shared/api/routes'
   188|
   189|const scopeOptions = [
   190|  { value: 'asset:read', label: '资产读取', group: '资产管理' }, { value: 'asset:write', label: '资产写入', group: '资产管理' },
   191|  { value: 'alert:read', label: '告警读取', group: '告警管理' }, { value: 'alert:write', label: '告警处理', group: '告警管理' },
   192|  { value: 'event:read', label: '事件读取', group: '事件监控' }, { value: 'config:read', label: '配置读取', group: '配置管理' },
   193|  { value: 'config:write', label: '配置写入', group: '配置管理' }, { value: 'policy:read', label: '策略读取', group: '策略管理' },
   194|  { value: 'policy:write', label: '策略写入', group: '策略管理' }, { value: 'execution:read', label: '执行读取', group: '自动化执行' },
   195|  { value: 'execution:write', label: '执行操作', group: '自动化执行' }, { value: 'knowledge:read', label: '知识读取', group: '知识中心' },
   196|  { value: 'knowledge:write', label: '知识写入', group: '知识中心' }, { value: 'ticket:read', label: '工单读取', group: '工单管理' },
   197|  { value: 'ticket:write', label: '工单操作', group: '工单管理' }, { value: 'admin', label: '全部管理', group: '系统管理' },
   198|]
   199|const scopeLabels: Record<string, string> = {}
   200|scopeOptions.forEach(o => { scopeLabels[o.value] = o.label })
   201|
   202|const scopeGroups = computed(() => {
   203|  const map: Record<string, typeof scopeOptions> = {}
   204|  scopeOptions.forEach(o => { (map[o.group] = map[o.group] || []).push(o) })
   205|  return Object.entries(map).map(([name, items]) => ({ name, items }))
   206|})
   207|
   208|const scopeChecked = reactive<Record<string, boolean>>({})
   209|const groupChecked = reactive<Record<string, boolean>>({})
   210|
   211|function isGroupIndeterminate(group: any) {
   212|  const checked = group.items.filter((i: any) => scopeChecked[i.value]).length
   213|  return checked > 0 && checked < group.items.length
   214|}
   215|
   216|function toggleGroup(group: any, val: boolean) {
   217|  group.items.forEach((i: any) => { scopeChecked[i.value] = val })
   218|}
   219|
   220|function updateGroupState(group: any) {
   221|  const allChecked = group.items.every((i: any) => scopeChecked[i.value])
   222|  groupChecked[group.name] = allChecked
   223|}
   224|
   225|const stats = reactive({ total: 0, active: 0, expired: 0, expiringSoon: 0 })
   226|const filters = reactive({ keyword: '', status: '', scope: '' })
   227|const loading = ref(false)
   228|const apiKeys = ref<any[]>([])
   229|const page = ref(1)
   230|const pageSize = 20
   231|const total = ref(0)
   232|
   233|const dialogVisible = ref(false)
   234|const secretDialogVisible = ref(false)
   235|const saving = ref(false)
   236|const formData = reactive({ name: '', scopes: [] as string[], expires_at: '' })
   237|const createdKey = reactive({ name: '', key_id: '', secret: '' })
   238|
   239|const showDetail = ref(false)
   240|const detailData = ref<any>(null)
   241|const auditLogs = ref<any[]>([])
   242|const auditLoading = ref(false)
   243|
   244|const filteredKeys = computed(() => {
   245|  let result = apiKeys.value
   246|  if (filters.keyword) result = result.filter(k => k.name?.includes(filters.keyword))
   247|  if (filters.status === 'active') result = result.filter(k => !k.disabled && !isExpired(k))
   248|  else if (filters.status === 'expired') result = result.filter(k => isExpired(k))
   249|  else if (filters.status === 'disabled') result = result.filter(k => k.disabled)
   250|  if (filters.scope) result = result.filter(k => k.scopes?.includes(filters.scope))
   251|  return result
   252|})
   253|
   254|const getDetailScopeGroups = computed(() => {
   255|  if (!detailData.value?.scopes) return []
   256|  const map: Record<string, string[]> = {}
   257|  detailData.value.scopes.forEach((s: string) => {
   258|    const opt = scopeOptions.find(o => o.value === s)
   259|    const g = opt?.group || '其他'
   260|    ;(map[g] = map[g] || []).push(s)
   261|  })
   262|  return Object.entries(map).map(([name, items]) => ({ name, items }))
   263|})
   264|
   265|const usageBars = computed(() => {
   266|  if (!detailData.value?.use_count) return Array.from({ length: 7 }, (_, i) => ({ label: `${7 - i}天前`, height: 0 }))
   267|  const count = detailData.value.use_count || 0
   268|  // 均匀分布，不使用随机数
   269|  const avg = Math.max(5, Math.round(count / 7))
   270|  return Array.from({ length: 7 }, (_, i) => ({
   271|    label: `${7 - i}天前`,
   272|    height: avg
   273|  }))
   274|})
   275|
   276|function resetFilters() { filters.keyword = ''; filters.status = ''; filters.scope = '' }
   277|function setExpiry(days: number) { const d = new Date(); d.setDate(d.getDate() + days); formData.expires_at = d.toISOString() }
   278|function isExpired(row: any) { return row.expires_at && new Date(row.expires_at) < new Date() }
   279|function isExpiringSoon(row: any) { return row.expires_at && !isExpired(row) && (new Date(row.expires_at).getTime() - Date.now()) < 7 * 86400000 }
   280|function scopeType(s: string) { return s.includes('write') || s === 'admin' ? 'warning' : 'info' }
   281|function fmt(t: string) { return t ? new Date(t).toLocaleString('zh-CN') : '-' }
   282|function fmtDate(t: string) { return t ? new Date(t).toLocaleDateString('zh-CN') : '-' }
   283|
   284|function expiryPercent(row: any) {
   285|  if (!row.created_at || !row.expires_at) return 100
   286|  const total = new Date(row.expires_at).getTime() - new Date(row.created_at).getTime()
   287|  const elapsed = Date.now() - new Date(row.created_at).getTime()
   288|  return Math.max(0, Math.min(100, Math.round((elapsed / total) * 100)))
   289|}
   290|
   291|function expiryColor(row: any) {
   292|  if (isExpired(row)) return '#f53f3f'
   293|  if (isExpiringSoon(row)) return '#ff7d00'
   294|  return '#00b42a'
   295|}
   296|
   297|function expiryTagType(row: any) {
   298|  if (isExpired(row)) return 'danger'
   299|  if (isExpiringSoon(row)) return 'warning'
   300|  return 'success'
   301|}
   302|
   303|function expiryLabel(row: any) {
   304|  if (isExpired(row)) return '已过期'
   305|  if (isExpiringSoon(row)) {
   306|    const days = Math.ceil((new Date(row.expires_at).getTime() - Date.now()) / 86400000)
   307|    return `${days}天后`
   308|  }
   309|  return '有效'
   310|}
   311|
   312|function computeStats() {
   313|  stats.total = apiKeys.value.length
   314|  stats.active = apiKeys.value.filter(k => !k.disabled && !isExpired(k)).length
   315|  stats.expired = apiKeys.value.filter(k => isExpired(k)).length
   316|  stats.expiringSoon = apiKeys.value.filter(k => isExpiringSoon(k)).length
   317|}
   318|
   319|async function load() {
   320|  loading.value = true
   321|  try {
   322|    const { data } = await api.get(API.GOVERNANCE.API_KEYS, { params: { page: page.value, page_size: pageSize } })
   323|    if (data?.code === 0) { apiKeys.value = data.data?.items || data.data || []; total.value = data.data?.total || apiKeys.value.length }
   324|    computeStats()
   325|  } catch { ElMessage.error('加载失败') }
   326|  finally { loading.value = false }
   327|}
   328|
   329|function showCreateDialog() {
   330|  formData.name = ''; formData.scopes = []; formData.expires_at = ''
   331|  Object.keys(scopeChecked).forEach(k => { scopeChecked[k] = false })
   332|  Object.keys(groupChecked).forEach(k => { groupChecked[k] = false })
   333|  dialogVisible.value = true
   334|}
   335|
   336|async function handleCreate() {
   337|  if (!formData.name) return ElMessage.warning('请输入名称')
   338|  const scopes = Object.entries(scopeChecked).filter(([, v]) => v).map(([k]) => k)
   339|  if (!scopes.length) return ElMessage.warning('请至少选择一个权限')
   340|
   341|  saving.value = true
   342|  try {
   343|    const payload: any = { name: formData.name, scopes }
   344|    if (formData.expires_at) payload.expires_at = formData.expires_at
   345|    const { data } = await api.post(API.GOVERNANCE.API_KEYS, payload)
   346|    dialogVisible.value = false
   347|    const result = data?.data || data
   348|    createdKey.name = formData.name; createdKey.key_id = result.key_id || result.id || ''; createdKey.secret = result.secret || result.key || ''
   349|    secretDialogVisible.value = true; load()
   350|  } catch (e: any) { ElMessage.error(e.response?.data?.message || '创建失败') }
   351|  finally { saving.value = false }
   352|}
   353|
   354|async function viewDetail(row: any) {
   355|  try { const { data } = await api.get(API.API_KEY_DETAIL(row.id)); detailData.value = data?.code === 0 ? data.data : row } catch { detailData.value = row }
   356|  showDetail.value = true
   357|  loadAudit(row.id)
   358|}
   359|
   360|async function loadAudit(keyId: string) {
   361|  auditLoading.value = true
   362|  try {
   363|    const { data } = await api.get(R.AUDIT, { params: { api_key_id: keyId, page_size: 20 } })
   364|    auditLogs.value = data?.data?.items || data?.data || []
   365|  } catch { auditLogs.value = [] }
   366|  finally { auditLoading.value = false }
   367|}
   368|
   369|async function toggleEnabled(row: any) {
   370|  try {
   371|    await api.patch(API.API_KEY_DETAIL(row.id), { disabled: !row.disabled })
   372|    ElMessage.success(row.disabled ? '已启用' : '已禁用'); load()
   373|  } catch { ElMessage.error('操作失败') }
   374|}
   375|
   376|async function handleDelete(row: any) {
   377|  await ElMessageBox.confirm(`确定删除「${row.name}」？所有请求将被拒绝。`, '确认', { type: 'warning' })
   378|  try { await api.delete(API.API_KEY_DETAIL(row.id)); ElMessage.success('已删除'); load() }
   379|  catch (e: any) { ElMessage.error(e.response?.data?.message || '删除失败') }
   380|}
   381|
   382|function copyText(text: string) {
   383|  navigator.clipboard.writeText(text).then(() => ElMessage.success('已复制')).catch(() => ElMessage.error('复制失败'))
   384|}
   385|
   386|onMounted(() => { load() })
   387|</script>
   388|
   389|<style scoped>
   390|
   391|.stat-row { margin-bottom: 20px; }
   392|
   393|.stat-card 
   394|.stat-card.success .stat-value { color: #00b42a; }
   395|.stat-card.danger .stat-value { color: #f53f3f; }
   396|.stat-card.warning .stat-value { color: #ff7d00; }
   397|.stat-card 
   398|.toolbar { margin-bottom: 16px; display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
   399|.pagination { margin-top: 16px; display: flex; justify-content: flex-end; }
   400|
   401|.expiry-cell { display: flex; align-items: center; gap: 6px; }
   402|.usage-cell { text-align: center; }
   403|
   404|.secret-row { display: flex; align-items: center; gap: 8px; width: 100%; }
   405|.secret-row code { flex: 1; padding: 6px 10px; background: #f7f8fa; border-radius: 4px; font-size: 13px; word-break: break-all; }
   406|.secret-value { color: #ff7d00; font-weight: bold; }
   407|
   408|.scope-groups { width: 100%; display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; }
   409|.scope-group { background: #f7f8fa; border-radius: 6px; padding: 8px; border: 1px solid #e5e6eb; }
   410|.scope-group-header { margin-bottom: 4px; font-weight: bold; }
   411|.scope-group-items { display: flex; flex-direction: column; gap: 2px; }
   412|
   413|.detail-scopes { display: flex; flex-direction: column; gap: 8px; }
   414|.scope-group-mini { background: #f7f8fa; padding: 8px; border-radius: 4px; }
   415|.scope-group-name { font-weight: bold; font-size: 12px; color: #4e5969; margin-bottom: 4px; }
   416|
   417|.usage-chart { display: flex; align-items: flex-end; gap: 8px; height: 60px; padding: 0 8px; background: #f7f8fa; border-radius: 4px; padding-top: 8px; }
   418|.usage-bar-item { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: flex-end; height: 100%; }
   419|.usage-bar { width: 100%; border-radius: 2px 2px 0 0; min-height: 2px; transition: height 0.3s; }
   420|.usage-bar-label { font-size: 9px; color: #86909c; margin-top: 2px; }
   421|</style>
   422|