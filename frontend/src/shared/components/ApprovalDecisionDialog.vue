<template>
  <el-dialog v-model="visible" title="审批决策" width="500" destroy-on-close>
    <el-descriptions :column="1" border size="small">
      <el-descriptions-item label="任务名称">{{ task?.name }}</el-descriptions-item>
      <el-descriptions-item label="风险等级">
        <el-tag :type="riskType" size="small">{{ task?.risk_level }}</el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="申请人">{{ task?.requester }}</el-descriptions-item>
      <el-descriptions-item label="影响范围">{{ task?.scope }}</el-descriptions-item>
    </el-descriptions>
    <div style="margin-top:16px">
      <el-form label-width="80px">
        <el-form-item label="审批意见"><el-input type="textarea" v-model="comment" :rows="3" placeholder="输入审批意见" /></el-form-item>
      </el-form>
    </div>
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="danger" @click="reject">驳回</el-button>
      <el-button type="primary" @click="approve">批准</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed } from "vue"
import { ElMessage } from "element-plus"

const props = defineProps<{ modelValue: boolean; task?: { name: string; risk_level: string; requester: string; scope: string } }>()
const emit = defineEmits<{ "update:modelValue": [v: boolean]; approve: [comment: string]; reject: [comment: string] }>()

const visible = computed({ get: () => props.modelValue, set: v => emit("update:modelValue", v) })
const comment = ref("")

const riskType = computed(() => ({ low: "success", medium: "warning", high: "danger", critical: "danger" } as any)[props.task?.risk_level || ""] || "info")

function approve() { emit("approve", comment.value); visible.value = false; ElMessage.success("已批准") }
function reject() { emit("reject", comment.value); visible.value = false; ElMessage.info("已驳回") }
</script>
