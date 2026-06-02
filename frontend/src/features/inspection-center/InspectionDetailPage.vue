<template>
  <div class="page-container">
    <el-page-header @back="$router.back()" :title="'返回'">
      <template #content>
        <span>巡检详情</span>
        <el-tag v-if="detail" :type="statusTagType(detail.status)" size="small" style="margin-left: 8px">
          {{ statusLabel(detail.status) }}
        </el-tag>
      </template>
    </el-page-header>

    <el-row :gutter="16" style="margin-top: 16px" v-if="detail">
      <!-- 基本信息 -->
      <el-col :span="16">
        <el-card shadow="never">
          <template #header><span>基本信息</span></template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="任务ID">{{ detail.id }}</el-descriptions-item>
            <el-descriptions-item label="巡检计划">{{ detail.planName }}</el-descriptions-item>
            <el-descriptions-item label="巡检模板">{{ detail.templateName }}</el-descriptions-item>
            <el-descriptions-item label="执行时间">{{ detail.startTime }}</el-descriptions-item>
            <el-descriptions-item label="完成时间">{{ detail.endTime }}</el-descriptions-item>
            <el-descriptions-item label="执行耗时">{{ detail.duration }}</el-descriptions-item>
            <el-descriptions-item label="目标范围">{{ detail.scope }}</el-descriptions-item>
            <el-descriptions-item label="检查项数">{{ detail.totalChecks }}</el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 检查结果统计 -->
        <el-card shadow="never" style="margin-top: 16px">
          <template #header><span>检查结果统计</span></template>
          <el-row :gutter="16">
            <el-col :span="6">
              <el-statistic title="通过" :value="detail.passed" />
            </el-col>
            <el-col :span="6">
              <el-statistic title="警告" :value="detail.warned" />
            </el-col>
            <el-col :span="6">
              <el-statistic title="失败" :value="detail.failed" />
            </el-col>
            <el-col :span="6">
              <el-statistic title="跳过" :value="detail.skipped" />
            </el-col>
          </el-row>
        </el-card>

        <!-- 检查项详情列表 -->
        <el-card shadow="never" style="margin-top: 16px">
          <template #header>
            <div style="display:flex;justify-content:space-between;align-items:center">
              <span>检查项详情</span>
              <el-input v-model="checkFilter" placeholder="搜索检查项" style="width:200px" clearable :prefix-icon="Search" />
            </div>
          </template>
          <el-table :data="filteredChecks" stripe max-height="400">
            <el-table-column prop="name" label="检查项" min-width="180" />
            <el-table-column prop="category" label="分类" width="120" />
            <el-table-column prop="target" label="检查对象" width="150" />
            <el-table-column prop="status" label="状态" width="90">
              <template #default="{ row }">
                <el-tag :type="checkStatusType(row.status)" size="small">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="expected" label="期望值" width="120" />
            <el-table-column prop="actual" label="实际值" width="120" />
            <el-table-column prop="message" label="说明" min-width="200" show-overflow-tooltip />
          </el-table>
        </el-card>
      </el-col>

      <!-- 右侧面板 -->
      <el-col :span="8">
        <el-card shadow="never">
          <template #header><span>操作</span></template>
          <el-space direction="vertical" fill style="width:100%">
            <el-button type="primary" style="width:100%" @click="rerunInspection">重新巡检</el-button>
            <el-button style="width:100%" @click="exportReport">导出报告</el-button>
            <el-button type="warning" style="width:100%" @click="createTicket" v-if="detail.failed > 0">
              失败项转工单
            </el-button>
          </el-space>
        </el-card>

        <el-card shadow="never" style="margin-top: 16px">
          <template #header><span>巡检时间线</span></template>
          <el-timeline>
            <el-timeline-item
              v-for="item in timeline"
              :key="item.time"
              :timestamp="item.time"
              :type="item.type"
              placement="top"
            >
              {{ item.content }}
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'

const route = useRoute()
const checkFilter = ref('')

const detail = ref({
  id: String(route.params.id || 'INS-001'),
  planName: '每日基础巡检',
  templateName: 'Linux 服务器基础巡检模板',
  startTime: '2026-06-02 08:00:00',
  endTime: '2026-06-02 08:15:23',
  duration: '15m 23s',
  scope: '生产环境 Linux 服务器 (32台)',
  totalChecks: 96,
  passed: 78,
  warned: 12,
  failed: 4,
  skipped: 2,
  status: 'completed',
})

const checks = ref([
  { name: 'CPU 使用率', category: '性能', target: 'web-server-01', status: '通过', expected: '<80%', actual: '45%', message: '' },
  { name: '磁盘使用率', category: '容量', target: 'web-server-01', status: '通过', expected: '<85%', actual: '62%', message: '' },
  { name: '内存使用率', category: '性能', target: 'web-server-02', status: '警告', expected: '<80%', actual: '78%', message: '接近阈值' },
  { name: 'SSH 服务状态', category: '服务', target: 'db-server-01', status: '失败', expected: 'running', actual: 'stopped', message: 'SSH服务未运行' },
])

const filteredChecks = computed(() => {
  if (!checkFilter.value) return checks.value
  const kw = checkFilter.value.toLowerCase()
  return checks.value.filter(c => c.name.toLowerCase().includes(kw) || c.target.toLowerCase().includes(kw))
})

const timeline = ref([
  { time: '2026-06-02 08:15:23', content: '巡检完成', type: 'success' },
  { time: '2026-06-02 08:00:00', content: '开始巡检', type: 'primary' },
  { time: '2026-06-02 07:59:50', content: '任务调度触发', type: 'info' },
])

const statusTagType = (s: string) => s === 'completed' ? 'success' : s === 'running' ? 'warning' : s === 'failed' ? 'danger' : 'info'
const statusLabel = (s: string) => ({ completed: '已完成', running: '执行中', failed: '执行失败', pending: '待执行' }[s] || s)
const checkStatusType = (s: string) => s === '通过' ? 'success' : s === '警告' ? 'warning' : s === '失败' ? 'danger' : 'info'

function rerunInspection() { ElMessage.info('正在重新执行巡检...') }
function exportReport() { ElMessage.success('报告导出中...') }
function createTicket() { ElMessage.success('已创建工单') }
</script>

<style scoped>
.page-container { padding: 16px; }
</style>
