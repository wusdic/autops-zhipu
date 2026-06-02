<template>
  <div class="p-6">
    <h2 class="page-title">SLA 管理</h2>
    <div class="autops-card mb-lg">
      <div class="autops-card-header">
        <div class="autops-card-title">SLA 策略</div>
        <el-button type="primary" size="small" @click="createPolicy"><el-icon><Plus /></el-icon> 新建SLA策略</el-button>
      </div>
      <div class="autops-card-body" style="padding:0">
        <el-table :data="policies" stripe v-loading="loading" empty-text="暂无SLA策略">
          <el-table-column prop="name" label="策略名称" min-width="160" show-overflow-tooltip />
          <el-table-column prop="ticket_type" label="工单类型" width="100" />
          <el-table-column prop="priority" label="优先级" width="80" />
          <el-table-column prop="response_time" label="响应时间" width="100" />
          <el-table-column prop="resolve_time" label="解决时间" width="100" />
          <el-table-column prop="escalation" label="升级规则" width="120" />
          <el-table-column prop="enabled" label="启用" width="60">
            <template #default="{ row }"><el-switch v-model="row.enabled" size="small" /></template>
          </el-table-column>
          <el-table-column label="操作" width="140" fixed="right">
            <template #default="{ row }">
              <el-button text type="primary" size="small" @click="editPolicy(row)">编辑</el-button>
              <el-button text type="danger" size="small" @click="deletePolicy(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
    <div class="autops-card">
      <div class="autops-card-header"><div class="autops-card-title">SLA 达成统计</div></div>
      <div class="autops-card-body">
        <el-row :gutter="16">
          <el-col :span="6"><div class="sla-stat"><div class="sla-value">-</div><div class="sla-label">总体达成率</div></div></el-col>
          <el-col :span="6"><div class="sla-stat"><div class="sla-value">0</div><div class="sla-label">即将超时</div></div></el-col>
          <el-col :span="6"><div class="sla-stat"><div class="sla-value" style="color:#f53f3f">0</div><div class="sla-label">已超时</div></div></el-col>
          <el-col :span="6"><div class="sla-stat"><div class="sla-value" style="color:#00b42a">0</div><div class="sla-label">按时完成</div></div></el-col>
        </el-row>
      </div>
    </div>
    <el-dialog v-model="dialog" :title="editing ? '编辑SLA策略' : '新建SLA策略'" width="500">
      <el-form label-width="100px">
        <el-form-item label="策略名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="工单类型"><el-select v-model="form.ticket_type" style="width:100%">
          <el-option label="故障" value="fault" /><el-option label="告警" value="alert" /><el-option label="变更" value="change" />
        </el-select></el-form-item>
        <el-form-item label="优先级"><el-select v-model="form.priority" style="width:100%">
          <el-option label="紧急" value="urgent" /><el-option label="高" value="high" /><el-option label="中" value="medium" /><el-option label="低" value="low" />
        </el-select></el-form-item>
        <el-form-item label="响应时间(分)"><el-input-number v-model="form.response_time" :min="5" /></el-form-item>
        <el-form-item label="解决时间(分)"><el-input-number v-model="form.resolve_time" :min="15" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="dialog=false">取消</el-button><el-button type="primary" @click="savePolicy">保存</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from "vue"
import { Plus } from "@element-plus/icons-vue"
import { ElMessage } from "element-plus"

const loading = ref(false)
const policies = ref<any[]>([])
const dialog = ref(false)
const editing = ref(false)
const form = reactive({ name: "", ticket_type: "fault", priority: "high", response_time: 30, resolve_time: 240 })

function createPolicy() { editing.value = false; dialog.value = true }
function editPolicy(row: any) { editing.value = true; dialog.value = true }
function deletePolicy(row: any) { ElMessage.warning("确认删除？") }
function savePolicy() { dialog.value = false; ElMessage.success("SLA策略已保存") }
</script>

<style scoped>
.page-title { font-size: 18px; font-weight: 600; margin-bottom: 16px; color: #1d2129; }
.mb-lg { margin-bottom: 16px; }
.sla-stat { text-align: center; padding: 12px; }
.sla-value { font-size: 28px; font-weight: 700; color: #165dff; }
.sla-label { font-size: 13px; color: #86909c; margin-top: 4px; }
</style>
