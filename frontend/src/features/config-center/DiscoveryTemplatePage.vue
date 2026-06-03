<template>
  <div class="page-container">
    <div class="page-header">
      <h2>发现模板</h2>
      <el-button type="primary" @click="openCreateDialog">
        <el-icon><Plus /></el-icon> 新建模板
      </el-button>
    </div>

    <!-- Filters -->
    <el-card class="mb-md">
      <el-row :gutter="16">
        <el-col :span="8">
          <el-select v-model="filters.protocol" placeholder="协议" clearable @change="fetchData">
            <el-option label="SSH" value="ssh" />
            <el-option label="SNMP" value="snmp" />
            <el-option label="ICMP" value="icmp" />
            <el-option label="ARP" value="arp" />
            <el-option label="WMI" value="wmi" />
            <el-option label="Agent" value="agent" />
          </el-select>
        </el-col>
        <el-col :span="8">
          <el-select v-model="filters.enabled" placeholder="状态" clearable @change="fetchData">
            <el-option label="启用" :value="true" />
            <el-option label="禁用" :value="false" />
          </el-select>
        </el-col>
      </el-row>
    </el-card>

    <!-- Table -->
    <el-card v-loading="loading">
      <el-table :data="items" stripe empty-text="暂无发现模板" style="width: 100%">
        <el-table-column prop="name" label="模板名称" min-width="160" show-overflow-tooltip />
        <el-table-column prop="protocol" label="协议" width="100">
          <template #default="{ row }">
            <el-tag size="small" type="info">{{ row.protocol?.toUpperCase() }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="目标范围" min-width="200">
          <template #default="{ row }">
            <span class="text-tertiary">{{ scopePreview(row.target_scope) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="port_range" label="端口范围" width="140">
          <template #default="{ row }">{{ row.port_range || '默认' }}</template>
        </el-table-column>
        <el-table-column prop="scan_interval" label="扫描间隔" width="100">
          <template #default="{ row }">{{ formatInterval(row.scan_interval) }}</template>
        </el-table-column>
        <el-table-column prop="timeout" label="超时" width="80">
          <template #default="{ row }">{{ row.timeout }}s</template>
        </el-table-column>
        <el-table-column prop="is_builtin" label="内置" width="70">
          <template #default="{ row }">
            <el-tag v-if="row.is_builtin" size="small" type="info">内置</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="enabled" label="状态" width="80">
          <template #default="{ row }">
            <el-switch :model-value="row.enabled" @change="toggleTemplate(row)" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click="openEditDialog(row)">编辑</el-button>
            <el-popconfirm v-if="!row.is_builtin" title="确定删除此模板？" @confirm="deleteTemplate(row)">
              <template #reference>
                <el-button text type="danger" size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination
        v-if="total > pageSize"
        v-model:current-page="currentPage"
        :page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        style="margin-top: 16px; justify-content: flex-end"
        @current-change="fetchData"
      />
    </el-card>

    <!-- Create/Edit Dialog -->
    <el-dialog v-model="dialogVisible" :title="editingItem ? '编辑模板' : '新建模板'" width="600px" destroy-on-close>
      <el-form :model="formData" label-width="100px">
        <el-form-item label="模板名称" required>
          <el-input v-model="formData.name" placeholder="如：SSH标准发现" />
        </el-form-item>
        <el-form-item label="协议" required>
          <el-select v-model="formData.protocol" style="width: 100%">
            <el-option label="SSH" value="ssh" />
            <el-option label="SNMP" value="snmp" />
            <el-option label="ICMP" value="icmp" />
            <el-option label="ARP" value="arp" />
            <el-option label="WMI" value="wmi" />
            <el-option label="Agent" value="agent" />
          </el-select>
        </el-form-item>
        <el-form-item label="目标范围" required>
          <el-input v-model="formData.target_scope" type="textarea" :rows="3" placeholder='{"ip_ranges":["192.168.1.0/24"],"asset_groups":[],"exclude":[]}' />
        </el-form-item>
        <el-form-item label="端口范围">
          <el-input v-model="formData.port_range" placeholder="如：22,80,443 或 1-1024" />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="扫描间隔">
              <el-input-number v-model="formData.scan_interval" :min="60" :step="300" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="超时(秒)">
              <el-input-number v-model="formData.timeout" :min="30" :step="30" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="类型映射">
          <el-input v-model="formData.asset_type_mapping" type="textarea" :rows="2" placeholder='自动检测资产类型规则(JSON)' />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="formData.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { discoveryTemplateService } from '@/shared/api'

const loading = ref(false)
const items = ref<any[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = 20

const filters = reactive({ protocol: '', enabled: null as boolean | null })

async function fetchData() {
  loading.value = true
  try {
    const params: Record<string, any> = { page: currentPage.value, page_size: pageSize }
    if (filters.protocol) params.protocol = filters.protocol
    if (filters.enabled !== null) params.enabled = filters.enabled

    const resp = await discoveryTemplateService.list(params)
    if (resp.data?.code === 0) {
      items.value = resp.data.data?.items || []
      total.value = resp.data.data?.total || 0
    }
  } catch (e) {
    console.error('Failed to fetch discovery templates:', e)
  } finally {
    loading.value = false
  }
}

const dialogVisible = ref(false)
const editingItem = ref<any>(null)
const submitting = ref(false)
const formData = reactive({
  name: '', protocol: 'ssh', target_scope: '{"ip_ranges":[],"asset_groups":[],"exclude":[]}',
  port_range: '', scan_interval: 3600, timeout: 300, asset_type_mapping: '', description: '',
})

function openCreateDialog() {
  editingItem.value = null
  Object.assign(formData, { name: '', protocol: 'ssh', target_scope: '{"ip_ranges":[],"asset_groups":[],"exclude":[]}', port_range: '', scan_interval: 3600, timeout: 300, asset_type_mapping: '', description: '' })
  dialogVisible.value = true
}

function openEditDialog(row: any) {
  editingItem.value = row
  Object.assign(formData, { name: row.name, protocol: row.protocol, target_scope: row.target_scope, port_range: row.port_range || '', scan_interval: row.scan_interval, timeout: row.timeout, asset_type_mapping: row.asset_type_mapping || '', description: row.description || '' })
  dialogVisible.value = true
}

async function submitForm() {
  if (!formData.name || !formData.protocol) {
    ElMessage.warning('请填写必填项')
    return
  }
  submitting.value = true
  try {
    const data = { ...formData, port_range: formData.port_range || null, asset_type_mapping: formData.asset_type_mapping || null }
    if (editingItem.value) {
      await discoveryTemplateService.update(editingItem.value.id, data)
      ElMessage.success('模板已更新')
    } else {
      await discoveryTemplateService.create(data)
      ElMessage.success('模板已创建')
    }
    dialogVisible.value = false
    fetchData()
  } catch (e) {
    console.error('Submit failed:', e)
    ElMessage.error('操作失败')
  } finally {
    submitting.value = false
  }
}

async function toggleTemplate(row: any) {
  try {
    await discoveryTemplateService.toggle(row.id)
    fetchData()
  } catch { ElMessage.error('操作失败') }
}

async function deleteTemplate(row: any) {
  try {
    await discoveryTemplateService.delete(row.id)
    ElMessage.success('已删除')
    fetchData()
  } catch { ElMessage.error('删除失败') }
}

function scopePreview(s: string): string {
  try {
    const obj = JSON.parse(s)
    const parts: string[] = []
    if (obj.ip_ranges?.length) parts.push(\`IP: \${obj.ip_ranges.slice(0, 2).join(',')}\`)
    if (obj.asset_groups?.length) parts.push(\`分组: \${obj.asset_groups.length}个\`)
    return parts.length ? parts.join(' | ') : '未配置'
  } catch { return s?.slice(0, 50) || '未配置' }
}

function formatInterval(seconds: number): string {
  if (seconds >= 86400) return \`\${Math.round(seconds / 86400)}天\`
  if (seconds >= 3600) return \`\${Math.round(seconds / 3600)}小时\`
  return \`\${seconds}秒\`
}

onMounted(fetchData)
</script>

<style scoped>
.page-container { padding: 20px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.mb-md { margin-bottom: 16px; }
.text-tertiary { color: #86909c; }
</style>
