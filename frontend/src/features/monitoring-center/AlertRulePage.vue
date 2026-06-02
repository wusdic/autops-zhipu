<template>
  <div class="page-container">
    <!-- ========== Page Header ========== -->
    <div class="autops-page-header">
      <div>
        <div class="autops-page-title">告警规则</div>
        <div class="autops-page-subtitle">配置指标阈值与触发条件，实现自动化告警</div>
      </div>
    </div>

    <el-row :gutter="16" class="stat-row mb-lg">
      <el-col :span="6"><div class="autops-card stat-card"><div class="autops-card-body"><div class="stat-value">{{ stats.total }}</div><div class="stat-label">规则总数</div></div></div></el-col>
      <el-col :span="6"><div class="autops-card stat-card success"><div class="autops-card-body"><div class="stat-value">{{ stats.active }}</div><div class="stat-label">已启用</div></div></div></el-col>
      <el-col :span="6"><div class="autops-card stat-card warning"><div class="autops-card-body"><div class="stat-value">{{ stats.triggeredToday }}</div><div class="stat-label">今日触发</div></div></div></el-col>
      <el-col :span="6"><div class="autops-card stat-card primary"><div class="autops-card-body"><div class="stat-value">{{ stats.mostTriggered || '-' }}</div><div class="stat-label">最常触发</div></div></div></el-col>
    </el-row>

    <div class="autops-toolbar">
      <el-input v-model="filters.keyword" placeholder="搜索规则" clearable style="width:200px;" @clear="load" @keyup.enter="load" />
      <el-select v-model="filters.severity" placeholder="严重度" clearable style="width:120px;margin-right:8px">
        <el-option label="严重" value="critical" /><el-option label="警告" value="warning" /><el-option label="信息" value="info" />
      </el-select>
      <el-select v-model="filters.status" placeholder="状态" clearable style="width:120px;margin-right:8px">
        <el-option label="启用" value="active" /><el-option label="停用" value="inactive" />
      </el-select>
      <el-select v-model="filters.metric" placeholder="指标类型" clearable style="width:140px;margin-right:8px">
        <el-option label="CPU" value="cpu_usage" /><el-option label="内存" value="memory_usage" /><el-option label="磁盘" value="disk_usage" />
        <el-option label="网络入" value="network_in" /><el-option label="网络出" value="network_out" /><el-option label="响应时间" value="response_time" />
        <el-option label="状态检查" value="status_check" /><el-option label="自定义" value="custom" />
      </el-select>
      <el-button type="primary" @click="load"><el-icon><Search /></el-icon> 搜索</el-button>
      <el-button @click="resetFilters">重置</el-button>
      <div style="flex:1" />
      <el-button type="primary" @click="openCreate"><el-icon><Plus /></el-icon> 新建规则</el-button>
    </div>

    <el-table :data="items" v-loading="loading" stripe>
      <el-table-column prop="name" label="规则名称" min-width="160">
        <template #default="{ row }"><el-link type="primary" @click="viewDetail(row)">{{ row.name }}</el-link></template>
      </el-table-column>
      <el-table-column label="指标" width="120">
        <template #default="{ row }"><el-tag size="small">{{ metricLabel(row.metric) }}</el-tag></template>
      </el-table-column>
      <el-table-column label="条件" min-width="180">
        <template #default="{ row }">
          <span v-if="row.conditions?.length">
            <span v-for="(c,i) in row.conditions.slice(0,2)" :key="i">
              {{ c.field }} {{ c.operator }} {{ c.value }}{{ c.unit||'' }}
              <span v-if="i < Math.min(row.conditions.length,2)-1" style="color:#909399">{{ row.condition_logic||'AND' }} </span>
            </span>
            <span v-if="row.conditions.length > 2" style="color:#909399">+{{ row.conditions.length-2 }}</span>
          </span>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column prop="severity" label="严重度" width="90">
        <template #default="{ row }"><el-tag :type="severityType(row.severity)" size="small">{{ row.severity }}</el-tag></template>
      </el-table-column>
      <el-table-column label="状态" width="80">
        <template #default="{ row }">
          <el-switch v-model="row._active" size="small" @change="toggleRule(row)" />
        </template>
      </el-table-column>
      <el-table-column prop="trigger_count" label="触发次数" width="90" align="center" />
      <el-table-column prop="created_at" label="创建时间" width="170">
        <template #default="{ row }">{{ fmt(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="viewDetail(row)">详情</el-button>
          <el-button size="small" type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" @click="testRule(row)">测试</el-button>
          <el-button size="small" @click="duplicateRule(row)">复制</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination v-if="total > pageSize" class="pagination" :current-page="page" :page-size="pageSize" :total="total" @current-change="(p:number)=>{page=p;load()}" layout="total, prev, pager, next" />

    <!-- 创建/编辑对话框 -->
    <el-dialog v-model="showDialog" :title="editing?'编辑规则':'新建规则'" width="850px" top="5vh">
      <el-form :model="form" label-width="100px">
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="规则名称" required><el-input v-model="form.name" placeholder="例如: CPU使用率过高" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="严重度">
            <el-select v-model="form.severity" style="width:100%">
              <el-option label="严重" value="critical" /><el-option label="警告" value="warning" /><el-option label="信息" value="info" />
            </el-select>
          </el-form-item></el-col>
        </el-row>
        <el-form-item label="描述"><el-input v-model="form.description" type="textarea" :rows="2" /></el-form-item>

        <!-- 条件可视化编辑器 -->
        <el-divider content-position="left">告警条件</el-divider>
        <div class="condition-editor">
          <el-radio-group v-model="form.condition_logic" size="small" style="margin-bottom:8px">
            <el-radio-button value="AND">全部满足(AND)</el-radio-button>
            <el-radio-button value="OR">任一满足(OR)</el-radio-button>
          </el-radio-group>
          <div v-for="(cond, idx) in form.conditions" :key="idx" class="cond-row">
            <el-select v-model="cond.metric" placeholder="指标" style="width:160px" size="small">
              <el-option label="CPU使用率" value="cpu_usage" /><el-option label="内存使用率" value="memory_usage" />
              <el-option label="磁盘使用率" value="disk_usage" /><el-option label="网络入流量" value="network_in" />
              <el-option label="网络出流量" value="network_out" /><el-option label="响应时间" value="response_time" />
              <el-option label="状态码" value="status_code" /><el-option label="连接数" value="connection_count" />
              <el-option label="进程数" value="process_count" /><el-option label="自定义" value="custom" />
            </el-select>
            <el-select v-model="cond.operator" style="width:90px" size="small">
              <el-option label=">" value=">" /><el-option label=">=" value=">=" />
              <el-option label="<" value="<" /><el-option label="<=" value="<=" />
              <el-option label="=" value="=" /><el-option label="!=" value="!=" />
            </el-select>
            <el-input-number v-model="cond.value" :min="0" placeholder="阈值" style="width:130px" size="small" />
            <el-select v-model="cond.unit" style="width:80px" size="small" placeholder="单位">
              <el-option label="%" value="%" /><el-option label="ms" value="ms" />
              <el-option label="MB" value="MB" /><el-option label="GB" value="GB" />
              <el-option label="次" value="次" /><el-option label="" value="" />
            </el-select>
            <el-select v-model="cond.duration" style="width:120px" size="small" placeholder="持续时间">
              <el-option label="即时" value="" /><el-option label="30秒" value="30s" />
              <el-option label="1分钟" value="1m" /><el-option label="5分钟" value="5m" />
              <el-option label="15分钟" value="15m" /><el-option label="30分钟" value="30m" />
              <el-option label="1小时" value="1h" />
            </el-select>
            <el-button size="small" type="danger" @click="form.conditions.splice(idx,1)"><el-icon><Delete /></el-icon></el-button>
          </div>
          <el-button type="primary" plain size="small" @click="addCondition" style="margin-top:4px"><el-icon><Plus /></el-icon> 添加条件</el-button>
        </div>

        <el-row :gutter="16" style="margin-top:16px">
          <el-col :span="8"><el-form-item label="通知方式"><el-select v-model="form.notify_type" style="width:100%">
            <el-option label="站内通知" value="internal" /><el-option label="邮件" value="email" /><el-option label="全部" value="all" />
          </el-select></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="重复间隔"><el-select v-model="form.repeat_interval" style="width:100%">
            <el-option label="不重复" value="" /><el-option label="5分钟" value="5m" /><el-option label="15分钟" value="15m" />
            <el-option label="1小时" value="1h" /><el-option label="24小时" value="24h" />
          </el-select></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="状态"><el-switch v-model="form.active" active-text="启用" inactive-text="停用" /></el-form-item></el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="showDialog=false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <!-- 详情抽屉 -->
    <el-drawer v-model="showDetail" :title="detail?.name || '规则详情'" size="560px">
      <template v-if="detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="名称">{{ detail.name }}</el-descriptions-item>
          <el-descriptions-item label="严重度"><el-tag :type="severityType(detail.severity)" size="small">{{ detail.severity }}</el-tag></el-descriptions-item>
          <el-descriptions-item label="状态">{{ detail.active !== false ? '启用' : '停用' }}</el-descriptions-item>
          <el-descriptions-item label="触发次数">{{ detail.trigger_count || 0 }}</el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">{{ detail.description || '-' }}</el-descriptions-item>
        </el-descriptions>

        <h4 style="margin:16px 0 8px">条件详情</h4>
        <div v-if="detail.conditions?.length">
          <div v-for="(c,i) in detail.conditions" :key="i" style="margin-bottom:6px">
            <el-tag size="small">{{ metricLabel(c.metric) }}</el-tag>
            <strong style="margin:0 4px">{{ c.operator }}</strong>
            <el-tag size="small" type="warning">{{ c.value }}{{ c.unit||'' }}</el-tag>
            <span v-if="c.duration" style="color:#409eff;margin-left:4px">持续 {{ c.duration }}</span>
          </div>
          <p style="color:#909399;font-size:13px;margin-top:4px">逻辑: {{ detail.condition_logic || 'AND' }}</p>
        </div>

        <h4 style="margin:16px 0 8px">近期触发记录</h4>
        <el-table :data="triggerHistory" stripe size="small">
          <el-table-column prop="triggered_at" label="时间" width="170">
            <template #default="{ row }">{{ fmt(row.triggered_at) }}</template>
          </el-table-column>
          <el-table-column prop="asset_name" label="资产" min-width="120" />
          <el-table-column prop="actual_value" label="实际值" width="100" />
        </el-table>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Search, Delete } from '@element-plus/icons-vue'
import api from '@/shared/api/client'
import { API } from '@/shared/api/routes'

const stats = reactive({ total: 0, active: 0, triggeredToday: 0, mostTriggered: '' })
const filters = reactive({ keyword: '', severity: '', status: '', metric: '' })
const items = ref<any[]>([])
const loading = ref(false)
const page = ref(1)
const pageSize = 20
const total = ref(0)

const showDialog = ref(false)
const editing = ref(false)
const editId = ref('')
const form = reactive({
  name: '', description: '', severity: 'warning', condition_logic: 'AND',
  conditions: [] as any[], notify_type: 'internal', repeat_interval: '', active: true,
})

const showDetail = ref(false)
const detail = ref<any>(null)
const triggerHistory = ref<any[]>([])

function resetFilters() { Object.assign(filters, { keyword:'', severity:'', status:'', metric:'' }); load() }

async function load() {
  loading.value = true
  try {
    const params: any = { page: page.value, page_size: pageSize }
    if (filters.keyword) params.keyword = filters.keyword
    if (filters.severity) params.severity = filters.severity
    if (filters.status) params.status = filters.status === 'active'
    if (filters.metric) params.metric = filters.metric
    const res = await api.get(API.ALERT_RULES, { params })
    if (res.data?.code === 0) {
      items.value = (res.data.data?.items || res.data.data || []).map((r: any) => ({ ...r, _active: r.active !== false }))
      total.value = res.data.data?.total || items.value.length
    }
    computeStats()
  } catch { ElMessage.error('加载失败') }
  finally { loading.value = false }
}

function computeStats() {
  stats.total = items.value.length
  stats.active = items.value.filter(i => i._active).length
  stats.triggeredToday = items.value.reduce((a: number, i: any) => a + (i.trigger_count || 0), 0)
  const sorted = [...items.value].sort((a: any, b: any) => (b.trigger_count||0) - (a.trigger_count||0))
  stats.mostTriggered = sorted[0]?.name || ''
}

function addCondition() { form.conditions.push({ metric: 'cpu_usage', operator: '>', value: 90, unit: '%', duration: '' }) }

function openCreate() {
  editing.value = false; editId.value = ''
  Object.assign(form, { name:'', description:'', severity:'warning', condition_logic:'AND', conditions:[], notify_type:'internal', repeat_interval:'', active:true })
  addCondition()
  showDialog.value = true
}

function openEdit(row: any) {
  editing.value = true; editId.value = row.id
  Object.assign(form, {
    name: row.name, description: row.description||'', severity: row.severity||'warning',
    condition_logic: row.condition_logic||'AND', conditions: row.conditions?.length ? [...row.conditions] : [],
    notify_type: row.notify_type||'internal', repeat_interval: row.repeat_interval||'', active: row.active !== false,
  })
  if (!form.conditions.length) addCondition()
  showDialog.value = true
}

async function save() {
  if (!form.name) return ElMessage.warning('请输入名称')
  try {
    const payload = { ...form, active: form.active }
    if (editing.value) await api.put(`${API.ALERT_RULES}/${editId.value}`, payload)
    else await api.post(API.ALERT_RULES, payload)
    ElMessage.success('保存成功'); showDialog.value = false; load()
  } catch (e: any) { ElMessage.error(e?.message || '保存失败') }
}

async function viewDetail(row: any) {
  try {
    const res = await api.get(`${API.ALERT_RULES}/${row.id}`)
    if (res.data?.code === 0) detail.value = res.data.data
    else detail.value = row
  } catch { detail.value = row }
  triggerHistory.value = []
  showDetail.value = true
}

async function toggleRule(row: any) {
  try {
    await api.patch(`${API.ALERT_RULES}/${row.id}`, { active: row._active })
    ElMessage.success(row._active ? '已启用' : '已停用')
  } catch { row._active = !row._active; ElMessage.error('操作失败') }
}

async function testRule(row: any) {
  try {
    const res = await api.post(`${API.ALERT_RULES}/${row.id}/test`)
    ElMessage.success(res.data?.data?.matched ? '规则命中! 条件满足' : '规则未命中，条件不满足')
  } catch { ElMessage.warning('测试功能暂不可用') }
}

async function duplicateRule(row: any) {
  try {
    await api.post(API.ALERT_RULES, { ...row, name: `${row.name} (副本)`, active: false, id: undefined })
    ElMessage.success('复制成功'); load()
  } catch { ElMessage.error('复制失败') }
}

function metricLabel(m: string) {
  return ({ cpu_usage:'CPU使用率', memory_usage:'内存使用率', disk_usage:'磁盘使用率', network_in:'网络入', network_out:'网络出', response_time:'响应时间', status_check:'状态检查', status_code:'状态码', connection_count:'连接数', process_count:'进程数', custom:'自定义' })[m] || m
}
function severityType(s: string) { return ({ critical:'danger', warning:'warning', info:'info' })[s] || 'info' }
function fmt(t: string) { return t ? new Date(t).toLocaleString('zh-CN') : '-' }

onMounted(() => { load() })
</script>

<style scoped>
.page-container { padding: 20px; }
.stat-row { margin-bottom: 20px; }
.stat-card { text-align: center; }
.stat-card .stat-value { font-size: 28px; font-weight: bold; }
.stat-card.success .stat-value { color: #67c23a; }
.stat-card.warning .stat-value { color: #e6a23c; }
.stat-card.primary .stat-value { color: #409eff; font-size: 16px; }
.stat-card .stat-label { font-size: 13px; color: #909399; margin-top: 4px; }
.toolbar { margin-bottom: 16px; display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.pagination { margin-top: 16px; display: flex; justify-content: flex-end; }
.condition-editor { background: #f5f7fa; padding: 12px; border-radius: 4px; }
.cond-row { display: flex; gap: 6px; align-items: center; margin-bottom: 6px; }
</style>
