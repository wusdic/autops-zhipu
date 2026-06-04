<template>
  <div class="page-container">
    <div class="autops-page-header">
      <div class="autops-page-title">故障复盘</div>
      <el-button type="primary" @click="handleCreate" :icon="Plus">新建复盘</el-button>
    </div>
    <div class="page-toolbar" style="display:flex;gap:12px;margin-bottom:16px">
      <el-input v-model="query" placeholder="搜索复盘报告..." clearable style="width:300px" @clear="fetchList" @keyup.enter="fetchList">
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
      <el-select v-model="statusFilter" placeholder="状态" clearable style="width:140px" @change="fetchList">
        <el-option label="草稿" value="draft" />
        <el-option label="进行中" value="in_progress" />
        <el-option label="已完成" value="completed" />
      </el-select>
      <el-button @click="fetchList" :icon="Refresh">刷新</el-button>
    </div>
    <el-table stripe :data="list" v-loading="loading">
      <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip>
        <template #default="{ row }">
          <el-link type="primary" @click="viewDetail(row)">{{ row.title }}</el-link>
        </template>
      </el-table-column>
      <el-table-column prop="category" label="分类" width="120">
        <template #default="{ row }">
          <el-tag size="small">{{ row.category || 'postmortem' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="关联告警" width="120">
        <template #default="{ row }">{{ row.metadata?.alert_ids?.length ?? row.metadata?.alert_id ?? '-' }}</template>
      </el-table-column>
      <el-table-column prop="author_name" label="创建者" width="100" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag size="small" :type="statusType(row.status)">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="170">
        <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column prop="updated_at" label="更新时间" width="170">
        <template #default="{ row }">{{ formatTime(row.updated_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button plain type="primary" size="small" @click="viewDetail(row)">查看</el-button>
          <el-button plain type="primary" size="small" @click="handleEdit(row)">编辑</el-button>
          <el-button plain type="danger" size="small" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <div style="display:flex;justify-content:flex-end;margin-top:16px">
      <el-pagination v-model:current-page="page" v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]" :total="total" layout="total, sizes, prev, pager, next"
        @size-change="fetchList" @current-change="fetchList" />
    </div>

    <!-- Create/Edit Dialog -->
    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑复盘' : '新建复盘'" width="600px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="80px">
        <el-form-item label="标题" prop="title">
          <el-input v-model="form.title" placeholder="复盘报告标题" />
        </el-form-item>
        <el-form-item label="关联告警">
          <el-input v-model="form.alert_ids" placeholder="告警ID，逗号分隔" />
        </el-form-item>
        <el-form-item label="内容" prop="content">
          <el-input v-model="form.content" type="textarea" :rows="8" placeholder="复盘内容：时间线、根因、改进措施..." />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status">
            <el-option label="草稿" value="draft" />
            <el-option label="进行中" value="in_progress" />
            <el-option label="已完成" value="completed" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>

    <!-- Detail Drawer -->
    <el-drawer v-model="drawerVisible" title="复盘详情" size="600px">
      <el-descriptions :column="1" border v-if="currentItem">
        <el-descriptions-item label="标题">{{ currentItem.title }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="statusType(currentItem.status)">{{ statusLabel(currentItem.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="创建者">{{ currentItem.author_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatTime(currentItem.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ formatTime(currentItem.updated_at) }}</el-descriptions-item>
      </el-descriptions>
      <div style="margin-top:20px">
        <h4>复盘内容</h4>
        <div style="white-space:pre-wrap;background:#f7f8fa;padding:16px;border-radius:4px;margin-top:8px">
          {{ currentItem?.content || currentItem?.description || '暂无内容' }}
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import { knowledgeService } from '@/shared/api'

const loading = ref(false)
const submitting = ref(false)
const list = ref<any[]>([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const query = ref('')
const statusFilter = ref('')

const dialogVisible = ref(false)
const drawerVisible = ref(false)
const editingId = ref<string | null>(null)
const currentItem = ref<any>(null)
const formRef = ref<FormInstance>()

const form = ref({ title: '', alert_ids: '', content: '', status: 'draft' })
const rules: FormRules = { title: [{ required: true, message: '请输入标题', trigger: 'blur' }] }

function statusType(s: string) {
  return { draft: 'info', in_progress: 'warning', completed: 'success' }[s] || 'info'
}
function statusLabel(s: string) {
  return { draft: '草稿', in_progress: '进行中', completed: '已完成' }[s] || s || '-'
}
function formatTime(t: string) {
  if (!t) return '-'
  return new Date(t).toLocaleString('zh-CN')
}

async function fetchList() {
  loading.value = true
  try {
    const params: Record<string, any> = { page: page.value, page_size: pageSize.value, category: 'postmortem' }
    if (query.value) params.keyword = query.value
    if (statusFilter.value) params.status = statusFilter.value
    const res = await knowledgeService.list(params)
    const d = res.data?.data ?? res.data
    list.value = d?.items ?? d?.results ?? d?.list ?? (Array.isArray(d) ? d : [])
    total.value = d?.total ?? list.value.length
  } catch { ElMessage.error('获取复盘列表失败') }
  finally { loading.value = false }
}

function handleCreate() {
  editingId.value = null
  form.value = { title: '', alert_ids: '', content: '', status: 'draft' }
  dialogVisible.value = true
}

function handleEdit(row: any) {
  editingId.value = row.id
  form.value = { title: row.title, alert_ids: row.metadata?.alert_ids?.join(',') ?? '', content: row.content ?? row.description ?? '', status: row.status ?? 'draft' }
  dialogVisible.value = true
}

async function submitForm() {
  await formRef.value?.validate()
  submitting.value = true
  try {
    const data: Record<string, any> = {
      title: form.value.title,
      category: 'postmortem',
      content: form.value.content,
      status: form.value.status,
      metadata: { alert_ids: form.value.alert_ids ? form.value.alert_ids.split(',').map((s: string) => s.trim()) : [] },
    }
    if (editingId.value) {
      await knowledgeService.update(editingId.value, data)
      ElMessage.success('更新成功')
    } else {
      await knowledgeService.create(data)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchList()
  } catch { ElMessage.error('操作失败') }
  finally { submitting.value = false }
}

async function handleDelete(row: any) {
  try {
    await ElMessageBox.confirm('确认删除复盘报告"' + row.title + '"？', '确认', { type: 'warning' })
    await knowledgeService.delete(row.id)
    ElMessage.success('删除成功')
    fetchList()
  } catch {}
}

function viewDetail(row: any) {
  currentItem.value = row
  drawerVisible.value = true
}

onMounted(fetchList)
</script>
