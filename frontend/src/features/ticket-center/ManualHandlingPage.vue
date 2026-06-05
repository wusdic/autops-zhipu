<template>
  <div class="autops-page-container">
    <div class="autops-page-header autops-page-header--between">
      <div>
        <div class="autops-page-title-row">
          <el-button plain @click="router.back()"><el-icon><ArrowLeft /></el-icon> 返回</el-button>
          <span class="autops-page-title">人工处置台</span>
        </div>
        <div class="autops-page-desc">处理人工干预的工单，跟踪处置进度和 SLA</div>
      </div>
      <div class="autops-header-actions">
        <el-button type="primary" @click="openCreateDialog">
          <el-icon><Plus /></el-icon> 新建处置工单
        </el-button>
        <el-button @click="loadData" :loading="loading">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="16" class="metric-row">
      <el-col :span="6">
        <div class="autops-metric-card">
          <div class="metric-icon bg-warning"><el-icon :size="20"><Clock /></el-icon></div>
          <div class="metric-label">待处置</div>
          <div class="metric-value">{{ stats.pending }}</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="autops-metric-card">
          <div class="metric-icon bg-brand"><el-icon :size="20"><Loading /></el-icon></div>
          <div class="metric-label">进行中</div>
          <div class="metric-value">{{ stats.in_progress }}</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="autops-metric-card">
          <div class="metric-icon bg-success"><el-icon :size="20"><CircleCheck /></el-icon></div>
          <div class="metric-label">今日完成</div>
          <div class="metric-value">{{ stats.completed_today }}</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="autops-metric-card">
          <div class="metric-icon bg-info"><el-icon :size="20"><Timer /></el-icon></div>
          <div class="metric-label">平均处置时长</div>
          <div class="metric-value">{{ stats.avg_duration }}<span class="metric-suffix">分钟</span></div>
        </div>
      </el-col>
    </el-row>

    <!-- 筛选 -->
    <el-card class="mb-lg" shadow="never">
      <el-form :inline="true" :model="filters">
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部" clearable @change="loadData">
            <el-option label="待处置" value="pending" />
            <el-option label="进行中" value="in_progress" />
            <el-option label="已完成" value="completed" />
            <el-option label="已关闭" value="closed" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="filters.priority" placeholder="全部" clearable @change="loadData">
            <el-option label="紧急" value="urgent" />
            <el-option label="高" value="high" />
            <el-option label="中" value="medium" />
            <el-option label="低" value="low" />
          </el-select>
        </el-form-item>
        <el-form-item label="处置人">
          <el-input v-model="filters.handler" placeholder="处置人" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">搜索</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 工单列表 -->
    <el-card class="mt-lg" shadow="never">
      <el-table stripe :data="items" v-loading="loading"border>
        <el-table-column prop="id" label="工单号" width="120">
          <template #default="{ row }">
            <span style="font-family:monospace;font-size:12px">{{ row.id && String(row.id).length > 12 ? String(row.id).slice(0, 8) + '...' : (row.id || '-') }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="处置标题" min-width="250" />
        <el-table-column prop="priority" label="优先级" width="90">
          <template #default="{ row }">
            <el-tag :type="priorityType(row.priority)" size="small">{{ priorityLabel(row.priority) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="handler" label="处置人" width="100" />
        <el-table-column prop="asset_name" label="关联资产" width="140" />
        <el-table-column prop="source" label="来源" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ row.source }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="sla_remaining" label="SLA剩余" width="120">
          <template #default="{ row }">
            <span :class="{ 'sla-warning': row.sla_remaining && row.sla_remaining < 30 }">
              {{ row.sla_remaining ? row.sla_remaining + '分钟' : '-' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button plain type="primary" @click="viewDetail(row)">详情</el-button>
            <el-button plain type="primary" @click="startHandle(row)" v-if="row.status === 'pending'">接单</el-button>
            <el-button plain type="success" @click="completeHandle(row)" v-if="row.status === 'in_progress'">完成</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination class="mt-lg" v-model:current-page="pagination.page" v-model:page-size="pagination.size"
        :total="pagination.total" :page-sizes="[20, 50, 100]" layout="total, sizes, prev, pager, next"
        @size-change="loadData" @current-change="loadData" />
    </el-card>

    <!-- 详情 -->
    <el-dialog v-model="detailVisible" title="处置详情" width="780px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="工单号">{{ detailData.id }}</el-descriptions-item>
        <el-descriptions-item label="优先级">{{ detailData.priority }}</el-descriptions-item>
        <el-descriptions-item label="处置人">{{ detailData.handler || '未分配' }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ detailData.status }}</el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">{{ detailData.description }}</el-descriptions-item>
      </el-descriptions>
      <el-divider>处置记录</el-divider>
      <el-timeline>
        <el-timeline-item v-for="log in detailData.logs" :key="log.time" :timestamp="log.time" placement="top">
          {{ log.content }}
        </el-timeline-item>
      </el-timeline>
      <el-empty v-if="!detailData.logs?.length" description="暂无处置记录" />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus, Refresh, ArrowLeft, Clock, Loading, CircleCheck, Timer } from '@element-plus/icons-vue'
import client from '@/shared/api/client'

const router = useRouter()
const loading = ref(false)
const detailVisible = ref(false)
const items = ref<any[]>([])
const detailData = ref<any>({})

const stats = reactive({ pending: 0, in_progress: 0, completed_today: 0, avg_duration: 0 })
const filters = reactive({ status: '', priority: '', handler: '' })
const pagination = reactive({ page: 1, size: 20, total: 0 })

function priorityType(p: string) { return { urgent: 'danger', high: 'warning', medium: '', low: 'info' }[p] || 'info' }
function priorityLabel(p: string) { return { urgent: '紧急', high: '高', medium: '中', low: '低' }[p] || p }
function statusType(s: string) { return { pending: 'warning', in_progress: 'primary', completed: 'success', closed: 'info' }[s] || 'info' }
function statusLabel(s: string) { return { pending: '待处置', in_progress: '进行中', completed: '已完成', closed: '已关闭' }[s] || s }

async function loadData() {
  loading.value = true
  try {
    const params: Record<string, unknown> = { page: pagination.page, page_size: pagination.size }
    if (filters.status) params.status = filters.status
    if (filters.priority) params.priority = filters.priority
    const res = await client.get('/api/v1/tickets', { params })
    const data = res.data?.data ?? res.data
    items.value = data?.items || []
    pagination.total = data?.total || 0
  } catch { items.value = [] } finally { loading.value = false }
}

function openCreateDialog() { router.push('/tickets/new') }
function viewDetail(row: any) { detailData.value = row; detailVisible.value = true }

async function startHandle(row: any) {
  try {
    await client.put('/api/v1/tickets/' + row.id, { status: 'in_progress', handler: 'current_user' })
    ElMessage.success('已接单'); loadData()
  } catch { ElMessage.error('操作失败') }
}

async function completeHandle(row: any) {
  try {
    await client.put('/api/v1/tickets/' + row.id, { status: 'completed' })
    ElMessage.success('已完成'); loadData()
  } catch { ElMessage.error('操作失败') }
}

onMounted(loadData)
</script>

<style scoped>
.manual-handling-page { padding: var(--autops-space-xl); }
.mt-4 { margin-top: var(--autops-space-lg); }
.sla-warning { color: var(--autops-danger); font-weight: bold; }
</style>
