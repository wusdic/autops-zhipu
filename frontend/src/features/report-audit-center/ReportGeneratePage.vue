<template>
  <div class="p-6">
    <h2 class="page-title">生成报表</h2>
    <div class="autops-card" style="max-width: 680px">
      <div class="autops-card-body">
        <el-form :model="form" label-width="100px">
          <el-form-item label="报表模板">
            <el-select v-model="form.template_id"><el-option v-for="t in templateList" :key="t.value" :label="t.label" :value="t.value" /></el-select>
          </el-form-item>
          <el-form-item label="报表标题"><el-input v-model="form.title" placeholder="输入报表标题" /></el-form-item>
          <el-form-item label="时间范围">
            <el-date-picker v-model="form.date_range" type="daterange" range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期" />
          </el-form-item>
          <el-form-item label="资产范围"><el-input v-model="form.asset_scope" placeholder="全部 / 资产组 / 指定资产" /></el-form-item>
          <el-form-item label="输出格式">
            <el-radio-group v-model="form.format"><el-radio value="pdf">PDF</el-radio><el-radio value="html">HTML</el-radio><el-radio value="xlsx">Excel</el-radio></el-radio-group>
          </el-form-item>
          <el-form-item><el-button type="primary" @click="generate" :loading="generating">生成报表</el-button></el-form-item>
        </el-form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from "vue"
import { ElMessage } from "element-plus"

const generating = ref(false)
const form = reactive({ template_id: "inspection", title: "", date_range: null as any, asset_scope: "", format: "pdf" })
const templateList = [
  { label: "巡检报告", value: "inspection" }, { label: "资产台账", value: "assets" },
  { label: "SLA报告", value: "sla" }, { label: "安全审计", value: "audit" },
]
async function generate() {
  generating.value = true
  try { await new Promise(r => setTimeout(r, 1500)); ElMessage.success("报表生成任务已提交") }
  finally { generating.value = false }
}
</script>

<style scoped>
.page-title { font-size: 18px; font-weight: 600; margin-bottom: 16px; color: #1d2129; }
</style>
