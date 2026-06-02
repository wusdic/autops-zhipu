<template>
  <div class="p-6">
    <h2 class="page-title">今日摘要</h2>
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
      <el-col :span="12">
        <div class="autops-card">
          <div class="autops-card-header"><div class="autops-card-title">今日事件</div></div>
          <div class="autops-card-body" style="padding:0">
            <el-table :data="todayEvents" stripe size="small" empty-text="今日暂无事件">
              <el-table-column prop="time" label="时间" width="80" />
              <el-table-column prop="type" label="类型" width="80">
                <template #default="{ row }"><el-tag :type="eventTypeColor(row.type)" size="small">{{ row.type }}</el-tag></template>
              </el-table-column>
              <el-table-column prop="summary" label="摘要" min-width="200" show-overflow-tooltip />
            </el-table>
          </div>
        </div>
      </el-col>
      <el-col :span="12">
        <div class="autops-card">
          <div class="autops-card-header"><div class="autops-card-title">今日执行</div></div>
          <div class="autops-card-body" style="padding:0">
            <el-table :data="todayExecutions" stripe size="small" empty-text="今日暂无执行">
              <el-table-column prop="time" label="时间" width="80" />
              <el-table-column prop="name" label="任务" min-width="160" show-overflow-tooltip />
              <el-table-column prop="status" label="状态" width="80">
                <template #default="{ row }">
                  <el-tag :type="{ success:'success', failed:'danger', running:'warning' }[row.status as string]" size="small">{{ row.status }}</el-tag>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue"
import { Warning, CircleCheck, VideoPlay, Document } from "@element-plus/icons-vue"

const statCards = reactive([
  { label: "今日告警", value: 0, icon: Warning, bg: "#ffece8", color: "#f53f3f" },
  { label: "自动处置", value: 0, icon: VideoPlay, bg: "#e8f3ff", color: "#165dff" },
  { label: "已解决", value: 0, icon: CircleCheck, bg: "#e8ffea", color: "#00b42a" },
  { label: "巡检完成", value: 0, icon: Document, bg: "#fff7e8", color: "#ff7d00" },
])
const todayEvents = ref<any[]>([])
const todayExecutions = ref<any[]>([])

function eventTypeColor(t: string) { return ({ alert: "danger", inspection: "warning", execution: "", system: "info" } as any)[t] || "info" }
</script>

<style scoped>
.page-title { font-size: 18px; font-weight: 600; margin-bottom: 16px; color: #1d2129; }
.mb-lg { margin-bottom: 16px; }
</style>
