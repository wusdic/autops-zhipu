<template>
  <div class="autops-page-container">
    <PageHeader title="配置总览" desc="配置中心入口：发现模板、巡检规则、阈值规则、通知规则、配置版本统一入口">
      <template #actions>
        <el-button plain @click="loadCounts" :loading="loading"><el-icon><Refresh /></el-icon> 刷新</el-button>
      </template>
    </PageHeader>

    <!-- 入口卡片：点击进入对应专管页（不再在总览页内重复整张表格，避免双份实现） -->
    <el-row :gutter="16" class="mt-lg">
      <el-col :span="8" v-for="entry in entries" :key="entry.path" class="mb-lg">
        <div class="autops-metric-card config-entry" @click="router.push(entry.path)">
          <div class="config-entry-head">
            <div class="metric-icon" :class="entry.bgClass">
              <el-icon size="20"><component :is="entry.icon" /></el-icon>
            </div>
            <div class="config-entry-count" :class="entry.textClass">{{ entry.count }}</div>
          </div>
          <div class="config-entry-label">{{ entry.label }}</div>
          <div class="config-entry-desc">{{ entry.desc }}</div>
          <div class="config-entry-action">
            进入管理 <el-icon><ArrowRight /></el-icon>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh, ArrowRight, Monitor, Search, Warning, Bell, Document } from '@element-plus/icons-vue'
import PageHeader from '@/shared/components/PageHeader.vue'
import client from '@/shared/api/client'
import { API } from '@/shared/api/routes'

const router = useRouter()
const loading = ref(false)

const entries = ref([
  { key: 'discovery', label: '发现模板', desc: '资产发现的扫描协议与参数模板', path: '/config/discovery-templates', icon: Monitor, bgClass: 'bg-brand', textClass: 'text-brand', count: 0 },
  { key: 'inspection', label: '巡检规则', desc: '页面/配置/日志/基线等巡检检查项', path: '/config/inspection-rules', icon: Search, bgClass: 'bg-success', textClass: 'text-success', count: 0 },
  { key: 'threshold', label: '阈值规则', desc: '指标告警阈值与触发条件', path: '/config/threshold-rules', icon: Warning, bgClass: 'bg-warning', textClass: 'text-warning', count: 0 },
  { key: 'notification', label: '通知规则', desc: '告警/事件的通知渠道与接收人', path: '/config/notification-rules', icon: Bell, bgClass: 'bg-danger', textClass: 'text-danger', count: 0 },
  { key: 'version', label: '配置版本', desc: '配置变更历史与版本回滚', path: '/config/versions', icon: Document, bgClass: 'bg-info', textClass: 'text-info', count: 0 },
])

function unwrapTotal(res: any): number {
  const raw = res?.data ?? {}
  const payload = raw.data ?? raw
  if (typeof payload?.total === 'number') return payload.total
  const items = payload?.items ?? payload?.results ?? (Array.isArray(payload) ? payload : [])
  return Array.isArray(items) ? items.length : 0
}

async function loadCounts() {
  loading.value = true
  try {
    const settled = await Promise.allSettled([
      client.get(API.DISCOVERY_TEMPLATES, { params: { page_size: 1 } }),
      client.get(API.CONFIGS, { params: { page_size: 1, type: 'inspection_rule' } }),
      client.get(API.CONFIGS, { params: { page_size: 1, type: 'threshold_rule' } }),
      client.get(API.NOTIFICATION_RULES, { params: { page_size: 1 } }),
      client.get(API.CONFIGS, { params: { page_size: 1, type: 'version' } }),
    ])
    entries.value.forEach((e, i) => {
      e.count = settled[i].status === 'fulfilled' ? unwrapTotal((settled[i] as PromiseFulfilledResult<any>).value) : 0
    })
  } catch (e: any) {
    ElMessage.warning('部分统计加载失败: ' + (e?.message ?? '未知错误'))
  } finally {
    loading.value = false
  }
}

onMounted(loadCounts)
</script>

<style scoped>
.mt-lg { margin-top: var(--autops-space-lg); }
.mb-lg { margin-bottom: var(--autops-space-lg); }
.config-entry { cursor: pointer; transition: box-shadow .2s, transform .2s; }
.config-entry:hover { box-shadow: var(--autops-shadow-md, 0 4px 12px rgba(0,0,0,.1)); transform: translateY(-2px); }
.config-entry-head { display: flex; align-items: center; justify-content: space-between; }
.config-entry-count { font-size: 28px; font-weight: 600; }
.config-entry-label { margin-top: 8px; font-size: 15px; font-weight: 600; }
.config-entry-desc { margin-top: 4px; font-size: 12px; color: var(--autops-text-secondary, #909399); min-height: 32px; }
.config-entry-action { margin-top: 8px; font-size: 12px; color: var(--autops-color-primary, #409eff); display: flex; align-items: center; gap: 2px; }
</style>
