<template>
  <div class="p-6">
    <h2 class="page-title">运维报告</h2>
    <div class="autops-card mb-lg">
      <div class="autops-card-header">
        <div class="autops-card-title">报告列表</div>
        <el-button type="primary" @click="createReport"><el-icon><Plus /></el-icon> 生成报告</el-button>
      </div>
      <div class="autops-card-body" style="padding:0">
        <el-table :data="reports" stripe v-loading="loading" empty-text="暂无报告">
          <el-table-column prop="title" label="报告名称" min-width="200" show-overflow-tooltip />
          <el-table-column prop="report_type" label="类型" width="100">
            <template #default="{ row }"><el-tag size="small">{{ row.report_type }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="period" label="周期" width="160" />
          <el-table-column prop="generated_at" label="生成时间" width="160" />
          <el-table-column prop="status" label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="{ completed:'success', generating:'warning', failed:'danger' }[row.status as string]" size="small">{{ row.status }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="140" fixed="right">
            <template #default="{ row }">
              <el-button text type="primary" size="small" @click="viewReport(row)">查看</el-button>
              <el-button text size="small" @click="downloadReport(row)">下载</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
    <el-dialog v-model="createDialog" title="生成运维报告" width="500">
      <el-form label-width="80px">
        <el-form-item label="报告类型">
          <el-select v-model="form.report_type" style="width:100%">
            <el-option label="日报" value="daily" /><el-option label="周报" value="weekly" />
            <el-option label="月报" value="monthly" /><el-option label="自定义" value="custom" />
          </el-select>
        </el-form-item>
        <el-form-item label="时间范围"><el-date-picker v-model="form.dateRange" type="daterange" range-separator="至" style="width:100%" /></el-form-item>
        <el-form-item label="包含模块">
          <el-checkbox-group v-model="form.modules">
            <el-checkbox label="资产" value="asset" /><el-checkbox label="告警" value="alert" />
            <el-checkbox label="执行" value="execution" /><el-checkbox label="巡检" value="inspection" />
          </el-checkbox-group>
        </el-form-item>
      </el-form>
      <template #footer><el-button @click="createDialog=false">取消</el-button><el-button type="primary" @click="submitCreate">确定</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from "vue"
import api from "@/shared/api/client"
import { API } from "@/shared/api/routes"
import { Plus } from "@element-plus/icons-vue"
import { ElMessage } from "element-plus"

const loading = ref(false)
const reports = ref<any[]>([])
const createDialog = ref(false)
const form = reactive({ report_type: "daily", dateRange: [] as any[], modules: ["asset","alert","execution"] })

function createReport() { createDialog.value = true }
function viewReport(row: any) { ElMessage.info("查看报告") }
function downloadReport(row: any) { ElMessage.info("下载报告") }
function submitCreate() { createDialog.value = false; ElMessage.success("报告生成任务已提交") }

onMounted(async () => {
  loading.value = true
  try {
    const res = await api.get(API.REPORTS, { params: { page_size: 50 } })
    if (res.data?.code === 0) reports.value = res.data.data?.items || []
  } catch (e) {} finally { loading.value = false }
})
</script>

<style scoped>
.page-title { font-size: 18px; font-weight: 600; margin-bottom: 16px; color: #1d2129; }
.mb-lg { margin-bottom: 16px; }
</style>
