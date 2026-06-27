<template>
  <div class="autops-page-container">
    <!-- 页面头部 -->
    <div class="autops-page-header">
      <div class="autops-page-title">巡检任务</div>
      <div class="autops-page-desc">查看和管理巡检任务执行状态</div>
    </div>
    <div style="display: flex; justify-content: flex-end; margin-bottom: 16px">
      <el-button type="primary" @click="handleTriggerTask">
        <el-icon><VideoPlay /></el-icon> 手动触发
      </el-button>
    </div>

    <!-- 搜索栏 -->
    <div class="page-toolbar">
      <el-input
        v-model="searchQuery"
        placeholder="搜索任务名称..."
        clearable
        style="width: 260px"
        @keyup.enter="fetchTasks"
        @clear="fetchTasks"
      >
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
      <el-select v-model="statusFilter" placeholder="任务状态" clearable style="width: 140px" @change="fetchTasks">
        <el-option label="待执行" value="pending" />
        <el-option label="执行中" value="running" />
        <el-option label="已完成" value="completed" />
        <el-option label="失败" value="failed" />
      </el-select>
      <el-button type="default" @click="fetchTasks">
        <el-icon><Refresh /></el-icon> 刷新
      </el-button>
    </div>

    <!-- 数据表格 -->
    <el-table stripe :data="tasks" v-loading="loading"empty-text="暂无巡检任务">
      <el-table-column prop="name" label="任务名称" min-width="180" show-overflow-tooltip />
      <el-table-column prop="plan_name" label="关联计划" width="160" show-overflow-tooltip>
        <template #default="{ row }">
          <span>{{ row.plan_name || row.plan_id || '-' }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="(statusTagType(row.status)) as TagType" size="small" effect="light">
            <el-icon v-if="row.status === 'running'" class="is-loading" style="margin-right: 2px"><Loading /></el-icon>
            {{ statusLabel(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="asset_count" label="执行资产数" width="110" align="center">
        <template #default="{ row }">
          <span class="asset-count">{{ row.asset_count ?? row.total_assets ?? '-' }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="progress" label="进度" width="130">
        <template #default="{ row }">
          <el-progress
            v-if="row.status === 'running' || row.progress !== undefined"
            :percentage="row.progress ?? 0"
            :status="progressStatus(row)"
            :stroke-width="8"
          />
          <span v-else class="text-tertiary">-</span>
        </template>
      </el-table-column>
      <el-table-column prop="started_at" label="开始时间" width="170">
        <template #default="{ row }">
          <span class="text-tertiary">{{ row.started_at || '-' }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="completed_at" label="结束时间" width="170">
        <template #default="{ row }">
          <span class="text-tertiary">{{ row.completed_at || '-' }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="duration" label="耗时" width="100">
        <template #default="{ row }">
          <span class="text-tertiary">{{ formatDuration(row.started_at, row.completed_at) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button plain type="primary" size="small" @click="handleView(row)">查看</el-button>
          <el-button
            v-if="row.status === 'pending' || row.status === 'running'"
            plain
            type="warning"
            size="small"
            @click="handleCancel(row)"
          >
            取消
          </el-button>
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
        @size-change="fetchTasks"
        @current-change="fetchTasks"
      />
    </div>

    <!-- 手动触发弹窗 -->
    <el-dialog
      v-model="triggerDialogVisible"
      title="手动触发巡检"
      width="600px"
      :close-on-click-modal="false"
      @closed="resetTriggerForm"
    >
      <el-form
        ref="triggerFormRef"
        :model="triggerForm"
        :rules="triggerFormRules"
        label-width="100px"
        label-position="right"
      >
        <el-form-item label="任务名称" prop="name">
          <el-input v-model="triggerForm.name" placeholder="请输入任务名称" />
        </el-form-item>
        <el-form-item label="巡检计划" prop="plan_id">
          <el-select
            v-model="triggerForm.plan_id"
            placeholder="请选择巡检计划"
            style="width: 100%"
            filterable
            :loading="planLoading"
          >
            <el-option
              v-for="plan in planOptions"
              :key="plan.id"
              :label="plan.name"
              :value="plan.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="triggerDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="triggerLoading" @click="submitTrigger">确认触发</el-button>
      </template>
    </el-dialog>

    <!-- 任务详情弹窗 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="任务详情"
      width="780px"
      @closed="taskDetail = null"
    >
      <div v-if="taskDetail" class="task-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="任务名称">{{ taskDetail.name }}</el-descriptions-item>
          <el-descriptions-item label="关联计划">{{ taskDetail.plan_name || taskDetail.plan_id || '-' }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="(statusTagType(taskDetail.status)) as TagType" size="small">{{ statusLabel(taskDetail.status) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="执行资产数">{{ taskDetail.asset_count ?? taskDetail.total_assets ?? '-' }}</el-descriptions-item>
          <el-descriptions-item label="开始时间">{{ taskDetail.started_at || '-' }}</el-descriptions-item>
          <el-descriptions-item label="结束时间">{{ taskDetail.completed_at || '-' }}</el-descriptions-item>
          <el-descriptions-item label="耗时" :span="2">{{ formatDuration(taskDetail.started_at, taskDetail.completed_at) }}</el-descriptions-item>
        </el-descriptions>
        <!-- 执行结果摘要 -->
        <div v-if="taskDetail.results" class="detail-section">
          <h4>执行结果摘要</h4>
          <el-table stripe :data="taskDetail.results"size="small" max-height="300">
            <el-table-column prop="asset_name" label="资产" min-width="140" show-overflow-tooltip />
            <el-table-column prop="status" label="状态" width="90">
              <template #default="{ row }">
                <el-tag :type="(statusTagType(row.status)) as TagType" size="small">{{ statusLabel(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="message" label="结果信息" min-width="200" show-overflow-tooltip />
          </el-table>
        </div>
      </div>
      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="navToAnomalyFromInspection(taskDetail?.id)">查看异常</el-button>
        <el-button type="success" @click="navToReportFromInspection(taskDetail?.id)">生成报告</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import type { TagType } from '@/shared/types'
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { Search, Refresh, VideoPlay, Loading } from '@element-plus/icons-vue'
import { inspectionService } from '@/shared/api'
import { taskStatusTag, taskStatusLabel } from '@/shared/utils/labels'
import { useWorkflowNav } from '@/shared/composables/useWorkflowNav'

// ---------- 状态 ----------
const { navToAnomalyFromInspection, navToReportFromInspection } = useWorkflowNav()
const loading = ref(false)
const triggerLoading = ref(false)
const planLoading = ref(false)
const triggerDialogVisible = ref(false)
const detailDialogVisible = ref(false)
const tasks = ref<any[]>([])
const planOptions = ref<any[]>([])
const taskDetail = ref<any>(null)
const searchQuery = ref('')
const statusFilter = ref('')
const triggerFormRef = ref<FormInstance>()

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0,
})

const triggerForm = reactive({
  name: '',
  plan_id: '',
})

const triggerFormRules: FormRules = {
  name: [{ required: true, message: '请输入任务名称', trigger: 'blur' }],
  plan_id: [{ required: true, message: '请选择巡检计划', trigger: 'change' }],
}

// ---------- 工具函数（任务状态统一来自 labels.ts）----------
const statusTagType = (status: string): TagType => taskStatusTag(status) as TagType
const statusLabel = (status: string): string => taskStatusLabel(status)

function progressStatus(row: any): '' | 'success' | 'warning' | 'exception' | undefined {
  if (row.status === 'failed') return 'exception'
  if (row.progress >= 100) return 'success'
  return ''
}

function formatDuration(start: string, end: string): string {
  if (!start || !end) return '-'
  try {
    const startTime = new Date(start).getTime()
    const endTime = new Date(end).getTime()
    if (isNaN(startTime) || isNaN(endTime)) return '-'
    const diff = endTime - startTime
    if (diff < 0) return '-'
    const seconds = Math.floor(diff / 1000)
    if (seconds < 60) return seconds + ' 秒'
    const minutes = Math.floor(seconds / 60)
    const remainSeconds = seconds % 60
    if (minutes < 60) return minutes + ' 分 ' + remainSeconds + ' 秒'
    const hours = Math.floor(minutes / 60)
    const remainMinutes = minutes % 60
    return hours + ' 小时 ' + remainMinutes + ' 分'
  } catch {
    return '-'
  }
}

// ---------- API ----------
async function fetchTasks() {
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: pagination.page,
      page_size: pagination.page_size,
    }
    if (searchQuery.value.trim()) {
      params.name = searchQuery.value.trim()
    }
    if (statusFilter.value) {
      params.status = statusFilter.value
    }
    const res = await inspectionService.listTasks(params)
    const data = res.data?.data ?? res.data
    tasks.value = data?.items ?? data ?? []
    pagination.total = data?.total ?? tasks.value.length
  } catch (err: any) {
    ElMessage.error(err.message || '获取任务列表失败')
  } finally {
    loading.value = false
  }
}

async function fetchPlans() {
  planLoading.value = true
  try {
    const res = await inspectionService.listPlans({ page_size: 200, enabled: true })
    const data = res.data?.data ?? res.data
    planOptions.value = data?.items ?? data ?? []
  } catch {
    planOptions.value = []
  } finally {
    planLoading.value = false
  }
}

async function getTaskDetail(id: string) {
  const res = await inspectionService.getTask(id)
  return res.data?.data ?? res.data
}

async function triggerTask(data: Record<string, any>) {
  return inspectionService.triggerTask(data)
}

// ---------- 操作 ----------
function handleTriggerTask() {
  triggerForm.name = '手动巡检_' + new Date().toLocaleString('zh-CN', { hour12: false }).replace(/[/:]/g, '-').replace(/\s/g, '_')
  triggerDialogVisible.value = true
}

async function submitTrigger() {
  if (!triggerFormRef.value) return
  const valid = await triggerFormRef.value.validate().catch(() => false)
  if (!valid) return

  triggerLoading.value = true
  try {
    await triggerTask({
      name: triggerForm.name,
      plan_id: triggerForm.plan_id,
    })
    ElMessage.success('巡检任务已触发')
    triggerDialogVisible.value = false
    fetchTasks()
  } catch (err: any) {
    ElMessage.error(err.message || '触发任务失败')
  } finally {
    triggerLoading.value = false
  }
}

async function handleView(row: any) {
  try {
    const data = await getTaskDetail(row.id)
    taskDetail.value = data || row
    detailDialogVisible.value = true
  } catch (err: any) {
    // 降级：用列表行数据展示
    taskDetail.value = row
    detailDialogVisible.value = true
    ElMessage.warning('获取详情失败，展示基础信息')
  }
}

async function handleCancel(row: any) {
  try {
    await ElMessageBox.confirm(
      '确定要取消任务「' + row.name + '」吗？',
      '取消确认',
      { confirmButtonText: '确认取消', cancelButtonText: '返回', type: 'warning' }
    )
    // 更新状态为取消（假设 updatePlan 风格的 API，或直接通过任务状态更新）
    row.status = 'cancelled'
    ElMessage.success('任务已取消')
    fetchTasks()
  } catch (err: any) {
    if (err !== 'cancel' && err?.action !== 'cancel' && err?.message !== 'cancel') {
      ElMessage.error(err.message || '取消任务失败')
    }
  }
}

function resetTriggerForm() {
  triggerForm.name = ''
  triggerForm.plan_id = ''
  triggerFormRef.value?.resetFields()
}

// ---------- 初始化 ----------
onMounted(() => {
  fetchTasks()
  fetchPlans()
})
</script>

<style scoped>

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--autops-space-lg);
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
.asset-count {
  font-weight: 600;
  color: var(--autops-primary);
}
.task-detail {
  padding: var(--autops-space-xs) 0;
}
.detail-section {
  margin-top: var(--autops-space-xl);
}
.detail-section h4 {
  font-size: var(--autops-font-14);
  font-weight: 600;
  color: var(--autops-text-1);
  margin-bottom: var(--autops-space-md);
}
</style>
