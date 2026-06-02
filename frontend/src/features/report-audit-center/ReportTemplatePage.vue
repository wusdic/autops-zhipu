<template>
  <div class="p-6">
    <div class="page-header">
      <h2 class="page-title">报表模板</h2>
      <el-button type="primary" @click="showDialog = true"><el-icon><Plus /></el-icon> 新建模板</el-button>
    </div>
    <el-row :gutter="16">
      <el-col :xs="12" :sm="8" :md="6" v-for="tpl in templates" :key="tpl.id">
        <div class="template-card" @click="editTemplate(tpl)">
          <div class="template-icon" :style="{ background: tpl.bg }">
            <el-icon size="28" :color="tpl.color"><component :is="tpl.icon" /></el-icon>
          </div>
          <div class="template-name">{{ tpl.name }}</div>
          <div class="template-desc text-tertiary">{{ tpl.description }}</div>
          <div class="template-meta">
            <span>{{ tpl.sections }} 个章节</span>
            <el-tag size="small" :type="tpl.built_in ? 'info' : ''">{{ tpl.built_in ? '内置' : '自定义' }}</el-tag>
          </div>
        </div>
      </el-col>
    </el-row>
    <el-dialog v-model="showDialog" title="新建报表模板" width="560px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="模板名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="描述"><el-input type="textarea" v-model="form.description" /></el-form-item>
        <el-form-item label="报表章节">
          <el-checkbox-group v-model="form.sections">
            <el-checkbox label="概述" value="summary" /><el-checkbox label="资产统计" value="assets" />
            <el-checkbox label="巡检结果" value="inspection" /><el-checkbox label="告警汇总" value="alerts" />
            <el-checkbox label="SLA统计" value="sla" /><el-checkbox label="审计日志" value="audit" />
          </el-checkbox-group>
        </el-form-item>
      </el-form>
      <template #footer><el-button @click="showDialog=false">取消</el-button><el-button type="primary" @click="saveTemplate">确定</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from "vue"
import { Plus, Document, DataAnalysis, Warning, CircleCheck } from "@element-plus/icons-vue"

const showDialog = ref(false)
const form = reactive({ name: "", description: "", sections: [] as string[] })
const templates = ref([
  { id: "1", name: "巡检报告", description: "定期巡检结果汇总", sections: 5, built_in: true, icon: Document, bg: "#e8f3ff", color: "#165dff" },
  { id: "2", name: "资产台账", description: "资产清单与状态统计", sections: 4, built_in: true, icon: DataAnalysis, bg: "#e8ffea", color: "#00b42a" },
  { id: "3", name: "SLA报告", description: "服务等级达成率", sections: 3, built_in: true, icon: CircleCheck, bg: "#fff7e8", color: "#ff7d00" },
  { id: "4", name: "安全审计", description: "操作审计与安全事件", sections: 6, built_in: true, icon: Warning, bg: "#ffece8", color: "#f53f3f" },
])
function editTemplate(tpl: any) { /* TODO */ }
function saveTemplate() {
  templates.value.push({ id: Date.now().toString(), name: form.name, description: form.description, sections: form.sections.length, built_in: false, icon: Document, bg: "#f2f3f5", color: "#86909c" })
  showDialog.value = false
}
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-title { font-size: 18px; font-weight: 600; color: #1d2129; }
.template-card { background: #fff; border: 1px solid #e5e6eb; border-radius: 8px; padding: 20px; cursor: pointer; transition: all 0.2s; margin-bottom: 16px; }
.template-card:hover { border-color: #165dff; box-shadow: 0 2px 8px rgba(22,93,255,0.1); }
.template-icon { width: 48px; height: 48px; border-radius: 8px; display: flex; align-items: center; justify-content: center; margin-bottom: 12px; }
.template-name { font-size: 15px; font-weight: 600; color: #1d2129; margin-bottom: 4px; }
.template-desc { font-size: 12px; margin-bottom: 8px; }
.template-meta { display: flex; justify-content: space-between; align-items: center; font-size: 12px; color: #86909c; }
.text-tertiary { color: #86909c; }
</style>
