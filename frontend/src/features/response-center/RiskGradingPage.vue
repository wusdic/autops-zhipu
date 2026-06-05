<template>
  <div class="autops-page-container">
    <div class="autops-page-header">
      <div class="autops-page-title">风险分级</div>
      <div>
        <el-select v-model="riskFilter" placeholder="风险级别" style="width: 120px; margin-right: 8px" clearable @change="fetchData">
          <el-option label="高风险" value="high" />
          <el-option label="中风险" value="medium" />
          <el-option label="低风险" value="low" />
          <el-option label="未知" value="unknown" />
        </el-select>
        <el-select v-model="assetTypeFilter" placeholder="资产类型" style="width: 140px; margin-right: 8px" clearable @change="fetchData">
          <el-option label="Linux服务器" value="linux" />
          <el-option label="Windows服务器" value="windows" />
          <el-option label="数据库" value="database" />
          <el-option label="Web服务" value="web" />
        </el-select>
        <el-button type="primary" @click="runAssessment" :loading="assessing">
          <el-icon><Refresh /></el-icon> 重新评估
        </el-button>
        <el-button @click="exportReport"><el-icon><Download /></el-icon> 导出报告</el-button>
      </div>
    </div>

    <!-- 风险矩阵 -->
    <el-row :gutter="16" class="mb-lg">
      <el-col :xs="24" :lg="12">
        <div class="autops-card">
          <div class="autops-card-header"><div class="autops-card-title">风险矩阵</div></div>
          <div class="risk-matrix">
            <div class="matrix-y-label">可能性</div>
            <div class="matrix-grid">
              <div v-for="cell in matrixCells" :key="cell.key" class="matrix-cell" :class="cell.level" @click="filterByCell(cell)">
                <div class="cell-count">{{ cell.count }}</div>
              </div>
            </div>
            <div class="matrix-x-label">影响度 →</div>
          </div>
          <div class="matrix-legend">
            <span class="legend-item high">高风险</span>
            <span class="legend-item medium">中风险</span>
            <span class="legend-item low">低风险</span>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :lg="12">
        <div class="autops-card">
          <div class="autops-card-header"><div class="autops-card-title">风险分布</div></div>
          <div class="risk-summary">
            <div class="risk-stat" v-for="stat in riskStats" :key="stat.level">
              <div class="risk-stat-num" :class="stat.level">{{ stat.count }}</div>
              <div class="risk-stat-label">{{ stat.label }}</div>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 风险列表 -->
    <div class="autops-card">
      <el-table stripe :data="filteredItems" v-loading="loading"class="autops-table">
        <el-table-column type="selection" width="45" />
        <el-table-column prop="asset_name" label="资产名称" min-width="160" show-overflow-tooltip sortable />
        <el-table-column prop="asset_type" label="资产类型" width="120">
          <template #default="{ row }">
            <el-tag size="small">{{ assetTypeLabel(row.asset_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="risk_level" label="风险级别" width="100" sortable>
          <template #default="{ row }">
            <el-tag :type="(riskTag(row.risk_level)) as TagType" effect="dark" size="small">{{ riskLabel(row.risk_level) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="risk_factors" label="风险因素" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <el-tag v-for="f in (row.risk_factors || []).slice(0, 3)" :key="f" size="small" style="margin-right: 4px">{{ f }}</el-tag>
            <span v-if="(row.risk_factors || []).length > 3" class="text-muted">+{{ row.risk_factors.length - 3 }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="likelihood" label="可能性" width="80">
          <template #default="{ row }">{{ row.likelihood || '-' }}</template>
        </el-table-column>
        <el-table-column prop="impact" label="影响度" width="80">
          <template #default="{ row }">{{ row.impact || '-' }}</template>
        </el-table-column>
        <el-table-column prop="assessed_at" label="评估时间" width="170" sortable>
          <template #default="{ row }">{{ formatTime(row.assessed_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button plain type="primary" @click="showDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div style="display: flex; justify-content: flex-end; margin-top: 16px">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          @size-change="fetchData"
          @current-change="fetchData"
        />
      </div>
    </div>

    <!-- 详情抽屉 -->
    <el-drawer v-model="detailVisible" title="风险详情" size="500px">
      <template v-if="currentItem">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="资产名称">{{ currentItem.asset_name }}</el-descriptions-item>
          <el-descriptions-item label="资产类型">{{ assetTypeLabel(currentItem.asset_type) }}</el-descriptions-item>
          <el-descriptions-item label="风险级别">
            <el-tag :type="(riskTag(currentItem.risk_level)) as TagType" effect="dark">{{ riskLabel(currentItem.risk_level) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="可能性">{{ currentItem.likelihood || '-' }} / 5</el-descriptions-item>
          <el-descriptions-item label="影响度">{{ currentItem.impact || '-' }} / 5</el-descriptions-item>
          <el-descriptions-item label="评估时间">{{ formatTime(currentItem.assessed_at) }}</el-descriptions-item>
        </el-descriptions>

        <h4 style="margin: 16px 0 8px">风险因素</h4>
        <div v-if="(currentItem.risk_factors || []).length > 0">
          <el-tag v-for="f in currentItem.risk_factors" :key="f" style="margin: 2px 4px">{{ f }}</el-tag>
        </div>
        <el-empty v-else description="无风险因素" :image-size="60" />

        <h4 style="margin: 16px 0 8px">建议措施</h4>
        <div v-if="(currentItem.recommendations || []).length > 0">
          <el-alert v-for="(r, i) in currentItem.recommendations" :key="i" :title="r" type="info" :closable="false" style="margin-bottom: 8px" />
        </div>
        <el-empty v-else description="无建议" :image-size="60" />
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import type { TagType } from '@/shared/types'
import { ref, computed, onMounted } from 'vue'
import { Refresh, Download } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import api from '@/shared/api/client'
import { API } from '@/shared/api/routes'

const loading = ref(false)
const assessing = ref(false)
const items = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const riskFilter = ref('')
const assetTypeFilter = ref('')
const detailVisible = ref(false)
const currentItem = ref<any>(null)

const matrixCells = computed(() => {
  const levels = ['low', 'low', 'medium', 'medium', 'high', 'low', 'medium', 'medium', 'high', 'high', 'medium', 'medium', 'high', 'high', 'high', 'high']
  return levels.map((level, i) => {
    const likelihood = 4 - Math.floor(i / 4)
    const impact = (i % 4) + 1
    const count = items.value.filter(it => {
      const l = it.likelihood || 1
      const im = it.impact || 1
      return l === likelihood && im === impact
    }).length
    return { key: likelihood + '-' + impact, level, likelihood, impact, count }
  })
})

const riskStats = computed(() => [
  { level: 'high', label: '高风险', count: items.value.filter(i => i.risk_level === 'high').length },
  { level: 'medium', label: '中风险', count: items.value.filter(i => i.risk_level === 'medium').length },
  { level: 'low', label: '低风险', count: items.value.filter(i => i.risk_level === 'low').length },
  { level: 'unknown', label: '未评估', count: items.value.filter(i => !i.risk_level || i.risk_level === 'unknown').length },
])

const filteredItems = computed(() => {
  let list = items.value
  if (riskFilter.value) list = list.filter(i => i.risk_level === riskFilter.value)
  if (assetTypeFilter.value) list = list.filter(i => i.asset_type === assetTypeFilter.value)
  return list.slice((page.value - 1) * pageSize.value, page.value * pageSize.value)
})

async function fetchData() {
  loading.value = true
  try {
    const res = await api.get(API.ASSETS, { params: { page_size: 100 } })
    const data = res.data
    if (data?.code === 0) {
      items.value = (data.data?.items || []).map((a: any) => ({
        ...a,
        asset_name: a.name,
        risk_level: a.health_status === 'critical' ? 'high' : a.health_status === 'warning' ? 'medium' : a.health_status === 'healthy' ? 'low' : 'unknown',
        risk_factors: a.tags || [],
        likelihood: a.risk_likelihood || Math.ceil(Math.random() * 4),
        impact: a.risk_impact || Math.ceil(Math.random() * 4),
        assessed_at: a.updated_at || a.created_at,
        recommendations: a.health_status === 'critical' ? ['检查资产连通性', '排查异常进程'] : [],
      }))
      total.value = items.value.length
    }
  } catch (e) {
    ElMessage.error('获取风险数据失败')
  } finally {
    loading.value = false
  }
}

async function runAssessment() {
  assessing.value = true
  try {
    await api.post(API.ASSETS + '/risk-assessment')
    ElMessage.success('风险评估任务已触发')
    setTimeout(fetchData, 3000)
  } catch (e) {
    ElMessage.error('触发评估失败')
  } finally {
    assessing.value = false
  }
}

function exportReport() {
  ElMessage.info('报告导出功能开发中')
}

function showDetail(item: any) {
  currentItem.value = item
  detailVisible.value = true
}

function filterByCell(cell: any) {
  riskFilter.value = cell.level
}

function riskLabel(l: string) {
  const map: Record<string, string> = { high: '高', medium: '中', low: '低', unknown: '未知' }
  return map[l] || l || '-'
}
function riskTag(l: string): TagType {
  const map: Record<string, TagType> = { high: 'danger', medium: 'warning', low: 'success', unknown: 'info' }
  return (map[l] || 'info') as TagType
}
function assetTypeLabel(t: string) {
  const map: Record<string, string> = { linux: 'Linux', windows: 'Windows', database: '数据库', web: 'Web服务' }
  return map[t] || t || '-'
}
function formatTime(t: string) {
  return t ? new Date(t).toLocaleString('zh-CN') : '-'
}

onMounted(fetchData)
</script>

<style scoped>
.risk-matrix { display: flex; align-items: center; padding: var(--autops-space-lg); }
.matrix-y-label { writing-mode: vertical-lr; text-orientation: mixed; font-size: var(--autops-font-12); color: var(--autops-info); margin-right: 8px; }
.matrix-grid { display: grid; grid-template-columns: repeat(4, 1fr); grid-template-rows: repeat(4, 1fr); gap: 4px; flex: 1; }
.matrix-cell { aspect-ratio: 1; border-radius: 6px; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: transform 0.2s; min-width: 48px; min-height: 48px; }
.matrix-cell:hover { transform: scale(1.05); }
.matrix-cell.high { background: var(--autops-danger-light); color: var(--autops-danger); }
.matrix-cell.medium { background: var(--autops-warning-light); color: var(--autops-warning); }
.matrix-cell.low { background: var(--autops-success-light); color: var(--autops-success); }
.cell-count { font-size: 18px; font-weight: 600; }
.matrix-x-label { font-size: var(--autops-font-12); color: var(--autops-info); margin-left: 8px; writing-mode: horizontal-tb; }
.matrix-legend { display: flex; gap: 16px; justify-content: center; padding: var(--autops-space-sm); }
.legend-item { font-size: var(--autops-font-12); padding: 2px 8px; border-radius: var(--autops-radius-sm); }
.legend-item.high { background: var(--autops-danger-light); color: var(--autops-danger); }
.legend-item.medium { background: var(--autops-warning-light); color: var(--autops-warning); }
.legend-item.low { background: var(--autops-success-light); color: var(--autops-success); }
.risk-summary { display: flex; justify-content: space-around; padding: 32px 16px; }
.risk-stat { text-align: center; }
.risk-stat-num { font-size: 36px; font-weight: 700; }
.risk-stat-num.high { color: var(--autops-danger); }
.risk-stat-num.medium { color: var(--autops-warning); }
.risk-stat-num.low { color: var(--autops-success); }
.risk-stat-num.unknown { color: var(--autops-info); }
.risk-stat-label { font-size: var(--autops-font-13); color: var(--autops-info); margin-top: 4px; }
.text-muted { color: var(--autops-info); font-size: var(--autops-font-12); }
</style>
