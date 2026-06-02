<template>
  <div class="p-6">
    <h2 class="page-title">报表总览</h2>
    <el-row :gutter="16" class="mb-lg">
      <el-col :xs="12" :sm="6" v-for="card in statCards" :key="card.label">
        <div class="autops-metric-card" @click="card.route && $router.push(card.route)">
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
          <div class="autops-card-header"><div class="autops-card-title">最近报表</div></div>
          <div class="autops-card-body" style="padding:0">
            <el-table :data="recentReports" stripe size="small" empty-text="暂无报表">
              <el-table-column prop="title" label="报表名称" min-width="180" show-overflow-tooltip />
              <el-table-column prop="type" label="类型" width="100">
                <template #default="{ row }"><el-tag size="small">{{ row.type }}</el-tag></template>
              </el-table-column>
              <el-table-column prop="status" label="状态" width="80">
                <template #default="{ row }">
                  <el-tag :type="row.status === 'completed' ? 'success' : row.status === 'generating' ? 'warning' : 'info'" size="small">{{ row.status }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="period" label="周期" width="140" />
              <el-table-column prop="generated_at" label="生成时间" width="160">
                <template #default="{ row }"><span class="text-tertiary font-12">{{ row.generated_at }}</span></template>
              </el-table-column>
              <el-table-column label="操作" width="100">
                <template #default="{ row }">
                  <el-button v-if="row.status === 'completed'" text type="primary" size="small">预览</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="autops-card">
          <div class="autops-card-header"><div class="autops-card-title">快捷生成</div></div>
          <div class="autops-card-body" style="display:flex;flex-direction:column;gap:8px">
            <el-button @click="$router.push('/report-audit/generate')">巡检报告</el-button>
            <el-button @click="$router.push('/report-audit/generate')">资产台账</el-button>
            <el-button @click="$router.push('/report-audit/generate')">SLA报告</el-button>
            <el-button @click="$router.push('/report-audit/generate')">审计报告</el-button>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from "vue"
import { Document, DataAnalysis, Clock, CircleCheck } from "@element-plus/icons-vue"

const statCards = reactive([
  { label: "报表总数", value: 0, icon: Document, bg: "#e8f3ff", color: "#165dff", route: "/report-audit/archive" },
  { label: "本月生成", value: 0, icon: DataAnalysis, bg: "#e8ffea", color: "#00b42a", route: "/report-audit/tasks" },
  { label: "生成中", value: 0, icon: Clock, bg: "#fff7e8", color: "#ff7d00", route: "/report-audit/tasks" },
  { label: "模板数", value: 0, icon: CircleCheck, bg: "#f2f3f5", color: "#86909c", route: "/report-audit/templates" },
])
const recentReports = ref<any[]>([])
</script>

<style scoped>
.page-title { font-size: 18px; font-weight: 600; margin-bottom: 16px; color: #1d2129; }
.mb-lg { margin-bottom: 16px; }
.text-tertiary { color: #86909c; } .font-12 { font-size: 12px; }
</style>
