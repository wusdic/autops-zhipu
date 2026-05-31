<template>
  <div class="page-container">
    <div class="page-header">
      <h2>平台状态</h2>
      <el-button @click="loadStatus" :loading="loading">
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
    </div>

    <div class="status-grid" v-loading="loading">
      <el-card v-for="comp in components" :key="comp.key" class="status-card" shadow="hover">
        <div class="card-header">
          <span class="card-icon">{{ comp.icon }}</span>
          <span class="card-title">{{ comp.label }}</span>
          <el-tag :type="getTagType(comp.status)" size="small" effect="dark">
            {{ statusLabels[comp.status] || comp.status || '未知' }}
          </el-tag>
        </div>
        <div class="card-body" v-if="comp.detail">
          <div class="detail-row" v-for="(val, key) in comp.detail" :key="key">
            <span class="detail-key">{{ key }}</span>
            <span class="detail-val">{{ val }}</span>
          </div>
        </div>
        <div class="card-body" v-else>
          <span class="text-muted">暂无详情</span>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import api from '@/shared/api/client'
import { API as R } from '@/shared/api/routes'

interface StatusComponent {
  key: string
  label: string
  icon: string
  status: string
  detail: Record<string, string> | null
}

const statusLabels: Record<string, string> = {
  healthy: '正常',
  degraded: '降级',
  unhealthy: '异常',
  unknown: '未知',
}

const loading = ref(false)
const components = ref<StatusComponent[]>([
  { key: 'database', label: '数据库', icon: '🗄️', status: 'unknown', detail: null },
  { key: 'redis', label: 'Redis', icon: '⚡', status: 'unknown', detail: null },
  { key: 'llm', label: 'LLM 服务', icon: '🤖', status: 'unknown', detail: null },
  { key: 'collector', label: '采集器', icon: '📡', status: 'unknown', detail: null },
  { key: 'frontend', label: '前端', icon: '🖥️', status: 'healthy', detail: { status: 'running' } },
])

function getTagType(status: string): 'success' | 'warning' | 'danger' | 'info' {
  switch (status) {
    case 'healthy': return 'success'
    case 'degraded': return 'warning'
    case 'unhealthy': return 'danger'
    default: return 'info'
  }
}

async function loadStatus() {
  loading.value = true
  try {
    const { data } = await api.get(R.PLATFORM_STATUS)
    if (data.code === 0) {
      const result = data.data || data
      // 后端返回格式: { components: { database: { status, detail }, ... } }
      const statusData = result.components || result
      components.value.forEach(comp => {
        const info = statusData[comp.key]
        if (info) {
          comp.status = info.status || 'unknown'
          comp.detail = info.detail || null
        }
      })
    }
  } catch (e: any) {
    ElMessage.error('加载平台状态失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => { loadStatus() })
</script>

<style scoped>
.page-container { padding: 20px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h2 { margin: 0; font-size: 20px; color: #303133; }

.status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.status-card {
  border-radius: 8px;
}
.status-card :deep(.el-card__body) {
  padding: 16px 20px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-size: 15px;
  font-weight: 600;
}
.card-icon { font-size: 22px; }
.card-title { flex: 1; }

.card-body { font-size: 13px; }
.detail-row {
  display: flex;
  justify-content: space-between;
  padding: 4px 0;
  border-bottom: 1px solid #f0f0f0;
}
.detail-row:last-child { border-bottom: none; }
.detail-key { color: #909399; }
.detail-val { color: #303133; font-weight: 500; }

.text-muted { color: #909399; font-size: 13px; }
</style>
