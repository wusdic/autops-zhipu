     1|<template>
     2|  <div class="page-container">
     3|    <!-- 页面头部 -->
     4|    <div class="autops-page-header">
     5|      <div class="autops-page-title">页面巡检</div>
     6|      <div class="autops-page-desc">URL可用性、状态码、响应时间、页面关键字检测</div>
     7|    </div>
     8|
     9|    <!-- 搜索栏 -->
    10|    <div class="page-toolbar">
    11|      <el-input
    12|        v-model="searchQuery"
    13|        placeholder="搜索资产名 / URL..."
    14|        clearable
    15|        style="width: 280px"
    16|        @keyup.enter="fetchData"
    17|        @clear="fetchData"
    18|      >
    19|        <template #prefix><el-icon><Search /></el-icon></template>
    20|      </el-input>
    21|      <el-select v-model="statusFilter" placeholder="检查状态" clearable style="width: 140px" @change="fetchData">
    22|        <el-option label="通过" value="pass" />
    23|        <el-option label="失败" value="fail" />
    24|        <el-option label="警告" value="warn" />
    25|      </el-select>
    26|      <el-button type="default" @click="fetchData">
    27|        <el-icon><Refresh /></el-icon> 刷新
    28|      </el-button>
    29|    </div>
    30|
    31|    <!-- 数据表格 -->
    32|    <el-table stripe :data="tableData" v-loading="loading"empty-text="暂无页面巡检数据">
    33|      <el-table-column prop="asset_name" label="资产名" min-width="160" show-overflow-tooltip />
    34|      <el-table-column prop="url" label="URL" min-width="220" show-overflow-tooltip>
    35|        <template #default="{ row }">
    36|          <el-link type="primary" :href="row.url" target="_blank" :underline="false">
    37|            {{ row.url }}
    38|          </el-link>
    39|        </template>
    40|      </el-table-column>
    41|      <el-table-column prop="status_code" label="状态码" width="100" align="center">
    42|        <template #default="{ row }">
    43|          <span :class="statusCodeClass(row.status_code)">{{ row.status_code ?? '-' }}</span>
    44|        </template>
    45|      </el-table-column>
    46|      <el-table-column prop="response_time" label="响应时间(ms)" width="140" align="center">
    47|        <template #default="{ row }">
    48|          <span :class="responseTimeClass(row.response_time)">{{ row.response_time ?? '-' }}</span>
    49|        </template>
    50|      </el-table-column>
    51|      <el-table-column prop="checked_at" label="检查时间" width="180">
    52|        <template #default="{ row }">
    53|          <span class="text-tertiary">{{ row.checked_at || row.created_at || '-' }}</span>
    54|        </template>
    55|      </el-table-column>
    56|      <el-table-column prop="status" label="状态" width="100" align="center">
    57|        <template #default="{ row }">
    58|          <el-tag :type="statusTagType(row.status)" size="small" effect="light">
    59|            {{ statusLabel(row.status) }}
    60|          </el-tag>
    61|        </template>
    62|      </el-table-column>
    63|    </el-table>
    64|
    65|    <!-- 分页 -->
    66|    <div class="page-pagination">
    67|      <el-pagination
    68|        v-model:current-page="pagination.page"
    69|        v-model:page-size="pagination.page_size"
    70|        :total="pagination.total"
    71|        :page-sizes="[10, 20, 50, 100]"
    72|        layout="total, sizes, prev, pager, next, jumper"
    73|        background
    74|        @size-change="fetchData"
    75|        @current-change="fetchData"
    76|      />
    77|    </div>
    78|  </div>
    79|</template>
    80|
    81|<script setup lang="ts">
    82|import { ref, reactive, onMounted } from 'vue'
    83|import { ElMessage } from 'element-plus'
    84|import { Search, Refresh } from '@element-plus/icons-vue'
    85|import client from '@/shared/api/client'
    86|import { API } from '@/shared/api/routes'
    87|
    88|// ---------- 状态 ----------
    89|const loading = ref(false)
    90|const tableData = ref<any[]>([])
    91|const searchQuery = ref('')
    92|const statusFilter = ref('')
    93|
    94|const pagination = reactive({
    95|  page: 1,
    96|  page_size: 20,
    97|  total: 0,
    98|})
    99|
   100|// ---------- 工具函数 ----------
   101|const statusMap: Record<string, { label: string; type: string }> = {
   102|  pass: { label: '通过', type: 'success' },
   103|  fail: { label: '失败', type: 'danger' },
   104|  warn: { label: '警告', type: 'warning' },
   105|}
   106|
   107|function statusTagType(status: string): string {
   108|  return statusMap[status]?.type ?? 'info'
   109|}
   110|
   111|function statusLabel(status: string): string {
   112|  return statusMap[status]?.label ?? status ?? '-'
   113|}
   114|
   115|function statusCodeClass(code: number | undefined): string {
   116|  if (!code) return ''
   117|  if (code >= 200 && code < 300) return 'status-success'
   118|  if (code >= 300 && code < 400) return 'status-warning'
   119|  if (code >= 400) return 'status-danger'
   120|  return ''
   121|}
   122|
   123|function responseTimeClass(ms: number | undefined): string {
   124|  if (ms === undefined || ms === null) return ''
   125|  if (ms < 500) return 'status-success'
   126|  if (ms < 2000) return 'status-warning'
   127|  return 'status-danger'
   128|}
   129|
   130|// ---------- API ----------
   131|async function fetchData() {
   132|  loading.value = true
   133|  try {
   134|    const params: Record<string, any> = {
   135|      page: pagination.page,
   136|      page_size: pagination.page_size,
   137|    }
   138|    if (searchQuery.value.trim()) {
   139|      params.keyword = searchQuery.value.trim()
   140|    }
   141|    if (statusFilter.value) {
   142|      params.status = statusFilter.value
   143|    }
   144|    const res = await client.get(API.INSPECTION.PAGE_CHECKS, { params })
   145|    const data = res.data?.data ?? res.data
   146|    tableData.value = data?.items ?? data ?? []
   147|    pagination.total = data?.total ?? tableData.value.length
   148|  } catch (err: any) {
   149|    ElMessage.error(err.message || '获取页面巡检数据失败')
   150|  } finally {
   151|    loading.value = false
   152|  }
   153|}
   154|
   155|// ---------- 初始化 ----------
   156|onMounted(() => {
   157|  fetchData()
   158|})
   159|</script>
   160|
   161|<style scoped>
   162|
   165|.page-header {
   166|  display: flex;
   167|  justify-content: space-between;
   168|  align-items: center;
   169|  margin-bottom: 4px;
   170|}
   171|.page-title {
   172|  font-size: 18px;
   173|  font-weight: 600;
   174|  color: #1d2129;
   175|  margin: 0;
   176|}
   177|.page-desc {
   178|  font-size: 13px;
   179|  color: #86909c;
   180|  margin: 0 0 16px 0;
   181|}
   182|.page-toolbar {
   183|  display: flex;
   184|  align-items: center;
   185|  gap: 12px;
   186|  margin-bottom: 16px;
   187|}
   188|.page-pagination {
   189|  display: flex;
   190|  justify-content: flex-end;
   191|  margin-top: 16px;
   192|}
   193|.text-tertiary {
   194|  color: #86909c;
   195|  font-size: 13px;
   196|}
   197|.status-success {
   198|  color: #00b42a;
   199|  font-weight: 600;
   200|}
   201|.status-warning {
   202|  color: #ff7d00;
   203|  font-weight: 600;
   204|}
   205|.status-danger {
   206|  color: #f53f3f;
   207|  font-weight: 600;
   208|}
   209|</style>
   210|