<template>
  <div class="asset-discovery">
    <el-row :gutter="16">
      <!-- 左侧：创建发现任务 -->
      <el-col :span="10">
        <el-card>
          <template #header>
            <span>创建发现任务</span>
          </template>
          <el-form :model="taskForm" label-width="90px" :rules="taskRules" ref="formRef">
            <el-form-item label="IP 范围" prop="ip_range">
              <el-input
                v-model="taskForm.ip_range"
                placeholder="如 192.168.1.0/24 或 10.0.0.1-10.0.0.255"
                type="textarea"
                :rows="3"
              />
            </el-form-item>
            <el-form-item label="协议" prop="protocols">
              <el-checkbox-group v-model="taskForm.protocols">
                <el-checkbox label="SSH" value="ssh" />
                <el-checkbox label="SNMP" value="snmp" />
                <el-checkbox label="WMI" value="wmi" />
                <el-checkbox label="HTTP" value="http" />
                <el-checkbox label="ICMP" value="icmp" />
              </el-checkbox-group>
            </el-form-item>
            <el-form-item label="端口范围">
              <el-input v-model="taskForm.port_range" placeholder="如 22,80,443 或 1-1024" />
            </el-form-item>
            <el-form-item label="凭证" prop="credential_id">
              <el-select v-model="taskForm.credential_id" placeholder="选择凭证" clearable style="width: 100%">
                <el-option
                  v-for="c in credentials"
                  :key="c.id"
                  :label="`${c.name} (${c.credential_type})`"
                  :value="c.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="超时(秒)">
              <el-input-number v-model="taskForm.timeout" :min="5" :max="300" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="submitTask" :loading="submitting" :icon="Search">
                开始发现
              </el-button>
              <el-button @click="resetForm">重置</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <!-- 右侧：发现结果 -->
      <el-col :span="14">
        <el-card>
          <template #header>
            <div style="display:flex;justify-content:space-between;align-items:center">
              <span>发现结果</span>
              <div>
                <el-button @click="importSelected" :disabled="!selectedRows.length" type="success" :icon="Download">
                  导入选中 ({{ selectedRows.length }})
                </el-button>
                <el-button @click="loadResults" :icon="Refresh">刷新</el-button>
              </div>
            </div>
          </template>

          <el-table
            :data="results"
            v-loading="resultLoading"
            stripe
            @selection-change="handleSelectionChange"
          >
            <el-table-column type="selection" width="45" />
            <el-table-column prop="ip" label="IP" width="140" />
            <el-table-column prop="hostname" label="主机名" min-width="130" show-overflow-tooltip />
            <el-table-column prop="asset_type" label="类型" width="110">
              <template #default="{ row }">
                <el-tag size="small">{{ row.asset_type || '未知' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="os_type" label="系统" width="90" />
            <el-table-column prop="open_ports" label="开放端口" min-width="130">
              <template #default="{ row }">
                <span v-if="row.open_ports && row.open_ports.length">
                  {{ row.open_ports.join(', ') }}
                </span>
                <span v-else style="color: #c0c4cc">-</span>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="90">
              <template #default="{ row }">
                <el-tag :type="row.status === 'reachable' ? 'success' : row.status === 'unreachable' ? 'danger' : 'info'" size="small">
                  {{ row.status === 'reachable' ? '可达' : row.status === 'unreachable' ? '不可达' : row.status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="discovered_at" label="发现时间" width="160">
              <template #default="{ row }">{{ formatTime(row.discovered_at) }}</template>
            </el-table-column>
          </el-table>

          <el-empty v-if="!resultLoading && !results.length" description="暂无发现结果，请创建发现任务" />

          <el-pagination
            v-if="pagination.total > 0"
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.pageSize"
            :total="pagination.total"
            :page-sizes="[20, 50, 100]"
            layout="total, sizes, prev, pager, next"
            @change="loadResults"
            style="margin-top: 16px; justify-content: flex-end"
          />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { Search, Download, Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import api from '@/shared/api/client'
import { API as R } from '@/shared/api/routes'

const formRef = ref<FormInstance>()
const submitting = ref(false)
const resultLoading = ref(false)
const results = ref<any[]>([])
const selectedRows = ref<any[]>([])
const credentials = ref<any[]>([])

const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const taskForm = reactive({
  ip_range: '',
  protocols: ['icmp', 'ssh'] as string[],
  port_range: '',
  credential_id: '',
  timeout: 30,
})

const taskRules: FormRules = {
  ip_range: [{ required: true, message: '请输入IP范围', trigger: 'blur' }],
  protocols: [{ required: true, message: '请选择至少一个协议', trigger: 'change', type: 'array', min: 1 }],
}

function formatTime(t: string) {
  return t ? new Date(t).toLocaleString('zh-CN') : '-'
}

async function loadCredentials() {
  try {
    const { data } = await api.get(R.CREDENTIALS, { params: { page: 1, page_size: 100 } })
    if (data.code === 0) {
      credentials.value = data.data?.items || data.data || []
    }
  } catch {
    // 静默处理，凭证列表为辅助功能
  }
}

async function loadResults() {
  resultLoading.value = true
  try {
    const { data } = await api.get('/api/v1/discovery/results', {
      params: { page: pagination.page, page_size: pagination.pageSize },
    })
    if (data.code === 0) {
      results.value = data.data?.items || data.data || []
      pagination.total = data.data?.total || 0
    }
  } catch (e: any) {
    ElMessage.error('加载发现结果失败: ' + (e.message || e))
  } finally {
    resultLoading.value = false
  }
}

async function submitTask() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    const { data } = await api.post(R.ASSET_IMPORT, {
      ip_range: taskForm.ip_range,
      protocols: taskForm.protocols,
      port_range: taskForm.port_range || undefined,
      credential_id: taskForm.credential_id || undefined,
      timeout: taskForm.timeout,
    })
    if (data.code === 0) {
      ElMessage.success('发现任务已创建，正在执行...')
      setTimeout(() => loadResults(), 2000)
    } else {
      ElMessage.error(data.message || '创建任务失败')
    }
  } catch (e: any) {
    ElMessage.error('创建任务失败: ' + (e.message || e))
  } finally {
    submitting.value = false
  }
}

function resetForm() {
  formRef.value?.resetFields()
  Object.assign(taskForm, {
    ip_range: '',
    protocols: ['icmp', 'ssh'],
    port_range: '',
    credential_id: '',
    timeout: 30,
  })
}

function handleSelectionChange(rows: any[]) {
  selectedRows.value = rows
}

async function importSelected() {
  if (!selectedRows.value.length) return
  try {
    const assets = selectedRows.value.map((r) => ({
      name: r.hostname || r.ip,
      ip: r.ip,
      asset_type: r.asset_type || 'unknown',
      os_type: r.os_type || '',
    }))
    const { data } = await api.post(R.ASSET_IMPORT, { assets })
    if (data.code === 0) {
      ElMessage.success(`成功导入 ${selectedRows.value.length} 个资产`)
      loadResults()
    } else {
      ElMessage.error(data.message || '导入失败')
    }
  } catch (e: any) {
    ElMessage.error('导入失败: ' + (e.message || e))
  }
}

onMounted(() => {
  loadCredentials()
  loadResults()
})
</script>

<style scoped>
</style>
