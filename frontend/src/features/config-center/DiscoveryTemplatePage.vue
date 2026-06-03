     1|<template>
     2|  <div class="page-container">
     3|    <div class="autops-page-header">
     4|      <div class="autops-page-title">发现模板</div>
     5|      <el-button type="primary" @click="openCreateDialog">
     6|        <el-icon><Plus /></el-icon> 新建模板
     7|      </el-button>
     8|    </div>
     9|
    10|    <!-- Filters -->
    11|    <el-card class="mb-md">
    12|      <el-row :gutter="16">
    13|        <el-col :span="8">
    14|          <el-select v-model="filters.protocol" placeholder="协议" clearable @change="fetchData">
    15|            <el-option label="SSH" value="ssh" />
    16|            <el-option label="SNMP" value="snmp" />
    17|            <el-option label="ICMP" value="icmp" />
    18|            <el-option label="ARP" value="arp" />
    19|            <el-option label="WMI" value="wmi" />
    20|            <el-option label="Agent" value="agent" />
    21|          </el-select>
    22|        </el-col>
    23|        <el-col :span="8">
    24|          <el-select v-model="filters.enabled" placeholder="状态" clearable @change="fetchData">
    25|            <el-option label="启用" :value="true" />
    26|            <el-option label="禁用" :value="false" />
    27|          </el-select>
    28|        </el-col>
    29|      </el-row>
    30|    </el-card>
    31|
    32|    <!-- Table -->
    33|    <el-card v-loading="loading">
    34|      <el-table stripe :data="items"empty-text="暂无发现模板" style="width: 100%">
    35|        <el-table-column prop="name" label="模板名称" min-width="160" show-overflow-tooltip />
    36|        <el-table-column prop="protocol" label="协议" width="100">
    37|          <template #default="{ row }">
    38|            <el-tag size="small" type="info">{{ row.protocol?.toUpperCase() }}</el-tag>
    39|          </template>
    40|        </el-table-column>
    41|        <el-table-column label="目标范围" min-width="200">
    42|          <template #default="{ row }">
    43|            <span class="text-tertiary">{{ scopePreview(row.target_scope) }}</span>
    44|          </template>
    45|        </el-table-column>
    46|        <el-table-column prop="port_range" label="端口范围" width="140">
    47|          <template #default="{ row }">{{ row.port_range || '默认' }}</template>
    48|        </el-table-column>
    49|        <el-table-column prop="scan_interval" label="扫描间隔" width="100">
    50|          <template #default="{ row }">{{ formatInterval(row.scan_interval) }}</template>
    51|        </el-table-column>
    52|        <el-table-column prop="timeout" label="超时" width="80">
    53|          <template #default="{ row }">{{ row.timeout }}s</template>
    54|        </el-table-column>
    55|        <el-table-column prop="is_builtin" label="内置" width="70">
    56|          <template #default="{ row }">
    57|            <el-tag v-if="row.is_builtin" size="small" type="info">内置</el-tag>
    58|          </template>
    59|        </el-table-column>
    60|        <el-table-column prop="enabled" label="状态" width="80">
    61|          <template #default="{ row }">
    62|            <el-switch :model-value="row.enabled" @change="toggleTemplate(row)" />
    63|          </template>
    64|        </el-table-column>
    65|        <el-table-column label="操作" width="180" fixed="right">
    66|          <template #default="{ row }">
    67|            <el-button text type="primary" size="small" @click="openEditDialog(row)">编辑</el-button>
    68|            <el-popconfirm v-if="!row.is_builtin" title="确定删除此模板？" @confirm="deleteTemplate(row)">
    69|              <template #reference>
    70|                <el-button text type="danger" size="small">删除</el-button>
    71|              </template>
    72|            </el-popconfirm>
    73|          </template>
    74|        </el-table-column>
    75|      </el-table>
    76|      <el-pagination
    77|        v-if="total > pageSize"
    78|        v-model:current-page="currentPage"
    79|        :page-size="pageSize"
    80|        :total="total"
    81|        layout="total, prev, pager, next"
    82|        style="margin-top: 16px; justify-content: flex-end"
    83|        @current-change="fetchData"
    84|      />
    85|    </el-card>
    86|
    87|    <!-- Create/Edit Dialog -->
    88|    <el-dialog v-model="dialogVisible" :title="editingItem ? '编辑模板' : '新建模板'" width="600px" destroy-on-close>
    89|      <el-form :model="formData" label-width="100px">
    90|        <el-form-item label="模板名称" required>
    91|          <el-input v-model="formData.name" placeholder="如：SSH标准发现" />
    92|        </el-form-item>
    93|        <el-form-item label="协议" required>
    94|          <el-select v-model="formData.protocol" style="width: 100%">
    95|            <el-option label="SSH" value="ssh" />
    96|            <el-option label="SNMP" value="snmp" />
    97|            <el-option label="ICMP" value="icmp" />
    98|            <el-option label="ARP" value="arp" />
    99|            <el-option label="WMI" value="wmi" />
   100|            <el-option label="Agent" value="agent" />
   101|          </el-select>
   102|        </el-form-item>
   103|        <el-form-item label="目标范围" required>
   104|          <el-input v-model="formData.target_scope" type="textarea" :rows="3" placeholder='{"ip_ranges":["192.168.1.0/24"],"asset_groups":[],"exclude":[]}' />
   105|        </el-form-item>
   106|        <el-form-item label="端口范围">
   107|          <el-input v-model="formData.port_range" placeholder="如：22,80,443 或 1-1024" />
   108|        </el-form-item>
   109|        <el-row :gutter="16">
   110|          <el-col :span="12">
   111|            <el-form-item label="扫描间隔">
   112|              <el-input-number v-model="formData.scan_interval" :min="60" :step="300" style="width: 100%" />
   113|            </el-form-item>
   114|          </el-col>
   115|          <el-col :span="12">
   116|            <el-form-item label="超时(秒)">
   117|              <el-input-number v-model="formData.timeout" :min="30" :step="30" style="width: 100%" />
   118|            </el-form-item>
   119|          </el-col>
   120|        </el-row>
   121|        <el-form-item label="类型映射">
   122|          <el-input v-model="formData.asset_type_mapping" type="textarea" :rows="2" placeholder='自动检测资产类型规则(JSON)' />
   123|        </el-form-item>
   124|        <el-form-item label="描述">
   125|          <el-input v-model="formData.description" type="textarea" :rows="2" />
   126|        </el-form-item>
   127|      </el-form>
   128|      <template #footer>
   129|        <el-button @click="dialogVisible = false">取消</el-button>
   130|        <el-button type="primary" :loading="submitting" @click="submitForm">确定</el-button>
   131|      </template>
   132|    </el-dialog>
   133|  </div>
   134|</template>
   135|
   136|<script setup lang="ts">
   137|import { ref, reactive, onMounted } from 'vue'
   138|import { ElMessage } from 'element-plus'
   139|import { Plus } from '@element-plus/icons-vue'
   140|import { discoveryTemplateService } from '@/shared/api'
   141|
   142|const loading = ref(false)
   143|const items = ref<any[]>([])
   144|const total = ref(0)
   145|const currentPage = ref(1)
   146|const pageSize = 20
   147|
   148|const filters = reactive({ protocol: '', enabled: null as boolean | null })
   149|
   150|async function fetchData() {
   151|  loading.value = true
   152|  try {
   153|    const params: Record<string, any> = { page: currentPage.value, page_size: pageSize }
   154|    if (filters.protocol) params.protocol = filters.protocol
   155|    if (filters.enabled !== null) params.enabled = filters.enabled
   156|
   157|    const resp = await discoveryTemplateService.list(params)
   158|    if (resp.data?.code === 0) {
   159|      items.value = resp.data.data?.items || []
   160|      total.value = resp.data.data?.total || 0
   161|    }
   162|  } catch (e) {
   163|    console.error('Failed to fetch discovery templates:', e)
   164|  } finally {
   165|    loading.value = false
   166|  }
   167|}
   168|
   169|const dialogVisible = ref(false)
   170|const editingItem = ref<any>(null)
   171|const submitting = ref(false)
   172|const formData = reactive({
   173|  name: '', protocol: 'ssh', target_scope: '{"ip_ranges":[],"asset_groups":[],"exclude":[]}',
   174|  port_range: '', scan_interval: 3600, timeout: 300, asset_type_mapping: '', description: '',
   175|})
   176|
   177|function openCreateDialog() {
   178|  editingItem.value = null
   179|  Object.assign(formData, { name: '', protocol: 'ssh', target_scope: '{"ip_ranges":[],"asset_groups":[],"exclude":[]}', port_range: '', scan_interval: 3600, timeout: 300, asset_type_mapping: '', description: '' })
   180|  dialogVisible.value = true
   181|}
   182|
   183|function openEditDialog(row: any) {
   184|  editingItem.value = row
   185|  Object.assign(formData, { name: row.name, protocol: row.protocol, target_scope: row.target_scope, port_range: row.port_range || '', scan_interval: row.scan_interval, timeout: row.timeout, asset_type_mapping: row.asset_type_mapping || '', description: row.description || '' })
   186|  dialogVisible.value = true
   187|}
   188|
   189|async function submitForm() {
   190|  if (!formData.name || !formData.protocol) {
   191|    ElMessage.warning('请填写必填项')
   192|    return
   193|  }
   194|  submitting.value = true
   195|  try {
   196|    const data = { ...formData, port_range: formData.port_range || null, asset_type_mapping: formData.asset_type_mapping || null }
   197|    if (editingItem.value) {
   198|      await discoveryTemplateService.update(editingItem.value.id, data)
   199|      ElMessage.success('模板已更新')
   200|    } else {
   201|      await discoveryTemplateService.create(data)
   202|      ElMessage.success('模板已创建')
   203|    }
   204|    dialogVisible.value = false
   205|    fetchData()
   206|  } catch (e) {
   207|    console.error('Submit failed:', e)
   208|    ElMessage.error('操作失败')
   209|  } finally {
   210|    submitting.value = false
   211|  }
   212|}
   213|
   214|async function toggleTemplate(row: any) {
   215|  try {
   216|    await discoveryTemplateService.toggle(row.id)
   217|    fetchData()
   218|  } catch { ElMessage.error('操作失败') }
   219|}
   220|
   221|async function deleteTemplate(row: any) {
   222|  try {
   223|    await discoveryTemplateService.delete(row.id)
   224|    ElMessage.success('已删除')
   225|    fetchData()
   226|  } catch { ElMessage.error('删除失败') }
   227|}
   228|
   229|function scopePreview(s: string): string {
   230|  try {
   231|    const obj = JSON.parse(s)
   232|    const parts: string[] = []
   233|    if (obj.ip_ranges?.length) parts.push('IP: ' + obj.ip_ranges.slice(0, 2).join(','))
   234|    if (obj.asset_groups?.length) parts.push('分组: ' + obj.asset_groups.length + '个')
   235|    return parts.length ? parts.join(' | ') : '未配置'
   236|  } catch { return s?.slice(0, 50) || '未配置' }
   237|}
   238|
   239|function formatInterval(seconds: number): string {
   240|  if (seconds >= 86400) return Math.round(seconds / 86400) + '天'
   241|  if (seconds >= 3600) return Math.round(seconds / 3600) + '小时'
   242|  return seconds + '秒'
   243|}
   244|
   245|onMounted(fetchData)
   246|</script>
   247|
   248|<style scoped>
   249|
   250|.mb-md { margin-bottom: 16px; }
   251|.text-tertiary { color: #86909c; }
   252|</style>
   253|