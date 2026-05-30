<template>
  <div>
    <el-card>
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span>审计日志</span>
          <div>
            <el-date-picker v-model="dateRange" type="datetimerange" range-separator="至"
              start-placeholder="开始时间" end-placeholder="结束时间"
              style="margin-right:8px" @change="loadLogs" />
            <el-input v-model="filters.user" placeholder="用户" style="width:120px;margin-right:8px" clearable @change="loadLogs" />
            <el-input v-model="filters.action" placeholder="操作" style="width:120px;margin-right:8px" clearable @change="loadLogs" />
            <el-button @click="loadLogs">刷新</el-button>
          </div>
        </div>
      </template>

      <el-table :data="logs" v-loading="loading" stripe>
        <el-table-column prop="action" label="操作" width="140" />
        <el-table-column prop="resource_type" label="资源类型" width="120" />
        <el-table-column prop="resource_id" label="资源ID" width="160" show-overflow-tooltip />
        <el-table-column prop="user_id" label="用户" width="120" />
        <el-table-column prop="detail" label="详情" min-width="250" show-overflow-tooltip />
        <el-table-column prop="ip_address" label="IP" width="130" />
        <el-table-column prop="trace_id" label="TraceID" width="140" show-overflow-tooltip />
        <el-table-column prop="created_at" label="时间" width="170" sortable>
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
      </el-table>

      <el-pagination v-model:current-page="page" :page-size="pageSize" :total="total"
        :page-sizes="[20,50,100]" layout="total, sizes, prev, pager, next"
        @change="loadLogs" style="margin-top:16px;justify-content:flex-end" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import api from '@/shared/api/client'

const loading = ref(false)
const logs = ref<any[]>([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const dateRange = ref<any>(null)
const filters = reactive({ user: '', action: '' })

function formatTime(t: string) { return t ? new Date(t).toLocaleString('zh-CN') : '' }

async function loadLogs() {
  loading.value = true
  try {
    const params: any = { page: page.value, page_size: pageSize.value }
    if (filters.user) params.user_id = filters.user
    if (filters.action) params.action = filters.action
    const { data } = await api.get('/api/v1/audit-logs', { params })
    if (data.code === 0) { logs.value = data.data.items || []; total.value = data.data.total || 0 }
  } finally { loading.value = false }
}

onMounted(() => loadLogs())
</script>
