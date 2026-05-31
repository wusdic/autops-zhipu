<template>
  <div class="execution-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>执行历史</span>
        </div>
      </template>

      <!-- Filters -->
      <el-form :inline="true" class="filter-form">
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部" clearable @change="loadExecutions">
            <el-option label="待审批" value="pending" />
            <el-option label="执行中" value="running" />
            <el-option label="已完成" value="completed" />
            <el-option label="失败" value="failed" />
            <el-option label="已取消" value="cancelled" />
          </el-select>
        </el-form-item>
        <el-form-item label="搜索">
          <el-input v-model="filters.search" placeholder="执行ID / 策略名" clearable @clear="loadExecutions" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadExecutions">查询</el-button>
        </el-form-item>
      </el-form>

      <!-- Table -->
      <el-table :data="executions" v-loading="loading" stripe>
        <el-table-column prop="id" label="执行ID" width="200" show-overflow-tooltip />
        <el-table-column prop="policy_name" label="策略名称" min-width="160" />
        <el-table-column prop="status" label="状态" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="started_at" label="开始时间" width="180" />
        <el-table-column prop="duration" label="耗时" width="100" align="center">
          <template #default="{ row }">
            {{ row.duration ? row.duration + 's' : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="goDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        @change="loadExecutions"
        style="margin-top: 16px; justify-content: flex-end"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '@/shared/api/client'
import { API } from '@/shared/api/routes'

const router = useRouter()

const loading = ref(false)
const executions = ref<any[]>([])

const filters = reactive({ status: '', search: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

function statusType(s: string) {
  const map: Record<string, string> = {
    pending: 'warning', running: '', completed: 'success', failed: 'danger', cancelled: 'info',
  }
  return map[s] || 'info'
}

function statusLabel(s: string) {
  const map: Record<string, string> = {
    pending: '待审批', running: '执行中', completed: '已完成', failed: '失败', cancelled: '已取消',
  }
  return map[s] || s
}

async function loadExecutions() {
  loading.value = true
  try {
    const params: any = { page: pagination.page, page_size: pagination.pageSize }
    if (filters.status) params.status = filters.status
    if (filters.search) params.search = filters.search
    const { data } = await api.get(API.EXECUTIONS, { params })
    if (data.code === 0) {
      executions.value = data.data.items || []
      pagination.total = data.data.total || 0
    }
  } catch (e: any) {
    ElMessage.error('加载执行历史失败: ' + (e.message || e))
  } finally {
    loading.value = false
  }
}

function goDetail(row: any) {
  router.push({ name: 'execution-detail', params: { id: row.id } })
}

onMounted(() => loadExecutions())
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
.filter-form { margin-bottom: 16px; }
</style>
