<template>
  <div class="p-6">
    <h2 class="page-title">Prompt 模板</h2>
    <div class="autops-card mb-lg">
      <div class="autops-card-header">
        <div class="autops-card-title">模板列表</div>
        <el-button type="primary" size="small" @click="createTemplate"><el-icon><Plus /></el-icon> 新建模板</el-button>
      </div>
      <div class="autops-card-body" style="padding:0">
        <el-table :data="templates" stripe v-loading="loading" empty-text="暂无模板">
          <el-table-column prop="name" label="模板名称" min-width="180" show-overflow-tooltip />
          <el-table-column prop="scene" label="使用场景" width="120" />
          <el-table-column prop="model" label="适用模型" width="120" />
          <el-table-column prop="version" label="版本" width="60" />
          <el-table-column prop="updated_at" label="更新时间" width="140" />
          <el-table-column label="操作" width="160" fixed="right">
            <template #default="{ row }">
              <el-button text type="primary" size="small" @click="editTemplate(row)">编辑</el-button>
              <el-button text size="small" @click="testTemplate(row)">测试</el-button>
              <el-button text type="danger" size="small" @click="deleteTemplate(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
    <el-dialog v-model="dialog" :title="editing ? '编辑模板' : '新建模板'" width="700">
      <el-form label-width="90px">
        <el-form-item label="模板名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="使用场景"><el-select v-model="form.scene" style="width:100%">
          <el-option label="根因分析" value="root_cause" /><el-option label="日志解读" value="log_interpret" />
          <el-option label="处置建议" value="remediation" /><el-option label="知识提取" value="knowledge_extract" />
        </el-select></el-form-item>
        <el-form-item label="适用模型"><el-input v-model="form.model" placeholder="留空表示通用" /></el-form-item>
        <el-form-item label="System Prompt"><el-input type="textarea" v-model="form.system_prompt" :rows="4" /></el-form-item>
        <el-form-item label="User Prompt"><el-input type="textarea" v-model="form.user_prompt" :rows="6" placeholder="使用 {{variable}} 作为变量占位符" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="dialog=false">取消</el-button><el-button type="primary" @click="saveTemplate">保存</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from "vue"
import { Plus } from "@element-plus/icons-vue"
import { ElMessage } from "element-plus"

const loading = ref(false)
const templates = ref<any[]>([])
const dialog = ref(false)
const editing = ref(false)
const form = reactive({ name: "", scene: "", model: "", system_prompt: "", user_prompt: "" })

function createTemplate() { editing.value = false; Object.assign(form, { name: "", scene: "", model: "", system_prompt: "", user_prompt: "" }); dialog.value = true }
function editTemplate(row: any) { editing.value = true; Object.assign(form, row); dialog.value = true }
function testTemplate(row: any) { ElMessage.info("测试功能开发中") }
function deleteTemplate(row: any) { ElMessage.warning("确认删除？") }
function saveTemplate() { dialog.value = false; ElMessage.success("模板已保存") }
</script>

<style scoped>
.page-title { font-size: 18px; font-weight: 600; margin-bottom: 16px; color: #1d2129; }
.mb-lg { margin-bottom: 16px; }
</style>
