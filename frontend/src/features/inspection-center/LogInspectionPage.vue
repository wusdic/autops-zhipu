<template>
  <div class="autops-page-container">
    <!-- 页面头部 -->
    <div class="autops-page-header">
      <div class="autops-page-title">日志巡检</div>
      <div class="autops-page-desc">日志源、匹配规则、命中数量、样例日志</div>
    </div>

    <!-- 搜索栏 -->
    <div class="page-toolbar">
      <el-input
        v-model="searchQuery"
        placeholder="搜索资产名 / 日志路径..."
        clearable
        style="width: 280px"
        @keyup.enter="fetchData"
        @clear="fetchData"
      >
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
      <el-select v-model="severityFilter" placeholder="严重级别" clearable style="width: 140px" @change="fetchData">
        <el-option label="错误" value="error" />
        <el-option label="警告" value="warning" />
        <el-option label="信息" value="info" />
      </el-select>
      <el-button type="default" @click="fetchData">
        <el-icon><Refresh /></el-icon> 刷新
      </el-button>
    </div>

    <!-- 数据表格 -->
    <el-table stripe :data="tableData" v-loading="loading"empty-text="暂无日志巡检数据">
      <el-table-column prop="asset_name" label="资产名" min-width="160" show-overflow-tooltip />
      <el-table-column prop="log_path" label="日志路径" min-width="220" show-overflow-tooltip>
        <template #default="{ row }">
          <span class="log-path">{{ row.log_path ?? row.log_source ?? '-' }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="error_count" label="错误数" width="100" align="center">
        <template #default="{ row }">
          <el-badge
            v-if="row.error_count && row.error_count > 0"
            :value="row.error_count"
            :max="9999"
            type="danger"
            class="count-badge"
          >
            <span class="count-value danger">{{ row.error_count }}</span>
          </el-badge>
          <span v-else class="count-value">{{ row.error_count ?? 0 }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="warning_count" label="警告数" width="100" align="center">
        <template #default="{ row }">
          <span :class="['count-value', row.warning_count > 0 ? 'warning' : '']">
            {{ row.warning_count ?? 0 }}
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="pattern" label="关键模式匹配" min-width="200" show-overflow-tooltip>
        <template #default="{ row }">
          <template v-if="row.patterns && Array.isArray(row.patterns) && row.patterns.length > 0">
            <el-tag
              v-for="(p, idx) in row.patterns.slice(0, 3)"
              :key="idx"
              size="small"
              effect="plain"
              class="pattern-tag"
            >
              {{ p }}
            </el-tag>
            <span v-if="row.patterns.length > 3" class="text-tertiary">
              +{{ row.patterns.length - 3 }}
            </span>
          </template>
          <template v-else-if="row.pattern">
            <el-tag size="small" effect="plain">{{ row.pattern }}</el-tag>
          </template>
          <template v-else-if="row.match_rule">
            <el-tag size="small" effect="plain">{{ row.match_rule }}</el-tag>
          </template>
          <span v-else class="text-tertiary">-</span>
        </template>
      </el-table-column>
      <el-table-column prop="checked_at" label="检查时间" width="180">
        <template #default="{ row }">
          <span class="text-tertiary">{{ row.checked_at || row.created_at || '-' }}</span>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="page-pagination">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.page_size"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        background
        @size-change="fetchData"
        @current-change="fetchData"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh } from '@element-plus/icons-vue'
import client from '@/shared/api/client'
import { API } from '@/shared/api/routes'

// ---------- 状态 ----------
const loading = ref(false)
const tableData = ref<any[]>([])
const searchQuery = ref('')
const severityFilter = ref('')

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0,
})

// ---------- API ----------
async function fetchData() {
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: pagination.page,
      page_size: pagination.page_size,
    }
    if (searchQuery.value.trim()) {
      params.keyword = searchQuery.value.trim()
    }
    if (severityFilter.value) {
      params.severity = severityFilter.value
    }
    const res = await client.get(API.INSPECTION.LOG_CHECKS, { params })
    const data = res.data?.data ?? res.data
    tableData.value = data?.items ?? data ?? []
    pagination.total = data?.total ?? tableData.value.length
  } catch (err: any) {
    ElMessage.error(err.message || '获取日志巡检数据失败')
  } finally {
    loading.value = false
  }
}

// ---------- 初始化 ----------
onMounted(() => {
  fetchData()
})
</script>

<style scoped>

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.page-desc {
  font-size: var(--autops-font-13);
  color: var(--autops-info);
  margin: 0 0 16px 0;
}
.page-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: var(--autops-space-lg);
}
.page-pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: var(--autops-space-lg);
}
.text-tertiary {
  color: var(--autops-info);
  font-size: var(--autops-font-13);
}
.log-path {
  font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
  font-size: var(--autops-font-13);
  color: var(--autops-text-2);
}
.count-value {
  font-weight: 600;
  font-size: var(--autops-font-14);
}
.count-value.danger {
  color: var(--autops-danger);
}
.count-value.warning {
  color: var(--autops-warning);
}
.count-badge {
  display: inline-flex;
  align-items: center;
}
.pattern-tag {
  margin-right: 4px;
  margin-bottom: 2px;
}
</style>
