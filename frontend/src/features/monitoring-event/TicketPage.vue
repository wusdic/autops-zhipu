<template>
  <div>
    <el-card>
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span>工单中心</span>
          <el-button type="primary" @click="showCreate = true">新建工单</el-button>
        </div>
      </template>

      <el-table :data="tickets" v-loading="loading" stripe>
        <el-table-column prop="priority" label="优先级" width="80">
          <template #default="{ row }">
            <el-tag :type="row.priority==='critical'?'danger':row.priority==='high'?'warning':'info'" size="small">
              {{ row.priority }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" min-width="200" />
        <el-table-column prop="ticket_type" label="类型" width="90" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewTicket(row)">查看</el-button>
            <el-button v-if="row.status==='open'" size="small" type="success"
              @click="closeTicket(row.id)">关闭</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination v-model:current-page="page" v-model:page-size="pageSize" :total="total"
        layout="total, prev, pager, next" @change="load" style="margin-top:16px;justify-content:flex-end" />
    </el-card>

    <el-dialog v-model="showCreate" title="新建工单" width="500px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="标题"><el-input v-model="form.title" /></el-form-item>
        <el-form-item label="类型">
          <el-select v-model="form.ticket_type"><el-option label="事件" value="incident" />
            <el-option label="变更" value="change" /><el-option label="任务" value="task" /></el-select>
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="form.priority"><el-option label="紧急" value="critical" />
            <el-option label="高" value="high" /><el-option label="中" value="medium" />
            <el-option label="低" value="low" /></el-select>
        </el-form-item>
        <el-form-item label="描述"><el-input v-model="form.description" type="textarea" :rows="3" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" @click="createTicket">创建</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="showDetail" title="工单详情" size="450px">
      <template v-if="current">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="标题">{{ current.title }}</el-descriptions-item>
          <el-descriptions-item label="类型">{{ current.ticket_type }}</el-descriptions-item>
          <el-descriptions-item label="状态"><el-tag>{{ current.status }}</el-tag></el-descriptions-item>
          <el-descriptions-item label="优先级">{{ current.priority }}</el-descriptions-item>
          <el-descriptions-item label="描述">{{ current.description || '-' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ current.created_at }}</el-descriptions-item>
        </el-descriptions>
        <h4 style="margin-top:20px">评论</h4>
        <div v-for="c in comments" :key="c.id" style="margin:8px 0;padding:8px;background:#f5f7fa;border-radius:4px">
          <div style="font-size:12px;color:#909399">{{ c.created_at }}</div>
          <div>{{ c.content }}</div>
        </div>
        <el-input v-model="commentText" placeholder="输入评论" style="margin-top:8px">
          <template #append><el-button @click="addComment(current.id)">发送</el-button></template>
        </el-input>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/shared/api/client'

const loading = ref(false)
const tickets = ref<any[]>([])
const showCreate = ref(false)
const showDetail = ref(false)
const current = ref<any>(null)
const comments = ref<any[]>([])
const commentText = ref('')
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const form = reactive({ title: '', ticket_type: 'incident', priority: 'medium', description: '' })
const API = '/api/v1/tickets'

async function load() {
  loading.value = true
  try {
    const { data } = await api.get(API, { params: { page: page.value, page_size: pageSize.value } })
    if (data.code === 0) { tickets.value = data.data.items || []; total.value = data.data.total || 0 }
  } finally { loading.value = false }
}

async function createTicket() {
  const { data } = await api.post(API, form)
  if (data.code === 0) { ElMessage.success('创建成功'); showCreate.value = false; load() }
}

async function viewTicket(row: any) {
  current.value = row
  showDetail.value = true
  const { data } = await api.get(`${API}/${row.id}/comments`)
  if (data.code === 0) comments.value = data.data || []
}

async function addComment(id: string) {
  if (!commentText.value.trim()) return
  const { data } = await api.post(`${API}/${id}/comments`, { content: commentText.value })
  if (data.code === 0) { commentText.value = ''; viewTicket(current.value) }
}

async function closeTicket(id: string) {
  const { data } = await api.put(`${API}/${id}`, { status: 'closed' })
  if (data.code === 0) { ElMessage.success('工单已关闭'); load() }
}

onMounted(() => load())
</script>
