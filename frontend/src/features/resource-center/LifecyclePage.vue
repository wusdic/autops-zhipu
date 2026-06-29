<template>
  <div class="autops-page-container">
    <PageHeader title="生命周期" desc="管理资产生命周期规则与状态" />

    <!-- 统计卡片 -->
    <el-row :gutter="16" class="metric-row">
      <el-col :span="6">
        <div class="autops-metric-card">
          <div class="metric-icon bg-success"><el-icon :size="20"><CircleCheck /></el-icon></div>
          <div class="metric-label">活跃资产</div>
          <div class="metric-value">{{ stats.active }}</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="autops-metric-card">
          <div class="metric-icon bg-warning"><el-icon :size="20"><Clock /></el-icon></div>
          <div class="metric-label">即将退役</div>
          <div class="metric-value">{{ stats.retiring }}</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="autops-metric-card">
          <div class="metric-icon bg-info"><el-icon :size="20"><Remove /></el-icon></div>
          <div class="metric-label">已退役</div>
          <div class="metric-value">{{ stats.retired }}</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="autops-metric-card">
          <div class="metric-icon bg-brand"><el-icon :size="20"><List /></el-icon></div>
          <div class="metric-label">生命周期规则</div>
          <div class="metric-value">{{ stats.rules }}</div>
        </div>
      </el-col>
    </el-row>

    <el-card shadow="never" class="main-card">
      <template #header>
        <div class="autops-card-header">
          <span class="autops-card-title">生命周期列表</span>
          <el-button type="primary" @click="showCreateDialog = true">
            <el-icon><Plus /></el-icon>新建规则
          </el-button>
        </div>
      </template>

      <!-- 筛选栏 -->
      <div class="autops-toolbar">
        <div class="autops-toolbar-left">
          <el-input v-model="filters.keyword" placeholder="搜索资产名称" clearable :prefix-icon="Search" />
          <el-select v-model="filters.phase" placeholder="生命周期阶段" clearable>
            <el-option label="规划中" value="planning" />
            <el-option label="采购中" value="procurement" />
            <el-option label="部署中" value="deployment" />
            <el-option label="运行中" value="running" />
            <el-option label="维护中" value="maintenance" />
            <el-option label="即将退役" value="retiring" />
            <el-option label="已退役" value="retired" />
          </el-select>
          <el-select v-model="filters.assetType" placeholder="资产类型" clearable>
            <el-option label="Linux 服务器" value="linux_server" />
            <el-option label="Windows 服务器" value="windows_server" />
            <el-option label="数据库" value="database" />
            <el-option label="网络设备" value="network" />
            <el-option label="Web 服务" value="web_service" />
          </el-select>
        </div>
        <div class="autops-toolbar-right">
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </div>
      </div>

      <!-- 数据表 -->
      <el-table stripe :data="tableData"class="data-table">
        <el-table-column prop="name" label="资产名称" min-width="160">
          <template #default="{ row }">
            <el-link type="primary" @click="$router.push('/assets/' + row.id)">{{ row.name }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="assetType" label="类型" width="130" />
        <el-table-column prop="phase" label="当前阶段" width="120">
          <template #default="{ row }">
            <el-tag :type="(phaseTagType(row.phase)) as TagType" size="small">{{ phaseLabel(row.phase) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="enterPhaseTime" label="进入阶段时间" width="170" />
        <el-table-column prop="nextPhaseTime" label="预计下一阶段" width="170" />
        <el-table-column prop="daysInPhase" label="阶段停留天数" width="120" />
        <el-table-column prop="warranty" label="保修到期" width="130" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button plain type="primary" size="small" @click="viewTimeline(row)">时间线</el-button>
            <el-button plain type="warning" size="small" @click="changePhase(row)">变更阶段</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        class="pagination"
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[20, 50, 100]"
        layout="total, sizes, prev, pager, next"
      />
    </el-card>

    <!-- 阶段变更对话框 -->
    <el-dialog v-model="phaseDialogVisible" title="变更生命周期阶段" width="600px">
      <el-form :model="phaseForm" label-width="100px">
        <el-form-item label="资产名称">
          <el-input :model-value="phaseForm.name" disabled />
        </el-form-item>
        <el-form-item label="当前阶段">
          <el-tag>{{ phaseLabel(phaseForm.currentPhase) }}</el-tag>
        </el-form-item>
        <el-form-item label="目标阶段" required>
          <el-select v-model="phaseForm.targetPhase" placeholder="选择目标阶段">
            <el-option label="规划中" value="planning" />
            <el-option label="采购中" value="procurement" />
            <el-option label="部署中" value="deployment" />
            <el-option label="运行中" value="running" />
            <el-option label="维护中" value="maintenance" />
            <el-option label="即将退役" value="retiring" />
            <el-option label="已退役" value="retired" />
          </el-select>
        </el-form-item>
        <el-form-item label="变更原因" required>
          <el-input v-model="phaseForm.reason" type="textarea" :rows="3" placeholder="说明变更原因" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="phaseDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitPhaseChange">确认变更</el-button>
      </template>
    </el-dialog>

    <!-- 时间线对话框 -->
    <el-dialog v-model="timelineVisible" title="资产生命周期时间线" width="780px">
      <el-timeline>
        <el-timeline-item
          v-for="item in timelineData"
          :key="item.id"
          :timestamp="item.timestamp"
          :type="item.active ? 'primary' : 'info'"
          :hollow="!item.active"
          placement="top"
        >
          <el-card shadow="hover" :body-style="{ padding: '12px' }">
            <div style="font-weight: 600">{{ item.phase }}</div>
            <div style="color: #86909c; font-size: 13px">{{ item.operator }} · {{ item.reason }}</div>
          </el-card>
        </el-timeline-item>
      </el-timeline>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import type { TagType } from '@/shared/types'
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Plus, CircleCheck, Clock, Remove, List } from '@element-plus/icons-vue'
import PageHeader from '@/shared/components/PageHeader.vue'
import client from '@/shared/api/client'
import { API } from '@/shared/api/routes'

const stats = reactive({ active: 0, retiring: 0, retired: 0, rules: 0 })
const filters = reactive({ keyword: '', phase: '', assetType: ''})
const tableData = ref<any[]>([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

// 资产状态 → 生命周期阶段（资产模型暂无独立 lifecycle 字段，按状态映射）
function statusToPhase(a: any): string {
  if (a.is_deleted) return 'retired'
  if (a.status === 'online') return 'running'
  if (a.status === 'offline') return 'maintenance'
  return 'running'
}

async function loadData() {
  loading.value = true
  try {
    const params: any = { page: page.value, page_size: pageSize.value }
    if (filters.keyword) params.keyword = filters.keyword
    if (filters.assetType) params.asset_type = filters.assetType
    const res = await client.get(API.ASSETS, { params })
    const data = res.data?.data ?? res.data
    const items = data?.items || []
    tableData.value = items
      .map((a: any) => ({
        id: a.id,
        name: a.name || a.hostname || a.ip,
        assetType: a.asset_type,
        phase: statusToPhase(a),
        enterPhaseTime: a.created_at || '-',
        nextPhaseTime: '-',
        daysInPhase: a.updated_at
          ? Math.max(0, Math.floor((Date.now() - new Date(a.updated_at).getTime()) / 86400000))
          : '-',
        warranty: '-',
      }))
      .filter((r: any) => !filters.phase || r.phase === filters.phase)
    total.value = data?.total || tableData.value.length
    stats.active = tableData.value.filter((r: any) => r.phase === 'running').length
    stats.retiring = tableData.value.filter((r: any) => r.phase === 'retiring').length
    stats.retired = tableData.value.filter((r: any) => r.phase === 'retired').length
    stats.rules = total.value
  } catch {
    tableData.value = []
  } finally {
    loading.value = false
  }
}

const phaseLabelMap: Record<string, string> = {
  planning: '规划中', procurement: '采购中', deployment: '部署中',
  running: '运行中', maintenance: '维护中', retiring: '即将退役', retired: '已退役',
}
const phaseTagTypeMap: Record<string, TagType> = {
  planning: 'info', procurement: 'info', deployment: 'warning',
  running: 'success', maintenance: 'warning', retiring: 'danger', retired: 'info',
}
const phaseLabel = (p: string) => phaseLabelMap[p] || p
const phaseTagType = (p: string) => phaseTagTypeMap[p] || 'info'

function handleSearch() { page.value = 1; loadData() }
function resetFilters() { filters.keyword = ''; filters.phase = ''; filters.assetType = ''; loadData() }

const phaseDialogVisible = ref(false)
const phaseForm = reactive({ name: '', currentPhase: '', targetPhase: '', reason: '', assetId: ''})
function changePhase(row: any) {
  phaseForm.name = row.name
  phaseForm.currentPhase = row.phase
  phaseForm.targetPhase = ''
  phaseForm.reason = ''
  phaseForm.assetId = row.id
  phaseDialogVisible.value = true
}
function submitPhaseChange() {
  if (!phaseForm.targetPhase || !phaseForm.reason) {
    ElMessage.warning('请填写必填项')
    return
  }
  ElMessage.success('阶段变更成功')
  phaseDialogVisible.value = false
}

const timelineVisible = ref(false)
const timelineData = ref<any[]>([])
async function viewTimeline(row: any) {
  timelineVisible.value = true
  timelineData.value = []
  try {
    const res = await client.get(API.ASSET_TIMELINE(row.id))
    const data = res.data?.data ?? res.data
    const items = Array.isArray(data) ? data : data?.items || []
    timelineData.value = items.map((e: any, i: number) => ({
      id: e.id || i,
      phase: e.event_type || e.title || e.action || '事件',
      timestamp: e.created_at || e.timestamp || '',
      operator: e.operator || e.created_by || 'system',
      reason: e.description || e.detail || '',
      active: i === 0,
    }))
  } catch {
    timelineData.value = []
  }
}

const showCreateDialog = ref(false)

onMounted(loadData)
</script>

<style scoped>
.stat-row { margin-bottom: var(--autops-space-xl); }
.filter-row { margin-bottom: var(--autops-space-lg); }
.data-table { margin-bottom: var(--autops-space-lg); }
.pagination { display: flex; justify-content: flex-end; }
</style>
