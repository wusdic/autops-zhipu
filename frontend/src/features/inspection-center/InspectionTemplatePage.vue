<template>
  <div class="p-6">
    <div class="page-header">
      <h2 class="page-title">巡检模板</h2>
      <el-button type="primary" @click="showDialog = true"><el-icon><Plus /></el-icon> 新建模板</el-button>
    </div>
    <el-table :data="templates" stripe v-loading="loading" empty-text="暂无巡检模板">
      <el-table-column prop="name" label="模板名称" min-width="180" show-overflow-tooltip />
      <el-table-column prop="asset_types" label="适用资产" width="160">
        <template #default="{ row }"><el-tag v-for="t in (row.asset_types || [])" :key="t" size="small" style="margin-right:4px">{{ t }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="check_items" label="巡检项数" width="90" />
      <el-table-column prop="modules" label="巡检模块" min-width="200">
        <template #default="{ row }"><el-tag v-for="m in (row.modules || [])" :key="m" size="small" type="info" style="margin-right:4px">{{ m }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="updated_at" label="更新时间" width="160">
        <template #default="{ row }"><span class="text-tertiary">{{ row.updated_at }}</span></template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button text type="primary" size="small" @click="editTemplate(row)">编辑</el-button>
          <el-button text type="success" size="small" @click="cloneTemplate(row)">克隆</el-button>
          <el-button text type="danger" size="small" @click="deleteTemplate(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-dialog v-model="showDialog" :title="editing ? '编辑模板' : '新建模板'" width="640px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="模板名称"><el-input v-model="form.name" placeholder="如：Linux基础巡检" /></el-form-item>
        <el-form-item label="适用资产">
          <el-select v-model="form.asset_types" multiple><el-option label="Linux服务器" value="linux_server" /><el-option label="Windows服务器" value="windows_server" /><el-option label="数据库" value="database" /><el-option label="Web服务" value="web_service" /></el-select>
        </el-form-item>
        <el-form-item label="巡检模块">
          <el-checkbox-group v-model="form.modules">
            <el-checkbox label="指标采集" value="metrics" /><el-checkbox label="日志巡检" value="logs" /><el-checkbox label="配置巡检" value="config" />
            <el-checkbox label="页面巡检" value="page" /><el-checkbox label="基线巡检" value="baseline" /><el-checkbox label="证书检查" value="certificate" />
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="描述"><el-input type="textarea" v-model="form.description" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="showDialog=false">取消</el-button><el-button type="primary" @click="saveTemplate">确定</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from "vue"
import { Plus } from "@element-plus/icons-vue"

const loading = ref(false)
const templates = ref<any[]>([])
const showDialog = ref(false)
const editing = ref<any>(null)
const form = reactive({ name: "", asset_types: [] as string[], modules: [] as string[], description: "" })

function editTemplate(row: any) { editing.value = row; Object.assign(form, row); showDialog.value = true }
function cloneTemplate(row: any) { templates.value.push({ ...row, id: Date.now().toString(), name: row.name + " (副本)" }) }
function deleteTemplate(row: any) { templates.value = templates.value.filter(t => t !== row) }
function saveTemplate() {
  if (editing.value) { Object.assign(editing.value, form) }
  else { templates.value.push({ ...form, id: Date.now().toString(), check_items: 0, updated_at: new Date().toLocaleDateString("zh-CN") }) }
  showDialog.value = false; editing.value = null; Object.assign(form, { name: "", asset_types: [], modules: [], description: "" })
}
onMounted(() => { loading.value = false })
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-title { font-size: 18px; font-weight: 600; color: #1d2129; }
.text-tertiary { color: #86909c; font-size: 12px; }
</style>
