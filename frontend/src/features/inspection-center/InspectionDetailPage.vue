<template>
  <div class="page-container">
    <div class="autops-page-header">
      <div class="autops-page-title">巡检详情</div>
      <div>
        <el-button @click="goBack"><el-icon><ArrowLeft /></el-icon> 返回</el-button>
        <el-button type="primary" @click="rerunInspection" :loading="rerunning"><el-icon><Refresh /></el-icon> 重新巡检</el-button>
      </div>
    </div>

    <div v-loading="loading">
      <!-- 基本信息 -->
      <div class="autops-card" style="margin-bottom: 16px">
        <el-descriptions :column="3" border>
          <el-descriptions-item label="巡检任务ID">{{ taskDetail?.id?.slice(0, 8) || '-' }}</el-descriptions-item>
          <el-descriptions-item label="巡检模板">{{ taskDetail?.template_name || taskDetail?.inspection_type || '-' }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="statusTag(taskDetail?.status)" effect="dark">{{ statusLabel(taskDetail?.status) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="资产数量">{{ taskDetail?.asset_count || taskDetail?.target_assets?.length || 0 }}</el-descriptions-item>
          <el-descriptions-item label="开始时间">{{ formatTime(taskDetail?.started_at) }}</el-descriptions-item>
          <el-descriptions-item label="完成时间">{{ formatTime(taskDetail?.completed_at) }}</el-descriptions-item>
          <el-descriptions-item label="巡检类型">{{ typeLabel(taskDetail?.inspection_type) }}</el-descriptions-item>
          <el-descriptions-item label="创建人">{{ taskDetail?.created_by || 'system' }}</el-descriptions-item>
          <el-descriptions-item label="耗时">{{ taskDetail?.duration || '-' }}</el-descriptions-item>
        </el-descriptions>
      </div>

      <!-- 结果概要 -->
      <el-row :gutter="16" style="margin-bottom: 16px">
        <el-col :xs="12" :sm="6" v-for="stat in resultStats" :key="stat.label">
          <div class="autops-metric-card">
            <div class="metric-label">{{ stat.label }}</div>
            <div class="metric-value" :style="{ color: stat.color }">{{ stat.value }}</div>
          </div>
        </el-col>
      </el-row>

      <!-- 巡检项明细 -->
      <div class="autops-card" style="margin-bottom: 16px">
        <div class="autops-card-header">
          <div class="autops-card-title">巡检项明细</div>
          <div>
            <el-select v-model="resultFilter" placeholder="结果筛选" style="width: 120px" clearable>
              <el-option label="通过" value="pass" />
              <el-option label="失败" value="fail" />
              <el-option label="警告" value="warning" />
              <el-option label="跳过" value="skip" />
            </el-select>
          </div>
        </div>
        <el-table stripe :data="filteredResults"class="autops-table" @expand-change="handleExpand">
          <el-table-column type="expand">
            <template #default="{ row }">
              <div style="padding: 12px 24px">
                <h4>详细结果</h4>
                <el-descriptions :column="2" border size="small">
                  <el-descriptions-item label="检查项">{{ row.check_item }}</el-descriptions-item>
                  <el-descriptions-item label="实际值">{{ row.actual_value || '-' }}</el-descriptions-item>
                  <el-descriptions-item label="期望值">{{ row.expected_value || '-' }}</el-descriptions-item>
                  <el-descriptions-item label="差异说明">{{ row.diff_description || '-' }}</el-descriptions-item>
                </el-descriptions>
                <div v-if="row.recommendation" style="margin-top: 8px">
                  <el-alert type="info" :closable="false"><strong>建议:</strong> {{ row.recommendation }}</el-alert>
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="asset_name" label="资产" min-width="140" show-overflow-tooltip />
          <el-table-column prop="check_item" label="检查项" min-width="160" show-overflow-tooltip />
          <el-table-column prop="module" label="模块" width="100">
            <template #default="{ row }">
              <el-tag size="small">{{ row.module || '-' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="result" label="结果" width="80">
            <template #default="{ row }">
              <el-tag :type="resultTag(row.result)" size="small">{{ resultLabel(row.result) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="severity" label="严重度" width="80">
            <template #default="{ row }">
              <el-tag v-if="row.result === 'fail'" :type="severityTag(row.severity)" size="small">{{ row.severity || '-' }}</el-tag>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="message" label="信息" min-width="200" show-overflow-tooltip />
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="{ row }">
              <el-button v-if="row.result === 'fail'" plain type="warning" @click="navToAnomalyFromInspection(taskDetail?.id)">报异常</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 工作流操作 -->
      <div class="autops-card">
        <div class="autops-card-header"><div class="autops-card-title">后续操作</div></div>
        <div style="display: flex; gap: 8px; padding: 12px">
          <el-button type="warning" @click="navToAnomalyFromInspection(taskDetail?.id)">
            <el-icon><Warning /></el-icon> 查看异常项
          </el-button>
          <el-button type="primary" @click="navToReportFromInspection(taskDetail?.id)">
            <el-icon><Document /></el-icon> 生成报告
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Refresh, Warning, Document } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import api from '@/shared/api'
import { routes as API } from '@/shared/api/routes'
import { useWorkflowNav } from '@/shared/composables/useWorkflowNav'

const route = useRoute()
const router = useRouter()
const { navToAnomalyFromInspection, navToReportFromInspection } = useWorkflowNav()

const loading = ref(false)
const rerunning = ref(false)
const taskDetail = ref<any>(null)
const checkResults = ref<any[]>([])
const resultFilter = ref('')

const taskId = computed(() => route.params.id as string || route.query.task_id as string)

const resultStats = computed(() => {
  const all = checkResults.value
  return [
    { label: '检查项总数', value: all.length, color: '#165dff' },
    { label: '通过', value: all.filter(r => r.result === 'pass').length, color: '#00b42a' },
    { label: '失败', value: all.filter(r => r.result === 'fail').length, color: '#f53f3f' },
    { label: '警告', value: all.filter(r => r.result === 'warning').length, color: '#ff7d00' },
  ]
})

const filteredResults = computed(() => {
  if (!resultFilter.value) return checkResults.value
  return checkResults.value.filter(r => r.result === resultFilter.value)
})

async function fetchDetail() {
  if (!taskId.value) return
  loading.value = true
  try {
    const res = await api.get(`${API.INSPECTION_TASKS}/${taskId.value}`)
    const data = res.data
    if (data?.code === 0) {
      taskDetail.value = data.data
      // Build check results from task detail
      const items = data.data?.items || data.data?.check_results || []
      checkResults.value = items.map((r: any) => ({
        ...r,
        asset_name: r.asset_name || r.asset?.name || '-',
        check_item: r.check_item || r.name || r.item_name || '-',
        result: r.result || r.status || 'pass',
        message: r.message || r.description || '',
        module: r.module || r.category || '-',
      }))
    }
  } catch (e) {
    ElMessage.error('获取巡检详情失败')
  } finally {
    loading.value = false
  }
}

async function rerunInspection() {
  rerunning.value = true
  try {
    await api.post(API.INSPECTION_TASKS, { template_id: taskDetail.value?.template_id, asset_ids: taskDetail.value?.target_assets })
    ElMessage.success('已触发重新巡检')
  } catch (e) {
    ElMessage.error('触发失败')
  } finally {
    rerunning.value = false
  }
}

function handleExpand(row: any) { /* expanded */ }

function goBack() { router.back() }

function statusTag(s: string) {
  const map: Record<string, string> = { running: 'warning', completed: 'success', failed: 'danger', pending: 'info' }
  return map[s] || 'info'
}
function statusLabel(s: string) {
  const map: Record<string, string> = { running: '执行中', completed: '已完成', failed: '失败', pending: '待执行' }
  return map[s] || s || '-'
}
function resultTag(r: string) {
  const map: Record<string, string> = { pass: 'success', fail: 'danger', warning: 'warning', skip: 'info' }
  return map[r] || 'info'
}
function resultLabel(r: string) {
  const map: Record<string, string> = { pass: '通过', fail: '失败', warning: '警告', skip: '跳过' }
  return map[r] || r || '-'
}
function severityTag(s: string) {
  const map: Record<string, string> = { critical: 'danger', high: 'danger', medium: 'warning', low: 'info' }
  return map[s] || 'info'
}
function typeLabel(t: string) {
  const map: Record<string, string> = { page: '页面巡检', log: '日志巡检', config: '配置巡检', performance: '性能巡检', security: '安全巡检', baseline: '基线巡检' }
  return map[t] || t || '-'
}
function formatTime(t: string) {
  return t ? new Date(t).toLocaleString('zh-CN') : '-'
}

onMounted(fetchDetail)
</script>

<style scoped>




</style>
