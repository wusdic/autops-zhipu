<template>
  <el-dialog v-model="visible" title="审批确认" width="500px" @close="$emit('cancel')">
    <el-form label-width="80px">
      <el-form-item label="审批结果">
        <el-radio-group v-model="decision">
          <el-radio value="approved">批准</el-radio>
          <el-radio value="rejected">驳回</el-radio>
        </el-radio-group>
      </el-form-item>
      <el-form-item label="审批意见">
        <el-input v-model="comment" type="textarea" :rows="3" placeholder="请输入审批意见" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" @click="submit" :disabled="!decision">提交</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'

const props = defineProps<{ modelValue: boolean; title?: string }>()
const emit = defineEmits(['update:modelValue', 'confirm', 'cancel'])

const visible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})
const decision = ref('')
const comment = ref('')

// 每次打开时清空上次的决定与意见，避免残留
watch(visible, (v) => {
  if (v) {
    decision.value = ''
    comment.value = ''
  }
})

function submit() {
  emit('confirm', { decision: decision.value, comment: comment.value })
  visible.value = false
}
</script>
