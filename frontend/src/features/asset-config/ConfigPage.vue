<template>
  <div>
    <el-card>
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span>配置管理</span>
          <div>
            <el-select v-model="configType" placeholder="配置类型" style="width:160px;margin-right:8px" @change="loadConfigs">
              <el-option label="采集模板" value="collection_template" />
              <el-option label="策略配置" value="policy_config" />
              <el-option label="通知配置" value="notification" />
              <el-option label="系统参数" value="system" />
            </el-select>
            <el-button type="primary" size="small" @click="showCreateDialog = true">新建配置</el-button>
          </div>
        </div>
      </template>

      <el-table :data="configs" v-loading="loading" stripe>
        <el-table-column prop="config_key" label="配置键" min-width="180" show-overflow-tooltip />
        <el-table-column prop="config_value" label="配置值" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <code style="font-size:12px">{{ truncate(row.config_value, 60) }}</code>
          </template>
        </el-table-column>
        <el-table-column prop="config_type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag size="small">{{ row.config_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="version" label="版本" width="60" />
        <el-table-column prop="is_active" label="激活" width="60">
          <template #default="{ row }">{{ row.is_active ? '✅' : '❌' }}</template>
        </el-table-column>
        <el-table-column prop="updated_at" label="更新时间" width="160">
          <template #default="{ row }">{{ formatTime(row.updated_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="editConfig(row)">编辑</el-button>
            <el-button size="small" type="warning" @click="viewHistory(row)">历史</el-button>
            <el-button size="small" type="danger" @click="deleteConfig(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建/编辑对话框 -->
    <el-dialog v-model="showCreateDialog" :title="editingConfig ? '编辑配置' : '新建配置'" width="500px">
      <el-form :model="configForm" label-width="80px">
        <el-form-item label="配置键">
          <el-input v-model="configForm.config_key" :disabled="!!editingConfig" />
        </el-form-item>
        <el-form-item label="配置值">
          <el-input type="textarea" v-model="configForm.config_value" :rows="6" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="configForm.config_type">
            <el-option label="采集模板" value="collection_template" />
            <el-option label="策略配置" value="policy_config" />
            <el-option label="通知配置" value="notification" />
            <el-option label="系统参数" value="system" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="configForm.description" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="saveConfig" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/shared/api/client'
import { API as R } from '@/shared/api/routes'

const loading = ref(false)
const saving = ref(false)
const configs = ref<any[]>([])
const configType = ref('')
const showCreateDialog = ref(false)
const editingConfig = ref<any>(null)
const configForm = reactive({ config_key: '', config_value: '', config_type: 'system', description: '' })
const API = R.CONFIGS

function formatTime(t: string) { return t ? new Date(t).toLocaleString('zh-CN') : '' }
function truncate(s: string, n: number) { return s && s.length > n ? s.substring(0, n) + '...' : s }

async function loadConfigs() {
  loading.value = true
  try {
    const params: any = { page: 1, page_size: 100 }
    if (configType.value) params.config_type = configType.value
    const { data } = await api.get(API, { params })
    if (data.code === 0) configs.value = data.data.items || []
  } finally { loading.value = false }
}

function editConfig(row: any) {
  editingConfig.value = row
  Object.assign(configForm, { config_key: row.config_key, config_value: row.config_value, config_type: row.config_type, description: row.description || '' })
  showCreateDialog.value = true
}

function viewHistory(row: any) {
  ElMessage.info(`配置 ${row.config_key} 版本历史: v1 → v${row.version}`)
}

async function saveConfig() {
  saving.value = true
  try {
    if (editingConfig.value) {
      const { data } = await api.put(`${API}/${editingConfig.value.id}`, configForm)
      if (data.code === 0) ElMessage.success('已更新')
    } else {
      const { data } = await api.post(API, configForm)
      if (data.code === 0) ElMessage.success('已创建')
    }
    showCreateDialog.value = false
    editingConfig.value = null
    loadConfigs()
  } finally { saving.value = false }
}

async function deleteConfig(id: string) {
  await ElMessageBox.confirm('确定删除此配置？', '确认', { type: 'warning' })
  const { data } = await api.delete(`${API}/${id}`)
  if (data.code === 0) { ElMessage.success('已删除'); loadConfigs() }
}

onMounted(() => loadConfigs())
</script>
