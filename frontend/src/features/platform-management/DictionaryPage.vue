<template>
  <div class="p-6">
    <div class="page-header">
      <h2 class="page-title">数据字典</h2>
      <el-button type="primary" @click="showDialog = true"><el-icon><Plus /></el-icon> 新增字典</el-button>
    </div>
    <el-table :data="dicts" stripe v-loading="loading" empty-text="暂无数据字典" row-key="id">
      <el-table-column prop="category" label="分类" width="140" />
      <el-table-column prop="key" label="键" min-width="160" show-overflow-tooltip />
      <el-table-column prop="value" label="值" min-width="160" show-overflow-tooltip />
      <el-table-column prop="label" label="显示名" min-width="140" />
      <el-table-column prop="sort_order" label="排序" width="70" />
      <el-table-column prop="is_active" label="启用" width="70">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'" size="small">{{ row.is_active ? '是' : '否' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="140" fixed="right">
        <template #default="{ row }">
          <el-button text type="primary" size="small" @click="editDict(row)">编辑</el-button>
          <el-button text type="danger" size="small" @click="deleteDict(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-dialog v-model="showDialog" :title="editing ? '编辑字典' : '新增字典'" width="480px">
      <el-form :model="form" label-width="70px">
        <el-form-item label="分类"><el-input v-model="form.category" placeholder="如 asset_type" /></el-form-item>
        <el-form-item label="键"><el-input v-model="form.key" /></el-form-item>
        <el-form-item label="值"><el-input v-model="form.value" /></el-form-item>
        <el-form-item label="显示名"><el-input v-model="form.label" /></el-form-item>
        <el-form-item label="排序"><el-input-number v-model="form.sort_order" :min="0" /></el-form-item>
        <el-form-item label="启用"><el-switch v-model="form.is_active" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="showDialog=false">取消</el-button><el-button type="primary" @click="saveDict">确定</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from "vue"
import { Plus } from "@element-plus/icons-vue"

const loading = ref(false)
const dicts = ref<any[]>([])
const showDialog = ref(false)
const editing = ref<any>(null)
const form = reactive({ category: "", key: "", value: "", label: "", sort_order: 0, is_active: true })

function editDict(row: any) { editing.value = row; Object.assign(form, row); showDialog.value = true }
function deleteDict(row: any) { dicts.value = dicts.value.filter(d => d !== row) }
function saveDict() {
  if (editing.value) { Object.assign(editing.value, form) }
  else { dicts.value.push({ ...form, id: Date.now().toString() }) }
  showDialog.value = false; editing.value = null
}
onMounted(() => { loading.value = false })
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-title { font-size: 18px; font-weight: 600; color: #1d2129; }
</style>
