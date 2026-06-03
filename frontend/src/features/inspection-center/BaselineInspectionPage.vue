     1|<template>
     2|  <div class="page-container">
     3|    <!-- 页面头部 -->
     4|    <div class="autops-page-header">
     5|      <div class="autops-page-title">基线巡检</div>
     6|      <div class="autops-page-desc">安全和运维基线检查、合规状态、整改建议</div>
     7|    </div>
     8|
     9|    <!-- 搜索栏 -->
    10|    <div class="page-toolbar">
    11|      <el-input
    12|        v-model="searchQuery"
    13|        placeholder="搜索资产名 / 检查项..."
    14|        clearable
    15|        style="width: 280px"
    16|        @keyup.enter="fetchData"
    17|        @clear="fetchData"
    18|      >
    19|        <template #prefix><el-icon><Search /></el-icon></template>
    20|      </el-input>
    21|      <el-select v-model="complianceFilter" placeholder="合规状态" clearable style="width: 150px" @change="fetchData">
    22|        <el-option label="合规" value="compliant" />
    23|        <el-option label="不合规" value="non-compliant" />
    24|      </el-select>
    25|      <el-button type="default" @click="fetchData">
    26|        <el-icon><Refresh /></el-icon> 刷新
    27|      </el-button>
    28|    </div>
    29|
    30|    <!-- 统计摘要 -->
    31|    <div v-if="summary.total > 0" class="summary-bar">
    32|      <div class="summary-item">
    33|        <span class="summary-label">总计</span>
    34|        <span class="summary-value">{{ summary.total }}</span>
    35|      </div>
    36|      <div class="summary-item">
    37|        <span class="summary-label">合规</span>
    38|        <span class="summary-value success">{{ summary.compliant }}</span>
    39|      </div>
    40|      <div class="summary-item">
    41|        <span class="summary-label">不合规</span>
    42|        <span class="summary-value danger">{{ summary.nonCompliant }}</span>
    43|      </div>
    44|      <div class="summary-item">
    45|        <span class="summary-label">合规率</span>
    46|        <span class="summary-value">{{ summary.rate }}%</span>
    47|      </div>
    48|    </div>
    49|
    50|    <!-- 数据表格 -->
    51|    <el-table stripe :data="tableData" v-loading="loading"empty-text="暂无基线巡检数据">
    52|      <el-table-column prop="asset_name" label="资产名" min-width="160" show-overflow-tooltip />
    53|      <el-table-column prop="check_item" label="检查项" min-width="180" show-overflow-tooltip>
    54|        <template #default="{ row }">
    55|          <span>{{ row.check_item ?? row.baseline_item ?? '-' }}</span>
    56|        </template>
    57|      </el-table-column>
    58|      <el-table-column prop="baseline_value" label="基线值" min-width="150" show-overflow-tooltip>
    59|        <template #default="{ row }">
    60|          <span class="value-text">{{ row.baseline_value ?? row.expected ?? '-' }}</span>
    61|        </template>
    62|      </el-table-column>
    63|      <el-table-column prop="current_value" label="当前值" min-width="150" show-overflow-tooltip>
    64|        <template #default="{ row }">
    65|          <span :class="{ 'value-drift': row.status === 'non-compliant', 'value-text': true }">
    66|            {{ row.current_value ?? row.actual ?? '-' }}
    67|          </span>
    68|        </template>
    69|      </el-table-column>
    70|      <el-table-column prop="status" label="合规状态" width="120" align="center">
    71|        <template #default="{ row }">
    72|          <el-tag :type="complianceTagType(row.status)" size="small" effect="light">
    73|            <el-icon v-if="row.status === 'non-compliant'" style="margin-right: 2px"><CircleCloseFilled /></el-icon>
    74|            <el-icon v-else-if="row.status === 'compliant'" style="margin-right: 2px"><CircleCheckFilled /></el-icon>
    75|            {{ complianceLabel(row.status) }}
    76|          </el-tag>
    77|        </template>
    78|      </el-table-column>
    79|      <el-table-column prop="checked_at" label="检查时间" width="180">
    80|        <template #default="{ row }">
    81|          <span class="text-tertiary">{{ row.checked_at || row.created_at || '-' }}</span>
    82|        </template>
    83|      </el-table-column>
    84|    </el-table>
    85|
    86|    <!-- 分页 -->
    87|    <div class="page-pagination">
    88|      <el-pagination
    89|        v-model:current-page="pagination.page"
    90|        v-model:page-size="pagination.page_size"
    91|        :total="pagination.total"
    92|        :page-sizes="[10, 20, 50, 100]"
    93|        layout="total, sizes, prev, pager, next, jumper"
    94|        background
    95|        @size-change="fetchData"
    96|        @current-change="fetchData"
    97|      />
    98|    </div>
    99|  </div>
   100|</template>
   101|
   102|<script setup lang="ts">
   103|import { ref, reactive, computed, onMounted } from 'vue'
   104|import { ElMessage } from 'element-plus'
   105|import { Search, Refresh, CircleCheckFilled, CircleCloseFilled } from '@element-plus/icons-vue'
   106|import client from '@/shared/api/client'
   107|import { API } from '@/shared/api/routes'
   108|
   109|// ---------- 状态 ----------
   110|const loading = ref(false)
   111|const tableData = ref<any[]>([])
   112|const searchQuery = ref('')
   113|const complianceFilter = ref('')
   114|
   115|const pagination = reactive({
   116|  page: 1,
   117|  page_size: 20,
   118|  total: 0,
   119|})
   120|
   121|// ---------- 统计摘要 ----------
   122|const summary = computed(() => {
   123|  const total = tableData.value.length
   124|  const compliant = tableData.value.filter(r => r.status === 'compliant').length
   125|  const nonCompliant = tableData.value.filter(r => r.status === 'non-compliant').length
   126|  const rate = total > 0 ? Math.round((compliant / total) * 100) : 0
   127|  return { total, compliant, nonCompliant, rate }
   128|})
   129|
   130|// ---------- 工具函数 ----------
   131|const complianceMap: Record<string, { label: string; type: string }> = {
   132|  compliant: { label: '合规', type: 'success' },
   133|  'non-compliant': { label: '不合规', type: 'danger' },
   134|}
   135|
   136|function complianceTagType(status: string): string {
   137|  return complianceMap[status]?.type ?? 'info'
   138|}
   139|
   140|function complianceLabel(status: string): string {
   141|  return complianceMap[status]?.label ?? status ?? '-'
   142|}
   143|
   144|// ---------- API ----------
   145|async function fetchData() {
   146|  loading.value = true
   147|  try {
   148|    const params: Record<string, any> = {
   149|      page: pagination.page,
   150|      page_size: pagination.page_size,
   151|    }
   152|    if (searchQuery.value.trim()) {
   153|      params.keyword = searchQuery.value.trim()
   154|    }
   155|    if (complianceFilter.value) {
   156|      params.status = complianceFilter.value
   157|    }
   158|    const res = await client.get(API.INSPECTION.BASELINE_CHECKS, { params })
   159|    const data = res.data?.data ?? res.data
   160|    tableData.value = data?.items ?? data ?? []
   161|    pagination.total = data?.total ?? tableData.value.length
   162|  } catch (err: any) {
   163|    ElMessage.error(err.message || '获取基线巡检数据失败')
   164|  } finally {
   165|    loading.value = false
   166|  }
   167|}
   168|
   169|// ---------- 初始化 ----------
   170|onMounted(() => {
   171|  fetchData()
   172|})
   173|</script>
   174|
   175|<style scoped>
   176|
   179|.page-header {
   180|  display: flex;
   181|  justify-content: space-between;
   182|  align-items: center;
   183|  margin-bottom: 4px;
   184|}
   185|.page-title {
   186|  font-size: 18px;
   187|  font-weight: 600;
   188|  color: #1d2129;
   189|  margin: 0;
   190|}
   191|.page-desc {
   192|  font-size: 13px;
   193|  color: #86909c;
   194|  margin: 0 0 16px 0;
   195|}
   196|.page-toolbar {
   197|  display: flex;
   198|  align-items: center;
   199|  gap: 12px;
   200|  margin-bottom: 16px;
   201|}
   202|.page-pagination {
   203|  display: flex;
   204|  justify-content: flex-end;
   205|  margin-top: 16px;
   206|}
   207|.text-tertiary {
   208|  color: #86909c;
   209|  font-size: 13px;
   210|}
   211|.value-text {
   212|  font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
   213|  font-size: 13px;
   214|}
   215|.value-drift {
   216|  color: #f53f3f;
   217|  font-weight: 600;
   218|}
   219|
   220|/* 统计摘要 */
   221|.summary-bar {
   222|  display: flex;
   223|  align-items: center;
   224|  gap: 24px;
   225|  padding: 12px 20px;
   226|  margin-bottom: 16px;
   227|  background: #f7f8fa;
   228|  border-radius: 6px;
   229|}
   230|.summary-item {
   231|  display: flex;
   232|  align-items: center;
   233|  gap: 6px;
   234|}
   235|.summary-label {
   236|  font-size: 13px;
   237|  color: #86909c;
   238|}
   239|.summary-value {
   240|  font-size: 16px;
   241|  font-weight: 700;
   242|  color: #1d2129;
   243|}
   244|.summary-value.success {
   245|  color: #00b42a;
   246|}
   247|.summary-value.danger {
   248|  color: #f53f3f;
   249|}
   250|</style>
   251|