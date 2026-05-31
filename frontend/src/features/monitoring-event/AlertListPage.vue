<template>
  <div class="alert-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>告警中心</span>
          <div>
            <el-radio-group v-model="filters.status" @change="loadAlerts">
              <el-radio-button value="">全部</el-radio-button>
              <el-radio-button value="firing">告警中</el-radio-button>
              <el-radio-button value="acknowledged">已确认</el-radio-button>
              <el-radio-button value="resolved">已恢复</el-radio-button>
            </el-radio-group>
          </div>
        </div>
      </template>

      <el-table :data="alerts" v-loading="loading" stripe>
        <el-table-column prop="severity" label="级别" width="90">
          <template #default="{ row }">
            <el-tag :type="severityType(row.severity)" size="small" effect="dark">
              {{ severityLabel(row.severity) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="告警标题" min-width="200" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="触发时间" width="180" />
        <el-table-column prop="acknowledged_at" label="确认时间" width="180" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.status === 'firing'" size="small" type="warning"
              @click="ackAlert(row.id)">确认</el-button>
            <el-button v-if="row.status !== 'resolved'" size="small" type="success"
              @click="resolveAlert(row.id)">恢复</el-button>
            <el-button size="small" @click="createTicket(row)">转工单</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        layout="total, sizes, prev, pager, next"
        @change="loadAlerts"
        style="margin-top: 16px; justify-content: flex-end"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/shared/api/client'
import { API as R } from '@/shared/api/routes'

const loading = ref(false)
const alerts = ref<any[]>([])
const filters = reactive({ status: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })


function severityType(s: string) {
  return s === 'critical' ? 'danger' : s === 'warning' ? 'warning' : 'info'
}
function severityLabel(s: string) {
  return s === 'critical' ? '严重' : s === 'warning' ? '警告' : '信息'
}
function statusType(s: string) {
  return s === 'firing' ? 'danger' : s === 'acknowledged' ? 'warning' : 'success'
}
function statusLabel(s: string) {
  return s === 'firing' ? '告警中' : s === 'acknowledged' ? '已确认' : '已恢复'
}

async function loadAlerts() {
  loading.value = true
  try {
    const params: any = { page: pagination.page, page_size: pagination.pageSize }
    if (filters.status) params.status = filters.status
    const { data } = await api.get(R.ALERTS, { params })
    if (data.code === 0) {
      alerts.value = data.data.items || []
      pagination.total = data.data.total || 0
    }
  } catch (e: any) {
    ElMessage.error('加载告警失败')
  } finally {
    loading.value = false
  }
}

async function ackAlert(id: string) {
  try {
    const { data } = await api.post(R.ALERT_ACKNOWLEDGE(id))
    if (data.code === 0) {
      ElMessage.success('告警已确认')
      loadAlerts()
    }
  } catch (e: any) {
    ElMessage.error('操作失败')
  }
}

async function resolveAlert(id: string) {
  try {
    const { data } = await api.post(R.ALERT_RESOLVE(id))
    if (data.code === 0) {
      ElMessage.success('告警已恢复')
      loadAlerts()
    }
  } catch (e: any) {
    ElMessage.error('操作失败')
  }
}

async function createTicket(alert: any) {
  try {
    await ElMessageBox.prompt('工单描述（可选）', '转工单', {
      confirmButtonText: '创建',
      cancelButtonText: '取消',
      inputPlaceholder: '请输入工单描述',
    }).then(async ({ value }) => {
      const { data } = await api.post(R.TICKETS, {
        title: `[告警] ${alert.title}`,
        ticket_type: 'incident',
        priority: alert.severity === 'critical' ? 'high' : 'medium',
        description: value || alert.title,
        alert_ids: JSON.stringify([alert.id]),
      })
      if (data.code === 0) {
        ElMessage.success('工单已创建')
      }
    })
  } catch { /* cancelled */ }
}

onMounted(() => loadAlerts())
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
</style>
