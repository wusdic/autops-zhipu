<template>
  <div class="p-6">
    <h2 class="page-title">规则缺口分析</h2>
    <el-alert type="info" title="分析已有策略和知识的覆盖范围，识别未覆盖的故障场景" show-icon :closable="false" style="margin-bottom:16px" />
    <el-row :gutter="16" class="mb-lg">
      <el-col :span="16">
        <div class="autops-card">
          <div class="autops-card-header">
            <div class="autops-card-title">缺口列表</div>
            <el-button type="primary" size="small" @click="analyze" :loading="analyzing">执行分析</el-button>
          </div>
          <div class="autops-card-body" style="padding:0">
            <el-table :data="gaps" stripe size="small" empty-text="暂无缺口数据">
              <el-table-column prop="scenario" label="故障场景" min-width="200" show-overflow-tooltip />
              <el-table-column prop="asset_type" label="资产类型" width="100" />
              <el-table-column prop="event_count" label="历史发生" width="90" />
              <el-table-column prop="has_policy" label="有策略" width="70">
                <template #default="{ row }"><el-tag :type="row.has_policy ? 'success' : 'danger'" size="small">{{ row.has_policy ? '是' : '否' }}</el-tag></template>
              </el-table-column>
              <el-table-column prop="has_knowledge" label="有知识" width="70">
                <template #default="{ row }"><el-tag :type="row.has_knowledge ? 'success' : 'danger'" size="small">{{ row.has_knowledge ? '是' : '否' }}</el-tag></template>
              </el-table-column>
              <el-table-column prop="priority" label="优先级" width="80">
                <template #default="{ row }">
                  <el-tag :type="{ high:'danger', medium:'warning', low:'info' }[row.priority as string]" size="small">{{ row.priority }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="100">
                <template #default="{ row }">
                  <el-button text type="primary" size="small" @click="createPolicy(row)">补策略</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="autops-card">
          <div class="autops-card-header"><div class="autops-card-title">覆盖率</div></div>
          <div class="autops-card-body" style="text-align:center">
            <div style="font-size:36px;font-weight:700;color:#165dff;margin:20px 0">-</div>
            <div style="color:#86909c;margin-bottom:16px">策略+知识覆盖率</div>
            <el-descriptions :column="1" border size="small">
              <el-descriptions-item label="已覆盖场景">0</el-descriptions-item>
              <el-descriptions-item label="未覆盖场景">0</el-descriptions-item>
              <el-descriptions-item label="高优先级缺口">0</el-descriptions-item>
            </el-descriptions>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue"
import { ElMessage } from "element-plus"

const analyzing = ref(false)
const gaps = ref<any[]>([])

async function analyze() { analyzing.value = true; await new Promise(r => setTimeout(r, 2000)); analyzing.value = false; ElMessage.info("分析完成") }
function createPolicy(row: any) { ElMessage.info("跳转策略创建") }
</script>

<style scoped>
.page-title { font-size: 18px; font-weight: 600; margin-bottom: 16px; color: #1d2129; }
.mb-lg { margin-bottom: 16px; }
</style>
