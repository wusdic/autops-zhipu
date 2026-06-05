<template>
  <div class="remediation-template-page">
    <div class="autops-page-header">
      <div class="autops-page-title-row">
        <el-button plain @click="router.back()"><el-icon><ArrowLeft /></el-icon> 返回</el-button>
        <span class="autops-page-title">处置模板</span>
      </div>
      <div class="autops-page-desc">管理和配置自动处置模板，定义故障处置步骤</div>
    </div>
    <div style="display: flex; gap: 8px; margin-bottom: 16px">
      <el-button type="primary" @click="openDialog()">
        <el-icon><Plus /></el-icon> 新建模板
      </el-button>
      <el-button @click="loadData" :loading="loading">
        <el-icon><Refresh /></el-icon> 刷新
      </el-button>
    </div>

    <el-card class="mt-lg" shadow="never">
      <el-form :inline="true" :model="filters">
        <el-form-item label="模板名称">
          <el-input v-model="filters.keyword" placeholder="搜索" clearable @clear="loadData" />
        </el-form-item>
        <el-form-item label="场景类型">
          <el-select v-model="filters.scenario" placeholder="全部" clearable @change="loadData">
            <el-option label="磁盘空间" value="disk_full" />
            <el-option label="服务异常" value="service_down" />
            <el-option label="端口不可达" value="port_unreachable" />
            <el-option label="连接数过高" value="connection_high" />
            <el-option label="证书过期" value="cert_expiry" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">搜索</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="mt-lg" shadow="never">
      <el-table stripe :data="templates" v-loading="loading"border>
        <el-table-column type="selection" width="50" />
        <el-table-column prop="name" label="模板名称" min-width="200" sortable />
        <el-table-column prop="scenario" label="适用场景" width="140">
          <template #default="{ row }">
            <el-tag size="small">{{ scenarioName(row.scenario) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="risk_level" label="风险等级" width="100">
          <template #default="{ row }">
            <el-tag :type="riskType(row.risk_level)" size="small">{{ riskLabel(row.risk_level) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="steps_count" label="执行步骤" width="100" />
        <el-table-column prop="requires_approval" label="需要审批" width="100">
          <template #default="{ row }">
            <el-tag :type="row.requires_approval ? 'danger' : 'success'" size="small">
              {{ row.requires_approval ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="usage_count" label="使用次数" width="100" />
        <el-table-column prop="success_rate" label="成功率" width="100">
          <template #default="{ row }">
            <span :style="{ color: row.success_rate >= 90 ? '#00b42a' : row.success_rate >= 70 ? '#ff7d00' : '#f53f3f' }">
              {{ row.success_rate ?? '-' }}%
            </span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button plain type="primary" @click="openDialog(row)">编辑</el-button>
            <el-button plain type="primary" @click="dryRun(row)">Dry-Run</el-button>
            <el-button plain type="primary" @click="viewHistory(row)">历史</el-button>
            <el-button plain type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination class="mt-lg" v-model:current-page="pagination.page" v-model:page-size="pagination.size"
        :total="pagination.total" :page-sizes="[20, 50, 100]" layout="total, sizes, prev, pager, next"
        @size-change="loadData" @current-change="loadData" />
    </el-card>

    <!-- 新建/编辑 -->
    <el-dialog v-model="dialogVisible" :title="editing ? '编辑处置模板' : '新建处置模板'" width="780px" destroy-on-close>
      <el-form :model="form" label-width="100px" :rules="formRules" ref="formRef">
        <el-form-item label="模板名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="适用场景" prop="scenario">
          <el-select v-model="form.scenario" style="width: 100%">
            <el-option label="磁盘空间异常" value="disk_full" />
            <el-option label="服务异常" value="service_down" />
            <el-option label="端口不可达" value="port_unreachable" />
            <el-option label="连接数过高" value="connection_high" />
            <el-option label="证书过期" value="cert_expiry" />
          </el-select>
        </el-form-item>
        <el-form-item label="风险等级" prop="risk_level">
          <el-select v-model="form.risk_level" style="width: 100%">
            <el-option label="低" value="low" />
            <el-option label="中" value="medium" />
            <el-option label="高" value="high" />
            <el-option label="极高" value="critical" />
          </el-select>
        </el-form-item>
        <el-form-item label="适用资产类型">
          <el-select v-model="form.asset_types" multiple style="width: 100%">
            <el-option label="Linux服务器" value="linux_server" />
            <el-option label="Windows服务器" value="windows_server" />
            <el-option label="MySQL" value="mysql" />
            <el-option label="Web应用" value="web_app" />
          </el-select>
        </el-form-item>
        <el-form-item label="执行步骤">
          <div v-for="(step, idx) in form.steps" :key="idx" class="step-item">
            <el-row :gutter="8">
              <el-col :span="3"><el-tag>步骤{{ idx + 1 }}</el-tag></el-col>
              <el-col :span="8"><el-input v-model="step.name" placeholder="步骤名称" /></el-col>
              <el-col :span="9"><el-input v-model="step.command" placeholder="执行命令/脚本" /></el-col>
              <el-col :span="4">
                <el-button plain type="danger" @click="form.steps.splice(idx, 1)" v-if="form.steps.length > 1">删除</el-button>
              </el-col>
            </el-row>
          </div>
          <el-button @click="form.steps.push({ name: '', command: '' })" size="small">+ 添加步骤</el-button>
        </el-form-item>
        <el-form-item label="验证条件">
          <el-input v-model="form.verification" type="textarea" :rows="2" placeholder="执行后验证条件" />
        </el-form-item>
        <el-form-item label="回滚动作">
          <el-input v-model="form.rollback_action" type="textarea" :rows="2" placeholder="失败时回滚动作" />
        </el-form-item>
        <el-form-item label="需要审批">
          <el-switch v-model="form.requires_approval" />
          <span class="ml-2 text-muted">高风险模板建议开启审批</span>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="2" />
        </el-form-item>
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
import { Plus, Refresh, ArrowLeft } from '@element-plus/icons-vue'

const router = useRouter()
const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const editing = ref<any>(null)
const templates = ref<any[]>([])
const formRef = ref()

const filters = reactive({ keyword: '', scenario: '' })
const pagination = reactive({ page: 1, size: 20, total: 0 })

const form = reactive({
  name: '', scenario: '', risk_level: 'low', asset_types: [] as string[],
  steps: [{ name: '', command: '' }] as { name: string; command: string }[],
  verification: '', rollback_action: '', requires_approval: false, description: '',
})
const formRules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  scenario: [{ required: true, message: '请选择场景', trigger: 'change' }],
}

const scenarioMap: Record<string, string> = { disk_full: '磁盘空间', service_down: '服务异常', port_unreachable: '端口不可达', connection_high: '连接数过高', cert_expiry: '证书过期' }
function scenarioName(s: string) { return scenarioMap[s] || s }
function riskType(r: string) { return { low: 'info', medium: '', high: 'warning', critical: 'danger' }[r] || 'info' }
function riskLabel(r: string) { return { low: '低', medium: '中', high: '高', critical: '极高' }[r] || r }

async function loadData() {
  loading.value = true
  try { templates.value = []; pagination.total = 0 } finally { loading.value = false }
}

function openDialog(row?: any) {
  editing.value = row || null
  if (row) Object.assign(form, row)
  else Object.assign(form, { name: '', scenario: '', risk_level: 'low', asset_types: [], steps: [{ name: '', command: '' }], verification: '', rollback_action: '', requires_approval: false, description: '' })
  dialogVisible.value = true
}

async function handleSubmit() {
  await formRef.value?.validate()
  submitting.value = true
  try {
    ElMessage.success(editing.value ? '更新成功' : '创建成功')
    dialogVisible.value = false
    loadData()
  } finally { submitting.value = false }
}

async function dryRun(row: any) {
  try {
    await ElMessageBox.confirm('对模板「' + row.name + '」执行 Dry-Run？仅模拟不实际执行。', 'Dry-Run 确认', { type: 'info' })
    ElMessage.success('Dry-Run 已启动')
  } catch { /* cancelled */ }
}

function viewHistory(row: any) { ElMessage.info('历史记录功能开发中') }

async function handleDelete(row: any) {
  try {
    await ElMessageBox.confirm('确认删除「' + row.name + '」？', '删除确认', { type: 'warning' })
    ElMessage.success('已删除'); loadData()
  } catch { /* cancelled */ }
}

onMounted(loadData)
</script>

<style scoped>
.remediation-template-page { padding: var(--autops-space-xl); }
.mt-4 { margin-top: var(--autops-space-lg); }
.step-item { margin-bottom: var(--autops-space-sm); }
.ml-2 { margin-left: 8px; }
.text-muted { color: var(--autops-info); }
</style>
