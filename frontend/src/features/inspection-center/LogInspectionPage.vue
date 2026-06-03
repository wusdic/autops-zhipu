     1|<template>
     2|  <div class="page-container">
     3|    <!-- 页面头部 -->
     4|    <div class="autops-page-header">
     5|      <div class="autops-page-title">日志巡检</div>
     6|      <div class="autops-page-desc">日志源、匹配规则、命中数量、样例日志</div>
     7|    </div>
     8|
     9|    <!-- 搜索栏 -->
    10|    <div class="page-toolbar">
    11|      <el-input
    12|        v-model="searchQuery"
    13|        placeholder="搜索资产名 / 日志路径..."
    14|        clearable
    15|        style="width: 280px"
    16|        @keyup.enter="fetchData"
    17|        @clear="fetchData"
    18|      >
    19|        <template #prefix><el-icon><Search /></el-icon></template>
    20|      </el-input>
    21|      <el-select v-model="severityFilter" placeholder="严重级别" clearable style="width: 140px" @change="fetchData">
    22|        <el-option label="错误" value="error" />
    23|        <el-option label="警告" value="warning" />
    24|        <el-option label="信息" value="info" />
    25|      </el-select>
    26|      <el-button type="default" @click="fetchData">
    27|        <el-icon><Refresh /></el-icon> 刷新
    28|      </el-button>
    29|    </div>
    30|
    31|    <!-- 数据表格 -->
    32|    <el-table stripe :data="tableData" v-loading="loading"empty-text="暂无日志巡检数据">
    33|      <el-table-column prop="asset_name" label="资产名" min-width="160" show-overflow-tooltip />
    34|      <el-table-column prop="log_path" label="日志路径" min-width="220" show-overflow-tooltip>
    35|        <template #default="{ row }">
    36|          <span class="log-path">{{ row.log_path ?? row.log_source ?? '-' }}</span>
    37|        </template>
    38|      </el-table-column>
    39|      <el-table-column prop="error_count" label="错误数" width="100" align="center">
    40|        <template #default="{ row }">
    41|          <el-badge
    42|            v-if="row.error_count && row.error_count > 0"
    43|            :value="row.error_count"
    44|            :max="9999"
    45|            type="danger"
    46|            class="count-badge"
    47|          >
    48|            <span class="count-value danger">{{ row.error_count }}</span>
    49|          </el-badge>
    50|          <span v-else class="count-value">{{ row.error_count ?? 0 }}</span>
    51|        </template>
    52|      </el-table-column>
    53|      <el-table-column prop="warning_count" label="警告数" width="100" align="center">
    54|        <template #default="{ row }">
    55|          <span :class="['count-value', row.warning_count > 0 ? 'warning' : '']">
    56|            {{ row.warning_count ?? 0 }}
    57|          </span>
    58|        </template>
    59|      </el-table-column>
    60|      <el-table-column prop="pattern" label="关键模式匹配" min-width="200" show-overflow-tooltip>
    61|        <template #default="{ row }">
    62|          <template v-if="row.patterns && Array.isArray(row.patterns) && row.patterns.length > 0">
    63|            <el-tag
    64|              v-for="(p, idx) in row.patterns.slice(0, 3)"
    65|              :key="idx"
    66|              size="small"
    67|              effect="plain"
    68|              class="pattern-tag"
    69|            >
    70|              {{ p }}
    71|            </el-tag>
    72|            <span v-if="row.patterns.length > 3" class="text-tertiary">
    73|              +{{ row.patterns.length - 3 }}
    74|            </span>
    75|          </template>
    76|          <template v-else-if="row.pattern">
    77|            <el-tag size="small" effect="plain">{{ row.pattern }}</el-tag>
    78|          </template>
    79|          <template v-else-if="row.match_rule">
    80|            <el-tag size="small" effect="plain">{{ row.match_rule }}</el-tag>
    81|          </template>
    82|          <span v-else class="text-tertiary">-</span>
    83|        </template>
    84|      </el-table-column>
    85|      <el-table-column prop="checked_at" label="检查时间" width="180">
    86|        <template #default="{ row }">
    87|          <span class="text-tertiary">{{ row.checked_at || row.created_at || '-' }}</span>
    88|        </template>
    89|      </el-table-column>
    90|    </el-table>
    91|
    92|    <!-- 分页 -->
    93|    <div class="page-pagination">
    94|      <el-pagination
    95|        v-model:current-page="pagination.page"
    96|        v-model:page-size="pagination.page_size"
    97|        :total="pagination.total"
    98|        :page-sizes="[10, 20, 50, 100]"
    99|        layout="total, sizes, prev, pager, next, jumper"
   100|        background
   101|        @size-change="fetchData"
   102|        @current-change="fetchData"
   103|      />
   104|    </div>
   105|  </div>
   106|</template>
   107|
   108|<script setup lang="ts">
   109|import { ref, reactive, onMounted } from 'vue'
   110|import { ElMessage } from 'element-plus'
   111|import { Search, Refresh } from '@element-plus/icons-vue'
   112|import client from '@/shared/api/client'
   113|import { API } from '@/shared/api/routes'
   114|
   115|// ---------- 状态 ----------
   116|const loading = ref(false)
   117|const tableData = ref<any[]>([])
   118|const searchQuery = ref('')
   119|const severityFilter = ref('')
   120|
   121|const pagination = reactive({
   122|  page: 1,
   123|  page_size: 20,
   124|  total: 0,
   125|})
   126|
   127|// ---------- API ----------
   128|async function fetchData() {
   129|  loading.value = true
   130|  try {
   131|    const params: Record<string, any> = {
   132|      page: pagination.page,
   133|      page_size: pagination.page_size,
   134|    }
   135|    if (searchQuery.value.trim()) {
   136|      params.keyword = searchQuery.value.trim()
   137|    }
   138|    if (severityFilter.value) {
   139|      params.severity = severityFilter.value
   140|    }
   141|    const res = await client.get(API.INSPECTION.LOG_CHECKS, { params })
   142|    const data = res.data?.data ?? res.data
   143|    tableData.value = data?.items ?? data ?? []
   144|    pagination.total = data?.total ?? tableData.value.length
   145|  } catch (err: any) {
   146|    ElMessage.error(err.message || '获取日志巡检数据失败')
   147|  } finally {
   148|    loading.value = false
   149|  }
   150|}
   151|
   152|// ---------- 初始化 ----------
   153|onMounted(() => {
   154|  fetchData()
   155|})
   156|</script>
   157|
   158|<style scoped>
   159|
   162|.page-header {
   163|  display: flex;
   164|  justify-content: space-between;
   165|  align-items: center;
   166|  margin-bottom: 4px;
   167|}
   168|.page-title {
   169|  font-size: 18px;
   170|  font-weight: 600;
   171|  color: #1d2129;
   172|  margin: 0;
   173|}
   174|.page-desc {
   175|  font-size: 13px;
   176|  color: #86909c;
   177|  margin: 0 0 16px 0;
   178|}
   179|.page-toolbar {
   180|  display: flex;
   181|  align-items: center;
   182|  gap: 12px;
   183|  margin-bottom: 16px;
   184|}
   185|.page-pagination {
   186|  display: flex;
   187|  justify-content: flex-end;
   188|  margin-top: 16px;
   189|}
   190|.text-tertiary {
   191|  color: #86909c;
   192|  font-size: 13px;
   193|}
   194|.log-path {
   195|  font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
   196|  font-size: 13px;
   197|  color: #4e5969;
   198|}
   199|.count-value {
   200|  font-weight: 600;
   201|  font-size: 14px;
   202|}
   203|.count-value.danger {
   204|  color: #f53f3f;
   205|}
   206|.count-value.warning {
   207|  color: #ff7d00;
   208|}
   209|.count-badge {
   210|  display: inline-flex;
   211|  align-items: center;
   212|}
   213|.pattern-tag {
   214|  margin-right: 4px;
   215|  margin-bottom: 2px;
   216|}
   217|</style>
   218|