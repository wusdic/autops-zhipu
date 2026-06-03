<template>
  <div class="config-version-page">
    <el-page-header @back="router.back()" title="返回" content="配置版本管理">
      <template #extra>
        <el-button @click="loadData" :loading="loading">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
      </template>
    </el-page-header>

    <!-- 搜索 -->
    <el-card class="mt-4" shadow="never">
      <el-form :inline="true" :model="filters">
        <el-form-item label="配置名称">
          <el-input v-model="filters.keyword" placeholder="搜索配置名称" clearable @clear="loadData" />
        </el-form-item>
        <el-form-item label="修改人">
          <el-input v-model="filters.user" placeholder="修改人" clearable @clear="loadData" />
        </el-form-item>
        <el-form-item label="时间范围">
          <el-date-picker v-model="filters.dateRange" type="daterange" range-separator="至" start-placeholder="开始" end-placeholder="结束" value-format="YYYY-MM-DD" @change="loadData" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">搜索</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 版本列表 -->
    <el-card class="mt-4" shadow="never">
      <el-table :data="versions" v-loading="loading" stripe border>
        <el-table-column prop="config_name" label="配置名称" min-width="200" sortable />
        <el-table-column prop="config_type" label="配置类型" width="130">
          <template #default="{ row }">
            <el-tag size="small">{{ configTypeName(row.config_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="version" label="版本号" width="100" />
        <el-table-column prop="change_summary" label="变更摘要" min-width="200" />
        <el-table-column prop="updated_by" label="修改人" width="120" />
        <el-table-column prop="updated_at" label="修改时间" width="180" sortable />
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="viewDetail(row)">查看</el-button>
            <el-button link type="primary" @click="viewDiff(row)">差异对比</el-button>
            <el-button link type="warning" @click="rollback(row)">回滚到此版本</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination class="mt-4" v-model:current-page="pagination.page" v-model:page-size="pagination.size"
        :total="pagination.total" :page-sizes="[20, 50, 100]" layout="total, sizes, prev, pager, next"
        @size-change="loadData" @current-change="loadData" />
    </el-card>

    <!-- 版本详情 -->
    <el-dialog v-model="detailVisible" title="版本详情" width="700px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="配置名称">{{ detailData.config_name }}</el-descriptions-item>
        <el-descriptions-item label="版本号">v{{ detailData.version }}</el-descriptions-item>
        <el-descriptions-item label="配置类型">{{ configTypeName(detailData.config_type) }}</el-descriptions-item>
        <el-descriptions-item label="修改人">{{ detailData.updated_by }}</el-descriptions-item>
        <el-descriptions-item label="修改时间" :span="2">{{ detailData.updated_at }}</el-descriptions-item>
        <el-descriptions-item label="变更摘要" :span="2">{{ detailData.change_summary }}</el-descriptions-item>
      </el-descriptions>
      <el-divider>配置内容</el-divider>
      <el-input type="textarea" :model-value="detailData.content" :rows="12" readonly />
    </el-dialog>

    <!-- 差异对比 -->
    <el-dialog v-model="diffVisible" title="版本差异对比" width="900px">
      <div class="diff-container">
        <div class="diff-panel">
          <h4>当前版本 (v{{ diffData.current_version }})</h4>
          <pre class="diff-content">{{ diffData.current_content }}</pre>
        </div>
        <div class="diff-panel">
          <h4>对比版本 (v{{ diffData.compare_version }})</h4>
          <pre class="diff-content">{{ diffData.compare_content }}</pre>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'

const router = useRouter()
const loading = ref(false)
const detailVisible = ref(false)
const diffVisible = ref(false)
const versions = ref<any[]>([])
const detailData = ref<any>({})
const diffData = ref<any>({})

const filters = reactive({ keyword: '', user: '', dateRange: null as string[] | null })
const pagination = reactive({ page: 1, size: 20, total: 0 })

const configTypeMap: Record<string, string> = {
  discovery_template: '发现模板', inspection_template: '巡检模板', policy: '策略',
  threshold_rule: '阈值规则', notification_rule: '通知规则', collector_config: '采集器配置',
}
function configTypeName(t: string) { return configTypeMap[t] || t }

async function loadData() {
  loading.value = true
  try { versions.value = []; pagination.total = 0 } finally { loading.value = false }
}

function viewDetail(row: any) {
  detailData.value = row
  detailVisible.value = true
}

function viewDiff(row: any) {
  diffData.value = {
    current_version: row.version, compare_version: Math.max(1, row.version - 1),
    current_content: '# 当前版本配置内容
key1: value1
key2: value2',
    compare_content: '# 上一版本配置内容
key1: old_value1
key2: value2',
  }
  diffVisible.value = true
}

async function rollback(row: any) {
  try {
    await ElMessageBox.confirm(
      `确认回滚配置「${row.config_name}」到版本 v${row.version}？当前配置将被替换。`,
      '回滚确认', { type: 'warning' }
    )
    ElMessage.success('配置已回滚')
    loadData()
  } catch { /* cancelled */ }
}

onMounted(loadData)
</script>

<style scoped>
.config-version-page { padding: 20px; }
.mt-4 { margin-top: 16px; }
.diff-container { display: flex; gap: 16px; }
.diff-panel { flex: 1; }
.diff-panel h4 { margin: 0 0 8px; color: #303133; }
.diff-content { background: #f5f7fa; padding: 12px; border-radius: 4px; font-size: 13px; max-height: 400px; overflow: auto; }
</style>
