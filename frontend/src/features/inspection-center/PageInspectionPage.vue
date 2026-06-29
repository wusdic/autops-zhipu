<template>
  <div class="autops-page-container">
    <PageHeader title="页面巡检" desc="URL可用性、状态码、响应时间、页面关键字检测" />

    <!-- 搜索栏 -->
    <div class="page-toolbar">
      <el-input
        v-model="searchQuery"
        placeholder="搜索资产名 / URL..."
        clearable
        style="width: 280px"
        @keyup.enter="fetchData"
        @clear="fetchData"
      >
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
      <el-select v-model="statusFilter" placeholder="检查状态" clearable style="width: 140px" @change="fetchData">
        <el-option label="通过" value="pass" />
        <el-option label="失败" value="fail" />
        <el-option label="警告" value="warn" />
      </el-select>
      <el-button type="default" @click="fetchData">
        <el-icon><Refresh /></el-icon> 刷新
      </el-button>
    </div>

    <!-- 数据表格 -->
    <el-table stripe :data="tableData" v-loading="loading"empty-text="暂无页面巡检数据">
      <el-table-column prop="asset_name" label="资产名" min-width="160" show-overflow-tooltip />
      <el-table-column prop="url" label="URL" min-width="220" show-overflow-tooltip>
        <template #default="{ row }">
          <el-link type="primary" :href="row.url" target="_blank" :underline="false">
            {{ row.url }}
          </el-link>
        </template>
      </el-table-column>
      <el-table-column prop="status_code" label="状态码" width="100" align="center">
        <template #default="{ row }">
          <span :class="statusCodeClass(row.status_code)">{{ row.status_code ?? '-' }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="response_time" label="响应时间(ms)" width="140" align="center">
        <template #default="{ row }">
          <span :class="responseTimeClass(row.response_time)">{{ row.response_time ?? '-' }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="checked_at" label="检查时间" width="180">
        <template #default="{ row }">
          <span class="text-tertiary">{{ row.checked_at || row.created_at || '-' }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100" align="center">
        <template #default="{ row }">
          <StatusBadge :status="row.status" />
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
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh } from '@element-plus/icons-vue'
import PageHeader from '@/shared/components/PageHeader.vue'
import StatusBadge from '@/shared/components/StatusBadge.vue'
import client from '@/shared/api/client'
import { checkResultTag, checkResultLabel } from '@/shared/utils/labels'
import { API } from '@/shared/api/routes'

// ---------- 状态 ----------
const loading = ref(false)
const tableData = ref<any[]>([])
const searchQuery = ref('')
const statusFilter = ref('')

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0,
})

// ---------- 工具函数（结果取值统一来自 labels.ts）----------
const statusTagType = (status: string): TagType => checkResultTag(status) as TagType
const statusLabel = (status: string): string => checkResultLabel(status)

function statusCodeClass(code: number | undefined): string {
  if (!code) return ''
  if (code >= 200 && code < 300) return 'status-success'
  if (code >= 300 && code < 400) return 'status-warning'
  if (code >= 400) return 'status-danger'
  return ''
}

function responseTimeClass(ms: number | undefined): string {
  if (ms === undefined || ms === null) return ''
  if (ms < 500) return 'status-success'
  if (ms < 2000) return 'status-warning'
  return 'status-danger'
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
    if (statusFilter.value) {
      params.status = statusFilter.value
    }
    const res = await client.get(API.INSPECTION.PAGE_CHECKS, { params })
    const data = res.data?.data ?? res.data
    tableData.value = data?.items ?? data ?? []
    pagination.total = data?.total ?? tableData.value.length
  } catch (err: any) {
    ElMessage.error(err.message || '获取页面巡检数据失败')
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
.status-success {
  color: var(--autops-success);
  font-weight: 600;
}
.status-warning {
  color: var(--autops-warning);
  font-weight: 600;
}
.status-danger {
  color: var(--autops-danger);
  font-weight: 600;
}
</style>
