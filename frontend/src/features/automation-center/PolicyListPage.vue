<template>
  <div class="autops-page-container">
    <div class="autops-page-header">
      <div>
        <div class="autops-page-title">策略管理</div>
        <div class="autops-page-desc">配置自动化触发策略</div>
      </div>
    </div>

    <el-row :gutter="16" class="stat-row">
      <el-col :span="6"><div class="autops-card stat-card stat-value stat-label"><div >{{ stats.total }}</div><div >策略总数</div></div></el-col>
      <el-col :span="6"><div class="autops-card stat-card success stat-value stat-label"><div >{{ stats.active }}</div><div >已激活</div></div></el-col>
      <el-col :span="6"><div class="autops-card stat-card danger stat-value stat-label"><div >{{ stats.highRisk }}</div><div >高风险</div></div></el-col>
      <el-col :span="6"><div class="autops-card stat-card warning stat-value stat-label"><div >{{ stats.pendingApproval }}</div><div >待审批</div></div></el-col>
    </el-row>

    <div class="autops-toolbar">
      <el-input v-model="filters.keyword" placeholder="搜索策略" clearable style="width:200px;margin-right:8px" @clear="load" @keyup.enter="load" />
      <el-select v-model="filters.status" placeholder="状态" clearable style="width:120px;margin-right:8px">
        <el-option label="草稿" value="draft" /><el-option label="已激活" value="active" /><el-option label="已废弃" value="deprecated" />
      </el-select>
      <el-select v-model="filters.risk_level" placeholder="风险等级" clearable style="width:120px;margin-right:8px">
        <el-option label="低" value="low" /><el-option label="中" value="medium" /><el-option label="高" value="high" /><el-option label="严重" value="critical" />
      </el-select>
      <el-select v-model="filters.trigger_source" placeholder="触发源" clearable style="width:130px;margin-right:8px">
        <el-option label="事件" value="event" /><el-option label="告警" value="alert" /><el-option label="状态变更" value="state_change" /><el-option label="手动" value="manual" /><el-option label="定时" value="schedule" />
      </el-select>
      <el-button type="primary" @click="load"><el-icon><Search /></el-icon> 搜索</el-button>
      <el-button @click="resetFilters">重置</el-button>
      <div style="flex:1" />
      <el-button type="primary" @click="openCreate"><el-icon><Plus /></el-icon> 新建策略</el-button>
    </div>

    <el-table stripe :data="items" v-loading="loading">
      <el-table-column prop="name" label="名称" min-width="160">
        <template #default="{ row }"><el-link type="primary" @click="viewDetail(row)">{{ row.name }}</el-link></template>
      </el-table-column>
      <el-table-column prop="trigger_type" label="触发类型" width="100">
        <template #default="{ row }"><el-tag size="small">{{ triggerLabel(row.trigger_type) }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="risk_level" label="风险" width="80">
        <template #default="{ row }"><el-tag :type="(riskType(row.risk_level)) as TagType" size="small">{{ row.risk_level }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="90">
        <template #default="{ row }"><el-tag :type="row.status==='active'?'success':'info'" size="small">{{ statusLabel(row.status) }}</el-tag></template>
      </el-table-column>
      <el-table-column label="范围" min-width="140" show-overflow-tooltip>
        <template #default="{ row }">{{ row.scope_description || '-' }}</template>
      </el-table-column>
      <el-table-column label="动作数" width="80" align="center">
        <template #default="{ row }">{{ row.action_chain?.length || 0 }}</template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="170">
        <template #default="{ row }">{{ fmt(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="240" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="viewDetail(row)">详情</el-button>
          <el-button size="small" type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" type="warning" @click="simulate(row)">模拟</el-button>
          <el-button size="small" @click="duplicate(row)">复制</el-button>
          <el-button size="small" :type="row.status==='active'?'info':'success'" @click="toggleStatus(row)">{{ row.status==='active'?'停用':'激活' }}</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination v-if="total > pageSize" class="pagination" :current-page="page" :page-size="pageSize" :total="total" @current-change="(p:number)=>{page=p;load()}" layout="total, prev, pager, next" />

    <!-- 创建/编辑对话框 -->
    <el-dialog v-model="showDialog" :title="editing?'编辑策略':'新建策略'" width="780px" top="5vh">
      <el-form :model="form" label-width="110px">
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="策略名称" required><el-input v-model="form.name" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="触发源">
            <el-select v-model="form.trigger_source" style="width:100%">
              <el-option label="事件" value="event" /><el-option label="告警" value="alert" /><el-option label="状态变更" value="state_change" /><el-option label="手动" value="manual" /><el-option label="定时" value="schedule" />
            </el-select>
          </el-form-item></el-col>
        </el-row>
        <el-form-item label="描述"><el-input v-model="form.description" type="textarea" :rows="2" /></el-form-item>

        <!-- 触发条件可视化编辑 -->
        <el-divider content-position="left">触发条件</el-divider>
        <div class="condition-builder">
          <el-radio-group v-model="form.condition_logic" size="small" style="margin-bottom:8px">
            <el-radio-button value="AND">全部满足(AND)</el-radio-button>
            <el-radio-button value="OR">任一满足(OR)</el-radio-button>
          </el-radio-group>
          <div v-for="(cond, idx) in form.conditions" :key="idx" class="condition-row">
            <el-select v-model="cond.field" placeholder="字段" style="width:180px" size="small">
              <el-option label="CPU使用率" value="cpu_usage" /><el-option label="内存使用率" value="memory_usage" />
              <el-option label="磁盘使用率" value="disk_usage" /><el-option label="响应时间" value="response_time" />
              <el-option label="状态码" value="status_code" /><el-option label="事件类型" value="event_type" />
              <el-option label="告警级别" value="alert_severity" /><el-option label="端口状态" value="port_status" />
              <el-option label="进程状态" value="process_status" /><el-option label="自定义" value="custom" />
            </el-select>
            <el-select v-model="cond.operator" style="width:100px" size="small">
              <el-option label=">" value="gt" /><el-option label=">=" value="gte" />
              <el-option label="<" value="lt" /><el-option label="<=" value="lte" />
              <el-option label="=" value="eq" /><el-option label="!=" value="neq" />
              <el-option label="包含" value="contains" /><el-option label="匹配" value="matches" />
            </el-select>
            <el-input v-model="cond.value" placeholder="值" style="width:150px" size="small" />
            <el-input v-model="cond.duration" placeholder="持续时间(可选)" style="width:130px" size="small" />
            <el-button size="small" type="danger" @click="form.conditions.splice(idx,1)"><el-icon><Delete /></el-icon></el-button>
          </div>
          <el-button type="primary" plain size="small" @click="addCondition" style="margin-top:4px"><el-icon><Plus /></el-icon> 添加条件</el-button>
        </div>

        <!-- 适用范围 -->
        <el-divider content-position="left">适用范围</el-divider>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="资产分组">
              <el-select v-model="form.scope_groups" multiple placeholder="选择分组" style="width:100%">
                <el-option v-for="g in groups" :key="g.id" :label="g.name" :value="g.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="资产类型">
              <el-select v-model="form.scope_asset_types" multiple placeholder="类型筛选" style="width:100%">
                <el-option label="Linux" value="linux_server" /><el-option label="Windows" value="windows_server" />
                <el-option label="网络设备" value="network_device" /><el-option label="数据库" value="database" />
                <el-option label="Web服务" value="web_service" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 动作链 -->
        <el-divider content-position="left">动作链</el-divider>
        <div class="action-chain">
          <div v-for="(act, idx) in form.actions" :key="idx" class="action-item">
            <span class="action-num">{{ idx+1 }}</span>
            <el-select v-model="act.type" style="width:130px" size="small">
              <el-option label="执行脚本" value="script" /><el-option label="执行Playbook" value="playbook" />
              <el-option label="发送通知" value="notification" /><el-option label="创建工单" value="ticket" />
              <el-option label="抑制告警" value="suppress" />
            </el-select>
            <el-input v-model="act.target" placeholder="目标(脚本/Playbook ID)" style="width:200px" size="small" />
            <el-input v-model="act.params_json" placeholder="参数 JSON" style="width:200px" size="small" />
            <el-button size="small" type="danger" @click="form.actions.splice(idx,1)"><el-icon><Delete /></el-icon></el-button>
          </div>
          <el-button type="primary" plain size="small" @click="addAction"><el-icon><Plus /></el-icon> 添加动作</el-button>
        </div>

        <el-row :gutter="16" style="margin-top:16px">
          <el-col :span="8"><el-form-item label="风险等级"><el-select v-model="form.risk_level" style="width:100%">
            <el-option label="低" value="low" /><el-option label="中" value="medium" /><el-option label="高" value="high" /><el-option label="严重" value="critical" />
          </el-select></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="需要审批"><el-switch v-model="form.requires_approval" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="最大影响面"><el-input-number v-model="form.max_impact" :min="1" :max="1000" style="width:100%" /></el-form-item></el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="showDialog=false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <!-- 详情抽屉 -->
    <el-drawer v-model="showDetail" :title="detail?.name || '策略详情'" size="620px">
      <template v-if="detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="名称">{{ detail.name }}</el-descriptions-item>
          <el-descriptions-item label="触发源"><el-tag size="small">{{ triggerLabel(detail.trigger_source) }}</el-tag></el-descriptions-item>
          <el-descriptions-item label="风险等级"><el-tag :type="(riskType(detail.risk_level)) as TagType" size="small">{{ detail.risk_level }}</el-tag></el-descriptions-item>
          <el-descriptions-item label="状态"><el-tag :type="detail.status==='active'?'success':'info'" size="small">{{ statusLabel(detail.status) }}</el-tag></el-descriptions-item>
          <el-descriptions-item label="需要审批">{{ detail.requires_approval ? '是' : '否' }}</el-descriptions-item>
          <el-descriptions-item label="最大影响面">{{ detail.max_impact || '-' }}</el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">{{ detail.description || '-' }}</el-descriptions-item>
        </el-descriptions>

        <h4 style="margin:16px 0 8px">触发条件</h4>
        <div v-if="detail.conditions?.length">
          <div v-for="(c,i) in detail.conditions" :key="i" class="cond-display">
            <el-tag size="small" type="info">{{ c.field }}</el-tag>
            <span class="cond-op">{{ c.operator }}</span>
            <el-tag size="small">{{ c.value }}</el-tag>
            <span v-if="c.duration" class="cond-dur">持续 {{ c.duration }}</span>
          </div>
          <div class="cond-logic">逻辑: <strong>{{ detail.condition_logic || 'AND' }}</strong></div>
        </div>
        <el-empty v-else description="无条件" :image-size="40" />

        <h4 style="margin:16px 0 8px">适用范围</h4>
        <el-tag v-for="g in detail.scope_groups" :key="g" style="margin-right:4px">{{ getGroupName(g) }}</el-tag>
        <el-tag v-for="t in detail.scope_asset_types" :key="t" type="info" style="margin-right:4px">{{ t }}</el-tag>

        <h4 style="margin:16px 0 8px">动作链</h4>
        <el-timeline v-if="detail.actions?.length">
          <el-timeline-item v-for="(a,i) in detail.actions" :key="i" :timestamp="'步骤 ' + i+1" placement="top">
            <el-tag>{{ actionTypeLabel(a.type) }}</el-tag> → {{ a.target || '-' }}
          </el-timeline-item>
        </el-timeline>
        <el-empty v-else description="无动作" :image-size="40" />

        <div style="margin-top:16px;display:flex;gap:8px">
          <el-button type="primary" @click="openEdit(detail);showDetail=false">编辑</el-button>
          <el-button type="warning" @click="simulate(detail);showDetail=false">模拟执行</el-button>
          <el-button @click="duplicate(detail);showDetail=false">复制</el-button>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import type { TagType } from '@/shared/types'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Delete } from '@element-plus/icons-vue'
import api from '@/shared/api/client'
import { API } from '@/shared/api/routes'

const router = useRouter()
const stats = reactive({ total: 0, active: 0, highRisk: 0, pendingApproval: 0 })
const filters = reactive({ keyword: 'primary', status: 'primary', risk_level: 'primary', trigger_source: 'primary'})
const items = ref<any[]>([])
const loading = ref(false)
const page = ref(1)
const pageSize = 20
const total = ref(0)
const groups = ref<any[]>([])

const showDialog = ref(false)
const editing = ref(false)
const editId = ref('')
const form = reactive({
  name: 'primary', description: 'primary', trigger_source: 'event', condition_logic: 'AND',
  conditions: [] as any[], scope_groups: [] as string[], scope_asset_types: [] as string[],
  actions: [] as any[], risk_level: 'low', requires_approval: false, max_impact: 10,
})

const showDetail = ref(false)
const detail = ref<any>(null)

function resetFilters() { Object.assign(filters, { keyword:'', status:'', risk_level:'', trigger_source:'' }); load() }

async function load() {
  loading.value = true
  try {
    const params: any = { page: page.value, page_size: pageSize }
    if (filters.keyword) params.keyword = filters.keyword
    if (filters.status) params.status = filters.status
    if (filters.risk_level) params.risk_level = filters.risk_level
    if (filters.trigger_source) params.trigger_source = filters.trigger_source
    const res = await api.get(API.POLICIES, { params })
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
  stats.highRisk = items.value.filter(i => ['high','critical'].includes(i.risk_level)).length
  stats.pendingApproval = items.value.filter(i => i.requires_approval && i.status === 'draft').length
}

async function loadGroups() {
  try {
    const res = await api.get(API.ASSET_GROUPS, { params: { page_size: 100 } })
    if (res.data?.code === 0) groups.value = res.data.data?.items || res.data.data || []
  } catch {}
}

function addCondition() { form.conditions.push({ field: 'primary', operator: 'gt', value: 'primary', duration: 'primary'}) }
function addAction() { form.actions.push({ type: 'script', target: 'primary', params_json: 'primary'}) }

function openCreate() {
  editing.value = false; editId.value = ''
  Object.assign(form, { name:'', description:'', trigger_source:'event', condition_logic:'AND', conditions:[], scope_groups:[], scope_asset_types:[], actions:[], risk_level:'low', requires_approval:false, max_impact:10 })
  showDialog.value = true
}

function openEdit(row: any) {
  editing.value = true; editId.value = row.id
  Object.assign(form, {
    name: row.name, description: row.description||'', trigger_source: row.trigger_source||'event',
    condition_logic: row.condition_logic||'AND', conditions: row.conditions?.length ? [...row.conditions] : [],
    scope_groups: row.scope_groups||[], scope_asset_types: row.scope_asset_types||[],
    actions: row.actions?.length ? [...row.actions] : [], risk_level: row.risk_level||'low',
    requires_approval: !!row.requires_approval, max_impact: row.max_impact||10,
  })
  showDialog.value = true
}

async function save() {
  if (!form.name) return ElMessage.warning('请输入名称')
  try {
    if (editing.value) await api.put(API.POLICY_DETAIL(editId.value), form)
    else await api.post(API.POLICIES, form)
    ElMessage.success('保存成功'); showDialog.value = false; load()
  } catch (e: any) { ElMessage.error(e?.message || '保存失败') }
}

async function viewDetail(row: any) {
  try {
    const res = await api.get(API.POLICY_DETAIL(row.id))
    if (res.data?.code === 0) detail.value = res.data.data
    else detail.value = row
  } catch { detail.value = row }
  showDetail.value = true
}

function simulate(row: any) { router.push('/policies/' + row.id + '/simulate') }

async function duplicate(row: any) {
  try {
    const payload = { ...row, name: row.name + ' (副本)', status: 'draft', id: undefined }
    await api.post(API.POLICIES, payload)
    ElMessage.success('复制成功'); load()
  } catch { ElMessage.error('复制失败') }
}

async function toggleStatus(row: any) {
  const newStatus = row.status === 'active' ? 'draft' : 'active'
  try {
    await api.patch(API.POLICY_DETAIL(row.id), { status: newStatus })
    ElMessage.success(newStatus === 'active' ? '已激活' : '已停用'); load()
  } catch { ElMessage.error('操作失败') }
}

function getGroupName(id: string) { return groups.value.find(g => g.id === id)?.name || id }
function triggerLabel(s: string) { return ({ event:'事件', alert:'告警', state_change:'状态变更', manual:'手动', schedule:'定时' })[s] || s }
function actionTypeLabel(t: string) { return ({ script:'脚本', playbook:'Playbook', notification:'通知', ticket:'工单', suppress:'抑制' })[t] || t }
function statusLabel(s: string) { return ({ draft:'草稿', active:'已激活', deprecated:'已废弃' })[s] || s }
function riskType(r: string): TagType { return (({ low:'info', medium:'warning', high:'danger', critical:'danger' })[r] ?? 'info') as TagType }
function fmt(t: string) { return t ? new Date(t).toLocaleString('zh-CN') : '-' }

onMounted(() => { load(); loadGroups() })
</script>

<style scoped>

.stat-row { margin-bottom: var(--autops-space-xl); }

.autops-metric-card 
.autops-metric-card.success .stat-value { color: var(--autops-success); }
.autops-metric-card.danger .stat-value { color: var(--autops-danger); }
.autops-metric-card.warning .stat-value { color: var(--autops-warning); }
.autops-metric-card 
.toolbar { margin-bottom: var(--autops-space-lg); display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.pagination { margin-top: var(--autops-space-lg); display: flex; justify-content: flex-end; }
.condition-builder { background: var(--autops-bg-2); padding: var(--autops-space-md); border-radius: var(--autops-radius-sm); }
.condition-row { display: flex; gap: 6px; align-items: center; margin-bottom: 6px; }
.action-chain { background: var(--autops-bg-2); padding: var(--autops-space-md); border-radius: var(--autops-radius-sm); }
.action-item { display: flex; gap: 6px; align-items: center; margin-bottom: 6px; }
.action-num { width: 22px; height: 22px; background: var(--autops-warning); color: var(--autops-bg-1); border-radius: 50%; text-align: center; line-height: 22px; font-size: 11px; }
.cond-display { display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }
.cond-op { color: var(--autops-info); font-weight: bold; }
.cond-dur { color: var(--autops-primary); font-size: var(--autops-font-12); }
.cond-logic { margin-top: 6px; color: var(--autops-text-2); font-size: var(--autops-font-13); }
</style>
