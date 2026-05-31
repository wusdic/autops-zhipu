<template>
  <div class="dashboard">
    <el-row :gutter="16">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-number critical">{{ stats.criticalAlerts }}</div>
          <div class="stat-label">严重告警</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-number warning">{{ stats.totalAlerts }}</div>
          <div class="stat-label">活跃告警</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-number success">{{ stats.totalAssets }}</div>
          <div class="stat-label">资产总数</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-number info">{{ stats.runningExecutions }}</div>
          <div class="stat-label">执行中任务</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="16">
        <el-card>
          <template #header><span>最近告警</span></template>
          <el-table :data="recentAlerts" stripe size="small" max-height="350">
            <el-table-column prop="severity" label="级别" width="80">
              <template #default="{ row }">
                <el-tag :type="row.severity === 'critical' ? 'danger' : 'warning'" size="small" effect="dark">
                  {{ row.severity === 'critical' ? '严重' : '警告' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="title" label="告警" min-width="200" />
            <el-table-column prop="status" label="状态" width="80">
              <template #default="{ row }">
                <el-tag size="small">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="时间" width="170" />
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header><span>资产健康概览</span></template>
          <div class="health-overview">
            <div class="health-item">
              <span>健康</span>
              <el-progress :percentage="healthPercent.healthy" status="success" />
            </div>
            <div class="health-item">
              <span>异常</span>
              <el-progress :percentage="healthPercent.warning" status="warning" />
            </div>
            <div class="health-item">
              <span>故障</span>
              <el-progress :percentage="healthPercent.critical" status="exception" />
            </div>
            <div class="health-item">
              <span>未知</span>
              <el-progress :percentage="healthPercent.unknown" />
            </div>
          </div>
        </el-card>

        <el-card style="margin-top: 16px">
          <template #header><span>快捷操作</span></template>
          <div class="quick-actions">
            <el-button type="primary" @click="$router.push('/assets')">资产管理</el-button>
            <el-button type="danger" @click="$router.push('/alerts')">告警处理</el-button>
            <el-button @click="$router.push('/tickets')">工单中心</el-button>
            <el-button @click="$router.push('/knowledge')">知识库</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import api from '@/shared/api/client'
import { API as R } from '@/shared/api/routes'

const stats = reactive({ criticalAlerts: 0, totalAlerts: 0, totalAssets: 0, runningExecutions: 0 })
const recentAlerts = ref<any[]>([])
const assetHealth = reactive({ healthy: 0, warning: 0, critical: 0, unknown: 0 })


const healthPercent = computed(() => {
  const total = assetHealth.healthy + assetHealth.warning + assetHealth.critical + assetHealth.unknown || 1
  return {
    healthy: Math.round((assetHealth.healthy / total) * 100),
    warning: Math.round((assetHealth.warning / total) * 100),
    critical: Math.round((assetHealth.critical / total) * 100),
    unknown: Math.round((assetHealth.unknown / total) * 100),
  }
})

async function loadDashboard() {
  // Load alerts
  try {
    const { data: alertData } = await api.get(R.ALERTS, { params: { page_size: 10 } })
    if (alertData.code === 0) {
      recentAlerts.value = alertData.data.items || []
      stats.totalAlerts = alertData.data.total || 0
      stats.criticalAlerts = recentAlerts.value.filter((a: any) => a.severity === 'critical').length
    }
  } catch {}

  // Load assets
  try {
    const { data: assetData } = await api.get(R.ASSETS, { params: { page_size: 100 } })
    if (assetData.code === 0) {
      const items = assetData.data.items || []
      stats.totalAssets = assetData.data.total || 0
      items.forEach((a: any) => { assetHealth[a.health_status] = (assetHealth[a.health_status] || 0) + 1 })
    }
  } catch {}

  // Load executions
  try {
    const { data: execData } = await api.get(R.EXECUTIONS, { params: { status: 'running', page_size: 1 } })
    if (execData.code === 0) {
      stats.runningExecutions = execData.data.total || 0
    }
  } catch {}
}

onMounted(() => loadDashboard())
</script>

<style scoped>
.stat-card { text-align: center; padding: 20px 0; }
.stat-number { font-size: 36px; font-weight: bold; }
.stat-number.critical { color: #f56c6c; }
.stat-number.warning { color: #e6a23c; }
.stat-number.success { color: #67c23a; }
.stat-number.info { color: #409eff; }
.stat-label { color: #909399; margin-top: 8px; }
.health-overview { display: flex; flex-direction: column; gap: 16px; }
.health-item { display: flex; align-items: center; gap: 12px; }
.health-item span { width: 40px; color: #606266; }
.quick-actions { display: flex; flex-direction: column; gap: 8px; }
.quick-actions .el-button { width: 100%; }
</style>
