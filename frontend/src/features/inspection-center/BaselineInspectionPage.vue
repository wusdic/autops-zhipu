<template>
  <div class="autops-page-container">
    <!-- 页面头部 -->
    <div class="autops-page-header">
      <div class="autops-page-title">基线巡检</div>
      <div class="autops-page-desc">安全和运维基线检查、合规状态、整改建议</div>
    </div>

    <!-- 搜索栏 -->
    <div class="autops-toolbar">
      <el-input
        v-model="searchQuery"
        placeholder="搜索资产名 / 检查项..."
        clearable
        style="width: 280px"
        @keyup.enter="fetchData"
        @clear="fetchData"
      >
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
      <el-select v-model="complianceFilter" placeholder="合规状态" clearable style="width: 150px" @change="fetchData">
        <el-option label="合规" value="compliant" />
        <el-option label="不合规" value="non-compliant" />
      </el-select>
      <el-button type="default" @click="fetchData">
        <el-icon><Refresh /></el-icon> 刷新
      </el-button>
    </div>

    <!-- 统计摘要 -->
    <div v-if="summary.total > 0" class="summary-bar">
      <div class="summary-item">
        <span class="summary-label">总计</span>
        <span class="summary-value">{{ summary.total }}</span>
      </div>
      <div class="summary-item">
        <span class="summary-label">合规</span>
        <span class="summary-value success">{{ summary.compliant }}</span>
      </div>
      <div class="summary-item">
        <span class="summary-label">不合规</span>
        <span class="summary-value danger">{{ summary.nonCompliant }}</span>
      </div>
      <div class="summary-item">
        <span class="summary-label">合规率</span>
        <span class="summary-value">{{ summary.rate }}%</span>
      </div>
    </div>

    <!-- 数据表格 -->
    <el-table stripe :data="tableData" v-loading="loading"empty-text="暂无基线巡检数据">
      <el-table-column prop="asset_name" label="资产名" min-width="160" show-overflow-tooltip />
      <el-table-column prop="check_item" label="检查项" min-width="180" show-overflow-tooltip>
        <template #default="{ row }">
          <span>{{ row.check_item ?? row.baseline_item ?? '-' }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="baseline_value" label="基线值" min-width="150" show-overflow-tooltip>
        <template #default="{ row }">
          <span class="value-text">{{ row.baseline_value ?? row.expected ?? '-' }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="current_value" label="当前值" min-width="150" show-overflow-tooltip>
        <template #default="{ row }">
          <span :class="{ 'value-drift': row.status === 'non-compliant', 'value-text': true }">
            {{ row.current_value ?? row.actual ?? '-' }}
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="合规状态" width="120" align="center">
        <template #default="{ row }">
          <el-tag :type="(complianceTagType(row.status)) as TagType" size="small" effect="light">
            <el-icon v-if="row.status === 'non-compliant'" style="margin-right: 2px"><CircleCloseFilled /></el-icon>
            <el-icon v-else-if="row.status === 'compliant'" style="margin-right: 2px"><CircleCheckFilled /></el-icon>
            {{ complianceLabel(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="checked_at" label="检查时间" width="180">
        <template #default="{ row }">
          <span class="text-tertiary">{{ row.checked_at || row.created_at || '-' }}</span>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="page-pagination">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.page_size"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        background
        @size-change="fetchData"
        @current-change="fetchData"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import type { TagType } from '@/shared/types'
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh, CircleCheckFilled, CircleCloseFilled } from '@element-plus/icons-vue'
import client from '@/shared/api/client'
import { API } from '@/shared/api/routes'

// ---------- 状态 ----------
const loading = ref(false)
const tableData = ref<any[]>([])
const searchQuery = ref('')
const complianceFilter = ref('')

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0,
})

// ---------- 统计摘要 ----------
const summary = computed(() => {
  const total = tableData.value.length
  const compliant = tableData.value.filter(r => r.status === 'compliant').length
  const nonCompliant = tableData.value.filter(r => r.status === 'non-compliant').length
  const rate = total > 0 ? Math.round((compliant / total) * 100) : 0
  return { total, compliant, nonCompliant, rate }
})

// ---------- 工具函数 ----------
const complianceMap: Record<string, { label: string; type: string }> = {
  compliant: { label: '合规', type: 'success' },
  'non-compliant': { label: '不合规', type: 'danger' },
}

function complianceTagType(status: string): TagType {
  return (complianceMap[status]?.type ?? 'info') as TagType
}

function complianceLabel(status: string): string {
  return complianceMap[status]?.label ?? status ?? '-'
}

// ---------- API ----------
async function fetchData() {
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: pagination.page,
      page_size: pagination.page_size,
    }
    if (searchQuery.value.trim()) {
      params.keyword = searchQuery.value.trim()
    }
    if (complianceFilter.value) {
      params.status = complianceFilter.value
    }
    const res = await client.get(API.INSPECTION.BASELINE_CHECKS, { params })
    const data = res.data?.data ?? res.data
    tableData.value = data?.items ?? data ?? []
    pagination.total = data?.total ?? tableData.value.length
  } catch (err: any) {
    ElMessage.error(err.message || '获取基线巡检数据失败')
  } finally {
    loading.value = false
  }
}

// ---------- 初始化 ----------
onMounted(() => {
  fetchData()
})
</script>

<style scoped>

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.page-desc {
  font-size: var(--autops-font-13);
  color: var(--autops-info);
  margin: 0 0 16px 0;
}
.page-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: var(--autops-space-lg);
}
.page-pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: var(--autops-space-lg);
}
.text-tertiary {
  color: var(--autops-info);
  font-size: var(--autops-font-13);
}
.value-text {
  font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
  font-size: var(--autops-font-13);
}
.value-drift {
  color: var(--autops-danger);
  font-weight: 600;
}

/* 统计摘要 */
.summary-bar {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: var(--autops-space-md) 20px;
  margin-bottom: var(--autops-space-lg);
  background: var(--autops-bg-2);
  border-radius: 6px;
}
.summary-item {
  display: flex;
  align-items: center;
  gap: 6px;
}
.summary-label {
  font-size: var(--autops-font-13);
  color: var(--autops-info);
}
.summary-value {
  font-size: var(--autops-font-16);
  font-weight: 700;
  color: var(--autops-text-1);
}
.summary-value.success {
  color: var(--autops-success);
}
.summary-value.danger {
  color: var(--autops-danger);
}
</style>
