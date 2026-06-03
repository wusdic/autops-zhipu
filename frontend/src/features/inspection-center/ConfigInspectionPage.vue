     1|<template>
     2|  <div class="page-container">
     3|    <div class="autops-page-header">
     4|      <h2>配置巡检</h2>
     5|      <div>
     6|        <el-input v-model="searchQuery" placeholder="搜索名称/资产" style="width: 200px; margin-right: 8px" clearable @clear="fetchItems" @keyup.enter="fetchItems">
     7|          <template #prefix><el-icon><Search /></el-icon></template>
     8|        </el-input>
     9|        <el-select v-model="filterStatus" placeholder="状态" style="width: 120px; margin-right: 8px" clearable @change="fetchItems">
    10|          <el-option label="正常" value="normal" />
    11|          <el-option label="异常" value="abnormal" />
    12|          <el-option label="未执行" value="pending" />
    13|        </el-select>
    14|        <el-select v-model="filterType" placeholder="检查类型" style="width: 140px; margin-right: 8px" clearable @change="fetchItems">
    15|          <el-option label="配置漂移" value="drift" />
    16|          <el-option label="合规检查" value="compliance" />
    17|          <el-option label="基线对比" value="baseline" />
    18|        </el-select>
    19|        <el-button type="primary" :loading="runLoading" @click="handleRunInspection">
    20|          <el-icon><VideoPlay /></el-icon> 执行巡检
    21|        </el-button>
    22|      </div>
    23|    </div>
    24|
    25|    <div class="autops-card">
    26|      <el-table stripe :data="filteredItems" v-loading="loading"class="autops-table" @sort-change="handleSortChange">
    27|        <el-table-column type="selection" width="45" />
    28|        <el-table-column prop="name" label="巡检项名称" min-width="160" sortable="custom" show-overflow-tooltip />
    29|        <el-table-column prop="asset_name" label="目标资产" min-width="140" show-overflow-tooltip />
    30|        <el-table-column prop="config_path" label="配置路径" min-width="180" show-overflow-tooltip>
    31|          <template #default="{ row }">
    32|            <el-text type="info" size="small" family="monospace">{{ row.config_path || '-' }}</el-text>
    33|          </template>
    34|        </el-table-column>
    35|        <el-table-column prop="check_type" label="检查类型" width="120">
    36|          <template #default="{ row }">
    37|            <el-tag :type="checkTypeTag(row.check_type)" size="small">{{ checkTypeLabel(row.check_type) }}</el-tag>
    38|          </template>
    39|        </el-table-column>
    40|        <el-table-column prop="status" label="状态" width="100">
    41|          <template #default="{ row }">
    42|            <el-tag :type="statusTag(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
    43|          </template>
    44|        </el-table-column>
    45|        <el-table-column prop="last_checked_at" label="最后检查" width="170" sortable="custom">
    46|          <template #default="{ row }">
    47|            {{ formatTime(row.last_checked_at) }}
    48|          </template>
    49|        </el-table-column>
    50|        <el-table-column prop="result_summary" label="结果摘要" min-width="200" show-overflow-tooltip>
    51|          <template #default="{ row }">
    52|            <span v-if="row.status === 'abnormal'" class="text-danger">{{ row.result_summary || '存在差异' }}</span>
    53|            <span v-else-if="row.status === 'normal'" class="text-success">{{ row.result_summary || '配置一致' }}</span>
    54|            <span v-else class="text-muted">-</span>
    55|          </template>
    56|        </el-table-column>
    57|        <el-table-column label="操作" width="180" fixed="right">
    58|          <template #default="{ row }">
    59|            <el-button link type="primary" @click="showDetail(row)">详情</el-button>
    60|            <el-button link type="warning" @click="runSingle(row)" :loading="row._running">执行</el-button>
    61|            <el-button link type="danger" v-if="row.status === 'abnormal'" @click="createAnomaly(row)">报异常</el-button>
    62|          </template>
    63|        </el-table-column>
    64|      </el-table>
    65|
    66|      <div style="display: flex; justify-content: flex-end; margin-top: 16px">
    67|        <el-pagination
    68|          v-model:current-page="page"
    69|          v-model:page-size="pageSize"
    70|          :total="total"
    71|          :page-sizes="[20, 50, 100]"
    72|          layout="total, sizes, prev, pager, next"
    73|          @size-change="fetchItems"
    74|          @current-change="fetchItems"
    75|        />
    76|      </div>
    77|    </div>
    78|
    79|    <!-- 详情对话框 -->
    80|    <el-dialog v-model="detailVisible" title="配置巡检详情" width="780px" destroy-on-close>
    81|      <el-descriptions :column="2" border v-if="currentItem">
    82|        <el-descriptions-item label="巡检项名称">{{ currentItem.name }}</el-descriptions-item>
    83|        <el-descriptions-item label="目标资产">{{ currentItem.asset_name }}</el-descriptions-item>
    84|        <el-descriptions-item label="配置路径" :span="2">
    85|          <el-text family="monospace">{{ currentItem.config_path }}</el-text>
    86|        </el-descriptions-item>
    87|        <el-descriptions-item label="检查类型">{{ checkTypeLabel(currentItem.check_type) }}</el-descriptions-item>
    88|        <el-descriptions-item label="状态">
    89|          <el-tag :type="statusTag(currentItem.status)">{{ statusLabel(currentItem.status) }}</el-tag>
    90|        </el-descriptions-item>
    91|        <el-descriptions-item label="最后检查">{{ formatTime(currentItem.last_checked_at) }}</el-descriptions-item>
    92|        <el-descriptions-item label="基线版本">{{ currentItem.baseline_version || '-' }}</el-descriptions-item>
    93|      </el-descriptions>
    94|
    95|      <!-- 配置差异展示 -->
    96|      <div v-if="currentItem?.diff_content" style="margin-top: 16px">
    97|        <h4>配置差异</h4>
    98|        <div class="diff-content">
    99|          <pre style="background: #1e1e1e; color: #c9cdd4; padding: 12px; border-radius: 4px; font-size: 12px; max-height: 300px; overflow: auto">{{ currentItem.diff_content }}</pre>
   100|        </div>
   101|      </div>
   102|
   103|      <div v-if="currentItem?.result_summary" style="margin-top: 16px">
   104|        <h4>结果摘要</h4>
   105|        <el-alert :type="currentItem.status === 'normal' ? 'success' : 'error'" :closable="false" show-icon>
   106|          {{ currentItem.result_summary }}
   107|        </el-alert>
   108|      </div>
   109|
   110|      <template #footer>
   111|        <el-button @click="detailVisible = false">关闭</el-button>
   112|        <el-button type="primary" @click="runSingle(currentItem)">重新检查</el-button>
   113|      </template>
   114|    </el-dialog>
   115|  </div>
   116|</template>
   117|
   118|<script setup lang="ts">
   119|import { ref, computed, onMounted } from 'vue'
   120|import { Search, VideoPlay } from '@element-plus/icons-vue'
   121|import { ElMessage } from 'element-plus'
   122|import api from '@/shared/api'
   123|import { routes as API } from '@/shared/api/routes'
   124|import { useRouter } from 'vue-router'
   125|
   126|const router = useRouter()
   127|
   128|// ─── State ───
   129|const loading = ref(false)
   130|const runLoading = ref(false)
   131|const items = ref<any[]>([])
   132|const total = ref(0)
   133|const page = ref(1)
   134|const pageSize = ref(20)
   135|const searchQuery = ref('')
   136|const filterStatus = ref('')
   137|const filterType = ref('')
   138|const sortField = ref('last_checked_at')
   139|const sortOrder = ref('desc')
   140|const detailVisible = ref(false)
   141|const currentItem = ref<any>(null)
   142|
   143|// ─── Computed ───
   144|const filteredItems = computed(() => {
   145|  let list = items.value
   146|  if (searchQuery.value) {
   147|    const q = searchQuery.value.toLowerCase()
   148|    list = list.filter(i => (i.name || '').toLowerCase().includes(q) || (i.asset_name || '').toLowerCase().includes(q))
   149|  }
   150|  if (filterStatus.value) {
   151|    list = list.filter(i => i.status === filterStatus.value)
   152|  }
   153|  if (filterType.value) {
   154|    list = list.filter(i => i.check_type === filterType.value)
   155|  }
   156|  return list
   157|})
   158|
   159|// ─── API ───
   160|async function fetchItems() {
   161|  loading.value = true
   162|  try {
   163|    const params: any = {
   164|      page: page.value,
   165|      page_size: pageSize.value,
   166|      type: 'config',
   167|    }
   168|    if (sortField.value) params.sort_by = sortField.value
   169|    if (sortOrder.value) params.sort_order = sortOrder.value
   170|    const res = await api.get(API.INSPECTION_TEMPLATES, { params })
   171|    const data = res.data
   172|    if (data?.code === 0) {
   173|      items.value = (data.data?.items || []).map((i: any) => ({ ...i, _running: false }))
   174|      total.value = data.data?.total || 0
   175|    }
   176|  } catch (e) {
   177|    console.error('Fetch config inspection items error:', e)
   178|    ElMessage.error('获取配置巡检列表失败')
   179|  } finally {
   180|    loading.value = false
   181|  }
   182|}
   183|
   184|async function handleRunInspection() {
   185|  runLoading.value = true
   186|  try {
   187|    await api.post(API.INSPECTION_TASKS, { type: 'config', template_ids: filteredItems.value.filter(i => i.id).map(i => i.id) })
   188|    ElMessage.success('配置巡检任务已创建')
   189|    setTimeout(fetchItems, 2000)
   190|  } catch (e) {
   191|    ElMessage.error('执行巡检失败')
   192|  } finally {
   193|    runLoading.value = false
   194|  }
   195|}
   196|
   197|async function runSingle(item: any) {
   198|  item._running = true
   199|  try {
   200|    await api.post(API.INSPECTION_TASKS, { type: 'config', template_id: item.id })
   201|    ElMessage.success(`巡检项 ${item.name} 已触发`)
   202|    setTimeout(fetchItems, 2000)
   203|  } catch (e) {
   204|    ElMessage.error('执行失败')
   205|  } finally {
   206|    item._running = false
   207|  }
   208|}
   209|
   210|function createAnomaly(item: any) {
   211|  router.push({ path: '/response/anomalies', query: { from: 'inspection', item_id: item.id } })
   212|}
   213|
   214|function showDetail(item: any) {
   215|  currentItem.value = item
   216|  detailVisible.value = true
   217|}
   218|
   219|function handleSortChange({ prop, order }: any) {
   220|  sortField.value = prop || 'last_checked_at'
   221|  sortOrder.value = order === 'ascending' ? 'asc' : 'desc'
   222|  fetchItems()
   223|}
   224|
   225|// ─── Helpers ───
   226|function checkTypeLabel(t: string) {
   227|  const map: Record<string, string> = { drift: '配置漂移', compliance: '合规检查', baseline: '基线对比' }
   228|  return map[t] || t || '-'
   229|}
   230|function checkTypeTag(t: string) {
   231|  const map: Record<string, string> = { drift: 'warning', compliance: '', baseline: 'info' }
   232|  return map[t] || 'info'
   233|}
   234|function statusLabel(s: string) {
   235|  const map: Record<string, string> = { normal: '正常', abnormal: '异常', pending: '未执行' }
   236|  return map[s] || s || '-'
   237|}
   238|function statusTag(s: string) {
   239|  const map: Record<string, string> = { normal: 'success', abnormal: 'danger', pending: 'info' }
   240|  return map[s] || 'info'
   241|}
   242|function formatTime(t: string) {
   243|  return t ? new Date(t).toLocaleString('zh-CN') : '-'
   244|}
   245|
   246|onMounted(fetchItems)
   247|</script>
   248|
   249|<style scoped>
   250|
   251|.diff-content { border-radius: 4px; overflow: hidden; }
   252|
   253|
   254|.text-muted { color: #86909c; }
   255|</style>
   256|