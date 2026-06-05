<template>
  <div class="audit-filter-panel">
    <el-form :inline="true" :model="modelValue" @submit.prevent="$emit('search')">
      <el-form-item label="操作人">
        <el-input :model-value="modelValue.user_name" @update:model-value="updateField('user_name', $event)" placeholder="用户名" clearable style="width:130px" />
      </el-form-item>
      <el-form-item label="操作类型">
        <el-select :model-value="modelValue.action" @update:model-value="updateField('action', $event)" clearable style="width:120px">
          <el-option v-for="a in actionTypes" :key="a.value" :label="a.label" :value="a.value" />
        </el-select>
      </el-form-item>
      <el-form-item label="资源类型">
        <el-select :model-value="modelValue.resource_type" @update:model-value="updateField('resource_type', $event)" clearable style="width:120px">
          <el-option v-for="r in resourceTypes" :key="r" :label="r" :value="r" />
        </el-select>
      </el-form-item>
      <el-form-item label="时间范围">
        <el-date-picker :model-value="modelValue.date_range" @update:model-value="updateField('date_range', $event)"
          type="datetimerange" range-separator="至" style="width:340px" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="$emit('search')">查询</el-button>
        <el-button @click="$emit('reset')">重置</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  modelValue: Record<string, any>
  actionTypes?: { label: string; value: string }[]
  resourceTypes?: string[]
}>()

const emit = defineEmits<{ "update:modelValue": [v: any]; search: []; reset: [] }>()

const defaultActionTypes = [
  { label: "创建", value: "create" }, { label: "修改", value: "update" },
  { label: "删除", value: "delete" }, { label: "登录", value: "login" },
  { label: "执行", value: "execute" }, { label: "审批", value: "approve" },
]
const defaultResourceTypes = ["asset", "credential", "policy", "script", "playbook", "user", "role", "ticket", "knowledge"]

const actionTypes = props.actionTypes || defaultActionTypes
const resourceTypes = props.resourceTypes || defaultResourceTypes

function updateField(field: string, value: any) {
  emit("update:modelValue", { ...props.modelValue, [field]: value })
}
</script>

<style scoped>
.audit-filter-panel { padding: var(--autops-space-md) 16px; background: var(--autops-bg-1); border-radius: var(--autops-radius-md); border: 1px solid var(--autops-bg-4); margin-bottom: var(--autops-space-lg); }
.audit-filter-panel :deep(.el-form-item) { margin-bottom: 0; }
</style>
