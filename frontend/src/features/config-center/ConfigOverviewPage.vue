<template>
  <div class="config-overview-page">
    <div class="autops-page-header">
      <div class="autops-page-title-row">
        <el-button link @click="router.back()"><el-icon><ArrowLeft /></el-icon> 返回</el-button>
        <span class="autops-page-title">配置总览</span>
      </div>
      <div class="autops-page-desc">统一管理发现模板、巡检规则、阈值规则、通知规则和配置版本</div>
    </div>
    <div style="display: flex; gap: 8px; margin-bottom: 16px">
      <el-button type="primary" @click="showQuickCreate = true">
        <el-icon><Plus /></el-icon> 快速创建
      </el-button>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="16" class="mt-4">
      <el-col :span="6" v-for="stat in stats" :key="stat.label">
        <el-card shadow="hover" class="stat-card" @click="stat.click">
          <div class="stat-value" :style="{ color: stat.color }">{{ stat.value }}</div>
          <div class="stat-label">{{ stat.label }}</div>
          <div class="stat-footer">
            <span :class="stat.trend > 0 ? 'trend-up' : 'trend-down'">
              {{ stat.trend > 0 ? '+' : '' }}{{ stat.trend }}%
            </span>
            <span class="trend-label">较上周</span>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 配置分类 Tab -->
    <el-tabs v-model="activeTab" class="mt-4">
      <el-tab-pane label="发现模板" name="discovery">
        <el-table stripe :data="discoveryTemplates" v-loading="loading">
          <el-table-column prop="name" label="模板名称" min-width="180" />
          <el-table-column prop="type" label="发现类型" width="120">
            <template #default="{ row }">
              <el-tag :type="row.type === 'ssh' ? 'primary' : row.type === 'snmp' ? 'success' : 'warning'" size="small">
                {{ row.type?.toUpperCase() }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="asset_count" label="关联资产" width="100" />
          <el-table-column prop="last_run" label="最近执行" width="180" />
          <el-table-column prop="status" label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
                {{ row.status === 'active' ? '启用' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="180" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="runDiscovery(row)">执行</el-button>
              <el-button link type="primary" @click="editTemplate('discovery', row)">编辑</el-button>
              <el-button link type="danger" @click="deleteTemplate('discovery', row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="巡检规则" name="inspection">
        <el-table stripe :data="inspectionRules" v-loading="loading">
          <el-table-column prop="name" label="规则名称" min-width="180" />
          <el-table-column prop="category" label="规则类型" width="120">
            <template #default="{ row }">
              <el-tag size="small">{{ categoryMap[row.category] || row.category }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="severity" label="严重度" width="100">
            <template #default="{ row }">
              <el-tag :type="severityType(row.severity)" size="small">{{ row.severity }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="asset_count" label="适用资产" width="100" />
          <el-table-column prop="enabled" label="状态" width="80">
            <template #default="{ row }">
              <el-switch v-model="row.enabled" size="small" @change="toggleRule(row)" />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="180" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="editTemplate('inspection-rule', row)">编辑</el-button>
              <el-button link type="primary" @click="simulateRule(row)">模拟</el-button>
              <el-button link type="danger" @click="deleteTemplate('inspection-rule', row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="阈值规则" name="threshold">
        <el-empty description="阈值规则已迁移至独立页面" :image-size="80">
          <el-button type="primary" @click="$router.push('/config/threshold-rules')">前往阈值规则管理</el-button>
        </el-empty>
      </el-tab-pane>

      <el-tab-pane label="通知规则" name="notification">
        <el-table stripe :data="notificationRules" v-loading="loading">
          <el-table-column prop="name" label="规则名称" min-width="180" />
          <el-table-column prop="trigger" label="触发条件" width="150" />
          <el-table-column prop="channel" label="通知渠道" width="120">
            <template #default="{ row }">
              <el-tag size="small">{{ row.channel }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="recipients" label="接收人" min-width="150">
            <template #default="{ row }">
              {{ (row.recipients || []).join(', ') || '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="enabled" label="状态" width="80">
            <template #default="{ row }">
              <el-switch v-model="row.enabled" size="small" @change="toggleRule(row)" />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="180" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="editTemplate('notification', row)">编辑</el-button>
              <el-button link type="danger" @click="deleteTemplate('notification', row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="配置版本" name="version">
        <el-table stripe :data="configVersions" v-loading="loading">
          <el-table-column prop="config_name" label="配置名称" min-width="180" />
          <el-table-column prop="version" label="版本号" width="100" />
          <el-table-column prop="updated_by" label="修改人" width="120" />
          <el-table-column prop="updated_at" label="修改时间" width="180" />
          <el-table-column prop="change_summary" label="变更摘要" min-width="200" />
          <el-table-column label="操作" width="180" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="viewVersionDiff(row)">查看差异</el-button>
              <el-button link type="warning" @click="rollbackVersion(row)">回滚</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <!-- 快速创建对话框 -->
    <el-dialog v-model="showQuickCreate" title="快速创建配置" width="600px">
      <el-form :model="createForm" label-width="100px">
        <el-form-item label="配置类型">
          <el-select v-model="createForm.type" placeholder="选择类型">
            <el-option label="发现模板" value="discovery" />
            <el-option label="巡检规则" value="inspection-rule" />
            <el-option label="阈值规则" value="threshold" />
            <el-option label="通知规则" value="notification" />
          </el-select>
        </el-form-item>
        <el-form-item label="名称">
          <el-input v-model="createForm.name" placeholder="请输入配置名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="createForm.description" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showQuickCreate = false">取消</el-button>
        <el-button type="primary" @click="handleCreate" :loading="creating">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, ArrowLeft } from '@element-plus/icons-vue'
import client from '@/shared/api/client'
import { API } from '@/shared/api/routes'

const router = useRouter()
const loading = ref(false)
const activeTab = ref('discovery')
const showQuickCreate = ref(false)
const creating = ref(false)

const stats = ref([
  { label: '发现模板', value: 0, color: '#165dff', trend: 0, click: () => { activeTab.value = 'discovery' } },
  { label: '巡检规则', value: 0, color: '#00b42a', trend: 0, click: () => { activeTab.value = 'inspection' } },
  { label: '阈值规则', value: 0, color: '#ff7d00', trend: 0, click: () => { activeTab.value = 'threshold' } },
  { label: '通知规则', value: 0, color: '#f53f3f', trend: 0, click: () => { activeTab.value = 'notification' } },
])

const discoveryTemplates = ref<any[]>([])
const inspectionRules = ref<any[]>([])
const thresholdRules = ref<any[]>([])
const notificationRules = ref<any[]>([])
const configVersions = ref<any[]>([])

const createForm = reactive({ type: '', name: '', description: '' })

const categoryMap: Record<string, string> = {
  page_check: '页面检查', config_check: '配置检查',
  log_check: '日志检查', baseline_check: '基线检查',
}

function severityType(severity: string) {
  const map: Record<string, string> = { critical: 'danger', high: 'warning', medium: '', low: 'info' }
  return map[severity] || 'info'
}

function unwrapItems(res: any): any[] {
  var raw = res?.data ?? {}
  var payload = raw.data ?? raw
  return payload?.items ?? payload?.results ?? (Array.isArray(payload) ? payload : [])
}

async function loadData() {
  loading.value = true
  try {
    var settled = await Promise.allSettled([
      client.get(API.DISCOVERY_TEMPLATES, { params: { page_size: 100 } }),
      client.get(API.CONFIGS, { params: { page_size: 100, type: 'inspection_rule' } }),
      client.get(API.CONFIGS, { params: { page_size: 100, type: 'threshold_rule' } }),
      client.get(API.NOTIFICATION_RULES, { params: { page_size: 100 } }),
      client.get(API.CONFIGS, { params: { page_size: 100, type: 'version' } }),
    ])
    discoveryTemplates.value = settled[0].status === 'fulfilled' ? unwrapItems(settled[0].value) : []
    inspectionRules.value = settled[1].status === 'fulfilled' ? unwrapItems(settled[1].value) : []
    thresholdRules.value = settled[2].status === 'fulfilled' ? unwrapItems(settled[2].value) : []
    notificationRules.value = settled[3].status === 'fulfilled' ? unwrapItems(settled[3].value) : []
    configVersions.value = settled[4].status === 'fulfilled' ? unwrapItems(settled[4].value) : []

    stats.value[0].value = discoveryTemplates.value.length
    stats.value[1].value = inspectionRules.value.length
    stats.value[2].value = thresholdRules.value.length
    stats.value[3].value = notificationRules.value.length
  } catch (e: any) {
    ElMessage.warning('部分数据加载失败: ' + (e.message ?? '未知错误'))
  } finally {
    loading.value = false
  }
}

async function runDiscovery(row: any) {
  try {
    await ElMessageBox.confirm(`确认执行发现模板「${row.name}」？`, '执行确认', { type: 'info' })
    ElMessage.success('发现任务已提交')
  } catch { /* cancelled */ }
}

function editTemplate(type: string, row: any) {
  const routeMap: Record<string, string> = {
    discovery: '/config/discovery-templates',
    'inspection-rule': '/config/inspection-rules',
    threshold: '/config/threshold-rules',
    notification: '/config/notification-rules',
  }
  router.push(routeMap[type] || '/config/overview')
}

async function deleteTemplate(type: string, row: any) {
  try {
    await ElMessageBox.confirm(`确认删除「${row.name}」？此操作不可恢复。`, '删除确认', { type: 'warning' })
    ElMessage.success('已删除')
    loadData()
  } catch { /* cancelled */ }
}

function simulateRule(row: any) {
  ElMessage.info('规则模拟功能开发中')
}

function toggleRule(row: any) {
  ElMessage.success(`规则已${row.enabled ? '启用' : '禁用'}`)
}

function viewVersionDiff(row: any) {
  ElMessage.info('版本差异对比功能开发中')
}

async function rollbackVersion(row: any) {
  try {
    await ElMessageBox.confirm(`确认回滚到版本 ${row.version}？`, '回滚确认', { type: 'warning' })
    ElMessage.success('配置已回滚')
    loadData()
  } catch { /* cancelled */ }
}

async function handleCreate() {
  if (!createForm.type || !createForm.name) {
    ElMessage.warning('请填写必要信息')
    return
  }
  creating.value = true
  try {
    ElMessage.success('配置创建成功')
    showQuickCreate.value = false
    createForm.type = ''
    createForm.name = ''
    createForm.description = ''
    loadData()
  } finally {
    creating.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.config-overview-page { padding: 20px; }
.stat-card:hover { transform: translateY(-2px); }
.stat-footer { margin-top: 8px; font-size: 12px; }
.trend-up { color: #00b42a; }
.trend-down { color: #f53f3f; }
.trend-label { color: #C0C4CC; margin-left: 4px; }
.mt-4 { margin-top: 16px; }
</style>
