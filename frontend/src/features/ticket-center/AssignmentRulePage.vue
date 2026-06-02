<template>
  <div class="p-6">
    <h2 class="page-title">分派规则</h2>
    <div class="autops-card mb-lg">
      <div class="autops-card-header">
        <div class="autops-card-title">规则列表</div>
        <el-button type="primary" size="small" @click="createRule"><el-icon><Plus /></el-icon> 新建规则</el-button>
      </div>
      <div class="autops-card-body" style="padding:0">
        <el-table :data="rules" stripe v-loading="loading" empty-text="暂无分派规则">
          <el-table-column prop="name" label="规则名称" min-width="180" show-overflow-tooltip />
          <el-table-column prop="condition" label="匹配条件" min-width="200" show-overflow-tooltip />
          <el-table-column prop="assign_to" label="分派给" width="120" />
          <el-table-column prop="priority" label="优先级" width="80" />
          <el-table-column prop="enabled" label="启用" width="60">
            <template #default="{ row }"><el-switch v-model="row.enabled" size="small" /></template>
          </el-table-column>
          <el-table-column label="操作" width="140" fixed="right">
            <template #default="{ row }">
              <el-button text type="primary" size="small" @click="editRule(row)">编辑</el-button>
              <el-button text type="danger" size="small" @click="deleteRule(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
    <el-dialog v-model="dialog" :title="editing ? '编辑规则' : '新建规则'" width="600">
      <el-form label-width="100px">
        <el-form-item label="规则名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="匹配条件">
          <el-select v-model="form.match_field" style="width:140px;margin-right:8px">
            <el-option label="告警级别" value="severity" /><el-option label="资产类型" value="asset_type" /><el-option label="来源" value="source" />
          </el-select>
          <el-input v-model="form.match_value" style="width:200px" placeholder="匹配值" />
        </el-form-item>
        <el-form-item label="分派给"><el-input v-model="form.assign_to" placeholder="处理人或组" /></el-form-item>
        <el-form-item label="优先级"><el-select v-model="form.priority" style="width:100%">
          <el-option label="最高" value="1" /><el-option label="高" value="2" /><el-option label="中" value="3" /><el-option label="低" value="4" />
        </el-select></el-form-item>
      </el-form>
      <template #footer><el-button @click="dialog=false">取消</el-button><el-button type="primary" @click="saveRule">保存</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from "vue"
import { Plus } from "@element-plus/icons-vue"
import { ElMessage } from "element-plus"

const loading = ref(false)
const rules = ref<any[]>([])
const dialog = ref(false)
const editing = ref(false)
const form = reactive({ name: "", match_field: "severity", match_value: "", assign_to: "", priority: "3" })

function createRule() { editing.value = false; dialog.value = true }
function editRule(row: any) { editing.value = true; dialog.value = true }
function deleteRule(row: any) { ElMessage.warning("确认删除？") }
function saveRule() { dialog.value = false; ElMessage.success("规则已保存") }
</script>

<style scoped>
.page-title { font-size: 18px; font-weight: 600; margin-bottom: 16px; color: #1d2129; }
.mb-lg { margin-bottom: 16px; }
</style>
