<template>
  <div class="p-6">
    <div class="page-header">
      <h2 class="page-title">业务系统</h2>
      <el-button type="primary" @click="showCreateDialog = true"><el-icon><Plus /></el-icon> 新建业务系统</el-button>
    </div>
    <el-table :data="systems" stripe v-loading="loading" empty-text="暂无业务系统">
      <el-table-column prop="name" label="系统名称" min-width="160" />
      <el-table-column prop="owner" label="负责人" width="120" />
      <el-table-column prop="level" label="重要等级" width="100">
        <template #default="{ row }">
          <el-tag :type="levelTag(row.level)" size="small">{{ row.level }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="asset_count" label="关联资产" width="100" />
      <el-table-column prop="sla_level" label="SLA等级" width="100" />
      <el-table-column prop="status" label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">{{ row.status === 'active' ? '正常' : '停用' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="140" fixed="right">
        <template #default="{ row }">
          <el-button text type="primary" size="small" @click="editSystem(row)">编辑</el-button>
          <el-button text type="danger" size="small" @click="deleteSystem(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showCreateDialog" :title="editingSystem ? '编辑业务系统' : '新建业务系统'" width="520px">
      <el-form :model="formData" label-width="90px">
        <el-form-item label="系统名称"><el-input v-model="formData.name" /></el-form-item>
        <el-form-item label="负责人"><el-input v-model="formData.owner" /></el-form-item>
        <el-form-item label="重要等级">
          <el-select v-model="formData.level"><el-option label="核心" value="critical" /><el-option label="重要" value="high" /><el-option label="一般" value="medium" /><el-option label="低" value="low" /></el-select>
        </el-form-item>
        <el-form-item label="SLA等级"><el-input v-model="formData.sla_level" /></el-form-item>
        <el-form-item label="描述"><el-input type="textarea" v-model="formData.description" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="saveSystem">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from "vue"
import { Plus } from "@element-plus/icons-vue"

interface BusinessSystem {
  id?: string; name: string; owner: string; level: string; asset_count: number; sla_level: string; status: string; description?: string
}

const loading = ref(false)
const systems = ref<BusinessSystem[]>([])
const showCreateDialog = ref(false)
const editingSystem = ref<BusinessSystem | null>(null)
const formData = reactive<BusinessSystem>({ name: "", owner: "", level: "medium", asset_count: 0, sla_level: "", status: "active", description: "" })

function levelTag(level: string) { return { critical: "danger", high: "warning", medium: "", low: "info" }[level] || "info" }
function editSystem(row: BusinessSystem) { editingSystem.value = row; Object.assign(formData, row); showCreateDialog.value = true }
function deleteSystem(row: BusinessSystem) { systems.value = systems.value.filter(s => s.id !== row.id) }
function saveSystem() {
  if (editingSystem.value) { Object.assign(editingSystem.value, formData) }
  else { systems.value.push({ ...formData, id: Date.now().toString(), asset_count: 0 }) }
  showCreateDialog.value = false; editingSystem.value = null; Object.assign(formData, { name: "", owner: "", level: "medium", sla_level: "", description: "" })
}
onMounted(() => { loading.value = false })
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-title { font-size: 18px; font-weight: 600; color: #1d2129; }
</style>
