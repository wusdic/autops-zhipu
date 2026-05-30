<template>
  <div>
    <el-row :gutter="16">
      <!-- 采集器列表 -->
      <el-col :span="16">
        <el-card>
          <template #header>
            <div style="display:flex;justify-content:space-between;align-items:center">
              <span>采集器管理</span>
              <el-button @click="loadCollectors">刷新</el-button>
            </div>
          </template>
          <el-table :data="collectors" v-loading="loading" stripe>
            <el-table-column prop="name" label="名称" min-width="140" />
            <el-table-column prop="collector_type" label="类型" width="100">
              <template #default="{ row }">
                <el-tag size="small">{{ row.collector_type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="protocol" label="协议" width="80" />
            <el-table-column prop="status" label="状态" width="90">
              <template #default="{ row }">
                <el-tag :type="row.status==='active'?'success':row.status==='error'?'danger':'info'" size="small">
                  {{ row.status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="last_seen_at" label="最后上报" width="160">
              <template #default="{ row }">{{ formatTime(row.last_seen_at) }}</template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="160">
              <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
            </el-table-column>
            <el-table-column label="操作" width="120" fixed="right">
              <template #default="{ row }">
                <el-button size="small" @click="viewCollector(row)">详情</el-button>
                <el-button size="small" type="danger" @click="deleteCollector(row.id)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <!-- 最近采集结果 -->
      <el-col :span="8">
        <el-card>
          <template #header><span>最近采集结果</span></template>
          <el-table :data="results" v-loading="resultLoading" stripe size="small" max-height="500">
            <el-table-column prop="status" label="状态" width="60">
              <template #default="{ row }">
                <el-tag :type="row.status==='success'?'success':'danger'" size="small">{{ row.status === 'success' ? '✅' : '❌' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="collector_id" label="采集器" width="110" show-overflow-tooltip />
            <el-table-column prop="created_at" label="时间" width="140">
              <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/shared/api/client'
import { API as R } from '@/shared/api/routes'

const loading = ref(false)
const collectors = ref<any[]>([])
const resultLoading = ref(false)
const results = ref<any[]>([])

function formatTime(t: string) { return t ? new Date(t).toLocaleString('zh-CN') : '' }

async function loadCollectors() {
  loading.value = true
  try {
    const { data } = await api.get(R.COLLECTORS, { params: { page: 1, page_size: 50 } })
    if (data.code === 0) collectors.value = data.data.items || []
  } finally { loading.value = false }
}

async function loadResults() {
  resultLoading.value = true
  try {
    const { data } = await api.get(R.COLLECTION_JOBS, { params: { page: 1, page_size: 20 } })
    if (data.code === 0) results.value = data.data.items || []
  } finally { resultLoading.value = false }
}

function viewCollector(row: any) { ElMessage.info(`采集器: ${row.name} (${row.collector_type})`) }

async function deleteCollector(id: string) {
  await ElMessageBox.confirm('确定删除此采集器？', '确认', { type: 'warning' })
  const { data } = await api.delete(`/api/v1/collectors/${id}`)
  if (data.code === 0) { ElMessage.success('已删除'); loadCollectors() }
}

onMounted(() => { loadCollectors(); loadResults() })
</script>
