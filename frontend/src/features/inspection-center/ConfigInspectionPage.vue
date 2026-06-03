<template>
  <div class="page-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <h2 class="page-title">配置巡检</h2>
    </div>
    <p class="page-desc">期望配置与实际配置对比，发现配置漂移</p>

    <!-- 搜索栏 -->
    <div class="page-toolbar">
      <el-input
        v-model="searchQuery"
        placeholder="搜索资产名 / 配置项..."
        clearable
        style="width: 280px"
        @keyup.enter="fetchData"
        @clear="fetchData"
      >
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
      <el-select v-model="driftFilter" placeholder="漂移状态" clearable style="width: 140px" @change="fetchData">
        <el-option label="已漂移" value="drifted" />
        <el-option label="一致" value="matched" />
        <el-option label="未知" value="unknown" />
      </el-select>
      <el-button type="default" @click="fetchData">
        <el-icon><Refresh /></el-icon> 刷新
      </el-button>
    </div>

    <!-- 数据表格 -->
    <el-table :data="tableData" v-loading="loading" stripe empty-text="暂无配置巡检数据">
      <el-table-column prop="asset_name" label="资产名" min-width="160" show-overflow-tooltip />
      <el-table-column prop="config_item" label="配置项" min-width="180" show-overflow-tooltip />
      <el-table-column prop="expected_value" label="期望值" min-width="150" show-overflow-tooltip>
        <template #default="{ row }">
          <span class="value-text">{{ row.expected_value ?? row.expected ?? '-' }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="actual_value" label="实际值" min-width="150" show-overflow-tooltip>
        <template #default="{ row }">
          <span :class="{ 'value-drift': isDrifted(row) }">
            {{ row.actual_value ?? row.actual ?? '-' }}
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="drift_status" label="漂移状态" width="110" align="center">
        <template #default="{ row }">
          <el-tag :type="driftTagType(row.drift_status ?? row.status)" size="small" effect="light">
            <el-icon v-if="isDrifted(row)" style="margin-right: 2px"><WarningFilled /></el-icon>
            {{ driftLabel(row.drift_status ?? row.status) }}
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
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh, WarningFilled } from '@element-plus/icons-vue'
import client from '@/shared/api/client'
import { API } from '@/shared/api/routes'

// ---------- 状态 ----------
const loading = ref(false)
const tableData = ref<any[]>([])
const searchQuery = ref('')
const driftFilter = ref('')

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0,
})

// ---------- 工具函数 ----------
const driftMap: Record<string, { label: string; type: string }> = {
  drifted: { label: '已漂移', type: 'danger' },
  matched: { label: '一致', type: 'success' },
  unknown: { label: '未知', type: 'info' },
}

function driftTagType(status: string): string {
  return driftMap[status]?.type ?? 'info'
}

function driftLabel(status: string): string {
  return driftMap[status]?.label ?? status ?? '-'
}

function isDrifted(row: any): boolean {
  const status = row.drift_status ?? row.status
  return status === 'drifted'
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
    if (driftFilter.value) {
      params.drift_status = driftFilter.value
    }
    const res = await client.get(API.INSPECTION.CONFIG_CHECKS, { params })
    const data = res.data?.data ?? res.data
    tableData.value = data?.items ?? data ?? []
    pagination.total = data?.total ?? tableData.value.length
  } catch (err: any) {
    ElMessage.error(err.message || '获取配置巡检数据失败')
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
.page-container {
  padding: 24px;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}
.page-title {
  font-size: 18px;
  font-weight: 600;
  color: #1d2129;
  margin: 0;
}
.page-desc {
  font-size: 13px;
  color: #86909c;
  margin: 0 0 16px 0;
}
.page-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}
.page-pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
.text-tertiary {
  color: #86909c;
  font-size: 13px;
}
.value-text {
  font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
}
.value-drift {
  color: #f53f3f;
  font-weight: 600;
  font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
}
</style>
