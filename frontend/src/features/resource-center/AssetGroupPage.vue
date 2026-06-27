<template>
  <div class="asset-group">
    <!-- 页面头部 -->
    <div class="autops-page-header">
      <span class="autops-page-title">资产分组</span>
    </div>

    <el-row :gutter="16">
      <!-- 左侧：分组列表 -->
      <el-col :span="10">
        <div class="autops-card">
          <div class="autops-card-header">
            <span class="autops-card-title">资产分组</span>
            <el-button type="primary" size="small" @click="openCreateDialog" :icon="Plus">新建分组</el-button>
          </div>
          <div class="autops-card-body">

          <el-input
            v-model="groupSearch"
            placeholder="搜索分组名称"
            clearable
            class="mb-md"
            :prefix-icon="Search"
          />

          <div v-loading="groupLoading">
            <el-empty v-if="!groupLoading && !filteredGroups.length" description="暂无分组" />

            <div
              v-for="g in filteredGroups"
              :key="g.id"
              class="group-item"
              :class="{ active: currentGroup?.id === g.id }"
              @click="selectGroup(g)"
            >
              <div class="group-info">
                <div class="group-name">
                  <el-icon style="margin-right: 4px"><Folder /></el-icon>
                  {{ g.name }}
                </div>
                <div class="group-meta">
                  <el-tag size="small" type="info">{{ g.asset_count || 0 }} 个资产</el-tag>
                </div>
              </div>
              <div class="group-actions" @click.stop>
                <el-button size="small" plain type="primary" @click="openEditDialog(g)">编辑</el-button>
                <el-popconfirm title="确认删除此分组?" @confirm="deleteGroup(g.id)">
                  <template #reference>
                    <el-button size="small" plain type="danger">删除</el-button>
                  </template>
                </el-popconfirm>
              </div>
            </div>
          </div>
          </div>
        </div>
      </el-col>

      <!-- 右侧：分组内资产列表 -->
      <el-col :span="14">
        <div class="autops-card">
          <div class="autops-card-header">
            <span class="autops-card-title">{{ currentGroup ? '分组: ' + currentGroup.name : '分组资产列表' }}</span>
            <div v-if="currentGroup">
              <el-button type="primary" size="small" @click="showAddMemberDialog = true" :icon="Plus">
                添加资产
              </el-button>
            </div>
          </div>
          <div class="autops-card-body">

          <template v-if="currentGroup">
            <!-- 分组描述 -->
            <div v-if="currentGroup.description" class="group-desc">
              <el-text type="info">{{ currentGroup.description }}</el-text>
            </div>

            <el-table stripe :data="members" v-loading="memberLoading">
              <el-table-column prop="name" label="名称" min-width="140" show-overflow-tooltip />
              <el-table-column prop="ip" label="IP" width="140" />
              <el-table-column prop="asset_type" label="类型" width="110">
                <template #default="{ row }">
                  <el-tag size="small">{{ formatType(row.asset_type) }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="status" label="状态" width="90">
                <template #default="{ row }">
                  <el-tag :type="(statusType(row.status)) as TagType" size="small">{{ row.status }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="os_type" label="系统" width="80" />
              <el-table-column label="操作" width="100" fixed="right">
                <template #default="{ row }">
                  <el-popconfirm title="确认从此分组移除?" @confirm="removeMember(row.id)">
                    <template #reference>
                      <el-button size="small" plain type="danger">移除</el-button>
                    </template>
                  </el-popconfirm>
                </template>
              </el-table-column>
            </el-table>

            <el-empty v-if="!memberLoading && !members.length" description="此分组暂无资产" />
          </template>

          <el-empty v-else description="请在左侧选择一个分组查看资产" />
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 创建/编辑分组弹窗 -->
    <el-dialog v-model="showFormDialog" :title="isEditing ? '编辑分组' : '新建分组'" width="600px">
      <el-form :model="groupForm" label-width="80px" ref="groupFormRef" :rules="groupRules">
        <el-form-item label="名称" prop="name">
          <el-input v-model="groupForm.name" placeholder="输入分组名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="groupForm.description" type="textarea" :rows="3" placeholder="分组描述(可选)" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showFormDialog = false">取消</el-button>
        <el-button type="primary" @click="saveGroup" :loading="saving">{{ isEditing ? '保存' : '创建' }}</el-button>
      </template>
    </el-dialog>

    <!-- 添加资产到分组弹窗 -->
    <el-dialog v-model="showAddMemberDialog" title="添加资产到分组" width="600px">
      <el-input
        v-model="assetSearch"
        placeholder="搜索资产名称或IP"
        clearable
        class="mb-md"
        :prefix-icon="Search"
        @input="searchAssets"
      />
      <el-table stripe
 :data="availableAssets"
 v-loading="assetSearchLoading"max-height="400"
 @selection-change="handleAssetSelection"
 >
        <el-table-column type="selection" width="45" />
        <el-table-column prop="name" label="名称" min-width="140" show-overflow-tooltip />
        <el-table-column prop="ip" label="IP" width="140" />
        <el-table-column prop="asset_type" label="类型" width="110">
          <template #default="{ row }">
            <el-tag size="small">{{ formatType(row.asset_type) }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="showAddMemberDialog = false">取消</el-button>
        <el-button type="primary" @click="addMembers" :disabled="!selectedAssets.length" :loading="addingMembers">
          添加 ({{ selectedAssets.length }})
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import type { TagType } from '@/shared/types'
import { Plus, Search, Folder } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import api from '@/shared/api/client'
import { assetStatusTag } from '@/shared/utils/labels'
import { API as R } from '@/shared/api/routes'

// 分组列表
const groupLoading = ref(false)
const groups = ref<any[]>([])
const currentGroup = ref<any>(null)
const groupSearch = ref('')
const showFormDialog = ref(false)
const isEditing = ref(false)
const editingId = ref('')
const saving = ref(false)
const groupFormRef = ref<FormInstance>()

const groupForm = reactive({ name: '', description: ''})
const groupRules: FormRules = {
  name: [{ required: true, message: '请输入分组名称', trigger: 'blur' }],
}

const filteredGroups = computed(() => {
  if (!groupSearch.value) return groups.value
  const q = groupSearch.value.toLowerCase()
  return groups.value.filter((g) => g.name.toLowerCase().includes(q))
})

// 分组成员
const memberLoading = ref(false)
const members = ref<any[]>([])

// 添加资产
const showAddMemberDialog = ref(false)
const assetSearch = ref('')
const availableAssets = ref<any[]>([])
const selectedAssets = ref<any[]>([])
const assetSearchLoading = ref(false)
const addingMembers = ref(false)

function formatType(t: string): string {
  const map: Record<string, string> = {
    linux_server: 'Linux', windows_server: 'Windows', database: '数据库',
    network_device: '网络设备', web_service: 'Web服务',
  }
  return map[t] || t || '-'
}

const statusType = (s: string): TagType => assetStatusTag(s) as TagType

async function loadGroups() {
  groupLoading.value = true
  try {
    const { data } = await api.get(R.ASSET_GROUPS, { params: { page: 1, page_size: 100 } })
    if (data.code === 0) {
      groups.value = data.data?.items || data.data || []
    }
  } catch (e: any) {
    ElMessage.error('加载分组失败: ' + (e.message || e))
  } finally {
    groupLoading.value = false
  }
}

async function selectGroup(g: any) {
  currentGroup.value = g
  await loadMembers(g.id)
}

async function loadMembers(groupId: string) {
  memberLoading.value = true
  try {
    const { data } = await api.get(R.ASSET_GROUP_MEMBERS(groupId))
    if (data.code === 0) {
      members.value = data.data?.items || data.data || []
    }
  } catch (e: any) {
    ElMessage.error('加载分组成员失败: ' + (e.message || e))
  } finally {
    memberLoading.value = false
  }
}

function openCreateDialog() {
  isEditing.value = false
  editingId.value = ''
  Object.assign(groupForm, { name: '', description: ''})
  showFormDialog.value = true
}

function openEditDialog(g: any) {
  isEditing.value = true
  editingId.value = g.id
  Object.assign(groupForm, { name: g.name, description: g.description || '' })
  showFormDialog.value = true
}

async function saveGroup() {
  const valid = await groupFormRef.value?.validate().catch(() => false)
  if (!valid) return

  saving.value = true
  try {
    if (isEditing.value) {
      const { data } = await api.put(R.ASSET_GROUP_DETAIL(editingId.value), groupForm)
      if (data.code === 0) {
        ElMessage.success('分组已更新')
        showFormDialog.value = false
        loadGroups()
      } else {
        ElMessage.error(data.message || '更新失败')
      }
    } else {
      const { data } = await api.post(R.ASSET_GROUPS, groupForm)
      if (data.code === 0) {
        ElMessage.success('分组已创建')
        showFormDialog.value = false
        loadGroups()
      } else {
        ElMessage.error(data.message || '创建失败')
      }
    }
  } catch (e: any) {
    ElMessage.error((isEditing.value ? '更新' : '创建') + '失败: ' + (e.message || e))
  } finally {
    saving.value = false
  }
}

async function deleteGroup(id: string) {
  try {
    const { data } = await api.delete(R.ASSET_GROUP_DETAIL(id))
    if (data.code === 0) {
      ElMessage.success('分组已删除')
      if (currentGroup.value?.id === id) {
        currentGroup.value = null
        members.value = []
      }
      loadGroups()
    }
  } catch (e: any) {
    ElMessage.error('删除失败: ' + (e.message || e))
  }
}

async function searchAssets() {
  assetSearchLoading.value = true
  try {
    const params: any = { page: 1, page_size: 50 }
    if (assetSearch.value) params.search = assetSearch.value
    const { data } = await api.get(R.ASSETS, { params })
    if (data.code === 0) {
      // 排除已在分组中的资产
      const memberIds = new Set(members.value.map((m) => m.id))
      availableAssets.value = (data.data?.items || []).filter((a: any) => !memberIds.has(a.id))
    }
  } catch {
    // 静默
  } finally {
    assetSearchLoading.value = false
  }
}

function handleAssetSelection(rows: any[]) {
  selectedAssets.value = rows
}

async function addMembers() {
  if (!currentGroup.value || !selectedAssets.value.length) return
  addingMembers.value = true
  try {
    const asset_ids = selectedAssets.value.map((a) => a.id)
    const { data } = await api.post(R.ASSET_GROUP_MEMBERS(currentGroup.value.id), { asset_ids })
    if (data.code === 0) {
      ElMessage.success('已添加 ' + selectedAssets.value.length + ' 个资产')
      showAddMemberDialog.value = false
      selectedAssets.value = []
      assetSearch.value = ''
      loadMembers(currentGroup.value.id)
      // 更新分组的资产计数
      loadGroups()
    } else {
      ElMessage.error(data.message || '添加失败')
    }
  } catch (e: any) {
    ElMessage.error('添加失败: ' + (e.message || e))
  } finally {
    addingMembers.value = false
  }
}

async function removeMember(assetId: string) {
  if (!currentGroup.value) return
  try {
    const { data } = await api.delete(R.ASSET_GROUP_MEMBER(currentGroup.value.id, assetId))
    if (data.code === 0) {
      ElMessage.success('已移除')
      loadMembers(currentGroup.value.id)
      loadGroups()
    }
  } catch (e: any) {
    ElMessage.error('移除失败: ' + (e.message || e))
  }
}

onMounted(() => {
  loadGroups()
})
</script>

<style scoped>
.group-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
  margin-bottom: 4px;
}
.group-item:hover {
  background: var(--autops-bg-2);
}
.group-item.active {
  background: var(--autops-primary-light-5);
  border: 1px solid var(--autops-primary-light-4);
}
.group-info {
  flex: 1;
  min-width: 0;
}
.group-name {
  font-weight: 500;
  font-size: var(--autops-font-14);
  display: flex;
  align-items: center;
}
.group-meta {
  margin-top: 4px;
}
.group-actions {
  flex-shrink: 0;
  margin-left: 8px;
}
.group-desc {
  margin-bottom: var(--autops-space-md);
  padding: var(--autops-space-sm) 12px;
  background: var(--autops-bg-2);
  border-radius: var(--autops-radius-sm);
}
</style>
