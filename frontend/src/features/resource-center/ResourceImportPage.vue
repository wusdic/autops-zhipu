<template>
  <div class="p-6">
    <h2 class="page-title">资源导入</h2>
    <el-row :gutter="24">
      <el-col :span="12">
        <div class="autops-card">
          <div class="autops-card-header"><div class="autops-card-title">上传文件</div></div>
          <div class="autops-card-body">
            <el-upload drag accept=".csv,.xlsx,.xls" :auto-upload="false" :on-change="handleFile" :limit="1">
              <el-icon size="48" color="#c9cdd4"><Upload /></el-icon>
              <div style="margin-top: 8px">将 Excel/CSV 文件拖到此处，或 <em>点击上传</em></div>
              <template #tip><div class="el-upload__tip">支持 .xlsx / .csv，最大 10MB</div></template>
            </el-upload>
            <el-divider />
            <el-button type="primary" :disabled="!uploadedFile" @click="startImport" :loading="importing">
              开始导入
            </el-button>
          </div>
        </div>
      </el-col>
      <el-col :span="12">
        <div class="autops-card">
          <div class="autops-card-header"><div class="autops-card-title">导入模板</div></div>
          <div class="autops-card-body">
            <p class="text-tertiary mb-md">请按以下格式准备导入文件：</p>
            <el-table :data="templateFields" stripe size="small">
              <el-table-column prop="field" label="字段名" /><el-table-column prop="required" label="必填" width="60" /><el-table-column prop="example" label="示例" />
            </el-table>
            <el-button style="margin-top: 16px" @click="downloadTemplate">下载导入模板</el-button>
          </div>
        </div>
      </el-col>
    </el-row>
    <!-- 导入结果 -->
    <div v-if="importResult" class="autops-card" style="margin-top: 16px">
      <div class="autops-card-header"><div class="autops-card-title">导入结果</div></div>
      <div class="autops-card-body">
        <el-result :icon="importResult.failed === 0 ? 'success' : 'warning'" :title="`成功导入 ${importResult.success} 条，失败 ${importResult.failed} 条`" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue"
import { Upload } from "@element-plus/icons-vue"
import { ElMessage } from "element-plus"

const uploadedFile = ref<File | null>(null)
const importing = ref(false)
const importResult = ref<{ success: number; failed: number } | null>(null)

const templateFields = ref([
  { field: "name", required: "是", example: "web-server-01" },
  { field: "asset_type", required: "是", example: "linux_server" },
  { field: "ip", required: "是", example: "192.168.1.100" },
  { field: "os_info", required: "否", example: "CentOS 7.9" },
  { field: "environment", required: "否", example: "production" },
  { field: "tags", required: "否", example: "web,nginx" },
])

function handleFile(file: any) { uploadedFile.value = file.raw }
function downloadTemplate() { ElMessage.info("模板下载功能开发中") }
async function startImport() {
  importing.value = true
  try { await new Promise(r => setTimeout(r, 1500)); importResult.value = { success: 0, failed: 0 }; ElMessage.success("导入完成") }
  finally { importing.value = false }
}
</script>

<style scoped>
.page-title { font-size: 18px; font-weight: 600; margin-bottom: 16px; color: #1d2129; }
.text-tertiary { color: #86909c; } .mb-md { margin-bottom: 12px; }
</style>
