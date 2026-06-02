<template>
  <div class="page-container">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>风险分级管理</span>
          <el-button type="primary" @click="showConfigDialog = true">
            <el-icon><Setting /></el-icon>分级配置
          </el-button>
        </div>
      </template>

      <!-- 风险等级统计 -->
      <el-row :gutter="16" class="stat-row">
        <el-col :span="4" v-for="level in riskLevels" :key="level.key">
          <el-card :body-style="{ padding: '16px', textAlign: 'center' }" :style="{ borderTop: \`3px solid \${level.color}\` }">
            <div :style="{ fontSize: '28px', fontWeight: 700, color: level.color }">{{ level.count }}</div>
            <div style="color: #86909c; margin-top: 4px">{{ level.label }}</div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 筛选栏 -->
      <el-row :gutter="12" class="filter-row">
        <el-col :span="5">
          <el-input v-model="filters.keyword" placeholder="搜索异常/告警名称" clearable :prefix-icon="Search" />
        </el-col>
        <el-col :span="4">
          <el-select v-model="filters.riskLevel" placeholder="风险等级" clearable>
            <el-option v-for="l in riskLevels" :key="l.key" :label="l.label" :value="l.key" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-select v-model="filters.sourceType" placeholder="来源类型" clearable>
            <el-option label="异常检测" value="anomaly" />
            <el-option label="告警触发" value="alert" />
            <el-option label="巡检发现" value="inspection" />
            <el-option label="手动评估" value="manual" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-select v-model="filters.assetType" placeholder="资产类型" clearable>
            <el-option label="Linux 服务器" value="linux_server" />
            <el-option label="Windows 服务器" value="windows_server" />
            <el-option label="数据库" value="database" />
            <el-option label="网络设备" value="network" />
          </el-select>
        </el-col>
        <el-col :span="3">
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-col>
      </el-row>

      <!-- 数据表 -->
      <el-table :data="tableData" stripe class="data-table" @sort-change="handleSort">
        <el-table-column prop="name" label="异常/告警名称" min-width="180" show-overflow-tooltip />
        <el-table-column prop="sourceType" label="来源" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ sourceTypeLabel(row.sourceType) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="riskLevel" label="风险等级" width="100" sortable="custom">
          <template #default="{ row }">
            <el-tag :color="getRiskColor(row.riskLevel)" style="color:#fff;border:none" size="small">
              {{ getRiskLabel(row.riskLevel) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="impactScope" label="影响范围" width="120" />
        <el-table-column prop="assetName" label="关联资产" width="140" />
        <el-table-column prop="autoEscalate" label="自动升级" width="90">
          <template #default="{ row }">
            <el-switch v-model="row.autoEscalate" size="small" @change="toggleEscalate(row)" />
          </template>
        </el-table-column>
        <el-table-column prop="score" label="风险评分" width="90" sortable="custom">
          <template #default="{ row }">
            <span :style="{ color: row.score >= 80 ? '#f53f3f' : row.score >= 50 ? '#ff7d00' : '#00b42a', fontWeight: 600 }">
              {{ row.score }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="gradedBy" label="分级人" width="100" />
        <el-table-column prop="gradedAt" label="分级时间" width="170" />
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="regrade(row)">重新分级</el-button>
            <el-button link type="warning" size="small" @click="viewDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        class="pagination"
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[20, 50, 100]"
        layout="total, sizes, prev, pager, next"
      />
    </el-card>

    <!-- 重新分级对话框 -->
    <el-dialog v-model="regradeVisible" title="重新风险分级" width="500px">
      <el-form :model="regradeForm" label-width="100px">
        <el-form-item label="名称">{{ regradeForm.name }}</el-form-item>
        <el-form-item label="当前等级">
          <el-tag :color="getRiskColor(regradeForm.currentLevel)" style="color:#fff;border:none">
            {{ getRiskLabel(regradeForm.currentLevel) }}
          </el-tag>
        </el-form-item>
        <el-form-item label="目标等级" required>
          <el-select v-model="regradeForm.targetLevel" placeholder="选择目标等级">
            <el-option v-for="l in riskLevels" :key="l.key" :label="l.label" :value="l.key" />
          </el-select>
        </el-form-item>
        <el-form-item label="分级原因" required>
          <el-input v-model="regradeForm.reason" type="textarea" :rows="3" placeholder="说明变更原因" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="regradeVisible = false">取消</el-button>
        <el-button type="primary" @click="submitRegrade">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Setting } from '@element-plus/icons-vue'

const riskLevels = [
  { key: 'critical', label: '严重', color: '#f53f3f', count: 3 },
  { key: 'high', label: '高危', color: '#ff7d00', count: 8 },
  { key: 'medium', label: '中危', color: '#ffb400', count: 15 },
  { key: 'low', label: '低危', color: '#00b42a', count: 24 },
  { key: 'info', label: '信息', color: '#86909c', count: 42 },
]

const getRiskLabel = (k: string) => riskLevels.find(l => l.key === k)?.label || k
const getRiskColor = (k: string) => riskLevels.find(l => l.key === k)?.color || '#86909c'
const sourceTypeLabel = (s: string) => ({ anomaly: '异常', alert: '告警', inspection: '巡检', manual: '手动' }[s] || s)

const filters = reactive({ keyword: '', riskLevel: '', sourceType: '', assetType: '' })
const tableData = ref<any[]>([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

function handleSearch() { page.value = 1 }
function resetFilters() { Object.assign(filters, { keyword: '', riskLevel: '', sourceType: '', assetType: '' }) }
function handleSort() {}

function toggleEscalate(row: any) {
  ElMessage.success(\`\${row.autoEscalate ? '已启用' : '已关闭'}自动升级\`)
}

const regradeVisible = ref(false)
const regradeForm = reactive({ name: '', currentLevel: '', targetLevel: '', reason: '', id: '' })
function regrade(row: any) {
  regradeForm.name = row.name
  regradeForm.currentLevel = row.riskLevel
  regradeForm.targetLevel = ''
  regradeForm.reason = ''
  regradeForm.id = row.id
  regradeVisible.value = true
}
function submitRegrade() {
  if (!regradeForm.targetLevel || !regradeForm.reason) {
    ElMessage.warning('请填写必填项')
    return
  }
  ElMessage.success('分级变更成功')
  regradeVisible.value = false
}
function viewDetail(row: any) {
  ElMessage.info('查看详情: ' + row.name)
}

const showConfigDialog = ref(false)
</script>

<style scoped>
.page-container { padding: 16px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.stat-row { margin-bottom: 20px; }
.filter-row { margin-bottom: 16px; }
.data-table { margin-bottom: 16px; }
.pagination { display: flex; justify-content: flex-end; }
</style>
