<template>
  <div class="page-container">
    <div class="page-header">
      <h2>系统配置</h2>
      <el-button type="primary" @click="loadConfigs" :loading="loading">刷新</el-button>
    </div>

    <el-table :data="configs" v-loading="loading" stripe border style="width: 100%">
      <el-table-column prop="key" label="参数 Key" width="260">
        <template #default="{ row }">
          <code style="font-size: 13px">{{ row.key }}</code>
        </template>
      </el-table-column>
      <el-table-column label="Value" min-width="300">
        <template #default="{ row }">
          <div v-if="editingKey === row.key" class="inline-edit">
            <el-input v-model="editValue" size="small" style="flex: 1" @keyup.enter="saveEdit(row)" />
            <el-button size="small" type="primary" @click="saveEdit(row)" :loading="saving">保存</el-button>
            <el-button size="small" @click="cancelEdit">取消</el-button>
          </div>
          <div v-else class="value-cell">
            <span class="value-text">{{ row.value }}</span>
            <el-button size="small" link type="primary" @click="startEdit(row)">
              <el-icon><Edit /></el-icon>
            </el-button>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="description" label="描述" min-width="200" />
      <el-table-column prop="updated_at" label="更新时间" width="180" />
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Edit } from '@element-plus/icons-vue'
import api from '@/shared/api/client'
import { API as R } from '@/shared/api/routes'

const loading = ref(false)
const saving = ref(false)
const configs = ref<any[]>([])
const editingKey = ref('')
const editValue = ref('')

async function loadConfigs() {
  loading.value = true
  try {
    const { data } = await api.get(R.CONFIGS)
    if (data.code === 0) {
      configs.value = data.data.items || data.data || []
    }
  } catch (e: any) {
    ElMessage.error('加载系统配置失败')
  } finally {
    loading.value = false
  }
}

function startEdit(row: any) {
  editingKey.value = row.key
  editValue.value = row.value
}

function cancelEdit() {
  editingKey.value = ''
  editValue.value = ''
}

async function saveEdit(row: any) {
  saving.value = true
  try {
    await api.put(R.CONFIG_DETAIL(row.id || row.key), { value: editValue.value })
    row.value = editValue.value
    editingKey.value = ''
    ElMessage.success('配置已更新')
    loadConfigs()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.message || '更新失败')
  } finally {
    saving.value = false
  }
}

onMounted(() => { loadConfigs() })
</script>

<style scoped>
.page-container { padding: 20px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h2 { margin: 0; font-size: 20px; color: #303133; }
.inline-edit { display: flex; align-items: center; gap: 8px; }
.value-cell { display: flex; align-items: center; gap: 4px; }
.value-text { flex: 1; word-break: break-all; }
</style>
