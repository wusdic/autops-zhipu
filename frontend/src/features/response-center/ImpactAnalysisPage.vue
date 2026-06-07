<template>
  <div class="p-6">
    <div class="autops-page-header">
      <div class="autops-page-title">影响分析</div>
    </div>

    <!-- 选择异常 -->
    <div class="autops-card mb-lg">
      <div class="autops-card-header">
        <div class="autops-card-title">选择异常</div>
      </div>
      <div class="autops-card-body">
        <el-form :inline="true" @submit.prevent="fetchAnomalies">
          <el-form-item label="搜索">
            <el-input v-model="searchKeyword" placeholder="异常标题" clearable style="width: 240px" @clear="fetchAnomalies" />
          </el-form-item>
          <el-form-item label="严重级别">
            <el-select v-model="filterSeverity" placeholder="全部" clearable style="width: 120px">
              <el-option label="严重" value="critical" />
              <el-option label="高" value="high" />
              <el-option label="中" value="medium" />
              <el-option label="低" value="low" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="fetchAnomalies">查询</el-button>
          </el-form-item>
        </el-form>

        <el-table stripe
 :data="anomalies"size="small"
 v-loading="anomalyLoading"
 empty-text="暂无异常"
 highlight-current-row
 @current-change="handleAnomalySelect"
 class="mt-md"
 >
          <el-table-column prop="title" label="异常标题" min-width="200" show-overflow-tooltip />
          <el-table-column prop="severity" label="级别" width="80">
            <template #default="{ row }">
              <el-tag :type="(severityType(row.severity)) as TagType" size="small">{{ severityLabel(row.severity) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="asset_name" label="资产" width="140" show-overflow-tooltip />
          <el-table-column prop="status" label="状态" width="90">
            <template #default="{ row }">
              <el-tag :type="(statusType(row.status)) as TagType" size="small">{{ statusLabel(row.status) }}</el-tag>
            </template>
          </el-table-column>
        </el-table>

        <div style="padding: 12px 0; display: flex; justify-content: flex-end">
          <el-pagination
            v-model:current-page="anomalyPage"
            :page-size="10"
            :total="anomalyTotal"
            layout="total, prev, pager, next"
            @current-change="fetchAnomalies"
          />
        </div>
      </div>
    </div>

    <!-- 影响分析结果 -->
    <el-row :gutter="16">
      <!-- 受影响资产表 -->
      <el-col :span="16">
        <div class="autops-card">
          <div class="autops-card-header">
            <div class="autops-card-title">
              {{ selectedAnomaly ? '「' + selectedAnomaly.title + '」影响范围' : '影响范围' }}
            </div>
            <el-button
              type="primary"
              size="small"
              :loading="analysisLoading"
              :disabled="!selectedAnomaly"
              @click="runAnalysis"
            >
              分析影响
            </el-button>
          </div>
          <div class="autops-card-body p-0">
            <el-table stripe
 :data="affectedAssets"v-loading="analysisLoading"
 empty-text="选择异常并分析影响"
 >
              <el-table-column prop="name" label="资产名称" min-width="160" show-overflow-tooltip />
              <el-table-column prop="asset_type" label="资产类型" width="120" />
              <el-table-column prop="impact_type" label="影响类型" width="100">
                <template #default="{ row }">
                  <el-tag :type="(impactTypeTag(row.impact_type)) as TagType" size="small">{{ row.impact_type }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="impact_level" label="影响程度" width="100">
                <template #default="{ row }">
                  <span :style="{ color: levelColor(row.impact_level) }" style="font-weight: 600">
                    {{ levelLabel(row.impact_level) }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="business_system" label="所属业务" width="140" show-overflow-tooltip />
              <el-table-column prop="description" label="影响说明" min-width="200" show-overflow-tooltip />
            </el-table>
          </div>
        </div>

        <!-- 爆炸半径可视化 -->
        <div class="autops-card mt-lg" v-if="blastRadius.length">
          <div class="autops-card-header">
            <div class="autops-card-title">爆炸半径</div>
          </div>
          <div class="autops-card-body">
            <div class="blast-grid">
              <div v-for="(level, lidx) in blastRadius" :key="lidx" class="blast-level">
                <div class="blast-level-title">
                  <el-tag :type="(levelColor(lidx)) as TagType" size="small">第 {{ lidx + 1 }} 层</el-tag>
                  <span style="margin-left: 8px; font-weight: 500">{{ level.length }} 个资产</span>
                </div>
                <div class="blast-nodes">
                  <div v-for="node in level" :key="node.name" class="blast-node" :class="'blast-' + severityFromLevel(lidx)">
                    <div class="blast-node-name">{{ node.name }}</div>
                    <div class="blast-node-type">{{ node.asset_type || '-' }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-col>

      <!-- 影响统计 -->
      <el-col :span="8">
        <div class="autops-card">
          <div class="autops-card-header">
            <div class="autops-card-title">影响统计</div>
          </div>
          <div class="autops-card-body">
            <el-descriptions :column="1" border size="small">
              <el-descriptions-item label="直接影响资产">{{ impactStats.direct }}</el-descriptions-item>
              <el-descriptions-item label="间接影响资产">{{ impactStats.indirect }}</el-descriptions-item>
              <el-descriptions-item label="影响业务系统">{{ impactStats.business_systems }}</el-descriptions-item>
              <el-descriptions-item label="受影响用户">{{ impactStats.affected_users }}</el-descriptions-item>
            </el-descriptions>
          </div>
        </div>

        <!-- 严重度分布 -->
        <div class="autops-card mt-lg" v-if="severityDistribution.length">
          <div class="autops-card-header">
            <div class="autops-card-title">严重度分布</div>
          </div>
          <div class="autops-card-body">
            <div v-for="item in severityDistribution" :key="item.level" class="dist-item">
              <div class="dist-label">
                <span :style="{ color: levelColor(item.level) }" style="font-weight: 600">{{ levelLabel(item.level) }}</span>
                <span class="text-tertiary">{{ item.count }} 个</span>
              </div>
              <el-progress
                :percentage="item.percentage"
                :color="levelColor(item.level)"
                :stroke-width="10"
                :show-text="false"
              />
            </div>
          </div>
        </div>

        <!-- 业务系统影响 -->
        <div class="autops-card mt-lg" v-if="businessImpact.length">
          <div class="autops-card-header">
            <div class="autops-card-title">业务系统影响</div>
          </div>
          <div class="autops-card-body p-0">
            <el-table stripe :data="businessImpact" size="small">
              <el-table-column prop="name" label="业务系统" min-width="120" show-overflow-tooltip />
              <el-table-column prop="impact" label="影响" width="80">
                <template #default="{ row }">
                  <span :style="{ color: levelColor(row.impact) }">{{ levelLabel(row.impact) }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="asset_count" label="受影响资产" width="90" />
            </el-table>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import type { TagType } from '@/shared/types'
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { anomalyService } from '@/shared/api'
import client from '@/shared/api/client'
import { API } from '@/shared/api/routes'

// Anomaly list
const anomalyLoading = ref(false)
const anomalies = ref<any[]>([])
const anomalyPage = ref(1)
const anomalyTotal = ref(0)
const searchKeyword = ref('')
const filterSeverity = ref('')
const selectedAnomaly = ref<any>(null)

// Impact analysis
const analysisLoading = ref(false)
const affectedAssets = ref<any[]>([])
const blastRadius = ref<any[][]>([])
const businessImpact = ref<any[]>([])
const severityDistribution = ref<any[]>([])

const impactStats = reactive({
  direct: 0,
  indirect: 0,
  business_systems: 0,
  affected_users: 0,
})

// Helpers
const severityMap: Record<string, string> = { critical: '严重', high: '高', medium: '中', low: '低' }
const severityLabel = (s: string) => severityMap[s] || s
const severityType = (s: string): '' | 'success' | 'warning' | 'danger' | 'info' =>
  ({ critical: 'danger', high: 'warning', medium: 'primary', low: 'info' } as any)[s] || 'info'

const statusMap: Record<string, string> = { open: '新建', acknowledged: '已确认', assigned: '已分配', closed: '已关闭' }
const statusLabel = (s: string) => statusMap[s] || s
const statusType = (s: string): '' | 'success' | 'warning' | 'danger' | 'info' =>
  ({ open: 'danger', acknowledged: 'warning', assigned: 'primary', closed: 'success' } as any)[s] || 'info'

const levelLabel = (l: number) => ['低', '中', '高', '严重'][l] || '-'
const levelColor = (l: number) => ['#00b42a', '#165dff', '#ff7d00', '#f53f3f'][l] || '#86909c'
const severityFromLevel = (l: number) => (['low', 'medium', 'high', 'critical'] as const)[l] || 'low'

const impactTypeTag = (t: string): '' | 'success' | 'warning' | 'danger' | 'info' =>
  ({ direct: 'danger', indirect: 'warning', cascade: 'primary'} as any)[t] || 'info'

// Fetch anomaly list
async function fetchAnomalies() {
  anomalyLoading.value = true
  try {
    const params: Record<string, any> = { page: anomalyPage.value, page_size: 10 }
    if (searchKeyword.value) params.keyword = searchKeyword.value
    if (filterSeverity.value) params.severity = filterSeverity.value
    const res = await anomalyService.list(params)
    const data = res.data?.data || res.data
    anomalies.value = data?.items || data || []
    anomalyTotal.value = data?.total || 0
  } catch (e: any) {
    ElMessage.error(e.message || '获取异常列表失败')
  } finally {
    anomalyLoading.value = false
  }
}

function handleAnomalySelect(row: any) {
  selectedAnomaly.value = row
  affectedAssets.value = []
  blastRadius.value = []
  businessImpact.value = []
  severityDistribution.value = []
  impactStats.direct = 0
  impactStats.indirect = 0
  impactStats.business_systems = 0
  impactStats.affected_users = 0
}

// Run impact analysis
async function runAnalysis() {
  if (!selectedAnomaly.value) return
  analysisLoading.value = true
  try {
    const res = await client.get(API.ANOMALY.IMPACT_ANALYSIS(selectedAnomaly.value.id))
    const data = res.data?.data || res.data

    // Parse affected assets
    const assets: any[] = data?.affected_assets || data?.assets || []
    affectedAssets.value = assets.map((a: any) => ({
      name: a.name || a.asset_name || '-',
      asset_type: a.asset_type || a.type || '-',
      impact_type: a.impact_type || 'direct',
      impact_level: a.impact_level ?? a.level ?? 2,
      business_system: a.business_system || a.system_name || '-',
      description: a.description || '-',
    }))

    // Build blast radius
    blastRadius.value = data?.blast_radius || buildBlastRadius(affectedAssets.value)

    // Stats
    impactStats.direct = data?.direct_count ?? affectedAssets.value.filter(a => a.impact_type === 'direct').length
    impactStats.indirect = data?.indirect_count ?? affectedAssets.value.filter(a => a.impact_type !== 'direct').length
    impactStats.business_systems = data?.business_system_count ?? new Set(affectedAssets.value.map(a => a.business_system)).size
    impactStats.affected_users = data?.affected_users ?? 0

    // Severity distribution
    severityDistribution.value = data?.severity_distribution || buildSeverityDist(affectedAssets.value)

    // Business impact
    businessImpact.value = data?.business_impact || buildBusinessImpact(affectedAssets.value)
  } catch (e: any) {
    ElMessage.error(e.message || '影响分析失败')
  } finally {
    analysisLoading.value = false
  }
}

function buildBlastRadius(assets: any[]): any[][] {
  const levels: any[][] = [[], [], [], []]
  assets.forEach(a => {
    const l = Math.min(Math.max(a.impact_level ?? 2, 0), 3)
    levels[l].push(a)
  })
  return levels.filter(l => l.length > 0)
}

function buildSeverityDist(assets: any[]): any[] {
  const counts = [0, 0, 0, 0]
  assets.forEach(a => counts[Math.min(Math.max(a.impact_level ?? 2, 0), 3)]++)
  const total = assets.length || 1
  return counts
    .map((count, level) => ({ level, count, percentage: Math.round((count / total) * 100) }))
    .filter(d => d.count > 0)
}

function buildBusinessImpact(assets: any[]): any[] {
  const map: Record<string, { name: string; impact: number; asset_count: number }> = {}
  assets.forEach(a => {
    const sys = a.business_system
    if (!sys || sys === '-') return
    if (!map[sys]) map[sys] = { name: sys, impact: 0, asset_count: 0 }
    map[sys].asset_count++
    map[sys].impact = Math.max(map[sys].impact, a.impact_level)
  })
  return Object.values(map)
}

onMounted(() => fetchAnomalies())
</script>

<style scoped>

.text-tertiary {
  color: var(--autops-info);
  font-size: var(--autops-font-12);
}

/* Blast radius */
.blast-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.blast-level-title {
  margin-bottom: var(--autops-space-sm);
}
.blast-nodes {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  padding-left: 20px;
  border-left: 2px solid var(--autops-bg-4);
}
.blast-node {
  border-radius: 6px;
  padding: 10px 14px;
  min-width: 100px;
  border: 1px solid var(--autops-bg-4);
}
.blast-node.blast-critical { border-left: 4px solid var(--autops-danger); background: var(--autops-danger-light); }
.blast-node.blast-high { border-left: 4px solid var(--autops-warning); background: var(--autops-warning-light); }
.blast-node.blast-medium { border-left: 4px solid var(--autops-primary); background: var(--autops-primary-light-5); }
.blast-node.blast-low { border-left: 4px solid var(--autops-success); background: var(--autops-success-light); }
.blast-node-name { font-weight: 600; font-size: var(--autops-font-13); color: var(--autops-text-1); }
.blast-node-type { font-size: var(--autops-font-12); color: var(--autops-info); margin-top: 2px; }

/* Distribution */
.dist-item { margin-bottom: var(--autops-space-md); }
.dist-label { display: flex; justify-content: space-between; margin-bottom: 4px; font-size: var(--autops-font-13); }
</style>
