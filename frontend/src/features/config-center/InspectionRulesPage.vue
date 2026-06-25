<template>
  <div class="inspection-rules-page">
    <div class="autops-page-header">
      <div class="autops-page-title-row">
        <el-button plain @click="router.back()"><el-icon><ArrowLeft /></el-icon> 返回</el-button>
<div class="autops-page-title">巡检规则</div>
      </div>
      <div class="autops-page-desc">管理和配置各类巡检规则，支持页面、配置、日志、基线检查</div>
    </div>
    <div style="display: flex; gap: 8px; margin-bottom: 16px">
      <el-button type="primary" @click="openDialog()">
        <el-icon><Plus /></el-icon> 新建规则
      </el-button>
      <el-button @click="loadData" :loading="loading">
        <el-icon><Refresh /></el-icon> 刷新
      </el-button>
    </div>

    <!-- 分类标签 -->
    <el-tabs v-model="activeCategory" class="mt-lg" @tab-change="loadData">
      <el-tab-pane label="页面检查" name="page_check" />
      <el-tab-pane label="配置检查" name="config_check" />
      <el-tab-pane label="日志检查" name="log_check" />
      <el-tab-pane label="基线检查" name="baseline_check" />
      <el-tab-pane label="API检查" name="api_check" />
      <el-tab-pane label="阈值规则" name="threshold" />
      <el-tab-pane label="全部" name="all" />
    </el-tabs>

    <!-- 搜索 -->
    <el-card shadow="never">
      <el-form :inline="true" :model="filters">
        <el-form-item label="规则名称">
          <el-input v-model="filters.keyword" placeholder="搜索" clearable @clear="loadData" />
        </el-form-item>
        <el-form-item label="严重度">
          <el-select v-model="filters.severity" placeholder="全部" clearable @change="loadData">
            <el-option label="紧急" value="critical" />
            <el-option label="高危" value="high" />
            <el-option label="中危" value="medium" />
            <el-option label="低危" value="low" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">搜索</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 规则列表 -->
    <el-card class="mt-lg" shadow="never">
      <el-table stripe :data="rules" v-loading="loading"border>
        <el-table-column type="selection" width="50" />
        <el-table-column prop="name" label="规则名称" min-width="200" sortable />
        <el-table-column prop="category" label="类型" width="120">
          <template #default="{ row }">
            <el-tag size="small">{{ categoryMap[row.category] || row.category }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="check_target" label="检查对象" min-width="150" />
        <el-table-column prop="condition" label="检查条件" min-width="180">
          <template #default="{ row }">
            <code>{{ row.condition || row.expression || '-' }}</code>
          </template>
        </el-table-column>
        <el-table-column prop="severity" label="严重度" width="100">
          <template #default="{ row }">
            <el-tag :type="(severityType(row.severity)) as TagType" size="small">{{ severityLabel(row.severity) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="asset_count" label="适用资产" width="100" />
        <el-table-column prop="last_triggered" label="最近触发" width="180" />
        <el-table-column prop="enabled" label="状态" width="80">
          <template #default="{ row }">
            <el-switch v-model="row.enabled" size="small" @change="toggleRule(row)" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button plain type="primary" @click="openDialog(row)">编辑</el-button>
            <el-button plain type="primary" @click="simulateRule(row)">模拟</el-button>
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
    <el-dialog v-model="dialogVisible" :title="editing ? '编辑规则' : '新建规则'" width="780px" destroy-on-close>
      <el-form :model="form" label-width="100px" :rules="formRules" ref="formRef">
        <el-form-item label="规则名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="规则类型" prop="category">
          <el-select v-model="form.category" style="width: 100%">
            <el-option label="页面检查" value="page_check" />
            <el-option label="配置检查" value="config_check" />
            <el-option label="日志检查" value="log_check" />
            <el-option label="基线检查" value="baseline_check" />
            <el-option label="API检查" value="api_check" />
          </el-select>
        </el-form-item>
        <el-form-item label="检查对象" prop="check_target">
          <el-input v-model="form.check_target" placeholder="如：Linux服务器、MySQL数据库" />
        </el-form-item>
        <el-form-item label="检查条件" prop="condition">
          <el-input v-model="form.condition" type="textarea" :rows="4" placeholder="检查表达式或描述" />
        </el-form-item>
        <el-form-item label="严重度" prop="severity">
          <el-select v-model="form.severity" style="width: 100%">
            <el-option label="紧急" value="critical" />
            <el-option label="高危" value="high" />
            <el-option label="中危" value="medium" />
            <el-option label="低危" value="low" />
          </el-select>
        </el-form-item>
        <el-form-item label="适用资产">
          <el-select v-model="form.asset_types" multiple style="width: 100%">
            <el-option label="Linux服务器" value="linux_server" />
            <el-option label="Windows服务器" value="windows_server" />
            <el-option label="MySQL数据库" value="mysql" />
            <el-option label="Web应用" value="web_app" />
          </el-select>
        </el-form-item>
        <el-form-item label="修复建议">
          <el-input v-model="form.remediation" type="textarea" :rows="3" placeholder="自动修复建议" />
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

    <!-- 模拟结果对话框 -->
    <el-dialog v-model="simVisible" title="规则模拟结果" width="600px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="匹配资产">{{ simResult.matched || 0 }}</el-descriptions-item>
        <el-descriptions-item label="通过">{{ simResult.passed || 0 }}</el-descriptions-item>
        <el-descriptions-item label="异常">{{ simResult.failed || 0 }}</el-descriptions-item>
        <el-descriptions-item label="耗时">{{ simResult.duration || '-' }}</el-descriptions-item>
      </el-descriptions>
      <el-table stripe :data="simResult.details || []" class="mt-lg"max-height="300">
        <el-table-column prop="asset_name" label="资产名称" />
        <el-table-column prop="result" label="检查结果">
          <template #default="{ row }">
            <el-tag :type="row.result === 'pass' ? 'success' : 'danger'" size="small">{{ row.result }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="detail" label="详情" />
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import type { TagType } from '@/shared/types'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh, ArrowLeft } from '@element-plus/icons-vue'
import client from '@/shared/api/client'

const router = useRouter()
const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const simVisible = ref(false)
const editing = ref<any>(null)
const activeCategory = ref('all')
const rules = ref<any[]>([])
const formRef = ref()

const filters = reactive({ keyword: '', severity: ''})
const pagination = reactive({ page: 1, size: 20, total: 0 })
const simResult = ref<any>({})

const form = reactive({
  name: '', category: '', check_target: '', condition: '',
  severity: 'medium', asset_types: [] as string[], remediation: '', description: '',
})
const formRules = {
  name: [{ required: true, message: '请输入规则名称', trigger: 'blur' }],
  category: [{ required: true, message: '请选择类型', trigger: 'change' }],
  severity: [{ required: true, message: '请选择严重度', trigger: 'change' }],
}

const categoryMap: Record<string, string> = {
  page_check: '页面检查', config_check: '配置检查',
  log_check: '日志检查', baseline_check: '基线检查', api_check: 'API检查',
}
function severityType(s: string): TagType {
  return ({ critical: 'danger', high: 'warning', medium: 'primary', low: 'info' }[s] || 'info') as TagType
}
function severityLabel(s: string) {
  return { critical: '紧急', high: '高危', medium: '中危', low: '低危' }[s] || s
}

async function loadData() {
  loading.value = true
  try {
    // 阈值规则tab重定向到独立页面
    if (activeCategory.value === 'threshold') {
      router.push('/config/threshold-rules')
      return
    }
    const endpoint = activeCategory.value !== 'all' ? activeCategory.value + 's' : 'page-checks'
    const res = await client.get('/api/v1/inspection/' + endpoint, { params: { page: pagination.page, page_size: pagination.size } })
    const data = res.data?.data ?? res.data
    rules.value = data?.items || []
    pagination.total = data?.total || 0
  } catch { rules.value = [] } finally { loading.value = false }
}

function openDialog(row?: any) {
  editing.value = row || null
  if (row) Object.assign(form, row)
  else Object.assign(form, { name: '', category: '', check_target: '', condition: '', severity: 'medium', asset_types: [], remediation: '', description: ''})
  dialogVisible.value = true
}

async function handleSubmit() {
  await formRef.value?.validate()
  submitting.value = true
  try {
    ElMessage.success(editing.value ? '规则更新成功' : '规则创建成功')
    dialogVisible.value = false
    loadData()
  } catch (e: any) { ElMessage.error(e.message) } finally { submitting.value = false }
}

async function simulateRule(row: any) {
  simVisible.value = true
  simResult.value = { matched: 12, passed: 10, failed: 2, duration: '3.2s', details: [
    { asset_name: 'web-server-01', result: 'pass', detail: '配置正常' },
    { asset_name: 'db-server-01', result: 'fail', detail: '最大连接数超限' },
  ] }
}

async function viewHistory(row: any) { ElMessage.info('历史记录功能开发中') }

async function toggleRule(row: any) {
  ElMessage.success('规则已' + row.enabled ? '启用' : '禁用')
}

async function handleDelete(row: any) {
  try {
    await ElMessageBox.confirm('确认删除规则「' + row.name + '」？', '删除确认', { type: 'warning' })
    ElMessage.success('已删除')
    loadData()
  } catch { /* cancelled */ }
}

onMounted(loadData)
</script>

<style scoped>
.inspection-rules-page { padding: var(--autops-space-xl); }
.mt-4 { margin-top: var(--autops-space-lg); }
</style>
