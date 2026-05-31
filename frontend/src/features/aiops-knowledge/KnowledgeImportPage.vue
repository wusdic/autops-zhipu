<template>
  <div class="knowledge-import">
    <div class="page-header">
      <el-button :icon="ArrowLeft" @click="$router.back()">返回</el-button>
      <h2 style="margin: 0 0 0 12px">知识库导入</h2>
    </div>

    <div style="margin-top: 16px">
      <el-tabs v-model="activeTab" type="border-card">
        <!-- 批量导入 -->
        <el-tab-pane label="批量导入" name="upload">
          <el-upload
            ref="uploadRef"
            drag
            :auto-upload="false"
            :limit="10"
            accept=".yaml,.yml,.json,.md"
            :on-change="handleFileChange"
            :file-list="fileList"
            multiple
          >
            <el-icon style="font-size: 48px; color: #c0c4cc"><UploadFilled /></el-icon>
            <div>拖拽文件到此处，或<em>点击上传</em></div>
            <template #tip>
              <div class="el-upload__tip">
                支持 YAML、JSON、Markdown 格式，单个文件不超过 5MB
              </div>
            </template>
          </el-upload>
          <el-button type="primary" style="margin-top: 16px" @click="startImport" :loading="importing" :disabled="!fileList.length">
            开始导入
          </el-button>
        </el-tab-pane>

        <!-- 粘贴导入 -->
        <el-tab-pane label="粘贴导入" name="paste">
          <el-form :model="pasteForm" label-width="100px">
            <el-form-item label="标题">
              <el-input v-model="pasteForm.title" placeholder="知识标题" />
            </el-form-item>
            <el-form-item label="分类">
              <el-select v-model="pasteForm.category" style="width: 100%">
                <el-option label="故障处置" value="troubleshooting" />
                <el-option label="操作指南" value="operation_guide" />
                <el-option label="最佳实践" value="best_practice" />
                <el-option label="配置参考" value="config_reference" />
                <el-option label="安全基线" value="security_baseline" />
              </el-select>
            </el-form-item>
            <el-form-item label="标签">
              <el-select v-model="pasteForm.tags" multiple filterable allow-create style="width: 100%" placeholder="输入标签">
                <el-option label="linux" value="linux" />
                <el-option label="windows" value="windows" />
                <el-option label="database" value="database" />
                <el-option label="web" value="web" />
                <el-option label="network" value="network" />
              </el-select>
            </el-form-item>
            <el-form-item label="内容">
              <el-input v-model="pasteForm.content" type="textarea" :rows="10" placeholder="Markdown 格式内容" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="submitPaste" :loading="importing">导入</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 标准方案导入 -->
        <el-tab-pane label="标准处置方案" name="standard">
          <p style="color: #666; margin-bottom: 16px">
            以下标准处置方案将批量导入知识库，关联对应的告警规则和自动化策略。
          </p>
          <el-table :data="standardSchemes" stripe>
            <el-table-column type="selection" width="55" />
            <el-table-column prop="title" label="方案名称" min-width="200" />
            <el-table-column prop="category" label="分类" width="120" />
            <el-table-column label="风险等级" width="100">
              <template #default="{ row }">
                <el-tag :type="row.risk_level === 'high' ? 'danger' : row.risk_level === 'medium' ? 'warning' : 'success'" size="small">
                  {{ row.risk_level }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag v-if="row.imported" type="success" size="small">已导入</el-tag>
                <el-tag v-else type="info" size="small">待导入</el-tag>
              </template>
            </el-table-column>
          </el-table>
          <el-button type="primary" style="margin-top: 16px" @click="importStandardSchemes" :loading="importing">
            批量导入选中方案
          </el-button>
        </el-tab-pane>
      </el-tabs>

      <!-- 导入结果 -->
      <el-dialog v-model="showResult" title="导入结果" width="600px">
        <el-result :icon="importResult.success > 0 ? 'success' : 'error'" :title="`成功 ${importResult.success} 条，失败 ${importResult.failed} 条`">
          <template #extra>
            <div v-if="importResult.errors.length">
              <h4>错误详情：</h4>
              <ul>
                <li v-for="(err, idx) in importResult.errors" :key="idx" style="color: #F56C6C">
                  {{ err }}
                </li>
              </ul>
            </div>
            <el-button type="primary" @click="showResult = false">确定</el-button>
          </template>
        </el-result>
      </el-dialog>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { ArrowLeft, UploadFilled } from '@element-plus/icons-vue'
import api from '@/shared/api/client'
import { API as R } from '@/shared/api/routes'
import type { UploadFile } from 'element-plus'

const activeTab = ref('upload')
const fileList = ref<UploadFile[]>([])
const importing = ref(false)
const showResult = ref(false)
const uploadRef = ref()

const importResult = reactive({
  success: 0,
  failed: 0,
  errors: [] as string[],
})

const pasteForm = reactive({
  title: '',
  category: 'troubleshooting',
  content: '',
  tags: [] as string[],
})

const standardSchemes = ref([
  { id: 'kb-linux-disk-high', title: 'Linux 磁盘空间异常处置', category: 'troubleshooting', risk_level: 'low', imported: false },
  { id: 'kb-windows-service-down', title: 'Windows 服务未运行处置', category: 'troubleshooting', risk_level: 'low', imported: false },
  { id: 'kb-web-port-unreachable', title: 'Web 端口不可达处置', category: 'troubleshooting', risk_level: 'medium', imported: false },
  { id: 'kb-db-conn-high', title: '数据库连接数过高处置', category: 'troubleshooting', risk_level: 'medium', imported: false },
  { id: 'kb-db-conn-failed', title: '数据库连接失败处置', category: 'troubleshooting', risk_level: 'high', imported: false },
  { id: 'kb-ssl-cert-expiring', title: 'SSL 证书即将过期处置', category: 'troubleshooting', risk_level: 'low', imported: false },
  { id: 'kb-collector-offline', title: '采集器离线处置', category: 'troubleshooting', risk_level: 'medium', imported: false },
  { id: 'kb-automation-failed', title: '自动化执行失败处置', category: 'troubleshooting', risk_level: 'high', imported: false },
])

function handleFileChange(file: UploadFile, files: UploadFile[]) {
  fileList.value = files
}

async function startImport() {
  importing.value = true
  importResult.success = 0
  importResult.failed = 0
  importResult.errors = []

  for (const file of fileList.value) {
    try {
      const raw = file.raw
      if (!raw) { importResult.failed++; continue }
      const text = await raw.text()
      let payload: any = { content: text, source: 'import', status: 'published' }

      // Parse YAML/JSON for structured knowledge
      if (raw.name.endsWith('.json')) {
        try {
          const parsed = JSON.parse(text)
          if (parsed.title) payload.title = parsed.title
          if (parsed.category) payload.category = parsed.category
          if (parsed.tags) payload.tags = parsed.tags
        } catch { /* use raw content */ }
      } else if (raw.name.endsWith('.yaml') || raw.name.endsWith('.yml')) {
        payload.title = raw.name.replace(/\.(yaml|yml)$/, '')
        payload.category = 'troubleshooting'
      } else if (raw.name.endsWith('.md')) {
        const titleMatch = text.match(/^#\s+(.+)/m)
        if (titleMatch) payload.title = titleMatch[1]
      }
      if (!payload.title) payload.title = raw.name

      const { data } = await api.post(R.KNOWLEDGE, payload)
      if (data.code === 0) {
        importResult.success++
      } else {
        importResult.failed++
        importResult.errors.push(`${raw.name}: ${data.message}`)
      }
    } catch (e: any) {
      importResult.failed++
      importResult.errors.push(`${file.name}: ${e.message || '未知错误'}`)
    }
  }

  importing.value = false
  showResult.value = true
  fileList.value = []
}

async function submitPaste() {
  if (!pasteForm.title || !pasteForm.content) {
    ElMessage.warning('请填写标题和内容')
    return
  }
  importing.value = true
  try {
    const { data } = await api.post(R.KNOWLEDGE, {
      title: pasteForm.title,
      content: pasteForm.content,
      category: pasteForm.category,
      tags: pasteForm.tags,
      source: 'manual',
      status: 'published',
    })
    if (data.code === 0) {
      ElMessage.success('导入成功')
      pasteForm.title = ''
      pasteForm.content = ''
      pasteForm.tags = []
    } else {
      ElMessage.error(data.message || '导入失败')
    }
  } catch {
    ElMessage.error('导入失败')
  } finally {
    importing.value = false
  }
}

async function importStandardSchemes() {
  importing.value = true
  importResult.success = 0
  importResult.failed = 0
  importResult.errors = []

  for (const scheme of standardSchemes.value) {
    if (scheme.imported) continue
    try {
      const { data } = await api.post(R.KNOWLEDGE, {
        title: scheme.title,
        content: `# ${scheme.title}\n\n## 触发条件\n- 资产类型: ${scheme.category}\n\n## 诊断步骤\n- 待补充\n\n## 处置动作\n- 待补充\n\n## 验证方法\n- 待补充`,
        category: scheme.category,
        source: 'standard',
        status: 'published',
        tags: ['standard', scheme.id],
      })
      if (data.code === 0) {
        importResult.success++
        scheme.imported = true
      } else {
        importResult.failed++
        importResult.errors.push(`${scheme.title}: ${data.message}`)
      }
    } catch (e: any) {
      importResult.failed++
      importResult.errors.push(`${scheme.title}: ${e.message || '未知错误'}`)
    }
  }

  importing.value = false
  if (importResult.failed > 0) showResult.value = true
  else ElMessage.success(`成功导入 ${importResult.success} 条标准方案`)
}

onMounted(() => {
  // Check which standard schemes already exist
  checkExisting()
})

async function checkExisting() {
  try {
    const { data } = await api.get(R.KNOWLEDGE, { params: { source: 'standard', page_size: 100 } })
    if (data.code === 0) {
      const items = data.data?.items || data.data || []
      const existingTags = new Set(items.flatMap((i: any) => i.tags || []))
      for (const scheme of standardSchemes.value) {
        scheme.imported = existingTags.has(scheme.id)
      }
    }
  } catch { /* ignore */ }
}
</script>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
}
</style>
