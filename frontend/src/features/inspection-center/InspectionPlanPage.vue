<template>
  <div class="p-6">
    <div class="page-header">
      <h2 class="page-title">巡检计划</h2>
      <el-button type="primary" @click="showDialog = true"><el-icon><Plus /></el-icon> 新建计划</el-button>
    </div>
    <el-table :data="plans" stripe v-loading="loading" empty-text="暂无巡检计划">
      <el-table-column prop="name" label="计划名称" min-width="180" show-overflow-tooltip />
      <el-table-column prop="template_name" label="巡检模板" width="150" />
      <el-table-column prop="cron" label="执行周期" width="120" />
      <el-table-column prop="asset_scope" label="资产范围" min-width="160" show-overflow-tooltip />
      <el-table-column prop="enabled" label="启用" width="70">
        <template #default="{ row }">
          <el-switch v-model="row.enabled" size="small" />
        </template>
      </el-table-column>
      <el-table-column prop="next_run" label="下次执行" width="160">
        <template #default="{ row }"><span class="text-tertiary">{{ row.next_run || "-" }}</span></template>
      </el-table-column>
      <el-table-column label="操作" width="140" fixed="right">
        <template #default="{ row }">
          <el-button text type="primary" size="small" @click="editPlan(row)">编辑</el-button>
          <el-button text type="danger" size="small" @click="deletePlan(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-dialog v-model="showDialog" :title="editing ? '编辑计划' : '新建计划'" width="560px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="计划名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="巡检模板"><el-select v-model="form.template_name"><el-option label="Linux基础巡检" value="linux-basic" /><el-option label="Web服务巡检" value="web-basic" /><el-option label="数据库巡检" value="db-basic" /></el-select></el-form-item>
        <el-form-item label="执行周期"><el-input v-model="form.cron" placeholder="如: 0 8 * * * (每天8:00)" /></el-form-item>
        <el-form-item label="资产范围"><el-input v-model="form.asset_scope" placeholder="资产组、标签或IP范围" /></el-form-item>
        <el-form-item label="失败重试"><el-input-number v-model="form.retry_count" :min="0" :max="3" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="showDialog=false">取消</el-button><el-button type="primary" @click="savePlan">确定</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from "vue"
import { Plus } from "@element-plus/icons-vue"

const loading = ref(false)
const plans = ref<any[]>([])
const showDialog = ref(false)
const editing = ref<any>(null)
const form = reactive({ name: "", template_name: "", cron: "0 8 * * *", asset_scope: "", retry_count: 1 })

function editPlan(row: any) { editing.value = row; Object.assign(form, row); showDialog.value = true }
function deletePlan(row: any) { plans.value = plans.value.filter(p => p !== row) }
function savePlan() {
  if (editing.value) { Object.assign(editing.value, form) }
  else { plans.value.push({ ...form, id: Date.now().toString(), enabled: true, next_run: "-" }) }
  showDialog.value = false; editing.value = null
}
onMounted(() => { loading.value = false })
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-title { font-size: 18px; font-weight: 600; color: #1d2129; }
.text-tertiary { color: #86909c; font-size: 12px; }
</style>
