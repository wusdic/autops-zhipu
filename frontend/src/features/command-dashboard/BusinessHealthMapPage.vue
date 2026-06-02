<template>
  <div class="p-6">
    <h2 class="page-title">业务健康地图</h2>
    <el-row :gutter="16" class="mb-lg">
      <el-col :xs="12" :sm="6" v-for="card in statCards" :key="card.label">
        <div class="autops-metric-card">
          <div class="metric-icon" :style="{ background: card.bg, color: card.color }">
            <el-icon size="20"><component :is="card.icon" /></el-icon>
          </div>
          <div class="metric-label">{{ card.label }}</div>
          <div class="metric-value" :style="{ color: card.color }">{{ card.value }}</div>
        </div>
      </el-col>
    </el-row>
    <el-row :gutter="16">
      <el-col :span="16">
        <div class="autops-card">
          <div class="autops-card-header"><div class="autops-card-title">业务系统健康视图</div></div>
          <div class="autops-card-body">
            <div class="health-grid">
              <div v-for="sys in businessSystems" :key="sys.name" class="health-card" :class="sys.health" @click="selectSystem(sys)">
                <div class="health-name">{{ sys.name }}</div>
                <div class="health-status">{{ healthLabel(sys.health) }}</div>
                <div class="health-meta">{{ sys.asset_count }} 资产 · {{ sys.alert_count }} 告警</div>
              </div>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="autops-card" v-if="selectedSystem">
          <div class="autops-card-header"><div class="autops-card-title">{{ selectedSystem.name }} 详情</div></div>
          <div class="autops-card-body">
            <el-descriptions :column="1" border size="small">
              <el-descriptions-item label="健康状态">{{ healthLabel(selectedSystem.health) }}</el-descriptions-item>
              <el-descriptions-item label="资产数">{{ selectedSystem.asset_count }}</el-descriptions-item>
              <el-descriptions-item label="活跃告警">{{ selectedSystem.alert_count }}</el-descriptions-item>
              <el-descriptions-item label="SLA达成率">{{ selectedSystem.sla }}%</el-descriptions-item>
              <el-descriptions-item label="负责人">{{ selectedSystem.owner }}</el-descriptions-item>
            </el-descriptions>
          </div>
        </div>
        <el-empty v-else description="点击左侧业务系统查看详情" :image-size="80" />
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from "vue"
import { CircleCheck, Warning, CircleClose, QuestionFilled } from "@element-plus/icons-vue"

const statCards = reactive([
  { label: "业务系统", value: 0, icon: QuestionFilled, bg: "#e8f3ff", color: "#165dff" },
  { label: "正常", value: 0, icon: CircleCheck, bg: "#e8ffea", color: "#00b42a" },
  { label: "告警", value: 0, icon: Warning, bg: "#fff7e8", color: "#ff7d00" },
  { label: "故障", value: 0, icon: CircleClose, bg: "#ffece8", color: "#f53f3f" },
])

const businessSystems = ref<any[]>([])
const selectedSystem = ref<any>(null)

function healthLabel(h: string) { return ({ healthy: "正常", warning: "告警", critical: "故障", unknown: "未知" } as any)[h] || h }
function selectSystem(sys: any) { selectedSystem.value = sys }
</script>

<style scoped>
.page-title { font-size: 18px; font-weight: 600; margin-bottom: 16px; color: #1d2129; }
.mb-lg { margin-bottom: 16px; }
.health-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 12px; }
.health-card { border-radius: 8px; padding: 16px; cursor: pointer; transition: all 0.2s; border: 1px solid #e5e6eb; }
.health-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
.health-card.healthy { border-left: 4px solid #00b42a; background: #f8fff9; }
.health-card.warning { border-left: 4px solid #ff7d00; background: #fffbf0; }
.health-card.critical { border-left: 4px solid #f53f3f; background: #fff5f3; }
.health-card.unknown { border-left: 4px solid #86909c; background: #fafafa; }
.health-name { font-weight: 600; color: #1d2129; margin-bottom: 4px; }
.health-status { font-size: 13px; margin-bottom: 4px; }
.health-meta { font-size: 12px; color: #86909c; }
</style>
