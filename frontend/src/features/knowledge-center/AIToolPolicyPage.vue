<template>
  <div class="p-6">
    <h2 class="page-title">AI 工具调用策略</h2>
    <el-alert type="warning" title="AI工具调用策略控制AI可执行的操作边界，确保AI不会绕过安全限制" show-icon :closable="false" style="margin-bottom:16px" />
    <div class="autops-card mb-lg">
      <div class="autops-card-header">
        <div class="autops-card-title">工具白名单</div>
        <el-button type="primary" size="small" @click="addTool"><el-icon><Plus /></el-icon> 添加工具</el-button>
      </div>
      <div class="autops-card-body" style="padding:0">
        <el-table :data="tools" stripe size="small" empty-text="暂无工具配置">
          <el-table-column prop="name" label="工具名称" min-width="160" show-overflow-tooltip />
          <el-table-column prop="category" label="分类" width="100" />
          <el-table-column prop="permission" label="权限" width="100">
            <template #default="{ row }">
              <el-tag :type="{ readonly:'success', execute:'warning', admin:'danger' }[row.permission as string]" size="small">{{ row.permission }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="risk_level" label="风险等级" width="80">
            <template #default="{ row }">
              <el-tag :type="{ low:'success', medium:'warning', high:'danger' }[row.risk_level as string]" size="small">{{ row.risk_level }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="requires_approval" label="需审批" width="70">
            <template #default="{ row }"><el-tag :type="row.requires_approval ? 'danger' : 'success'" size="small">{{ row.requires_approval ? '是' : '否' }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="enabled" label="启用" width="60">
            <template #default="{ row }"><el-switch v-model="row.enabled" size="small" /></template>
          </el-table-column>
          <el-table-column label="操作" width="80">
            <template #default="{ row }"><el-button text type="primary" size="small" @click="editTool(row)">编辑</el-button></template>
          </el-table-column>
        </el-table>
      </div>
    </div>
    <div class="autops-card">
      <div class="autops-card-header"><div class="autops-card-title">调用审计日志</div></div>
      <div class="autops-card-body" style="padding:0">
        <el-table :data="auditLogs" stripe size="small" empty-text="暂无调用记录">
          <el-table-column prop="time" label="时间" width="160" />
          <el-table-column prop="tool_name" label="工具" width="140" />
          <el-table-column prop="ai_session" label="AI会话" width="120" />
          <el-table-column prop="action" label="动作" min-width="200" show-overflow-tooltip />
          <el-table-column prop="result" label="结果" width="80">
            <template #default="{ row }"><el-tag :type="row.result === 'success' ? 'success' : 'danger'" size="small">{{ row.result }}</el-tag></template>
          </el-table-column>
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue"
import { Plus } from "@element-plus/icons-vue"
import { ElMessage } from "element-plus"

const tools = ref([
  { name: "query_asset", category: "资产查询", permission: "readonly", risk_level: "low", requires_approval: false, enabled: true },
  { name: "query_log", category: "日志查询", permission: "readonly", risk_level: "low", requires_approval: false, enabled: true },
  { name: "query_alert", category: "告警查询", permission: "readonly", risk_level: "low", requires_approval: false, enabled: true },
  { name: "execute_command", category: "命令执行", permission: "execute", risk_level: "high", requires_approval: true, enabled: false },
  { name: "create_ticket", category: "工单创建", permission: "execute", risk_level: "medium", requires_approval: false, enabled: true },
])
const auditLogs = ref<any[]>([])

function addTool() { ElMessage.info("添加工具") }
function editTool(row: any) { ElMessage.info("编辑工具") }
</script>

<style scoped>
.page-title { font-size: 18px; font-weight: 600; margin-bottom: 16px; color: #1d2129; }
.mb-lg { margin-bottom: 16px; }
</style>
