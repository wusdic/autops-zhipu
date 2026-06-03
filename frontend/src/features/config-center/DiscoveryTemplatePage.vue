<template>
  <div class="discovery-template-page">
    <el-page-header @back="router.back()" title="返回" content="发现模板管理">
      <template #extra>
        <el-button type="primary" @click="openDialog()">
          <el-icon><Plus /></el-icon> 新建模板
        </el-button>
        <el-button @click="loadData" :loading="loading">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
      </template>
    </el-page-header>

    <!-- 搜索过滤 -->
    <el-card class="mt-4" shadow="never">
      <el-form :inline="true" :model="filters">
        <el-form-item label="模板名称">
          <el-input v-model="filters.keyword" placeholder="搜索模板名称" clearable @clear="loadData" />
        </el-form-item>
        <el-form-item label="发现类型">
          <el-select v-model="filters.type" placeholder="全部类型" clearable @change="loadData">
            <el-option label="SSH发现" value="ssh" />
            <el-option label="SNMP发现" value="snmp" />
            <el-option label="ICMP扫描" value="icmp" />
            <el-option label="端口扫描" value="port_scan" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部" clearable @change="loadData">
            <el-option label="启用" value="active" />
            <el-option label="禁用" value="inactive" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">搜索</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 模板列表 -->
    <el-card class="mt-4" shadow="never">
      <el-table :data="templates" v-loading="loading" stripe border style="width: 100%">
        <el-table-column type="selection" width="50" />
        <el-table-column prop="name" label="模板名称" min-width="180" sortable />
        <el-table-column prop="type" label="发现类型" width="120">
          <template #default="{ row }">
            <el-tag :type="typeColor(row.type)" size="small">{{ typeName(row.type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="target" label="扫描目标" min-width="150">
          <template #default="{ row }">
            <code>{{ row.target || row.ip_range || '-' }}</code>
          </template>
        </el-table-column>
        <el-table-column prop="port_range" label="端口范围" width="120" />
        <el-table-column prop="credential" label="关联凭证" width="120" />
        <el-table-column prop="schedule" label="调度周期" width="120" />
        <el-table-column prop="last_run_at" label="最近执行" width="180" />
        <el-table-column prop="found_count" label="发现资产" width="100" />
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
              {{ row.status === 'active' ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="executeTemplate(row)">执行</el-button>
            <el-button link type="primary" @click="openDialog(row)">编辑</el-button>
            <el-button link type="primary" @click="viewHistory(row)">历史</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        class="mt-4"
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.size"
        :total="pagination.total"
        :page-sizes="[20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="loadData"
        @current-change="loadData"
      />
    </el-card>

    <!-- 新建/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="editing ? '编辑模板' : '新建模板'" width="650px" destroy-on-close>
      <el-form :model="form" label-width="100px" :rules="formRules" ref="formRef">
        <el-form-item label="模板名称" prop="name">
          <el-input v-model="form.name" placeholder="如：网段SSH发现" />
        </el-form-item>
        <el-form-item label="发现类型" prop="type">
          <el-select v-model="form.type" placeholder="选择发现类型" style="width: 100%">
            <el-option label="SSH发现" value="ssh" />
            <el-option label="SNMP发现" value="snmp" />
            <el-option label="ICMP扫描" value="icmp" />
            <el-option label="端口扫描" value="port_scan" />
          </el-select>
        </el-form-item>
        <el-form-item label="扫描目标" prop="target">
          <el-input v-model="form.target" placeholder="IP/子网，如 192.168.1.0/24" />
        </el-form-item>
        <el-form-item label="端口范围">
          <el-input v-model="form.port_range" placeholder="如 22,80,443 或 1-65535" />
        </el-form-item>
        <el-form-item label="关联凭证">
          <el-select v-model="form.credential_id" placeholder="选择凭证" clearable style="width: 100%">
            <el-option v-for="c in credentials" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="调度周期">
          <el-select v-model="form.schedule" placeholder="选择调度" clearable style="width: 100%">
            <el-option label="手动" value="manual" />
            <el-option label="每天" value="daily" />
            <el-option label="每周" value="weekly" />
            <el-option label="每月" value="monthly" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="模板描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">{{ editing ? '保存' : '创建' }}</el-button>
      </template>
    </el-dialog>

    <!-- 执行历史对话框 -->
    <el-dialog v-model="historyVisible" title="执行历史" width="700px">
      <el-table :data="historyList" v-loading="historyLoading" stripe>
        <el-table-column prop="executed_at" label="执行时间" width="180" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'success' ? 'success' : row.status === 'running' ? 'warning' : 'danger'" size="small">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="found" label="新发现" width="80" />
        <el-table-column prop="duration" label="耗时" width="100" />
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import { configService } from '@/shared/api'

const router = useRouter()
const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const historyVisible = ref(false)
const historyLoading = ref(false)
const editing = ref<any>(null)
const templates = ref<any[]>([])
const credentials = ref<any[]>([])
const historyList = ref<any[]>([])
const formRef = ref()

const filters = reactive({ keyword: '', type: '', status: '' })
const pagination = reactive({ page: 1, size: 20, total: 0 })
const form = reactive({
  name: '', type: '', target: '', port_range: '',
  credential_id: '', schedule: 'manual', description: '',
})
const formRules = {
  name: [{ required: true, message: '请输入模板名称', trigger: 'blur' }],
  type: [{ required: true, message: '请选择发现类型', trigger: 'change' }],
  target: [{ required: true, message: '请输入扫描目标', trigger: 'blur' }],
}

function typeName(t: string) {
  const m: Record<string, string> = { ssh: 'SSH', snmp: 'SNMP', icmp: 'ICMP', port_scan: '端口扫描' }
  return m[t] || t
}
function typeColor(t: string) {
  const m: Record<string, string> = { ssh: 'primary', snmp: 'success', icmp: 'warning', port_scan: 'danger' }
  return m[t] || 'info'
}

async function loadData() {
  loading.value = true
  try {
    const res = await configService.list({ ...filters, page: pagination.page, page_size: pagination.size })
    templates.value = res.data?.items || []
    pagination.total = res.data?.total || 0
  } catch (e: any) {
    ElMessage.error('加载失败: ' + (e.message || ''))
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  filters.keyword = ''; filters.type = ''; filters.status = ''
  pagination.page = 1
  loadData()
}

function openDialog(row?: any) {
  editing.value = row || null
  if (row) {
    Object.assign(form, row)
  } else {
    Object.assign(form, { name: '', type: '', target: '', port_range: '', credential_id: '', schedule: 'manual', description: '' })
  }
  dialogVisible.value = true
}

async function handleSubmit() {
  await formRef.value?.validate()
  submitting.value = true
  try {
    if (editing.value) {
      await configService.update(editing.value.id, form)
      ElMessage.success('模板更新成功')
    } else {
      await configService.create(form)
      ElMessage.success('模板创建成功')
    }
    dialogVisible.value = false
    loadData()
  } catch (e: any) {
    ElMessage.error('操作失败: ' + (e.message || ''))
  } finally {
    submitting.value = false
  }
}

async function executeTemplate(row: any) {
  try {
    await ElMessageBox.confirm(`确认执行发现模板「${row.name}」？`, '执行确认', { type: 'info' })
    await configService.executeDiscovery?.(row.id)
    ElMessage.success('发现任务已启动')
  } catch { /* cancelled */ }
}

async function viewHistory(row: any) {
  historyVisible.value = true
  historyLoading.value = true
  try {
    const res = await configService.getDiscoveryHistory?.(row.id) ?? { data: { items: [] } }
    historyList.value = (res as any).data?.items || []
  } catch { historyList.value = [] } finally { historyLoading.value = false }
}

async function handleDelete(row: any) {
  try {
    await ElMessageBox.confirm(`确认删除模板「${row.name}」？此操作不可恢复。`, '删除确认', { type: 'warning' })
    await configService.delete(row.id)
    ElMessage.success('已删除')
    loadData()
  } catch { /* cancelled */ }
}

onMounted(() => { loadData() })
</script>

<style scoped>
.discovery-template-page { padding: 20px; }
.mt-4 { margin-top: 16px; }
</style>
