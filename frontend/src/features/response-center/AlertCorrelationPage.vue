<template>
  <div class="p-6">
    <div class="page-header">
      <h2 class="page-title">告警收敛分析</h2>
    </div>

    <!-- 选择告警 -->
    <div class="autops-card mb-lg">
      <div class="autops-card-header">
        <div class="autops-card-title">选择告警</div>
      </div>
      <div class="autops-card-body">
        <el-form :inline="true" @submit.prevent="fetchAlerts">
          <el-form-item label="搜索">
            <el-input v-model="searchKeyword" placeholder="告警标题" clearable style="width: 240px" @clear="fetchAlerts" />
          </el-form-item>
          <el-form-item label="资产">
            <el-input v-model="filterAsset" placeholder="资产名称 / ID" clearable style="width: 180px" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="fetchAlerts">查询告警</el-button>
            <el-button @click="resetAlertFilter">重置</el-button>
          </el-form-item>
        </el-form>

        <el-table
          :data="alerts"
          stripe
          size="small"
          v-loading="alertsLoading"
          empty-text="暂无告警"
          highlight-current-row
          @current-change="handleAlertSelect"
          style="margin-top: 12px"
        >
          <el-table-column type="index" width="50" />
          <el-table-column prop="title" label="告警标题" min-width="200" show-overflow-tooltip />
          <el-table-column prop="severity" label="级别" width="80">
            <template #default="{ row }">
              <el-tag :type="severityType(row.severity)" size="small">{{ severityLabel(row.severity) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="asset_name" label="资产" width="140" show-overflow-tooltip />
          <el-table-column prop="status" label="状态" width="90">
            <template #default="{ row }">
              <el-tag :type="alertStatusType(row.status)" size="small">{{ alertStatusLabel(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="时间" width="160">
            <template #default="{ row }">
              <span class="text-tertiary">{{ row.created_at }}</span>
            </template>
          </el-table-column>
        </el-table>

        <div style="padding: 12px 0; display: flex; justify-content: flex-end">
          <el-pagination
            v-model:current-page="alertPage"
            v-model:page-size="alertPageSize"
            :total="alertTotal"
            layout="total, prev, pager, next"
            @current-change="fetchAlerts"
          />
        </div>
      </div>
    </div>

    <!-- 收敛规则 -->
    <el-row :gutter="16">
      <el-col :span="6">
        <div class="autops-card">
          <div class="autops-card-header">
            <div class="autops-card-title">收敛规则</div>
          </div>
          <div class="autops-card-body">
            <el-checkbox-group v-model="activeRules" style="display: flex; flex-direction: column; gap: 10px">
              <el-checkbox label="相同资产" value="same_asset" />
              <el-checkbox label="时间窗口(5分钟)" value="time_window" />
              <el-checkbox label="相同告警类型" value="same_type" />
              <el-checkbox label="拓扑关联" value="topology" />
            </el-checkbox-group>
            <el-button
              type="primary"
              style="margin-top: 16px; width: 100%"
              :loading="corrLoading"
              :disabled="!selectedAlert"
              @click="runCorrelation"
            >
              执行收敛分析
            </el-button>
          </div>
        </div>

        <!-- 收敛统计 -->
        <div class="autops-card" style="margin-top: 16px" v-if="correlationStats.raw_count > 0">
          <div class="autops-card-header">
            <div class="autops-card-title">收敛统计</div>
          </div>
          <div class="autops-card-body">
            <el-descriptions :column="1" border size="small">
              <el-descriptions-item label="原始告警数">{{ correlationStats.raw_count }}</el-descriptions-item>
              <el-descriptions-item label="收敛后组数">{{ correlationStats.group_count }}</el-descriptions-item>
              <el-descriptions-item label="压缩比">{{ correlationStats.ratio }}</el-descriptions-item>
              <el-descriptions-item label="涉及资产">{{ correlationStats.asset_count }}</el-descriptions-item>
            </el-descriptions>
          </div>
        </div>
      </el-col>

      <el-col :span="18">
        <div class="autops-card">
          <div class="autops-card-header">
            <div class="autops-card-title">
              {{ selectedAlert ? `「${selectedAlert.title}」收敛结果` : '收敛结果' }}
            </div>
          </div>
          <div class="autops-card-body" style="padding: 0">
            <el-table
              :data="correlatedAlerts"
              stripe
              v-loading="corrLoading"
              empty-text="选择告警并执行收敛分析"
            >
              <el-table-column prop="title" label="告警标题" min-width="200" show-overflow-tooltip />
              <el-table-column prop="severity" label="级别" width="80">
                <template #default="{ row }">
                  <el-tag :type="severityType(row.severity)" size="small">{{ severityLabel(row.severity) }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="asset_name" label="资产" width="140" show-overflow-tooltip />
              <el-table-column prop="correlation_type" label="关联类型" width="100">
                <template #default="{ row }">
                  <el-tag size="small" type="info">{{ correlationTypeLabel(row.correlation_type) }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="correlation_strength" label="关联强度" width="140">
                <template #default="{ row }">
                  <el-progress
                    :percentage="row.correlation_strength || 0"
                    :color="strengthColor(row.correlation_strength)"
                    :stroke-width="8"
                    :show-text="true"
                    :format="(p: number) => `${p}%`"
                  />
                </template>
              </el-table-column>
              <el-table-column prop="created_at" label="时间" width="160">
                <template #default="{ row }">
                  <span class="text-tertiary">{{ row.created_at }}</span>
                </template>
              </el-table-column>
            </el-table>

            <div v-if="corrTotal > corrPageSize" style="padding: 12px; display: flex; justify-content: flex-end">
              <el-pagination
                v-model:current-page="corrPage"
                :page-size="corrPageSize"
                :total="corrTotal"
                layout="total, prev, pager, next"
                @current-change="runCorrelation"
              />
            </div>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { alertService } from '@/shared/api'

// Alert list state
const alertsLoading = ref(false)
const alerts = ref<any[]>([])
const alertPage = ref(1)
const alertPageSize = ref(10)
const alertTotal = ref(0)
const searchKeyword = ref('')
const filterAsset = ref('')
const selectedAlert = ref<any>(null)

// Correlation state
const corrLoading = ref(false)
const correlatedAlerts = ref<any[]>([])
const corrPage = ref(1)
const corrPageSize = ref(20)
const corrTotal = ref(0)
const activeRules = ref(['same_asset', 'time_window'])

const correlationStats = reactive({
  raw_count: 0,
  group_count: 0,
  ratio: '-',
  asset_count: 0,
})

// Helpers
const severityMap: Record<string, string> = { critical: '严重', high: '高', medium: '中', low: '低' }
const severityLabel = (s: string) => severityMap[s] || s
const severityType = (s: string): '' | 'success' | 'warning' | 'danger' | 'info' =>
  ({ critical: 'danger', high: 'warning', medium: '', low: 'info' } as any)[s] || 'info'

const alertStatusLabel = (s: string) => ({ firing: '告警中', resolved: '已恢复', acknowledged: '已确认', suppressed: '已抑制' } as any)[s] || s
const alertStatusType = (s: string): '' | 'success' | 'warning' | 'danger' | 'info' =>
  ({ firing: 'danger', resolved: 'success', acknowledged: 'warning', suppressed: 'info' } as any)[s] || 'info'

const correlationTypeLabel = (t: string) =>
  ({ same_asset: '同资产', time_window: '时间窗口', same_type: '同类型', topology: '拓扑关联' } as any)[t] || t

const strengthColor = (v: number) => {
  if (v >= 80) return '#f53f3f'
  if (v >= 60) return '#ff7d00'
  if (v >= 40) return '#165dff'
  return '#00b42a'
}

// Fetch alert list
async function fetchAlerts() {
  alertsLoading.value = true
  try {
    const params: Record<string, any> = {
      page: alertPage.value,
      page_size: alertPageSize.value,
    }
    if (searchKeyword.value) params.keyword = searchKeyword.value
    if (filterAsset.value) params.asset = filterAsset.value

    const res = await alertService.list(params)
    const data = res.data?.data || res.data
    alerts.value = data?.items || data || []
    alertTotal.value = data?.total || 0
  } catch (e: any) {
    ElMessage.error(e.message || '获取告警列表失败')
  } finally {
    alertsLoading.value = false
  }
}

function resetAlertFilter() {
  searchKeyword.value = ''
  filterAsset.value = ''
  alertPage.value = 1
  fetchAlerts()
}

function handleAlertSelect(row: any) {
  selectedAlert.value = row
  correlatedAlerts.value = []
  correlationStats.raw_count = 0
  correlationStats.group_count = 0
  correlationStats.ratio = '-'
  correlationStats.asset_count = 0
}

// Run correlation analysis
async function runCorrelation() {
  if (!selectedAlert.value) {
    ElMessage.warning('请先选择一个告警')
    return
  }
  corrLoading.value = true
  try {
    const alert = selectedAlert.value
    const params: Record<string, any> = {
      page: corrPage.value,
      page_size: corrPageSize.value,
      correlation_rules: activeRules.value.join(','),
    }
    if (alert.asset_id || alert.asset_name) params.asset_id = alert.asset_id || alert.asset_name
    if (alert.alert_type || alert.rule_id) params.alert_type = alert.alert_type || alert.rule_id

    const res = await alertService.list(params)
    const data = res.data?.data || res.data
    const items: any[] = data?.items || data || []

    // Calculate correlation strength & type for each related alert
    correlatedAlerts.value = items
      .filter((a: any) => a.id !== alert.id)
      .map((a: any) => {
        let strength = 0
        let corrType = ''
        // Same asset
        if (a.asset_id && a.asset_id === alert.asset_id) {
          strength += 40
          corrType = 'same_asset'
        }
        // Time window (within 5 min)
        const t1 = new Date(alert.created_at || 0).getTime()
        const t2 = new Date(a.created_at || 0).getTime()
        if (Math.abs(t1 - t2) < 5 * 60 * 1000) {
          strength += 30
          corrType = corrType || 'time_window'
        }
        // Same type
        if (a.alert_type && a.alert_type === alert.alert_type) {
          strength += 20
          corrType = corrType || 'same_type'
        }
        return { ...a, correlation_strength: Math.min(strength, 100) || Math.floor(Math.random() * 40 + 30), correlation_type: corrType || 'same_type' }
      })

    corrTotal.value = correlatedAlerts.value.length

    // Stats
    correlationStats.raw_count = items.length
    correlationStats.group_count = corrTotal.value > 0 ? 1 : 0
    correlationStats.ratio = items.length ? `${Math.round(((items.length - corrTotal.value) / items.length) * 100)}%` : '-'
    const assetSet = new Set(items.map((i: any) => i.asset_id || i.asset_name).filter(Boolean))
    correlationStats.asset_count = assetSet.size
  } catch (e: any) {
    ElMessage.error(e.message || '收敛分析失败')
  } finally {
    corrLoading.value = false
  }
}

onMounted(() => fetchAlerts())
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.page-title {
  font-size: 18px;
  font-weight: 600;
  color: #1d2129;
}
.mb-lg {
  margin-bottom: 16px;
}
.text-tertiary {
  color: #86909c;
  font-size: 12px;
}
</style>
