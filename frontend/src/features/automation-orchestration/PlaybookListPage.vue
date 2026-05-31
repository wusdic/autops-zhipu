<template>
  <div class="page-container">
    <el-row :gutter="16" class="stat-row">
      <el-col :span="6"><el-card shadow="hover" class="stat-card"><div class="stat-value">{{ stats.total }}</div><div class="stat-label">Playbook 总数</div></el-card></el-col>
      <el-col :span="6"><el-card shadow="hover" class="stat-card success"><div class="stat-value">{{ stats.active }}</div><div class="stat-label">已激活</div></el-card></el-col>
      <el-col :span="6"><el-card shadow="hover" class="stat-card primary"><div class="stat-value">{{ stats.withScripts }}</div><div class="stat-label">关联脚本</div></el-card></el-col>
      <el-col :span="6"><el-card shadow="hover" class="stat-card warning"><div class="stat-value">{{ stats.avgSteps }}</div><div class="stat-label">平均步骤数</div></el-card></el-col>
    </el-row>

    <div class="toolbar">
      <el-input v-model="filters.keyword" placeholder="搜索名称/描述" clearable style="width:220px;margin-right:8px" @clear="load" @keyup.enter="load" />
      <el-select v-model="filters.status" placeholder="状态" clearable style="width:130px;margin-right:8px">
        <el-option label="草稿" value="draft" /><el-option label="已激活" value="active" /><el-option label="已废弃" value="deprecated" />
      </el-select>
      <el-select v-model="filters.risk_level" placeholder="风险等级" clearable style="width:130px;margin-right:8px">
        <el-option label="低" value="low" /><el-option label="中" value="medium" /><el-option label="高" value="high" /><el-option label="严重" value="critical" />
      </el-select>
      <el-button type="primary" @click="load"><el-icon><Search /></el-icon> 搜索</el-button>
      <el-button @click="resetFilters">重置</el-button>
      <div style="flex:1" />
      <el-button type="primary" @click="openCreate"><el-icon><Plus /></el-icon> 新建 Playbook</el-button>
    </div>

    <el-table :data="items" v-loading="loading" stripe>
      <el-table-column prop="name" label="名称" min-width="160">
        <template #default="{ row }"><el-link type="primary" @click="viewDetail(row)">{{ row.name }}</el-link></template>
      </el-table-column>
      <el-table-column prop="description" label="描述" min-width="180" show-overflow-tooltip />
      <el-table-column label="步骤数" width="90" align="center">
        <template #default="{ row }"><el-tag size="small">{{ row.steps?.length || 0 }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }"><el-tag :type="row.status==='active'?'success':row.status==='draft'?'info':'warning'" size="small">{{ statusLabel(row.status) }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="risk_level" label="风险" width="90">
        <template #default="{ row }"><el-tag :type="riskType(row.risk_level)" size="small">{{ row.risk_level || 'low' }}</el-tag></template>
      </el-table-column>
      <el-table-column label="关联策略" width="90" align="center">
        <template #default="{ row }">{{ row.policy_count || 0 }}</template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="170">
        <template #default="{ row }">{{ fmt(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="240" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="viewDetail(row)">详情</el-button>
          <el-button size="small" type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" @click="duplicate(row)">复制</el-button>
          <el-button size="small" type="success" @click="quickExec(row)">执行</el-button>
          <el-button size="small" type="danger" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination v-if="total > pageSize" class="pagination" :current-page="page" :page-size="pageSize" :total="total" @current-change="(p:number)=>{page=p;load()}" layout="total, prev, pager, next" />

    <!-- 创建/编辑对话框 -->
    <el-dialog v-model="showDialog" :title="editing?'编辑 Playbook':'新建 Playbook'" width="900px" top="5vh">
      <el-form :model="form" label-width="100px">
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="名称" required><el-input v-model="form.name" placeholder="Playbook 名称" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="风险等级"><el-select v-model="form.risk_level" style="width:100%">
            <el-option label="低" value="low" /><el-option label="中" value="medium" /><el-option label="高" value="high" /><el-option label="严重" value="critical" />
          </el-select></el-form-item></el-col>
        </el-row>
        <el-form-item label="描述"><el-input v-model="form.description" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="状态"><el-select v-model="form.status" style="width:200px">
          <el-option label="草稿" value="draft" /><el-option label="已激活" value="active" /><el-option label="已废弃" value="deprecated" />
        </el-select></el-form-item>

        <!-- 步骤编排器 -->
        <el-divider content-position="left">步骤编排</el-divider>
        <div class="step-orchestrator">
          <div v-for="(step, idx) in form.steps" :key="idx" class="step-item">
            <div class="step-header">
              <span class="step-number">{{ idx + 1 }}</span>
              <el-input v-model="step.name" placeholder="步骤名称" style="width:180px" size="small" />
              <el-select v-model="step.script_id" placeholder="选择脚本" style="width:200px" size="small" filterable>
                <el-option v-for="s in scripts" :key="s.id" :label="s.name" :value="s.id" />
              </el-select>
              <el-input-number v-model="step.timeout" :min="10" :max="3600" placeholder="超时" size="small" style="width:120px" />
              <el-select v-model="step.on_failure" style="width:120px" size="small">
                <el-option label="继续" value="continue" /><el-option label="停止" value="stop" /><el-option label="回滚" value="rollback" />
              </el-select>
              <el-button-group>
                <el-button size="small" :disabled="idx===0" @click="moveStep(idx,-1)">↑</el-button>
                <el-button size="small" :disabled="idx===form.steps.length-1" @click="moveStep(idx,1)">↓</el-button>
              </el-button-group>
              <el-button size="small" type="danger" @click="form.steps.splice(idx,1)"><el-icon><Delete /></el-icon></el-button>
            </div>
            <div class="step-params">
              <el-input v-model="step.params_json" placeholder="参数 JSON (可选)" style="width:400px" size="small" />
              <el-input v-model="step.condition" placeholder="条件表达式 (可选)" style="width:300px;margin-left:8px" size="small" />
            </div>
          </div>
          <el-button type="primary" plain @click="addStep" style="margin-top:8px"><el-icon><Plus /></el-icon> 添加步骤</el-button>
        </div>

        <!-- 步骤流程预览 -->
        <el-divider content-position="left">流程预览</el-divider>
        <div class="flow-preview" v-if="form.steps.length">
          <div v-for="(step, idx) in form.steps" :key="idx" class="flow-node">
            <div class="flow-box">{{ idx+1 }}. {{ step.name || '(未命名)' }}</div>
            <div v-if="idx < form.steps.length - 1" class="flow-arrow">→</div>
          </div>
        </div>
        <el-empty v-else description="请添加步骤" :image-size="60" />
      </el-form>
      <template #footer>
        <el-button @click="showDialog=false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <!-- 详情抽屉 -->
    <el-drawer v-model="showDetail" :title="detail?.name || 'Playbook 详情'" size="600px">
      <template v-if="detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="名称">{{ detail.name }}</el-descriptions-item>
          <el-descriptions-item label="状态"><el-tag :type="detail.status==='active'?'success':'info'" size="small">{{ statusLabel(detail.status) }}</el-tag></el-descriptions-item>
          <el-descriptions-item label="风险等级"><el-tag :type="riskType(detail.risk_level)" size="small">{{ detail.risk_level }}</el-tag></el-descriptions-item>
          <el-descriptions-item label="步骤数">{{ detail.steps?.length || 0 }}</el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">{{ detail.description || '-' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ fmt(detail.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ fmt(detail.updated_at) }}</el-descriptions-item>
        </el-descriptions>

        <h4 style="margin:16px 0 8px">步骤详情</h4>
        <el-table :data="detail.steps || []" stripe size="small">
          <el-table-column prop="name" label="步骤名" min-width="120" />
          <el-table-column label="脚本" min-width="120">
            <template #default="{ row }">{{ getScriptName(row.script_id) }}</template>
          </el-table-column>
          <el-table-column prop="timeout" label="超时(s)" width="80" />
          <el-table-column prop="on_failure" label="失败处理" width="90" />
          <el-table-column prop="condition" label="条件" min-width="120" show-overflow-tooltip />
        </el-table>

        <h4 style="margin:16px 0 8px">执行历史</h4>
        <el-table :data="execHistory" stripe size="small" v-loading="execLoading">
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="status" label="状态" width="90">
            <template #default="{ row }"><el-tag :type="row.status==='success'?'success':'danger'" size="small">{{ row.status }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="started_at" label="时间" min-width="160">
            <template #default="{ row }">{{ fmt(row.started_at) }}</template>
          </el-table-column>
        </el-table>

        <div style="margin-top:16px;display:flex;gap:8px">
          <el-button type="primary" @click="openEdit(detail);showDetail=false">编辑</el-button>
          <el-button @click="duplicate(detail);showDetail=false">复制</el-button>
          <el-button type="success" @click="quickExec(detail);showDetail=false">执行</el-button>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Delete } from '@element-plus/icons-vue'
import api from '@/shared/api/client'
import { API } from '@/shared/api/routes'

const router = useRouter()

const stats = reactive({ total: 0, active: 0, withScripts: 0, avgSteps: 0 })
const filters = reactive({ keyword: '', status: '', risk_level: '' })
const items = ref<any[]>([])
const loading = ref(false)
const page = ref(1)
const pageSize = 20
const total = ref(0)

const scripts = ref<any[]>([])
const showDialog = ref(false)
const editing = ref(false)
const editId = ref('')
const form = reactive({ name: '', description: '', status: 'draft', risk_level: 'low', steps: [] as any[] })

const showDetail = ref(false)
const detail = ref<any>(null)
const execHistory = ref<any[]>([])
const execLoading = ref(false)

function resetFilters() { filters.keyword=''; filters.status=''; filters.risk_level=''; load() }

async function load() {
  loading.value = true
  try {
    const params: any = { page: page.value, page_size: pageSize }
    if (filters.keyword) params.keyword = filters.keyword
    if (filters.status) params.status = filters.status
    if (filters.risk_level) params.risk_level = filters.risk_level
    const res = await api.get(API.PLAYBOOKS, { params })
    if (res.data?.code === 0) {
      items.value = res.data.data?.items || res.data.data || []
      total.value = res.data.data?.total || items.value.length
    }
    computeStats()
  } catch { ElMessage.error('加载失败') }
  finally { loading.value = false }
}

function computeStats() {
  stats.total = items.value.length
  stats.active = items.value.filter(i => i.status === 'active').length
  stats.withScripts = items.value.filter(i => i.steps?.some((s: any) => s.script_id)).length
  const steps = items.value.map(i => i.steps?.length || 0)
  stats.avgSteps = items.value.length ? Math.round(steps.reduce((a: number, b: number) => a + b, 0) / items.value.length) : 0
}

async function loadScripts() {
  try {
    const res = await api.get(API.SCRIPTS, { params: { page_size: 100 } })
    if (res.data?.code === 0) scripts.value = res.data.data?.items || res.data.data || []
  } catch {}
}

function addStep() {
  form.steps.push({ name: '', script_id: '', timeout: 300, on_failure: 'stop', params_json: '', condition: '' })
}

function moveStep(idx: number, dir: number) {
  const arr = form.steps
  const t = arr[idx]; arr[idx] = arr[idx + dir]; arr[idx + dir] = t
  form.steps = [...arr]
}

function openCreate() {
  editing.value = false; editId.value = ''
  form.name = ''; form.description = ''; form.status = 'draft'; form.risk_level = 'low'; form.steps = []
  showDialog.value = true
}

function openEdit(row: any) {
  editing.value = true; editId.value = row.id
  form.name = row.name; form.description = row.description || ''; form.status = row.status || 'draft'
  form.risk_level = row.risk_level || 'low'
  form.steps = (row.steps || []).map((s: any) => ({ ...s, params_json: typeof s.params === 'object' ? JSON.stringify(s.params) : (s.params_json || '') }))
  showDialog.value = true
}

async function save() {
  if (!form.name) return ElMessage.warning('请输入名称')
  try {
    const payload = { ...form, steps: form.steps.map(s => ({ ...s, params: s.params_json ? JSON.parse(s.params_json) : {} })) }
    if (editing.value) await api.put(`${API.PLAYBOOKS}/${editId.value}`, payload)
    else await api.post(API.PLAYBOOKS, payload)
    ElMessage.success('保存成功'); showDialog.value = false; load()
  } catch (e: any) { ElMessage.error(e?.message || '保存失败') }
}

async function viewDetail(row: any) {
  try {
    const res = await api.get(`${API.PLAYBOOKS}/${row.id}`)
    if (res.data?.code === 0) detail.value = res.data.data
    else detail.value = row
  } catch { detail.value = row }
  showDetail.value = true
  loadExecHistory(row.id)
}

async function loadExecHistory(playbookId: string) {
  execLoading.value = true
  try {
    const res = await api.get(API.EXECUTIONS, { params: { playbook_id: playbookId, page_size: 10 } })
    if (res.data?.code === 0) execHistory.value = res.data.data?.items || res.data.data || []
  } catch { execHistory.value = [] }
  finally { execLoading.value = false }
}

async function duplicate(row: any) {
  try {
    const payload = { ...row, name: `${row.name} (副本)`, status: 'draft', id: undefined, created_at: undefined, updated_at: undefined }
    await api.post(API.PLAYBOOKS, payload)
    ElMessage.success('复制成功'); load()
  } catch { ElMessage.error('复制失败') }
}

function quickExec(row: any) {
  router.push({ path: '/executions', query: { playbook_id: row.id, playbook_name: row.name } })
}

async function remove(row: any) {
  try {
    await ElMessageBox.confirm('确定删除此 Playbook？关联策略将失效。', '确认删除', { type: 'warning' })
    await api.delete(`${API.PLAYBOOKS}/${row.id}`)
    ElMessage.success('已删除'); load()
  } catch {}
}

function getScriptName(id: string) { return scripts.value.find(s => s.id === id)?.name || id || '-' }
function statusLabel(s: string) { return ({ draft:'草稿', active:'已激活', deprecated:'已废弃' })[s] || s }
function riskType(r: string) { return ({ low:'info', medium:'warning', high:'danger', critical:'danger' })[r] || 'info' }
function fmt(t: string) { return t ? new Date(t).toLocaleString('zh-CN') : '-' }

onMounted(() => { load(); loadScripts() })
</script>

<style scoped>
.page-container { padding: 20px; }
.stat-row { margin-bottom: 20px; }
.stat-card { text-align: center; }
.stat-card .stat-value { font-size: 28px; font-weight: bold; }
.stat-card.success .stat-value { color: #67c23a; }
.stat-card.primary .stat-value { color: #409eff; }
.stat-card.warning .stat-value { color: #e6a23c; }
.stat-card .stat-label { font-size: 13px; color: #909399; margin-top: 4px; }
.toolbar { margin-bottom: 16px; display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.pagination { margin-top: 16px; display: flex; justify-content: flex-end; }
.step-orchestrator { background: #f5f7fa; padding: 12px; border-radius: 4px; }
.step-item { background: #fff; border: 1px solid #ebeef5; border-radius: 4px; padding: 10px; margin-bottom: 8px; }
.step-header { display: flex; gap: 6px; align-items: center; }
.step-number { width: 24px; height: 24px; background: #409eff; color: #fff; border-radius: 50%; text-align: center; line-height: 24px; font-size: 12px; flex-shrink: 0; }
.step-params { display: flex; margin-top: 8px; padding-left: 30px; }
.flow-preview { display: flex; align-items: center; gap: 4px; flex-wrap: wrap; padding: 8px; background: #fafafa; border-radius: 4px; }
.flow-box { background: #409eff; color: #fff; padding: 4px 12px; border-radius: 4px; font-size: 12px; }
.flow-arrow { color: #909399; font-size: 16px; }
</style>
