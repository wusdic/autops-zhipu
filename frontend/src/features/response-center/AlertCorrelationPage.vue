<template>
  <div class="p-6">
    <div class="page-header">
      <h2 class="page-title">告警收敛</h2>
      <el-button type="primary" @click="runCorrelation" :loading="loading">执行收敛分析</el-button>
    </div>
    <el-row :gutter="16" style="margin-top:16px">
      <el-col :span="14">
        <div class="autops-card">
          <div class="autops-card-header"><div class="autops-card-title">收敛结果</div></div>
          <div class="autops-card-body" style="padding:0">
            <el-table :data="correlationGroups" stripe size="small" empty-text="暂无收敛结果">
              <el-table-column type="expand">
                <template #default="{ row }">
                  <el-table :data="row.alerts" size="small" style="margin:8px 16px">
                    <el-table-column prop="title" label="告警" min-width="200" />
                    <el-table-column prop="severity" label="级别" width="70" />
                    <el-table-column prop="asset" label="资产" width="120" />
                    <el-table-column prop="time" label="时间" width="140" />
                  </el-table>
                </template>
              </el-table-column>
              <el-table-column prop="group_name" label="收敛组" min-width="160" show-overflow-tooltip />
              <el-table-column prop="alert_count" label="告警数" width="80" />
              <el-table-column prop="root_alert" label="根因告警" min-width="160" show-overflow-tooltip />
              <el-table-column prop="status" label="状态" width="80">
                <template #default="{ row }">
                  <el-tag :type="row.status === 'confirmed' ? 'success' : 'warning'" size="small">{{ row.status }}</el-tag>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </el-col>
      <el-col :span="10">
        <div class="autops-card">
          <div class="autops-card-header"><div class="autops-card-title">收敛统计</div></div>
          <div class="autops-card-body">
            <el-descriptions :column="1" border size="small">
              <el-descriptions-item label="原始告警数">0</el-descriptions-item>
              <el-descriptions-item label="收敛后组数">0</el-descriptions-item>
              <el-descriptions-item label="压缩比">-</el-descriptions-item>
              <el-descriptions-item label="涉及资产">0</el-descriptions-item>
            </el-descriptions>
          </div>
        </div>
        <div class="autops-card" style="margin-top:16px">
          <div class="autops-card-header"><div class="autops-card-title">收敛规则</div></div>
          <div class="autops-card-body">
            <el-checkbox-group v-model="activeRules">
              <div style="display:flex;flex-direction:column;gap:8px">
                <el-checkbox label="相同资产" value="same_asset" />
                <el-checkbox label="时间窗口(5分钟)" value="time_window" />
                <el-checkbox label="相同告警类型" value="same_type" />
                <el-checkbox label="拓扑关联" value="topology" />
              </div>
            </el-checkbox-group>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue"
import { ElMessage } from "element-plus"

const loading = ref(false)
const correlationGroups = ref<any[]>([])
const activeRules = ref(["same_asset", "time_window"])

async function runCorrelation() {
  loading.value = true
  try { await new Promise(r => setTimeout(r, 1500)); ElMessage.info("收敛分析完成") }
  finally { loading.value = false }
}
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0; }
.page-title { font-size: 18px; font-weight: 600; color: #1d2129; }
</style>
