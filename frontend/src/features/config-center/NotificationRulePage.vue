<template>
  <div class="notification-rule-page">
    <el-page-header @back="router.back()" title="返回" content="通知规则管理">
      <template #extra>
        <el-button type="primary" @click="openDialog()">
          <el-icon><Plus /></el-icon> 新建通知规则
        </el-button>
        <el-button @click="loadData" :loading="loading">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
      </template>
    </el-page-header>

    <!-- 搜索 -->
    <el-card class="mt-4" shadow="never">
      <el-form :inline="true" :model="filters">
        <el-form-item label="规则名称">
          <el-input v-model="filters.keyword" placeholder="搜索" clearable @clear="loadData" />
        </el-form-item>
        <el-form-item label="通知渠道">
          <el-select v-model="filters.channel" placeholder="全部" clearable @change="loadData">
            <el-option label="邮件" value="email" />
            <el-option label="短信" value="sms" />
            <el-option label="钉钉" value="dingtalk" />
            <el-option label="企业微信" value="wecom" />
            <el-option label="Webhook" value="webhook" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">搜索</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 规则列表 -->
    <el-card class="mt-4" shadow="never">
      <el-table :data="rules" v-loading="loading" stripe border>
        <el-table-column type="selection" width="50" />
        <el-table-column prop="name" label="规则名称" min-width="200" sortable />
        <el-table-column prop="trigger_type" label="触发条件" width="150">
          <template #default="{ row }">
            <el-tag size="small">{{ triggerName(row.trigger_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="channel" label="通知渠道" width="120">
          <template #default="{ row }">
            <el-tag :type="channelType(row.channel)" size="small">{{ channelName(row.channel) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="recipients" label="接收人" min-width="150">
          <template #default="{ row }">
            <el-tag v-for="r in (row.recipients || []).slice(0, 3)" :key="r" size="small" class="mr-1">{{ r }}</el-tag>
            <span v-if="(row.recipients || []).length > 3" class="text-muted">+{{ row.recipients.length - 3 }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="cooldown" label="冷却时间" width="100" />
        <el-table-column prop="daily_limit" label="日限" width="80" />
        <el-table-column prop="sent_count" label="近7天" width="90" />
        <el-table-column prop="enabled" label="状态" width="80">
          <template #default="{ row }">
            <el-switch v-model="row.enabled" size="small" @change="toggleRule(row)" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDialog(row)">编辑</el-button>
            <el-button link type="primary" @click="testNotify(row)">测试</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination class="mt-4" v-model:current-page="pagination.page" v-model:page-size="pagination.size"
        :total="pagination.total" :page-sizes="[20, 50, 100]" layout="total, sizes, prev, pager, next"
        @size-change="loadData" @current-change="loadData" />
    </el-card>

    <!-- 新建/编辑 -->
    <el-dialog v-model="dialogVisible" :title="editing ? '编辑通知规则' : '新建通知规则'" width="650px" destroy-on-close>
      <el-form :model="form" label-width="100px" :rules="formRules" ref="formRef">
        <el-form-item label="规则名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="触发条件" prop="trigger_type">
          <el-select v-model="form.trigger_type" style="width: 100%">
            <el-option label="告警触发" value="alert" />
            <el-option label="异常触发" value="anomaly" />
            <el-option label="自动化失败" value="automation_failed" />
            <el-option label="采集器离线" value="collector_offline" />
            <el-option label="证书过期" value="cert_expiry" />
            <el-option label="工单创建" value="ticket_created" />
          </el-select>
        </el-form-item>
        <el-form-item label="告警级别过滤">
          <el-checkbox-group v-model="form.severity_filter">
            <el-checkbox label="critical">紧急</el-checkbox>
            <el-checkbox label="high">高危</el-checkbox>
            <el-checkbox label="medium">中危</el-checkbox>
            <el-checkbox label="low">低危</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="通知渠道" prop="channel">
          <el-select v-model="form.channel" style="width: 100%">
            <el-option label="邮件" value="email" />
            <el-option label="短信" value="sms" />
            <el-option label="钉钉" value="dingtalk" />
            <el-option label="企业微信" value="wecom" />
            <el-option label="Webhook" value="webhook" />
          </el-select>
        </el-form-item>
        <el-form-item label="接收人" prop="recipients">
          <el-select v-model="form.recipients" multiple filterable allow-create style="width: 100%" placeholder="输入接收人">
          </el-select>
        </el-form-item>
        <el-form-item label="通知模板">
          <el-input v-model="form.template" type="textarea" :rows="3" placeholder="支持变量：{alert_name}, {severity}, {asset_name}, {time}" />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="冷却时间">
              <el-input-number v-model="form.cooldown" :min="0" :max="1440" style="width: 100%" /> 分钟
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="每日上限">
              <el-input-number v-model="form.daily_limit" :min="0" :max="1000" style="width: 100%" /> 条
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'

const router = useRouter()
const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const editing = ref<any>(null)
const rules = ref<any[]>([])
const formRef = ref()

const filters = reactive({ keyword: '', channel: '' })
const pagination = reactive({ page: 1, size: 20, total: 0 })

const form = reactive({
  name: '', trigger_type: '', channel: 'email', recipients: [] as string[],
  template: '', cooldown: 30, daily_limit: 100, severity_filter: ['critical', 'high'] as string[],
})
const formRules = {
  name: [{ required: true, message: '请输入规则名称', trigger: 'blur' }],
  trigger_type: [{ required: true, message: '请选择触发条件', trigger: 'change' }],
  channel: [{ required: true, message: '请选择通知渠道', trigger: 'change' }],
  recipients: [{ type: 'array' as const, required: true, message: '请选择接收人', trigger: 'change' }],
}

const triggerMap: Record<string, string> = { alert: '告警触发', anomaly: '异常触发', automation_failed: '自动化失败', collector_offline: '采集器离线', cert_expiry: '证书过期', ticket_created: '工单创建' }
function triggerName(t: string) { return triggerMap[t] || t }
const channelMap: Record<string, string> = { email: '邮件', sms: '短信', dingtalk: '钉钉', wecom: '企业微信', webhook: 'Webhook' }
function channelName(c: string) { return channelMap[c] || c }
function channelType(c: string) { return { email: 'primary', sms: 'warning', dingtalk: 'success', wecom: '', webhook: 'info' }[c] || 'info' }

async function loadData() {
  loading.value = true
  try { rules.value = []; pagination.total = 0 } finally { loading.value = false }
}

function openDialog(row?: any) {
  editing.value = row || null
  if (row) Object.assign(form, row)
  else Object.assign(form, { name: '', trigger_type: '', channel: 'email', recipients: [], template: '', cooldown: 30, daily_limit: 100, severity_filter: ['critical', 'high'] })
  dialogVisible.value = true
}

async function handleSubmit() {
  await formRef.value?.validate()
  submitting.value = true
  try {
    ElMessage.success(editing.value ? '规则更新成功' : '规则创建成功')
    dialogVisible.value = false
    loadData()
  } finally { submitting.value = false }
}

async function toggleRule(row: any) { ElMessage.success(`规则已${row.enabled ? '启用' : '禁用'}`) }

async function testNotify(row: any) {
  try {
    ElMessage.success('测试通知已发送')
  } catch (e: any) { ElMessage.error('发送失败: ' + e.message) }
}

async function handleDelete(row: any) {
  try {
    await ElMessageBox.confirm(`确认删除「${row.name}」？`, '删除确认', { type: 'warning' })
    ElMessage.success('已删除')
    loadData()
  } catch { /* cancelled */ }
}

onMounted(loadData)
</script>

<style scoped>
.notification-rule-page { padding: 20px; }
.mt-4 { margin-top: 16px; }
.mr-1 { margin-right: 4px; }
.text-muted { color: #909399; font-size: 12px; }
</style>
