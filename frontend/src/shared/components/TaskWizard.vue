<template>
  <div class="task-wizard">
    <el-steps :active="currentStep" :space="200" finish-status="success" align-center class="wizard-steps">
      <el-step v-for="(step, idx) in steps" :key="idx" :title="step.title" :description="step.description" />
    </el-steps>

    <div class="wizard-content">
      <!-- Step content slot -->
      <slot :name="currentStepName" :step="currentStep" :data="formData" />

      <div v-if="!$slots[currentStepName]" class="wizard-default-content">
        <el-empty :description="steps[currentStep]?.description || '配置步骤'" :image-size="80" />
      </div>
    </div>

    <div class="wizard-footer">
      <el-button v-if="currentStep > 0" @click="prevStep">上一步</el-button>
      <el-button v-if="currentStep < steps.length - 1" type="primary" @click="nextStep" :disabled="!canNext">
        下一步
      </el-button>
      <el-button v-if="currentStep === steps.length - 1" type="primary" @click="handleSubmit" :loading="submitting">
        {{ submitText }}
      </el-button>
      <el-button @click="handleCancel">取消</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'

interface WizardStep {
  title: string
  description?: string
  name?: string
  validate?: () => boolean | Promise<boolean>
}

const props = withDefaults(defineProps<{
  steps: WizardStep[]
  submitText?: string
}>(), { submitText: '提交' })

const emit = defineEmits(['submit', 'cancel', 'step-change'])

const currentStep = ref(0)
const submitting = ref(false)
const formData = ref<Record<string, any>>({})

const currentStepName = computed(() => {
  return props.steps[currentStep.value]?.name || `step-${currentStep.value}`
})

const canNext = computed(() => {
  const step = props.steps[currentStep.value]
  if (step?.validate) return step.validate()
  return true
})

async function nextStep() {
  const step = props.steps[currentStep.value]
  if (step?.validate) {
    const valid = await step.validate()
    if (!valid) return
  }
  if (currentStep.value < props.steps.length - 1) {
    currentStep.value++
    emit('step-change', currentStep.value)
  }
}

function prevStep() {
  if (currentStep.value > 0) {
    currentStep.value--
    emit('step-change', currentStep.value)
  }
}

async function handleSubmit() {
  submitting.value = true
  try {
    emit('submit', formData.value)
  } finally {
    submitting.value = false
  }
}

function handleCancel() {
  emit('cancel')
}

defineExpose({ currentStep, formData, nextStep, prevStep })
</script>

<style scoped>
.task-wizard { padding: 20px; }
.wizard-steps { margin-bottom: 24px; }
.wizard-content {
  min-height: 200px; padding: 20px; border: 1px solid #f2f3f5;
  border-radius: 8px; background: #fafbfc; margin-bottom: 20px;
}
.wizard-default-content { display: flex; justify-content: center; align-items: center; min-height: 200px; }
.wizard-footer { display: flex; justify-content: flex-end; gap: 8px; }
</style>
