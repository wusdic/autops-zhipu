<template>
  <div class="autops-page-container">
    <!-- 页面头部 -->
    <div class="autops-page-header">
      <div class="autops-page-title">安全基线</div>
      <div class="autops-page-desc">查看和管理资产安全合规基线检查</div>
    </div>

    <!-- Search & Filter -->
    <el-card shadow="never" class="filter-card">
      <el-form :inline="true" :model="queryForm" @submit.prevent="handleSearch">
        <el-form-item label="资产名">
          <el-input v-model="queryForm.asset_name" placeholder="请输入资产名" clearable style="width: 200px" />
        </el-form-item>
        <el-form-item label="基线名称">
          <el-input v-model="queryForm.baseline_name" placeholder="请输入基线名称" clearable style="width: 200px" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="queryForm.status" placeholder="全部" clearable style="width: 160px">
            <el-option label="合规" value="compliant" />
            <el-option label="不合规" value="non-compliant" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>查询
          </el-button>
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon>重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Data Table -->
    <el-card shadow="never" class="table-card">
      <el-table stripe v-loading="loading" :data="tableData"border style="width: 100%">
        <el-table-column prop="asset_name" label="资产名" min-width="140" show-overflow-tooltip />
        <el-table-column prop="baseline_name" label="基线名称" min-width="160" show-overflow-tooltip />
        <el-table-column prop="check_items" label="检查项数" width="100" align="center">
          <template #default="{ row }">
            <el-tag size="small">{{ row.check_items ?? 0 }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="compliance_rate" label="合规率(%)" width="120" align="center">
          <template #default="{ row }">
            <el-progress
              :percentage="Number(row.compliance_rate ?? 0)"
              :color="getComplianceColor(row.compliance_rate)"
              :stroke-width="14"
              :text-inside="true"
              style="width: 100%"
            />
          </template>
        </el-table-column>
        <el-table-column prop="last_check_time" label="最后检查时间" width="180" align="center">
          <template #default="{ row }">
            {{ formatTime(row.last_check_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'compliant' ? 'success' : 'danger'" effect="dark" size="small">
              {{ row.status === 'compliant' ? '合规' : '不合规' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" plain size="small" @click="handleDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- Pagination -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          background
          @size-change="fetchData"
          @current-change="fetchData"
        />
      </div>
    </el-card>

    <!-- Detail Drawer -->
    <el-drawer v-model="drawerVisible" title="基线检查详情" size="500px">
      <template v-if="currentRow">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="资产名">{{ currentRow.asset_name }}</el-descriptions-item>
          <el-descriptions-item label="基线名称">{{ currentRow.baseline_name }}</el-descriptions-item>
          <el-descriptions-item label="检查项数">{{ currentRow.check_items }}</el-descriptions-item>
          <el-descriptions-item label="合规率">{{ currentRow.compliance_rate }}%</el-descriptions-item>
          <el-descriptions-item label="最后检查时间">{{ formatTime(currentRow.last_check_time) }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="currentRow.status === 'compliant' ? 'success' : 'danger'" effect="dark">
              {{ currentRow.status === 'compliant' ? '合规' : '不合规' }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>
        <div v-if="currentRow.details" class="detail-section">
          <h4>检查详情</h4>
          <el-table stripe  :data="currentRow.details" size="small" border>
            <el-table-column prop="item" label="检查项" />
            <el-table-column prop="result" label="结果" width="100">
              <template #default="{ row }">
                <el-tag :type="row.result === 'pass' ? 'success' : 'danger'" size="small">
                  {{ row.result === 'pass' ? '通过' : '未通过' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { Search, Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import client from '@/shared/api/client'
import { API } from '@/shared/api/routes'

interface BaselineRecord {
  id: string | number
  asset_name: string
  baseline_name: string
  check_items: number
  compliance_rate: number
  last_check_time: string
  status: 'compliant' | 'non-compliant'
  details?: Array<{ item: string; result: string }>
}

const loading = ref(false)
const tableData = ref<BaselineRecord[]>([])
const drawerVisible = ref(false)
const currentRow = ref<BaselineRecord | null>(null)

const queryForm = reactive({
  asset_name: '',
  baseline_name: '',
  status: '',
})

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0,
})

function formatTime(t: string | undefined): string {
  if (!t) return '-'
  return new Date(t).toLocaleString('zh-CN')
}

function getComplianceColor(rate: number | undefined): string {
  const r = rate ?? 0
  if (r >= 90) return '#00b42a'
  if (r >= 70) return '#ff7d00'
  return '#f53f3f'
}

function buildParams() {
  return {
    page: pagination.page,
    page_size: pagination.page_size,
    asset_name: queryForm.asset_name || undefined,
    baseline_name: queryForm.baseline_name || undefined,
    status: queryForm.status || undefined,
  }
}

async function fetchData() {
  loading.value = true
  try {
    const res = await client.get(API.INSPECTION.BASELINE_CHECKS, { params: buildParams() })
    const data = res.data?.data ?? res.data ?? {}
    tableData.value = data.items ?? data.records ?? data.list ?? []
    pagination.total = data.total ?? tableData.value.length
  } catch (e: any) {
    ElMessage.error('获取基线检查数据失败: ' + (e.message ?? '未知错误'))
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  pagination.page = 1
  fetchData()
}

function handleReset() {
  queryForm.asset_name = ''
  queryForm.baseline_name = ''
  queryForm.status = ''
  handleSearch()
}

function handleDetail(row: BaselineRecord) {
  currentRow.value = row
  drawerVisible.value = true
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.security-baseline-page {
  padding: var(--autops-space-lg);
}
.filter-card {
  margin-bottom: var(--autops-space-lg);
}
.table-card {
  margin-bottom: var(--autops-space-lg);
}
.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: var(--autops-space-lg);
}
.detail-section {
  margin-top: var(--autops-space-xl);
}
.detail-section h4 {
  margin-bottom: 10px;
  color: var(--autops-text-1);
}
</style>
