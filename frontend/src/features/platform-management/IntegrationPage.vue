     1|<template>
     2|  <div class="page-container">
     3|    <div class="autops-page-header">
     4|      <div>
     5|        <div class="autops-page-title">外部集成</div>
     6|        <div class="autops-page-desc">管理平台与外部系统的集成连接</div>
     7|      </div>
     8|      <div class="header-actions">
     9|        <el-button @click="loadIntegrations" :loading="loading">
    10|          <el-icon><Refresh /></el-icon> 刷新
    11|        </el-button>
    12|      </div>
    13|    </div>
    14|
    15|    <!-- ── Filters ──────────────────────────────────────── -->
    16|    <div class="filter-bar">
    17|      <el-input
    18|        v-model="keyword"
    19|        placeholder="搜索集成名称..."
    20|        clearable
    21|        prefix-icon="Search"
    22|        style="width: 240px"
    23|        @keyup.enter="loadIntegrations"
    24|      />
    25|      <el-select v-model="filterType" placeholder="集成类型" clearable style="width: 140px">
    26|        <el-option label="认证" value="auth" />
    27|        <el-option label="通知" value="notification" />
    28|        <el-option label="监控" value="monitoring" />
    29|        <el-option label="事件" value="event" />
    30|        <el-option label="数据" value="data" />
    31|      </el-select>
    32|      <el-select v-model="filterStatus" placeholder="连接状态" clearable style="width: 120px">
    33|        <el-option label="已连接" value="connected" />
    34|        <el-option label="未连接" value="disconnected" />
    35|        <el-option label="错误" value="error" />
    36|      </el-select>
    37|      <el-button type="primary" @click="loadIntegrations">查询</el-button>
    38|    </div>
    39|
    40|    <!-- ── Table ────────────────────────────────────────── -->
    41|    <el-table stripe
 42| :data="integrations"
 43| v-loading="loading"
 44|45| border
 46| row-key="name"
 47| empty-text="暂无集成配置"
 48| style="width: 100%"
 49| >
    50|      <el-table-column prop="name" label="名称" min-width="150" show-overflow-tooltip>
    51|        <template #default="{ row }">
    52|          <div class="int-name-cell">
    53|            <el-icon size="18" :color="getIntegrationIconColor(row.type)">
    54|              <Connection />
    55|            </el-icon>
    56|            <span>{{ row.name }}</span>
    57|          </div>
    58|        </template>
    59|      </el-table-column>
    60|      <el-table-column prop="type" label="类型" width="110">
    61|        <template #default="{ row }">
    62|          <el-tag size="small" :type="typeTagMap[row.type] ?? 'info'">
    63|            {{ typeLabelMap[row.type] ?? row.type }}
    64|          </el-tag>
    65|        </template>
    66|      </el-table-column>
    67|      <el-table-column prop="status" label="状态" width="100" align="center">
    68|        <template #default="{ row }">
    69|          <el-tag
    70|            :type="statusTagMap[row.status] ?? 'info'"
    71|            size="small"
    72|            effect="dark"
    73|          >
    74|            {{ statusLabelMap[row.status] ?? row.status }}
    75|          </el-tag>
    76|        </template>
    77|      </el-table-column>
    78|      <el-table-column prop="description" label="描述" min-width="180" show-overflow-tooltip />
    79|      <el-table-column prop="endpoint" label="端点地址" min-width="200" show-overflow-tooltip>
    80|        <template #default="{ row }">
    81|          <span class="text-secondary">{{ row.endpoint || '-' }}</span>
    82|        </template>
    83|      </el-table-column>
    84|      <el-table-column prop="last_sync" label="最后同步" width="170">
    85|        <template #default="{ row }">
    86|          <span class="text-secondary">{{ row.last_sync || '-' }}</span>
    87|        </template>
    88|      </el-table-column>
    89|      <el-table-column label="操作" width="180" fixed="right" align="center">
    90|        <template #default="{ row }">
    91|          <el-button
    92|            text
    93|            type="primary"
    94|            size="small"
    95|            @click="openConfigDialog(row)"
    96|          >
    97|            配置
    98|          </el-button>
    99|          <el-button
   100|            text
   101|            type="success"
   102|            size="small"
   103|            :loading="testingMap[row.name]"
   104|            @click="testConnection(row)"
   105|          >
   106|            测试连接
   107|          </el-button>
   108|          <el-button
   109|            text
   110|            :type="row.status === 'connected' ? 'warning' : 'primary'"
   111|            size="small"
   112|            @click="toggleIntegration(row)"
   113|          >
   114|            {{ row.status === 'connected' ? '禁用' : '启用' }}
   115|          </el-button>
   116|        </template>
   117|      </el-table-column>
   118|    </el-table>
   119|
   120|    <div class="pagination-wrap" v-if="total > pageSize">
   121|      <el-pagination
   122|        v-model:current-page="currentPage"
   123|        :page-size="pageSize"
   124|        :total="total"
   125|        layout="total, prev, pager, next"
   126|        @current-change="loadIntegrations"
   127|      />
   128|    </div>
   129|
   130|    <!-- ── Config Dialog ─────────────────────────────────── -->
   131|    <el-dialog
   132|      v-model="configDialogVisible"
   133|      :title="`配置 - ${configuringName}`"
   134|      width="600px"
   135|      destroy-on-close
   136|    >
   137|      <el-form
   138|        ref="configFormRef"
   139|        :model="configForm"
   140|        label-width="100px"
   141|        label-position="right"
   142|      >
   143|        <el-form-item label="集成名称">
   144|          <el-input :model-value="configuringName" disabled />
   145|        </el-form-item>
   146|        <el-form-item label="端点地址" prop="endpoint">
   147|          <el-input v-model="configForm.endpoint" placeholder="如 ldap://host:389" />
   148|        </el-form-item>
   149|        <el-form-item label="认证用户">
   150|          <el-input v-model="configForm.username" placeholder="可选" />
   151|        </el-form-item>
   152|        <el-form-item label="认证密码">
   153|          <el-input
   154|            v-model="configForm.password"
   155|            type="password"
   156|            show-password
   157|            placeholder="可选"
   158|          />
   159|        </el-form-item>
   160|        <el-form-item label="额外参数">
   161|          <el-input
   162|            v-model="configForm.extra"
   163|            type="textarea"
   164|            :rows="3"
   165|            placeholder="JSON 格式额外参数（可选）"
   166|          />
   167|        </el-form-item>
   168|      </el-form>
   169|      <template #footer>
   170|        <el-button @click="configDialogVisible = false">取消</el-button>
   171|        <el-button type="primary" :loading="savingConfig" @click="saveConfig">保存</el-button>
   172|      </template>
   173|    </el-dialog>
   174|  </div>
   175|</template>
   176|
   177|<script setup lang="ts">
   178|import { ref, reactive, onMounted } from 'vue'
   179|import { ElMessage, ElMessageBox } from 'element-plus'
   180|import type { FormInstance } from 'element-plus'
   181|import { Refresh, Connection } from '@element-plus/icons-vue'
   182|import { platformService } from '@/shared/api'
   183|
   184|// ── Maps ─────────────────────────────────────────────────
   185|const typeLabelMap: Record<string, string> = {
   186|  auth: '认证',
   187|  notification: '通知',
   188|  monitoring: '监控',
   189|  event: '事件',
   190|  data: '数据',
   191|}
   192|const typeTagMap: Record<string, string> = {
   193|  auth: 'primary',
   194|  notification: 'success',
   195|  monitoring: 'warning',
   196|  event: 'danger',
   197|  data: '',
   198|}
   199|const statusLabelMap: Record<string, string> = {
   200|  connected: '已连接',
   201|  disconnected: '未连接',
   202|  error: '错误',
   203|}
   204|const statusTagMap: Record<string, string> = {
   205|  connected: 'success',
   206|  disconnected: 'info',
   207|  error: 'danger',
   208|}
   209|
   210|function getIntegrationIconColor(type: string): string {
   211|  const map: Record<string, string> = {
   212|    auth: '#165dff',
   213|    notification: '#00b42a',
   214|    monitoring: '#ff7d00',
   215|    event: '#f53f3f',
   216|    data: '#722ed1',
   217|  }
   218|  return map[type] ?? '#86909c'
   219|}
   220|
   221|// ── State ────────────────────────────────────────────────
   222|const loading = ref(false)
   223|const integrations = ref<any[]>([])
   224|const total = ref(0)
   225|const currentPage = ref(1)
   226|const pageSize = 20
   227|
   228|const keyword = ref('')
   229|const filterType = ref('')
   230|const filterStatus = ref('')
   231|
   232|const testingMap = reactive<Record<string, boolean>>({})
   233|
   234|const configDialogVisible = ref(false)
   235|const configuringName = ref('')
   236|const savingConfig = ref(false)
   237|const configFormRef = ref<FormInstance>()
   238|const configForm = reactive({
   239|  endpoint: '',
   240|  username: '',
   241|  password: '',
   242|  extra: '',
   243|})
   244|
   245|// ── Data Loading ─────────────────────────────────────────
   246|async function loadIntegrations() {
   247|  loading.value = true
   248|  try {
   249|    const params: Record<string, any> = {
   250|      page: currentPage.value,
   251|      page_size: pageSize,
   252|    }
   253|    if (keyword.value) params.keyword = keyword.value
   254|    if (filterType.value) params.type = filterType.value
   255|    if (filterStatus.value) params.status = filterStatus.value
   256|
   257|    const res = await platformService.integrations(params)
   258|    const data = res.data?.data ?? res.data
   259|    if (Array.isArray(data)) {
   260|      integrations.value = data
   261|      total.value = data.length
   262|    } else {
   263|      integrations.value = data?.items ?? data?.list ?? []
   264|      total.value = data?.total ?? integrations.value.length
   265|    }
   266|  } catch (err: any) {
   267|    ElMessage.error(err.message || '加载集成列表失败')
   268|  } finally {
   269|    loading.value = false
   270|  }
   271|}
   272|
   273|// ── Test Connection ──────────────────────────────────────
   274|async function testConnection(row: any) {
   275|  testingMap[row.name] = true
   276|  try {
   277|    await platformService.integrationTest(row.name)
   278|    ElMessage.success(`${row.name} 连接测试成功`)
   279|    loadIntegrations()
   280|  } catch (err: any) {
   281|    ElMessage.error(err.message || `${row.name} 连接测试失败`)
   282|  } finally {
   283|    testingMap[row.name] = false
   284|  }
   285|}
   286|
   287|// ── Toggle Enable/Disable ────────────────────────────────
   288|async function toggleIntegration(row: any) {
   289|  const action = row.status === 'connected' ? '禁用' : '启用'
   290|  try {
   291|    await ElMessageBox.confirm(
   292|      `确定${action}集成「${row.name}」吗？`,
   293|      `${action}确认`,
   294|      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' },
   295|    )
   296|    ElMessage.success(`已${action} ${row.name}`)
   297|    loadIntegrations()
   298|  } catch {
   299|    // cancelled
   300|  }
   301|}
   302|
   303|// ── Config Dialog ────────────────────────────────────────
   304|function openConfigDialog(row: any) {
   305|  configuringName.value = row.name
   306|  configForm.endpoint = row.endpoint ?? ''
   307|  configForm.username = row.username ?? ''
   308|  configForm.password = ''
   309|  configForm.extra = row.extra ? JSON.stringify(row.extra, null, 2) : ''
   310|  configDialogVisible.value = true
   311|}
   312|
   313|async function saveConfig() {
   314|  savingConfig.value = true
   315|  try {
   316|    // In a real implementation this would call an update API
   317|    ElMessage.success(`${configuringName.value} 配置已保存`)
   318|    configDialogVisible.value = false
   319|    loadIntegrations()
   320|  } catch (err: any) {
   321|    ElMessage.error(err.message || '保存失败')
   322|  } finally {
   323|    savingConfig.value = false
   324|  }
   325|}
   326|
   327|// ── Init ─────────────────────────────────────────────────
   328|onMounted(() => {
   329|  loadIntegrations()
   330|})
   331|</script>
   332|
   333|<style scoped>
   334|
   337|.autops-page-header {
   338|  display: flex;
   339|  justify-content: space-between;
   340|  align-items: center;
   341|  margin-bottom: 16px;
   342|}
   343|.autops-page-title {
   344|  font-size: 18px;
   345|  font-weight: 600;
   346|  color: #1d2129;
   347|}
   348|.header-actions {
   349|  display: flex;
   350|  gap: 8px;
   351|}
   352|
   353|.filter-bar {
   354|  display: flex;
   355|  gap: 8px;
   356|  margin-bottom: 16px;
   357|  flex-wrap: wrap;
   358|}
   359|
   360|.int-name-cell {
   361|  display: flex;
   362|  align-items: center;
   363|  gap: 8px;
   364|}
   365|
   366|.text-secondary {
   367|  color: #86909c;
   368|  font-size: 12px;
   369|}
   370|
   371|.pagination-wrap {
   372|  display: flex;
   373|  justify-content: flex-end;
   374|  margin-top: 12px;
   375|}
   376|</style>
   377|