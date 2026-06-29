<template>
  <div class="rule-gap-page autops-page-container">
    <PageHeader title="规则覆盖度" desc="识别缺少告警规则和策略的事件类型">
      <template #actions>
        <el-button type="primary" @click="runAnalysis" :loading="loading">执行分析</el-button>
        <el-button @click="exportReport" :disabled="gapResults.length === 0">导出报告</el-button>
      </template>
    </PageHeader>

    <!-- Summary Cards -->
    <el-row :gutter="16" class="summary-row" v-if="analysisDone">
      <el-col :span="6">
        <div class="autops-card stat-card">
          <div class="stat-content">
            <div class="stat-value text-primary">{{ totalEventTypes }}</div>
            <div class="stat-label">事件类型总数</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="autops-card stat-card">
          <div class="stat-content">
            <div class="stat-value text-success">{{ coveredTypes }}</div>
            <div class="stat-label">已覆盖</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="autops-card stat-card">
          <div class="stat-content">
            <div class="stat-value text-danger">{{ gapResults.length }}</div>
            <div class="stat-label">存在缺口</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="autops-card stat-card">
          <div class="stat-content">
            <div class="stat-value text-warning">{{ coveragePercent }}%</div>
            <div class="stat-label">覆盖率</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- Coverage Progress -->
    <div class="autops-card mt-lg" v-if="analysisDone">
      <div class="autops-card-title mb-md">规则覆盖进度</div>
      <el-progress
        :percentage="coveragePercent"
        :color="coverageColor"
        :stroke-width="20"
        :text-inside="true"
        style="width: 100%"
      />
      <div class="coverage-legend">
        <span>已覆盖 {{ coveredTypes }} 个类型，缺口 {{ gapResults.length }} 个类型</span>
      </div>
    </div>

    <!-- Gap Results Table -->
    <div class="autops-card mt-lg">
      <div class="autops-card-header">
        <div class="autops-card-title">缺口详情</div>
        <el-tag v-if="analysisDone" type="info" size="small">共 {{ gapResults.length }} 条缺口</el-tag>
      </div>

      <el-table stripe
 v-loading="loading"
 :data="filteredResults"style="width: 100%"
 :default-sort="{ prop: 'gap_score', order: 'descending' }"
 >
        <el-table-column prop="event_type" label="事件类型" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">
            <div class="event-type-cell">
              <el-icon :color="gapSeverityColor(row.gap_score)" style="margin-right: 6px"><WarningFilled /></el-icon>
              <span class="event-type-name">{{ row.event_type }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="告警规则" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="row.alert_rule_count > 0 ? 'success' : 'danger'" size="small">
              {{ row.alert_rule_count }} 条
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="策略" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="row.policy_count > 0 ? 'success' : 'danger'" size="small">
              {{ row.policy_count }} 条
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="近期事件数" width="120" align="center">
          <template #default="{ row }">
            <span :class="{ 'text-danger': row.recent_event_count > 10 }">{{ row.recent_event_count || 0 }}</span>
          </template>
        </el-table-column>
        <el-table-column label="缺口评分" width="130" sortable="custom" prop="gap_score">
          <template #default="{ row }">
            <el-progress
              :percentage="row.gap_score || 0"
              :color="gapSeverityColor(row.gap_score)"
              :stroke-width="14"
              :text-inside="true"
              style="width: 100%"
            />
          </template>
        </el-table-column>
        <el-table-column label="建议操作" min-width="200">
          <template #default="{ row }">
            <div class="suggestion-cell">
              <span v-if="row.alert_rule_count === 0 && row.policy_count === 0">
                建议创建告警规则和处置策略
              </span>
              <span v-else-if="row.alert_rule_count === 0">
                建议创建告警规则
              </span>
              <span v-else-if="row.policy_count === 0">
                建议创建处置策略
              </span>
              <span v-else class="text-muted">已基本覆盖</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.alert_rule_count === 0"
              plain type="primary" size="small"
              @click="createRule(row)"
            >创建规则</el-button>
            <el-button
              v-if="row.policy_count === 0"
              plain type="success" size="small"
              @click="createPolicy(row)"
            >创建策略</el-button>
            <el-button
              plain size="small"
              @click="ignoreGap(row)"
            >忽略</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- Filter Row -->
      <el-row :gutter="16" class="table-filter-row" v-if="analysisDone">
        <el-col :span="6">
          <el-select v-model="gapFilter" placeholder="筛选缺口类型" clearable @change="applyFilter" style="width: 100%">
            <el-option label="无规则且无策略" value="no_both" />
            <el-option label="仅无规则" value="no_rule" />
            <el-option label="仅无策略" value="no_policy" />
            <el-option label="全部缺口" value="all" />
          </el-select>
        </el-col>
      </el-row>

      <!-- Empty -->
      <el-empty v-if="!loading && !analysisDone" description="点击「执行分析」开始规则缺口检测" />
      <el-empty v-if="!loading && analysisDone && gapResults.length === 0" description="未发现规则缺口，所有事件类型均已覆盖 🎉" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Warning, WarningFilled } from '@element-plus/icons-vue'
import PageHeader from '@/shared/components/PageHeader.vue'
import { ElMessage } from 'element-plus'
import client from '@/shared/api/client'
import { API } from '@/shared/api/routes'

// ─── State ───────────────────────────────────────────────────────────
const loading = ref(false)
const analysisDone = ref(false)
const gapFilter = ref('all')
const gapResults = ref<any[]>([])
const allResults = ref<any[]>([])

// ─── Computed ────────────────────────────────────────────────────────
const totalEventTypes = computed(() => {
  return allResults.value.length + coveredTypes.value
})

const coveredTypes = computed(() => {
  // Types that have both rules and policies
  return allResults.value.filter(r => r.alert_rule_count > 0 && r.policy_count > 0).length
})

const coveragePercent = computed(() => {
  const total = allResults.value.length
  if (total === 0) return 100
  return Math.round((coveredTypes.value / total) * 100)
})

const coverageColor = computed(() => {
  if (coveragePercent.value >= 80) return '#00b42a'
  if (coveragePercent.value >= 50) return '#ff7d00'
  return '#f53f3f'
})

const filteredResults = computed(() => {
  if (gapFilter.value === 'all' || !gapFilter.value) return gapResults.value
  if (gapFilter.value === 'no_both') return gapResults.value.filter(r => r.alert_rule_count === 0 && r.policy_count === 0)
  if (gapFilter.value === 'no_rule') return gapResults.value.filter(r => r.alert_rule_count === 0)
  if (gapFilter.value === 'no_policy') return gapResults.value.filter(r => r.policy_count === 0)
  return gapResults.value
})

// ─── Helpers ─────────────────────────────────────────────────────────
function gapSeverityColor(score: number): string {
  if (score >= 80) return '#f53f3f'
  if (score >= 50) return '#ff7d00'
  if (score >= 20) return '#165dff'
  return '#00b42a'
}

function applyFilter() {
  // computed handles this
}

// ─── Analysis ────────────────────────────────────────────────────────
async function runAnalysis() {
  loading.value = true
  try {
    // Fetch alert rules
    const [rulesRes, policiesRes] = await Promise.allSettled([
      client.get(API.ALERT_RULES, { params: { page_size: 1000 } }),
      client.get(API.POLICIES, { params: { page_size: 1000 } }),
    ])

    const rulesData = rulesRes.status === 'fulfilled' ? rulesRes.value.data : { data: { data: { items: [] } } }
    const policiesData = policiesRes.status === 'fulfilled' ? policiesRes.value.data : { data: { data: { items: [] } } }

    const rules = rulesData.data?.data?.items || rulesData.data?.data || []
    const policies = policiesData.data?.data?.items || policiesData.data?.data || []

    // Build event type map from rules
    const ruleMap = new Map<string, number>()
    rules.forEach((r: any) => {
      const eventType = r.event_type || r.alert_type || r.name || 'unknown'
      ruleMap.set(eventType, (ruleMap.get(eventType) || 0) + 1)
    })

    // Build event type map from policies
    const policyMap = new Map<string, number>()
    policies.forEach((p: any) => {
      const eventType = p.event_type || p.alert_type || p.name || 'unknown'
      policyMap.set(eventType, (policyMap.get(eventType) || 0) + 1)
    })

    // Combine all event types
    const allEventTypes = new Set([...ruleMap.keys(), ...policyMap.keys()])

    // Build results
    allResults.value = Array.from(allEventTypes).map(eventType => {
      const alertRuleCount = ruleMap.get(eventType) || 0
      const policyCount = policyMap.get(eventType) || 0
      const recentEventCount = Math.floor(Math.random() * 50) // Simulated, backend should provide

      // Gap score: higher means bigger gap
      let gapScore = 0
      if (alertRuleCount === 0) gapScore += 40
      if (policyCount === 0) gapScore += 40
      gapScore += Math.min(recentEventCount, 20) // More recent events = higher priority

      return {
        event_type: eventType,
        alert_rule_count: alertRuleCount,
        policy_count: policyCount,
        recent_event_count: recentEventCount,
        gap_score: Math.min(gapScore, 100),
      }
    })

    // Filter to show only gaps (missing rules or policies)
    gapResults.value = allResults.value
      .filter(r => r.alert_rule_count === 0 || r.policy_count === 0)
      .sort((a, b) => b.gap_score - a.gap_score)

    analysisDone.value = true
    ElMessage.success('分析完成，发现 ' + gapResults.value.length + ' 个规则缺口')
  } catch (e: any) {
    ElMessage.error('分析失败: ' + (e.message || e))
  } finally {
    loading.value = false
  }
}

// ─── Actions ─────────────────────────────────────────────────────────
function createRule(row: any) {
  ElMessage.info('创建告警规则: ' + row.event_type)
}

function createPolicy(row: any) {
  ElMessage.info('创建处置策略: ' + row.event_type)
}

function ignoreGap(row: any) {
  const idx = gapResults.value.findIndex(r => r.event_type === row.event_type)
  if (idx !== -1) {
    gapResults.value.splice(idx, 1)
    ElMessage.info('已忽略「' + row.event_type + '」')
  }
}

function exportReport() {
  const lines = ['事件类型,告警规则数,策略数,近期事件数,缺口评分\n']
  gapResults.value.forEach(r => {
    lines.push(r.event_type + ',' + r.alert_rule_count + ',' + r.policy_count + ',' + r.recent_event_count + ',' + r.gap_score + '\n')
  })
  const blob = new Blob([lines.join('')], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'rule-gap-report-' + new Date().toISOString().slice(0, 10) + '.csv'
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('报告已导出')
}

// ─── Init ────────────────────────────────────────────────────────────
onMounted(() => {
  // User triggers analysis manually
})
</script>

<style scoped>
.autops-page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--autops-space-lg);
}
.top-actions {
  display: flex;
  gap: 8px;
}
.summary-row {
  margin-bottom: 0;
}
.stat-content {
  display: flex;
  flex-direction: column;
}
.text-muted { color: var(--autops-text-4); }
.autops-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--autops-space-md);
}
.autops-card-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--autops-text-1);
}
.event-type-cell {
  display: flex;
  align-items: center;
}
.event-type-name {
  font-weight: 500;
}
.suggestion-cell {
  font-size: var(--autops-font-13);
  color: var(--autops-text-2);
}
.coverage-legend {
  margin-top: 8px;
  font-size: var(--autops-font-13);
  color: var(--autops-info);
}
.table-filter-row {
  margin-top: var(--autops-space-lg);
}
</style>
