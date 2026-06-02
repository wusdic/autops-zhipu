<template>
  <el-dialog v-model="visible" title="生成报告" width="600" destroy-on-close>
    <el-steps :active="step" finish-status="success" style="margin-bottom:24px">
      <el-step title="选择类型" /><el-step title="配置参数" /><el-step title="确认" />
    </el-steps>
    <div v-if="step === 0">
      <el-radio-group v-model="form.report_type" @change="step = 1">
        <div style="display:flex;flex-direction:column;gap:12px">
          <el-radio value="daily" border style="padding:12px">日报 — 每日运维概况</el-radio>
          <el-radio value="weekly" border style="padding:12px">周报 — 本周运维汇总</el-radio>
          <el-radio value="monthly" border style="padding:12px">月报 — 月度运维报告</el-radio>
          <el-radio value="custom" border style="padding:12px">自定义 — 选择时间范围</el-radio>
        </div>
      </el-radio-group>
    </div>
    <div v-if="step === 1">
      <el-form label-width="100px">
        <el-form-item label="时间范围">
          <el-date-picker v-model="form.dateRange" type="daterange" range-separator="至" style="width:100%" />
        </el-form-item>
        <el-form-item label="包含模块">
          <el-checkbox-group v-model="form.modules">
            <el-checkbox label="资产" value="asset" /><el-checkbox label="告警" value="alert" />
            <el-checkbox label="执行" value="execution" /><el-checkbox label="巡检" value="inspection" />
            <el-checkbox label="工单" value="ticket" />
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="格式">
          <el-radio-group v-model="form.format">
            <el-radio value="pdf">PDF</el-radio><el-radio value="html">HTML</el-radio><el-radio value="xlsx">Excel</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
    </div>
    <div v-if="step === 2">
      <el-descriptions :column="1" border size="small">
        <el-descriptions-item label="报告类型">{{ { daily: "日报", weekly: "周报", monthly: "月报", custom: "自定义" }[form.report_type as string] }}</el-descriptions-item>
        <el-descriptions-item label="时间范围">{{ form.dateRange?.[0] }} ~ {{ form.dateRange?.[1] }}</el-descriptions-item>
        <el-descriptions-item label="模块">{{ form.modules.join(", ") }}</el-descriptions-item>
        <el-descriptions-item label="格式">{{ form.format?.toUpperCase() }}</el-descriptions-item>
      </el-descriptions>
    </div>
    <template #footer>
      <el-button v-if="step > 0" @click="step--">上一步</el-button>
      <el-button v-if="step < 2" type="primary" @click="step++">下一步</el-button>
      <el-button v-if="step === 2" type="primary" @click="submit">确认生成</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from "vue"
import { ElMessage } from "element-plus"

const props = defineProps<{ modelValue: boolean }>()
const emit = defineEmits<{ "update:modelValue": [v: boolean]; submit: [form: any] }>()
const visible = computed({ get: () => props.modelValue, set: v => emit("update:modelValue", v) })

const step = ref(0)
const form = reactive({ report_type: "daily", dateRange: [] as any[], modules: ["asset", "alert", "execution"], format: "pdf" })

function submit() {
  emit("submit", { ...form })
  visible.value = false
  ElMessage.success("报告生成任务已提交")
}
</script>
