<template>
  <div class="autops-page-container">
    <!-- 页面头部 -->
    <div class="autops-page-header">
      <div class="autops-page-title">巡检模板</div>
      <div class="autops-page-desc">管理巡检模板，定义检查项和规则</div>
    </div>
    <div style="display: flex; justify-content: flex-end; margin-bottom: 16px">
      <el-button type="primary" @click="handleCreate">
        <el-icon><Plus /></el-icon> 新建模板
      </el-button>
    </div>

    <!-- 搜索栏 -->
    <div class="page-toolbar">
      <el-input
        v-model="searchQuery"
        placeholder="搜索模板名称..."
        clearable
        style="width: 260px"
        @keyup.enter="fetchList"
        @clear="fetchList"
      >
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
      <el-button type="default" @click="fetchList">
        <el-icon><Refresh /></el-icon> 刷新
      </el-button>
    </div>

    <!-- 数据表格 -->
    <el-table stripe :data="templates" v-loading="loading"empty-text="暂无巡检模板">
      <el-table-column prop="name" label="模板名称" min-width="180" show-overflow-tooltip />
      <el-table-column prop="check_type" label="检查类型" width="120">
        <template #default="{ row }">
          <el-tag size="small">{{ checkTypeLabel(row.check_type) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="asset_type" label="资产类型" width="120">
        <template #default="{ row }">
          <el-tag type="info" size="small">{{ assetTypeLabel(row.asset_type) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="check_items" label="检查项数" width="100" align="center">
        <template #default="{ row }">
          <span class="check-item-count">{{ row.check_items ?? 0 }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="170">
        <template #default="{ row }">
          <span class="text-tertiary">{{ formatTime(row.created_at) }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="description" label="描述" min-width="160" show-overflow-tooltip />
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button plain type="primary" size="small" @click="handleEdit(row)">编辑</el-button>
          <el-button plain type="danger" size="small" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="page-pagination">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.page_size"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        background
        @size-change="fetchList"
        @current-change="fetchList"
      />
    </div>

    <!-- 新建/编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑模板' : '新建模板'"
      width="600px"
      :close-on-click-modal="false"
      @closed="resetForm"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="90px"
        label-position="right"
      >
        <el-form-item label="模板名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入模板名称" maxlength="100" show-word-limit />
        </el-form-item>
        <el-form-item label="检查类型" prop="check_type">
          <el-select v-model="form.check_type" placeholder="请选择检查类型" style="width: 100%">
            <el-option label="基础巡检" value="basic" />
            <el-option label="指标采集" value="metrics" />
            <el-option label="日志巡检" value="logs" />
            <el-option label="配置巡检" value="config" />
            <el-option label="页面巡检" value="page" />
            <el-option label="基线巡检" value="baseline" />
            <el-option label="证书检查" value="certificate" />
            <el-option label="综合巡检" value="comprehensive" />
          </el-select>
        </el-form-item>
        <el-form-item label="资产类型" prop="asset_type">
          <el-select v-model="form.asset_type" placeholder="请选择资产类型" style="width: 100%">
            <el-option label="Linux 服务器" value="linux_server" />
            <el-option label="Windows 服务器" value="windows_server" />
            <el-option label="数据库" value="database" />
            <el-option label="Web 服务" value="web_service" />
            <el-option label="网络设备" value="network_device" />
            <el-option label="中间件" value="middleware" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="4"
            placeholder="请输入模板描述"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import type { TagType } from '@/shared/types'
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { Plus, Search, Refresh } from '@element-plus/icons-vue'
import { inspectionService } from '@/shared/api'

// ---------- 状态 ----------
const loading = ref(false)
const submitLoading = ref(false)
const dialogVisible = ref(false)
const isEditing = ref(false)
const editingId = ref<string>('')
const templates = ref<any[]>([])
const searchQuery = ref('')
const formRef = ref<FormInstance>()

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0,
})

const form = reactive({
  name: 'primary',
  check_type: 'primary',
  asset_type: 'primary',
  description: 'primary',
})

const formRules: FormRules = {
  name: [{ required: true, message: '请输入模板名称', trigger: 'blur' }],
  check_type: [{ required: true, message: '请选择检查类型', trigger: 'change' }],
  asset_type: [{ required: true, message: '请选择资产类型', trigger: 'change' }],
}

// ---------- 映射 ----------
const checkTypeMap: Record<string, string> = {
  basic: '基础巡检',
  metrics: '指标采集',
  logs: '日志巡检',
  config: '配置巡检',
  page: '页面巡检',
  baseline: '基线巡检',
  certificate: '证书检查',
  comprehensive: '综合巡检',
}

const assetTypeMap: Record<string, string> = {
  linux_server: 'Linux 服务器',
  windows_server: 'Windows 服务器',
  database: '数据库',
  web_service: 'Web 服务',
  network_device: '网络设备',
  middleware: '中间件',
}

function checkTypeLabel(val: string) {
  return checkTypeMap[val] || val || '-'
}

function assetTypeLabel(val: string) {
  return assetTypeMap[val] || val || '-'
}

function formatTime(val: string) {
  if (!val) return '-'
  return val
}

// ---------- API ----------
async function fetchList() {
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: pagination.page,
      page_size: pagination.page_size,
    }
    if (searchQuery.value.trim()) {
      params.name = searchQuery.value.trim()
    }
    const res = await inspectionService.listTemplates(params)
    const data = res.data?.data ?? res.data
    templates.value = data?.items ?? data ?? []
    pagination.total = data?.total ?? templates.value.length
  } catch (err: any) {
    ElMessage.error(err.message || '获取模板列表失败')
  } finally {
    loading.value = false
  }
}

async function createTemplate(data: Record<string, any>) {
  return inspectionService.createTemplate(data)
}

async function updateTemplate(id: string, data: Record<string, any>) {
  return inspectionService.updateTemplate(id, data)
}

async function deleteTemplate(id: string) {
  return inspectionService.deleteTemplate(id)
}

// ---------- 操作 ----------
function handleCreate() {
  isEditing.value = false
  editingId.value = ''
  dialogVisible.value = true
}

function handleEdit(row: any) {
  isEditing.value = true
  editingId.value = row.id
  form.name = row.name || ''
  form.check_type = row.check_type || ''
  form.asset_type = row.asset_type || ''
  form.description = row.description || ''
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitLoading.value = true
  try {
    const payload = {
      name: form.name,
      check_type: form.check_type,
      asset_type: form.asset_type,
      description: form.description,
    }
    if (isEditing.value) {
      await updateTemplate(editingId.value, payload)
      ElMessage.success('模板更新成功')
    } else {
      await createTemplate(payload)
      ElMessage.success('模板创建成功')
    }
    dialogVisible.value = false
    fetchList()
  } catch (err: any) {
    ElMessage.error(err.message || '操作失败')
  } finally {
    submitLoading.value = false
  }
}

async function handleDelete(row: any) {
  try {
    await ElMessageBox.confirm(
      '确定要删除模板「' + row.name + '」吗？此操作不可恢复。',
      '删除确认',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }
    )
    await deleteTemplate(row.id)
    ElMessage.success('模板已删除')
    fetchList()
  } catch (err: any) {
    if (err !== 'cancel') {
      ElMessage.error(err.message || '删除失败')
    }
  }
}

function resetForm() {
  form.name = ''
  form.check_type = ''
  form.asset_type = ''
  form.description = ''
  isEditing.value = false
  editingId.value = ''
  formRef.value?.resetFields()
}

// ---------- 初始化 ----------
onMounted(() => {
  fetchList()
})
</script>

<style scoped>

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--autops-space-lg);
}

.page-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: var(--autops-space-lg);
}
.page-pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: var(--autops-space-lg);
}
.text-tertiary {
  color: var(--autops-info);
  font-size: var(--autops-font-13);
}
.check-item-count {
  font-weight: 600;
  color: var(--autops-primary);
}
</style>
