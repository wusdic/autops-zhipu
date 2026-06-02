<template>
  <div class="p-6">
    <el-page-header @back="$router.back()" title="返回工单列表">
      <template #content><span class="page-title">创建工单</span></template>
    </el-page-header>
    <div class="autops-card" style="margin-top:16px">
      <div class="autops-card-body">
        <el-form ref="formRef" :model="form" :rules="rules" label-width="100px" style="max-width:700px">
          <el-form-item label="工单标题" prop="title"><el-input v-model="form.title" placeholder="简明描述问题" /></el-form-item>
          <el-form-item label="优先级" prop="priority">
            <el-select v-model="form.priority" style="width:100%">
              <el-option label="紧急" value="urgent" /><el-option label="高" value="high" />
              <el-option label="中" value="medium" /><el-option label="低" value="low" />
            </el-select>
          </el-form-item>
          <el-form-item label="工单类型" prop="ticket_type">
            <el-select v-model="form.ticket_type" style="width:100%">
              <el-option label="故障" value="fault" /><el-option label="告警" value="alert" />
              <el-option label="变更" value="change" /><el-option label="其他" value="other" />
            </el-select>
          </el-form-item>
          <el-form-item label="关联资产"><el-input v-model="form.asset" placeholder="资产名称或IP" /></el-form-item>
          <el-form-item label="关联告警"><el-input v-model="form.alert_id" placeholder="告警ID" /></el-form-item>
          <el-form-item label="指派给"><el-input v-model="form.assignee" placeholder="处理人" /></el-form-item>
          <el-form-item label="问题描述" prop="description"><el-input type="textarea" v-model="form.description" :rows="6" placeholder="详细描述问题现象和影响" /></el-form-item>
          <el-form-item label="附件"><el-upload action="" :auto-upload="false" :limit="5"><el-button>上传附件</el-button></el-upload></el-form-item>
          <el-form-item><el-button type="primary" @click="submitCreate" :loading="submitting">提交工单</el-button><el-button @click="$router.back()">取消</el-button></el-form-item>
        </el-form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from "vue"
import { useRouter } from "vue-router"
import api from "@/shared/api/client"
import { API } from "@/shared/api/routes"
import { ElMessage } from "element-plus"

const router = useRouter()
const formRef = ref<any>()
const submitting = ref(false)
const form = reactive({ title: "", priority: "medium", ticket_type: "fault", asset: "", alert_id: "", assignee: "", description: "" })
const rules = { title: [{ required: true, message: "请输入标题" }], priority: [{ required: true, message: "请选择优先级" }], description: [{ required: true, message: "请输入描述" }] }

async function submitCreate() {
  await formRef.value?.validate()
  submitting.value = true
  try {
    const res = await api.post(API.TICKETS, form)
    if (res.data?.code === 0) { ElMessage.success("工单创建成功"); router.push("/tickets") }
    else ElMessage.error(res.data?.message || "创建失败")
  } catch (e: any) { ElMessage.error(e.message || "创建失败") } finally { submitting.value = false }
}
</script>

<style scoped>
.page-title { font-size: 18px; font-weight: 600; color: #1d2129; }
</style>
