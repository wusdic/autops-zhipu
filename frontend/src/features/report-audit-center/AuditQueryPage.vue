<template>
  <div class="p-6">
    <div class="autops-page-header">
      <div class="autops-page-title">审计查询</div>
      <div class="autops-page-desc">查询系统操作审计日志</div>
    </div>

    <!-- 查询条件 -->
    <div class="autops-card mb-lg">
      <div class="autops-card-header">
        <div class="autops-card-title">查询条件</div>
      </div>
      <div class="autops-card-body">
        <el-form :inline="true" @submit.prevent="search">
          <el-form-item label="操作人">
            <el-input v-model="filter.user" placeholder="用户名" clearable style="width: 140px" />
          </el-form-item>
          <el-form-item label="操作类型">
            <el-select v-model="filter.action" clearable style="width: 140px" placeholder="全部">
              <el-option label="创建" value="create" />
              <el-option label="修改" value="update" />
              <el-option label="删除" value="delete" />
              <el-option label="登录" value="login" />
              <el-option label="执行" value="execute" />
              <el-option label="导出" value="export" />
              <el-option label="审批" value="approve" />
            </el-select>
          </el-form-item>
          <el-form-item label="目标资源">
            <el-input v-model="filter.resource" placeholder="资源名称 / ID" clearable style="width: 160px" />
          </el-form-item>
          <el-form-item label="结果">
            <el-select v-model="filter.result" clearable style="width: 100px" placeholder="全部">
              <el-option label="成功" value="success" />
              <el-option label="失败" value="failure" />
            </el-select>
          </el-form-item>
          <el-form-item label="时间范围">
            <el-date-picker
              v-model="filter.dateRange"
              type="datetimerange"
              range-separator="至"
              start-placeholder="开始时间"
              end-placeholder="结束时间"
              value-format="YYYY-MM-DD HH:mm:ss"
              style="width: 380px"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="search">查询</el-button>
            <el-button @click="resetFilter">重置</el-button>
          </el-form-item>
        </el-form>
      </div>
    </div>

    <!-- 操作栏 -->
    <div style="display: flex; justify-content: flex-end; margin-bottom: 12px">
      <el-button type="success" plain @click="handleExport" :loading="exportLoading">
        <el-icon style="margin-right: 4px"><Download /></el-icon>
        导出
      </el-button>
    </div>

    <!-- 审计日志表格 -->
    <div class="autops-card">
      <div class="autops-card-body p-0">
        <el-table stripe :data="logs"v-loading="loading" empty-text="暂无审计记录">
          <el-table-column prop="created_at" label="时间" width="170">
            <template #default="{ row }">
              <span class="text-tertiary">{{ row.created_at }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="user_name" label="用户" width="110">
            <template #default="{ row }">
              {{ row.user_name || row.username || row.user_id || '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="action" label="操作" width="180">
            <template #default="{ row }">
              <el-tag :type="(actionColor(row.action)) as TagType" size="small">{{ actionLabel(row.action) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="resource_type" label="目标类型" width="110">
            <template #default="{ row }">
              {{ row.resource_type || row.target_type || '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="resource_name" label="目标" min-width="180" show-overflow-tooltip>
            <template #default="{ row }">
              {{ row.resource_name || row.target_name || row.resource_id || '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="ip" label="IP" width="140">
            <template #default="{ row }">
              <span class="text-tertiary">{{ row.ip || row.source_ip || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="result" label="结果" width="80">
            <template #default="{ row }">
              <el-tag :type="row.result === 'success' ? 'success' : 'danger'" size="small">
                {{ row.result === 'success' ? '成功' : '失败' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="detail" label="详情" min-width="200" show-overflow-tooltip>
            <template #default="{ row }">
              {{ row.detail || row.message || '-' }}
            </template>
          </el-table-column>
        </el-table>
      </div>
      <div style="padding: 12px; display: flex; justify-content: flex-end">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="search"
          @size-change="search"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { TagType } from '@/shared/types'
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Download } from '@element-plus/icons-vue'
import { auditService } from '@/shared/api'

const loading = ref(false)
const exportLoading = ref(false)
const logs = ref<any[]>([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

const filter = reactive({
  user: 'primary',
  action: 'primary',
  resource: 'primary',
  result: 'primary',
  dateRange: [] as string[],
})

// Helpers
const actionLabelMap: Record<string, string> = {
  create: '创建', update: '修改', delete: '删除',
  login: '登录', execute: '执行', export: '导出', approve: '审批',
}
const actionLabel = (a: string) => actionLabelMap[a] || a

const actionColorMap: Record<string, TagType> = {
  create: 'success', update: 'primary', delete: 'danger',
  login: 'info', execute: 'warning', export: 'primary', approve: 'primary',
}
const actionColor = (a: string) => actionColorMap[a] || 'info'

// Search
async function search() {
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: page.value,
      page_size: pageSize.value,
    }
    if (filter.user) params.user_name = filter.user
    if (filter.action) params.action = filter.action
    if (filter.resource) params.resource = filter.resource
    if (filter.result) params.result = filter.result
    if (filter.dateRange?.length === 2) {
      params.start_time = filter.dateRange[0]
      params.end_time = filter.dateRange[1]
    }

    const res = await auditService.listLogs(params)
    const data = res.data?.data || res.data
    logs.value = data?.items || data || []
    total.value = data?.total || 0
  } catch (e: any) {
    ElMessage.error(e.message || '查询审计日志失败')
  } finally {
    loading.value = false
  }
}

// Reset
function resetFilter() {
  filter.user = ''
  filter.action = ''
  filter.resource = ''
  filter.result = ''
  filter.dateRange = []
  page.value = 1
  search()
}

// Export
async function handleExport() {
  exportLoading.value = true
  try {
    const params: Record<string, any> = {}
    if (filter.user) params.user_name = filter.user
    if (filter.action) params.action = filter.action
    if (filter.resource) params.resource = filter.resource
    if (filter.result) params.result = filter.result
    if (filter.dateRange?.length === 2) {
      params.start_time = filter.dateRange[0]
      params.end_time = filter.dateRange[1]
    }

    const res = await auditService.export(params)
    const blob = new Blob([res.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = 'audit_logs_' + new Date().toISOString().slice(0, 10) + '.xlsx'
    link.click()
    URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (e: any) {
    ElMessage.error(e.message || '导出失败')
  } finally {
    exportLoading.value = false
  }
}

onMounted(() => search())
</script>

<style scoped>

.text-tertiary {
  color: var(--autops-info);
  font-size: var(--autops-font-12);
}
</style>
