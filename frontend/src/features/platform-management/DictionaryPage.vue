<template>
  <div class="autops-page-container">
    <div class="autops-page-header">
      <div>
        <div class="autops-page-title">字典管理</div>
        <div class="autops-page-desc">管理系统字典分类与字典项</div>
      </div>
    </div>

    <div class="dict-layout">
      <!-- ── Left Panel: Dictionary Groups ────────────────── -->
      <div class="dict-left">
        <div class="panel-header">
          <span class="panel-title">字典分类</span>
          <el-input
            v-model="groupSearch"
            placeholder="搜索分类..."
            size="small"
            clearable
            prefix-icon="Search"
            style="width: 140px"
          />
        </div>
        <div class="group-list">
          <div
            v-for="group in filteredGroups"
            :key="group"
            class="group-item"
            :class="{ active: selectedGroup === group }"
            @click="selectGroup(group)"
          >
            <el-icon size="16" style="margin-right: 6px"><Folder /></el-icon>
            <span class="group-name">{{ group }}</span>
            <el-tag size="small" type="info" class="group-count">{{ groupItemCount(group) }}</el-tag>
          </div>
          <el-empty v-if="filteredGroups.length === 0" description="暂无分类" :image-size="60" />
        </div>
      </div>

      <!-- ── Right Panel: Dictionary Items Table ──────────── -->
      <div class="dict-right">
        <div class="right-toolbar">
          <div class="toolbar-left">
            <el-input
              v-model="keyword"
              placeholder="搜索键/值/显示名..."
              clearable
              prefix-icon="Search"
              style="width: 240px"
              @keyup.enter="loadItems"
            />
            <el-button @click="loadItems" :loading="loading">查询</el-button>
          </div>
          <el-button type="primary" @click="openCreateDialog">
            <el-icon><Plus /></el-icon> 新增字典项
          </el-button>
        </div>

        <el-table stripe
 :data="items"
 v-loading="loading"
63| border
 row-key="id"
 empty-text="暂无字典项"
 style="width: 100%"
 >
          <el-table-column prop="category" label="分类" width="150" show-overflow-tooltip />
          <el-table-column prop="key" label="键" min-width="150" show-overflow-tooltip />
          <el-table-column prop="value" label="值" min-width="150" show-overflow-tooltip />
          <el-table-column prop="label" label="显示名" min-width="130" show-overflow-tooltip />
          <el-table-column prop="sort_order" label="排序" width="70" align="center" />
          <el-table-column prop="is_active" label="启用" width="70" align="center">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
                {{ row.is_active ? '是' : '否' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="remark" label="备注" min-width="150" show-overflow-tooltip />
          <el-table-column label="操作" width="180" fixed="right" align="center">
            <template #default="{ row }">
              <el-button plain type="primary" size="small" @click="openEditDialog(row)">编辑</el-button>
              <el-button plain type="danger" size="small" @click="deleteItem(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="pagination-wrap" v-if="total > pageSize">
          <el-pagination
            v-model:current-page="currentPage"
            :page-size="pageSize"
            :total="total"
            layout="total, prev, pager, next"
            @current-change="loadItems"
          />
        </div>
      </div>
    </div>

    <!-- ── Create / Edit Dialog ───────────────────────────── -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑字典项' : '新增字典项'"
      width="600px"
      destroy-on-close
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="80px"
        label-position="right"
      >
        <el-form-item label="分类" prop="category">
          <el-select
            v-model="form.category"
            filterable
            allow-create
            default-first-option
            placeholder="选择或输入分类"
            style="width: 100%"
          >
            <el-option
              v-for="g in allGroups"
              :key="g"
              :label="g"
              :value="g"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="键" prop="key">
          <el-input v-model="form.key" placeholder="字典键，如 high / tcp" />
        </el-form-item>
        <el-form-item label="值" prop="value">
          <el-input v-model="form.value" placeholder="字典值" />
        </el-form-item>
        <el-form-item label="显示名" prop="label">
          <el-input v-model="form.label" placeholder="前端显示名称" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="0" :max="9999" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="form.is_active" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" placeholder="可选备注" />
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
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { Plus, Folder } from '@element-plus/icons-vue'
import { platformService } from '@/shared/api'

// ── State ────────────────────────────────────────────────
const loading = ref(false)
const submitting = ref(false)
const items = ref<any[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = 20

const selectedGroup = ref('')
const keyword = ref('')
const groupSearch = ref('')

const dialogVisible = ref(false)
const isEditing = ref(false)
const editingId = ref('')
const formRef = ref<FormInstance>()

const form = reactive({
  category: '',
  key: '',
  value: '',
  label: '',
  sort_order: 0,
  is_active: true,
  remark: '',
})

const formRules: FormRules = {
  category: [{ required: true, message: '请选择或输入分类', trigger: 'change' }],
  key: [{ required: true, message: '请输入字典键', trigger: 'blur' }],
  value: [{ required: true, message: '请输入字典值', trigger: 'blur' }],
}

// ── Computed ─────────────────────────────────────────────
const allGroups = computed(() => {
  const groups = new Set<string>()
  items.value.forEach((item) => groups.add(item.category))
  return Array.from(groups).sort()
})

const filteredGroups = computed(() => {
  if (!groupSearch.value) return allGroups.value
  const q = groupSearch.value.toLowerCase()
  return allGroups.value.filter((g) => g.toLowerCase().includes(q))
})

function groupItemCount(group: string): number {
  return items.value.filter((i) => i.category === group).length
}

// ── Data Loading ─────────────────────────────────────────
async function loadItems() {
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: currentPage.value,
      page_size: pageSize,
    }
    if (selectedGroup.value) params.category = selectedGroup.value
    if (keyword.value) params.keyword = keyword.value

    const res = await platformService.dictionaries(params)
    const data = res.data?.data ?? res.data
    if (Array.isArray(data)) {
      items.value = data
      total.value = data.length
    } else {
      items.value = data?.items ?? data?.list ?? []
      total.value = data?.total ?? items.value.length
    }
  } catch (err: any) {
    ElMessage.error(err.message || '加载字典失败')
  } finally {
    loading.value = false
  }
}

// ── Group Selection ──────────────────────────────────────
function selectGroup(group: string) {
  selectedGroup.value = selectedGroup.value === group ? '' : group
  currentPage.value = 1
  loadItems()
}

// ── Dialog ───────────────────────────────────────────────
function resetForm() {
  form.category = selectedGroup.value || ''
  form.key = ''
  form.value = ''
  form.label = ''
  form.sort_order = 0
  form.is_active = true
  form.remark = ''
}

function openCreateDialog() {
  isEditing.value = false
  editingId.value = ''
  resetForm()
  dialogVisible.value = true
}

function openEditDialog(row: any) {
  isEditing.value = true
  editingId.value = row.id
  Object.assign(form, {
    category: row.category,
    key: row.key,
    value: row.value,
    label: row.label,
    sort_order: row.sort_order ?? 0,
    is_active: row.is_active ?? true,
    remark: row.remark ?? '',
  })
  dialogVisible.value = true
}

async function submitForm() {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    const payload = { ...form }
    if (isEditing.value) {
      await platformService.dictionaryUpdate(editingId.value, payload)
      ElMessage.success('字典项已更新')
    } else {
      await platformService.dictionaryCreate(payload)
      ElMessage.success('字典项已创建')
    }
    dialogVisible.value = false
    loadItems()
  } catch (err: any) {
    ElMessage.error(err.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

// ── Delete ───────────────────────────────────────────────
async function deleteItem(row: any) {
  try {
    await ElMessageBox.confirm(
      '确定删除字典项「' + row.label || row.key + '」吗？',
      '删除确认',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' },
    )
    await platformService.dictionaryDelete(row.id)
    ElMessage.success('已删除')
    loadItems()
  } catch {
    // cancelled or API error handled globally
  }
}

// ── Init ─────────────────────────────────────────────────
onMounted(() => {
  loadItems()
})
</script>

<style scoped>

.autops-page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--autops-space-lg);
}


/* Layout */
.dict-layout {
  display: flex;
  gap: 16px;
}
.dict-left {
  width: 240px;
  min-width: 200px;
  flex-shrink: 0;
  background: var(--autops-bg-1);
  border: 1px solid var(--autops-bg-4);
  border-radius: var(--autops-radius-md);
  display: flex;
  flex-direction: column;
}
.dict-right {
  flex: 1;
  min-width: 0;
}

/* Panel */
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--autops-space-md);
  border-bottom: 1px solid var(--autops-bg-3);
}
.panel-title {
  font-weight: 600;
  font-size: var(--autops-font-14);
  color: var(--autops-text-1);
}
.group-list {
  flex: 1;
  overflow-y: auto;
  padding: var(--autops-space-xs) 0;
}
.group-item {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  cursor: pointer;
  transition: background 0.15s;
  border-left: 3px solid transparent;
}
.group-item:hover {
  background: var(--autops-bg-2);
}
.group-item.active {
  background: var(--autops-primary-light-5);
  border-left-color: var(--autops-primary);
}
.group-name {
  flex: 1;
  font-size: var(--autops-font-13);
  color: var(--autops-text-2);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.group-count {
  margin-left: 4px;
}

/* Right toolbar */
.right-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--autops-space-md);
}
.toolbar-left {
  display: flex;
  gap: 8px;
}

/* Pagination */
.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}
</style>
