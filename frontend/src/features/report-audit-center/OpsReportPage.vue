<template>
  <div class="autops-page-container">
    <div class="autops-page-header autops-page-header--between">
      <div>
        <div class="autops-page-title">运维报告</div>
        <div class="autops-page-desc">生成和查看运维报告</div>
      </div>
      <div class="autops-header-actions">
        <el-date-picker v-model="dateRange" type="daterange" range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期" style="margin-right: 8px" @change="fetchData" />
        <el-select v-model="moduleFilter" placeholder="报告类型" style="width: 140px; margin-right: 8px" clearable @change="fetchData">
          <el-option label="日报" value="daily" />
          <el-option label="周报" value="weekly" />
          <el-option label="月报" value="monthly" />
        </el-select>
        <el-button type="primary" @click="generateReport" :loading="generating"><el-icon><Document /></el-icon> 生成报告</el-button>
      </div>
    </div>

    <!-- 运维概要 -->
    <el-row :gutter="16" class="mb-lg">
      <el-col :xs="12" :sm="6" v-for="stat in summaryStats" :key="stat.label">
        <div class="autops-metric-card">
          <div class="metric-icon" :class="stat.bgClass">
            <el-icon :size="20"><component :is="stat.icon" /></el-icon>
          </div>
          <div class="metric-label">{{ stat.label }}</div>
          <div class="metric-value">{{ stat.value }}</div>
        </div>
      </el-col>
    </el-row>

    <!-- 报告列表 -->
    <div class="autops-card">
      <el-table stripe :data="reports" v-loading="loading"class="autops-table">
        <el-table-column prop="title" label="报告名称" min-width="200" show-overflow-tooltip sortable />
        <el-table-column prop="report_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ typeLabel(row.report_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="period_start" label="起始日期" width="110">
          <template #default="{ row }">{{ (row.period_start || '').slice(0, 10) }}</template>
        </el-table-column>
        <el-table-column prop="period_end" label="结束日期" width="110">
          <template #default="{ row }">{{ (row.period_end || '').slice(0, 10) }}</template>
        </el-table-column>
        <el-table-column prop="asset_count" label="覆盖资产" width="90" />
        <el-table-column prop="anomaly_count" label="异常数" width="80">
          <template #default="{ row }">
            <span :class="{ 'text-danger': row.anomaly_count > 0 }">{{ row.anomaly_count }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="auto_remediation_rate" label="自动处置率" width="110">
          <template #default="{ row }">{{ row.auto_remediation_rate || 0 }}%</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 'completed' ? 'success' : row.status === 'generating' ? 'warning' : 'info'" size="small">
              {{ row.status === 'completed' ? '已完成' : row.status === 'generating' ? '生成中' : '待生成' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="生成时间" width="170" sortable />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button plain type="primary" @click="viewReport(row)" :disabled="row.status !== 'completed'">查看</el-button>
            <el-button plain type="success" @click="downloadReport(row)" :disabled="row.status !== 'completed'">下载</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="mt-lg" style="display: flex; justify-content: flex-end">
        <el-pagination v-model:current-page="page" v-model:page-size="pageSize" :total="total" :page-sizes="[20, 50, 100]" layout="total, sizes, prev, pager, next" @size-change="fetchData" @current-change="fetchData" />
      </div>
    </div>

    <!-- 生成对话框 -->
    <el-dialog v-model="genVisible" title="生成运维报告" width="600px" destroy-on-close>
      <el-form :model="genForm" label-width="90px">
        <el-form-item label="报告类型">
          <el-select v-model="genForm.report_type" style="width: 100%">
            <el-option label="日报" value="daily" />
            <el-option label="周报" value="weekly" />
            <el-option label="月报" value="monthly" />
          </el-select>
        </el-form-item>
        <el-form-item label="时间范围">
          <el-date-picker v-model="genForm.period" type="daterange" range-separator="至" start-placeholder="开始" end-placeholder="结束" style="width: 100%" />
        </el-form-item>
        <el-form-item label="资产范围">
          <el-select v-model="genForm.asset_scope" style="width: 100%">
            <el-option label="全部资产" value="all" />
            <el-option label="按业务系统" value="business_system" />
            <el-option label="按资产类型" value="asset_type" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="genVisible = false">取消</el-button>
        <el-button type="primary" @click="doGenerate" :loading="generating">确认生成</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted } from 'vue'
import { Document, DataAnalysis, CircleCheck, Warning, Clock } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import api from '@/shared/api/client'
import { API } from '@/shared/api/routes'

const router = useRouter()
const loading = ref(false)
const generating = ref(false)
const reports = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const dateRange = ref<[Date, Date] | null>(null)
const moduleFilter = ref('')
const genVisible = ref(false)
const genForm = reactive({ report_type: 'weekly', period: null as [Date, Date] | null, asset_scope: 'all' })

const summaryStats = computed(() => {
  const completed = reports.value.filter(r => r.status === 'completed')
  return [
    { label: '报告总数', value: reports.value.length, bgClass: 'bg-brand', icon: DataAnalysis },
    { label: '已完成', value: completed.length, bgClass: 'bg-success', icon: CircleCheck },
    { label: '本月异常', value: reports.value.reduce((s, r) => s + (r.anomaly_count || 0), 0), bgClass: 'bg-warning', icon: Warning },
    { label: '自动处置率', value: completed.length > 0 ? Math.round(completed.reduce((s, r) => s + (r.auto_remediation_rate || 0), 0) / completed.length) + '%' : '0%', bgClass: 'bg-purple', icon: Clock },
  ]
})

async function fetchData() {
  loading.value = true
  try {
    const params: any = { page: page.value, page_size: pageSize.value }
    if (moduleFilter.value) params.report_type = moduleFilter.value
    const res = await api.get(API.REPORTS, { params })
    if (res.data?.code === 0) {
      reports.value = (res.data.data?.items || []).map((r: any) => ({
        ...r,
        title: r.title || typeLabel(r.report_type || 'weekly') + ' - ' + (r.period_start || '').slice(0, 10),
        anomaly_count: r.anomaly_count || 0,
        auto_remediation_rate: r.auto_remediation_rate || 0,
      }))
      total.value = res.data.data?.total || 0
    }
  } catch (e) {
    ElMessage.error('获取报告列表失败')
  } finally {
    loading.value = false
  }
}

function generateReport() { genVisible.value = true }

async function doGenerate() {
  generating.value = true
  try {
    await api.post(API.REPORTS, genForm)
    ElMessage.success('报告生成任务已创建')
    genVisible.value = false
    setTimeout(fetchData, 2000)
  } catch (e) {
    ElMessage.error('生成报告失败')
  } finally {
    generating.value = false
  }
}

function viewReport(row: any) {
  router.push({ path: '/report-audit/preview', query: { id: row.id } })
}

function downloadReport(row: any) {
  ElMessage.info('下载功能开发中')
}

function typeLabel(t: string) {
  const map: Record<string, string> = { daily: '日报', weekly: '周报', monthly: '月报' }
  return map[t] || t || '报告'
}

onMounted(fetchData)
</script>

<style scoped>
</style>
