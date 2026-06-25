<template>
  <div class="compliance-report-page">
    <div class="autops-page-header autops-page-header--between">
      <div>
        <div class="autops-page-title">合规报告</div>
        <div class="autops-page-desc">生成和查看合规检查报告，评估系统合规状态</div>
      </div>
      <div class="autops-header-actions">
        <el-button plain @click="router.back()"><el-icon><ArrowLeft /></el-icon> 返回</el-button>
        <el-button type="primary" @click="generateReport">
          <el-icon><Document /></el-icon> 生成报告
        </el-button>
        <el-button @click="loadData" :loading="loading">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
      </div>
    </div>

    <!-- 合规总览 -->
    <el-row :gutter="16" class="mt-lg">
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header><span>合规评分</span></template>
          <div class="score-circle">
            <el-progress type="circle" :percentage="complianceScore" :width="120" :color="scoreColor" />
            <div class="score-label">{{ complianceScore >= 90 ? '优秀' : complianceScore >= 70 ? '良好' : '需改进' }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header><span>检查项统计</span></template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="总检查项">{{ checkStats.total }}</el-descriptions-item>
            <el-descriptions-item label="通过"><span class="text-success">{{ checkStats.passed }}</span></el-descriptions-item>
            <el-descriptions-item label="不合规"><span class="text-danger">{{ checkStats.failed }}</span></el-descriptions-item>
            <el-descriptions-item label="不适用">{{ checkStats.na }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header><span>风险分布</span></template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="高风险"><el-tag type="danger" size="small">{{ riskStats.high }}</el-tag></el-descriptions-item>
            <el-descriptions-item label="中风险"><el-tag type="warning" size="small">{{ riskStats.medium }}</el-tag></el-descriptions-item>
            <el-descriptions-item label="低风险"><el-tag type="info" size="small">{{ riskStats.low }}</el-tag></el-descriptions-item>
            <el-descriptions-item label="已修复"><el-tag type="success" size="small">{{ riskStats.fixed }}</el-tag></el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>

    <!-- 报告列表 -->
    <el-card class="mt-lg" shadow="never">
      <template #header>
        <div class="autops-card-header">
          <span>合规报告列表</span>
          <el-form :inline="true" :model="filters" size="small">
            <el-form-item>
              <el-select v-model="filters.standard" placeholder="合规标准" clearable @change="loadData">
                <el-option label="等保2.0" value="mlps_2" />
                <el-option label="ISO 27001" value="iso_27001" />
                <el-option label="CIS Benchmark" value="cis" />
                <el-option label="GDPR" value="gdpr" />
              </el-select>
            </el-form-item>
          </el-form>
        </div>
      </template>
      <el-table stripe :data="reports" v-loading="loading"border>
        <el-table-column prop="name" label="报告名称" min-width="250" />
        <el-table-column prop="standard" label="合规标准" width="140">
          <template #default="{ row }">
            <el-tag size="small">{{ standardName(row.standard) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="score" label="合规评分" width="120">
          <template #default="{ row }">
            <span :class="row.score >= 90 ? 'text-success' : row.score >= 70 ? 'text-warning' : 'text-danger'" style="font-weight: bold">
              {{ row.score }}分
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="total_checks" label="检查项" width="90" />
        <el-table-column prop="passed" label="通过" width="80">
          <template #default="{ row }"><span class="text-success">{{ row.passed }}</span></template>
        </el-table-column>
        <el-table-column prop="failed" label="不合规" width="90">
          <template #default="{ row }"><span class="text-danger">{{ row.failed }}</span></template>
        </el-table-column>
        <el-table-column prop="generated_at" label="生成时间" width="180" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button plain type="primary" @click="viewReport(row)">查看</el-button>
            <el-button plain type="primary" @click="downloadReport(row)">下载</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination class="mt-lg" v-model:current-page="pagination.page" v-model:page-size="pagination.size"
        :total="pagination.total" :page-sizes="[10, 20, 50]" layout="total, sizes, prev, pager, next"
        @size-change="loadData" @current-change="loadData" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Document, Refresh, ArrowLeft } from '@element-plus/icons-vue'
import client from '@/shared/api/client'

const router = useRouter()
const loading = ref(false)
const reports = ref<any[]>([])
const filters = ref({ standard: ''})
const pagination = reactive({ page: 1, size: 10, total: 0 })

const complianceScore = ref(0)
const checkStats = ref({ total: 0, passed: 0, failed: 0, na: 0 })
const riskStats = ref({ high: 0, medium: 0, low: 0, fixed: 0 })


const scoreColor = computed(() => {
  if (complianceScore.value >= 90) return '#00b42a'
  if (complianceScore.value >= 70) return '#ff7d00'
  return '#f53f3f'
})

const standardMap: Record<string, string> = { mlps_2: '等保2.0', iso_27001: 'ISO 27001', cis: 'CIS Benchmark', gdpr: 'GDPR' }
function standardName(s: string) { return standardMap[s] || s }

async function loadData() {
  loading.value = true
  try {
    const res = await client.get('/api/v1/report/archive', { params: { type: 'compliance', page: pagination.page, page_size: pagination.size } })
    const data = res.data?.data ?? res.data
    reports.value = data?.items || []
    pagination.total = data?.total || 0
    // 从报告数据聚合统计
    const items = reports.value
    if (items.length > 0) {
      const totalChecks = items.reduce((s: number, r: any) => s + (r.total_checks || 0), 0)
      const totalPassed = items.reduce((s: number, r: any) => s + (r.passed || 0), 0)
      const totalFailed = items.reduce((s: number, r: any) => s + (r.failed || 0), 0)
      const avgScore = items.reduce((s: number, r: any) => s + (r.score || 0), 0) / items.length
      checkStats.value = { total: totalChecks, passed: totalPassed, failed: totalFailed, na: totalChecks - totalPassed - totalFailed }
      complianceScore.value = Math.round(avgScore)
      riskStats.value = { high: totalFailed, medium: Math.floor(totalFailed * 0.6), low: items.filter((r: any) => (r.score || 0) >= 90).length, fixed: totalPassed }
    } else {
      complianceScore.value = 0
      checkStats.value = { total: 0, passed: 0, failed: 0, na: 0 }
      riskStats.value = { high: 0, medium: 0, low: 0, fixed: 0 }
    }
  } catch { reports.value = [] } finally { loading.value = false }
}

async function generateReport() {
  try {
    await client.post('/api/v1/report/generate', { type: 'compliance', standard: filters.value.standard || 'mlps_2' })
    ElMessage.success('合规报告生成中...')
    setTimeout(loadData, 2000)
  } catch { ElMessage.error('生成失败') }
}

function viewReport(row: any) { router.push('/reports/archive/' + row.id) }
async function downloadReport(row: any) {
  window.open('/api/v1/report/tasks/' + row.id + '/download', '_blank')
}

onMounted(loadData)
</script>

<style scoped>
.compliance-report-page { padding: var(--autops-space-xl); }
.mt-4 { margin-top: var(--autops-space-lg); }
.score-circle { text-align: center; padding: var(--autops-space-xl); }
.score-label { margin-top: 12px; font-size: var(--autops-font-16); color: var(--autops-text-2); }
</style>
