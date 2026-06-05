<template>
  <div class="autops-page-container">
    <div class="autops-page-header autops-page-header--between">
      <div>
        <div class="autops-page-title">业务健康地图</div>
        <div class="autops-page-desc">监控各业务系统的健康状态和告警情况</div>
      </div>
      <div class="autops-header-actions">
        <el-button @click="fetchSystems" :loading="loading" type="primary" plain size="small">刷新</el-button>
      </div>
    </div>

    <!-- 总体健康评分 -->
    <el-row :gutter="16" class="mb-lg">
      <el-col :xs="12" :sm="6" v-for="card in statCards" :key="card.label">
        <div class="autops-metric-card">
          <div class="metric-icon" :class="card.bgClass">
            <el-icon size="20"><component :is="card.icon" /></el-icon>
          </div>
          <div class="metric-label">{{ card.label }}</div>
          <div class="metric-value" :class="card.textClass">{{ card.value }}</div>
        </div>
      </el-col>
    </el-row>

    <!-- 健康评分条 -->
    <div class="autops-card mb-lg" v-if="overallHealth !== null">
      <div class="autops-card-body" style="display: flex; align-items: center; gap: 20px">
        <span style="font-weight: 600; white-space: nowrap">总体健康评分</span>
        <el-progress
          :percentage="overallHealth"
          :color="healthColor(overallHealth)"
          :stroke-width="20"
          style="flex: 1"
          :format="(p: number) => p + '分'"
        />
        <el-tag :type="healthTagType(overallHealth)" size="large">
          {{ healthText(overallHealth) }}
        </el-tag>
      </div>
    </div>

    <!-- 搜索过滤 -->
    <div class="autops-card mb-lg">
      <div class="autops-card-body">
        <el-form :inline="true" @submit.prevent="filterSystems">
          <el-form-item label="搜索">
            <el-input v-model="searchKeyword" placeholder="业务系统名称" clearable style="width: 240px" @clear="filterSystems" />
          </el-form-item>
          <el-form-item label="健康状态">
            <el-select v-model="filterHealth" placeholder="全部" clearable style="width: 140px" @change="filterSystems">
              <el-option label="正常" value="healthy" />
              <el-option label="告警" value="warning" />
              <el-option label="故障" value="critical" />
              <el-option label="未知" value="unknown" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="filterSystems">筛选</el-button>
            <el-button @click="resetFilter">重置</el-button>
          </el-form-item>
        </el-form>
      </div>
    </div>

    <!-- 业务系统健康网格 -->
    <el-row :gutter="16">
      <el-col :span="16">
        <div class="autops-card">
          <div class="autops-card-header">
            <div class="autops-card-title">业务系统健康视图</div>
            <span class="text-tertiary">{{ filteredSystems.length }} 个系统</span>
          </div>
          <div class="autops-card-body">
            <div class="health-grid" v-loading="loading">
              <div
                v-for="sys in filteredSystems"
                :key="sys.id || sys.name"
                class="health-card"
                :class="sys.health"
                @click="selectSystem(sys)"
              >
                <div class="health-card-header">
                  <div class="health-indicator" :class="'indicator-' + sys.health"></div>
                  <div class="health-name">{{ sys.name }}</div>
                </div>
                <div class="health-status">{{ healthLabel(sys.health) }}</div>
                <div class="health-meta">
                  {{ sys.asset_count ?? 0 }} 资产 · {{ sys.alert_count ?? 0 }} 告警
                </div>
                <div class="health-sla" v-if="sys.sla !== undefined">
                  SLA: {{ sys.sla }}%
                </div>
              </div>
              <el-empty v-if="!loading && filteredSystems.length === 0" description="暂无业务系统" :image-size="60" />
            </div>
          </div>
        </div>
      </el-col>

      <!-- 详情面板 -->
      <el-col :span="8">
        <div class="autops-card" v-if="selectedSystem">
          <div class="autops-card-header">
            <div class="autops-card-title">{{ selectedSystem.name }} 详情</div>
            <el-tag :type="healthTagTypeFromStr(selectedSystem.health)" size="small">
              {{ healthLabel(selectedSystem.health) }}
            </el-tag>
          </div>
          <div class="autops-card-body">
            <el-descriptions :column="1" border size="small">
              <el-descriptions-item label="健康状态">
                <span :style="{ color: healthColorStr(selectedSystem.health), fontWeight: 600 }">
                  {{ healthLabel(selectedSystem.health) }}
                </span>
              </el-descriptions-item>
              <el-descriptions-item label="资产数">
                {{ selectedSystem.asset_count ?? '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="活跃告警">
                <span :class="{ 'text-danger': (selectedSystem.alert_count ?? 0) > 0 }">
                  {{ selectedSystem.alert_count ?? 0 }}
                </span>
              </el-descriptions-item>
              <el-descriptions-item label="SLA达成率">
                {{ selectedSystem.sla !== undefined ? selectedSystem.sla + '%' : '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="负责人">
                {{ selectedSystem.owner || '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="描述">
                {{ selectedSystem.description || '-' }}
              </el-descriptions-item>
            </el-descriptions>

            <!-- 该系统告警列表 -->
            <div class="mt-lg">
              <div style="font-weight: 600; margin-bottom: 8px; font-size: 13px">最近告警</div>
              <el-table stripe :data="systemAlerts" size="small"v-loading="sysAlertLoading" empty-text="暂无告警" max-height="200">
                <el-table-column prop="title" label="告警" min-width="120" show-overflow-tooltip />
                <el-table-column prop="severity" label="级别" width="60">
                  <template #default="{ row }">
                    <el-tag :type="severityType(row.severity)" size="small">{{ severityLabel(row.severity) }}</el-tag>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </div>
        </div>
        <el-empty v-else description="点击左侧业务系统查看详情" :image-size="80" />
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { CircleCheck, Warning, CircleClose, QuestionFilled } from '@element-plus/icons-vue'
import { dashboardService, alertService } from '@/shared/api'
import client from '@/shared/api/client'
import { API } from '@/shared/api/routes'

const loading = ref(false)
const sysAlertLoading = ref(false)
const businessSystems = ref<any[]>([])
const selectedSystem = ref<any>(null)
const systemAlerts = ref<any[]>([])
const searchKeyword = ref('')
const filterHealth = ref('')

const statCards = reactive([
  { label: '业务系统', value: 0, icon: QuestionFilled, bgClass: 'bg-brand', textClass: 'text-brand' },
  { label: '正常', value: 0, icon: CircleCheck, bgClass: 'bg-success', textClass: 'text-success' },
  { label: '告警', value: 0, icon: Warning, bgClass: 'bg-warning', textClass: 'text-warning' },
  { label: '故障', value: 0, icon: CircleClose, bgClass: 'bg-danger', textClass: 'text-danger' },
])

const overallHealth = ref<number | null>(null)

// Filtered systems
const filteredSystems = computed(() => {
  let list = businessSystems.value
  if (searchKeyword.value) {
    const kw = searchKeyword.value.toLowerCase()
    list = list.filter(s => (s.name || '').toLowerCase().includes(kw))
  }
  if (filterHealth.value) {
    list = list.filter(s => s.health === filterHealth.value)
  }
  return list
})

// Helpers
const healthLabelMap: Record<string, string> = { healthy: '正常', warning: '告警', critical: '故障', unknown: '未知' }
const healthLabel = (h: string) => healthLabelMap[h] || h

const severityMap: Record<string, string> = { critical: '严重', high: '高', medium: '中', low: '低' }
const severityLabel = (s: string) => severityMap[s] || s
const severityType = (s: string): '' | 'success' | 'warning' | 'danger' | 'info' =>
  ({ critical: 'danger', high: 'warning', medium: '', low: 'info' } as any)[s] || 'info'

function healthColor(p: number) {
  if (p >= 90) return '#00b42a'
  if (p >= 70) return '#165dff'
  if (p >= 50) return '#ff7d00'
  return '#f53f3f'
}
function healthText(p: number) {
  if (p >= 90) return '优秀'
  if (p >= 70) return '良好'
  if (p >= 50) return '一般'
  return '较差'
}
function healthTagType(p: number): '' | 'success' | 'warning' | 'danger' | 'info' {
  if (p >= 90) return 'success'
  if (p >= 70) return ''
  if (p >= 50) return 'warning'
  return 'danger'
}
function healthTagTypeFromStr(h: string): '' | 'success' | 'warning' | 'danger' | 'info' {
  return ({ healthy: 'success', warning: 'warning', critical: 'danger', unknown: 'info' } as any)[h] || 'info'
}
function healthColorStr(h: string) {
  return ({ healthy: '#00b42a', warning: '#ff7d00', critical: '#f53f3f', unknown: '#86909c' } as any)[h] || '#86909c'
}

function filterSystems() { /* computed handles filtering */ }
function resetFilter() {
  searchKeyword.value = ''
  filterHealth.value = ''
}

async function fetchSystems() {
  loading.value = true
  try {
    const [sysRes, discRes] = await Promise.allSettled([
      client.get(API.BUSINESS_SYSTEMS),
      dashboardService.assetDiscovery(),
    ])

    let systems: any[] = []
    if (sysRes.status === 'fulfilled') {
      const data = sysRes.value.data?.data || sysRes.value.data
      systems = data?.items || data || []
    }

    // Enrich with discovery data if available
    if (discRes.status === 'fulfilled') {
      const discData = discRes.value.data?.data || discRes.value.data
      if (discData?.systems) {
        // Merge discovery data into systems
        discData.systems.forEach((ds: any) => {
          const existing = systems.find(s => s.name === ds.name || s.id === ds.id)
          if (existing) {
            Object.assign(existing, ds)
          } else {
            systems.push(ds)
          }
        })
      }
    }

    businessSystems.value = systems
    updateStats(systems)
  } catch (e: any) {
    ElMessage.error(e.message || '获取业务系统失败')
  } finally {
    loading.value = false
  }
}

function updateStats(systems: any[]) {
  statCards[0].value = systems.length
  statCards[1].value = systems.filter(s => s.health === 'healthy').length
  statCards[2].value = systems.filter(s => s.health === 'warning').length
  statCards[3].value = systems.filter(s => s.health === 'critical').length

  // Calculate overall health
  if (systems.length > 0) {
    const healthyPct = (statCards[1].value / systems.length) * 100
    const warningPct = (statCards[2].value / systems.length) * 50
    overallHealth.value = Math.round(Math.min(healthyPct + warningPct, 100))
  } else {
    overallHealth.value = null
  }
}

async function selectSystem(sys: any) {
  selectedSystem.value = sys
  sysAlertLoading.value = true
  try {
    const res = await alertService.list({
      page_size: 10,
      business_system: sys.name || sys.id,
    })
    const data = res.data?.data || res.data
    systemAlerts.value = data?.items || data || []
  } catch {
    systemAlerts.value = []
  } finally {
    sysAlertLoading.value = false
  }
}

onMounted(() => fetchSystems())
</script>

<style scoped>


.text-tertiary {
  color: var(--autops-info);
  font-size: var(--autops-font-12);
}

.health-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 12px;
}
.health-card {
  border-radius: var(--autops-radius-md);
  padding: var(--autops-space-lg);
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid var(--autops-bg-4);
}
.health-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}
.health-card.healthy {
  border-left: 4px solid var(--autops-success);
  background: var(--autops-success-light);
}
.health-card.warning {
  border-left: 4px solid var(--autops-warning);
  background: var(--autops-warning-light);
}
.health-card.critical {
  border-left: 4px solid var(--autops-danger);
  background: var(--autops-danger-light);
}
.health-card.unknown {
  border-left: 4px solid var(--autops-info);
  background: var(--autops-bg-1);
}
.health-card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}
.health-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
.indicator-healthy { background: var(--autops-success); }
.indicator-warning { background: var(--autops-warning); }
.indicator-critical { background: var(--autops-danger); }
.indicator-unknown { background: var(--autops-info); }
.health-name {
  font-weight: 600;
  color: var(--autops-text-1);
}
.health-status {
  font-size: var(--autops-font-13);
  margin-bottom: 4px;
}
.health-meta {
  font-size: var(--autops-font-12);
  color: var(--autops-info);
}
.health-sla {
  font-size: var(--autops-font-12);
  color: var(--autops-primary);
  margin-top: 4px;
}
</style>
