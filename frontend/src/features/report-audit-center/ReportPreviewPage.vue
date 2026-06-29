<template>
  <div class="report-preview-page autops-page-container">
    <!-- Page Header -->
    <PageHeader title="报告预览" back desc="在线预览生成的报表内容">
      <template #actions>
        <el-button type="primary" :loading="downloading" @click="handleDownload">
          <el-icon style="margin-right: 4px"><Download /></el-icon>
          下载报表
        </el-button>
      </template>
    </PageHeader>

    <!-- Loading State -->
    <div v-if="loading" class="loading-wrapper">
      <el-skeleton :rows="12" animated />
    </div>

    <!-- Preview Content -->
    <div v-else-if="previewData" class="preview-content">
      <!-- Report Header -->
      <div class="autops-card mb-lg">
        <div class="autops-card-body">
          <div class="report-header">
            <h2 class="report-title">{{ previewData.title || '未命名报表' }}</h2>
            <div class="report-meta">
              <el-tag size="small">{{ previewData.template_name || '-' }}</el-tag>
              <el-tag type="success" size="small">{{ formatLabel(previewData.format) }}</el-tag>
              <span class="meta-text">生成时间: {{ formatTime(previewData.generated_at) }}</span>
            </div>
          </div>
          <el-descriptions :column="3" border size="small" class="mt-md">
            <el-descriptions-item label="报表类型">{{ previewData.type || '-' }}</el-descriptions-item>
            <el-descriptions-item label="时间范围">
              {{ previewData.start_date || '-' }} 至 {{ previewData.end_date || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="生成人">{{ previewData.created_by || '-' }}</el-descriptions-item>
          </el-descriptions>
        </div>
      </div>

      <!-- Report Sections -->
      <div v-for="(section, idx) in previewData.sections || []" :key="idx" class="autops-card mb-lg">
        <div class="autops-card-header">
          <span class="autops-card-title">{{ section.title || '章节 ' + idx + 1 }}</span>
        </div>
        <div class="autops-card-body">
          <!-- Summary Section -->
          <template v-if="section.type === 'summary'">
            <el-descriptions :column="2" border size="small">
              <el-descriptions-item
                v-for="(item, i) in section.items || []"
                :key="i"
                :label="item.label"
              >
                <span :style="{ color: item.color || '' }">{{ item.value }}</span>
              </el-descriptions-item>
            </el-descriptions>
          </template>

          <!-- Table Section -->
          <template v-else-if="section.type === 'table'">
            <el-table stripe
 :data="section.rows || []"border
 size="small"
 class="section-table"
 >
              <el-table-column
                v-for="(col, ci) in section.columns || []"
                :key="ci"
                :prop="col.prop"
                :label="col.label"
                :min-width="col.width || 120"
                show-overflow-tooltip
              >
                <template #default="{ row }">
                  <template v-if="col.type === 'tag'">
                    <el-tag :type="col.tagType || ''" size="small">{{ row[col.prop] }}</el-tag>
                  </template>
                  <template v-else-if="col.type === 'number'">
                    <span style="font-variant-numeric: tabular-nums">{{ row[col.prop] }}</span>
                  </template>
                  <template v-else>
                    {{ row[col.prop] ?? '-' }}
                  </template>
                </template>
              </el-table-column>
            </el-table>
          </template>

          <!-- Text Section -->
          <template v-else-if="section.type === 'text'">
            <div class="section-text">{{ section.content || '暂无内容' }}</div>
          </template>

          <!-- Fallback: render as descriptions -->
          <template v-else>
            <el-descriptions :column="2" border size="small">
              <el-descriptions-item
                v-for="(item, i) in section.items || []"
                :key="i"
                :label="item.label"
              >{{ item.value ?? '-' }}</el-descriptions-item>
            </el-descriptions>
          </template>
        </div>
      </div>

      <!-- Fallback when no sections -->
      <div v-if="!previewData.sections || previewData.sections.length === 0" class="autops-card">
        <div class="autops-card-body">
          <el-descriptions :column="2" border>
            <el-descriptions-item
              v-for="(value, key) in flatPreview"
              :key="key"
              :label="String(key)"
            >{{ value ?? '-' }}</el-descriptions-item>
          </el-descriptions>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="empty-state">
      <el-empty description="未找到报表数据">
        <el-button type="primary" @click="goBack">返回</el-button>
      </el-empty>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Download } from '@element-plus/icons-vue'
import { reportService } from '@/shared/api'
import PageHeader from '@/shared/components/PageHeader.vue'

const route = useRoute()
const router = useRouter()

// ── State ──────────────────────────────────────────────────────────
const loading = ref(false)
const downloading = ref(false)
const previewData = ref<any>(null)
const taskId = ref('')

// ── Computed ───────────────────────────────────────────────────────
const flatPreview = computed(() => {
  if (!previewData.value || previewData.value.sections?.length) return {}
  const { sections, ...rest } = previewData.value
  return rest
})

// ── Helpers ────────────────────────────────────────────────────────
function formatTime(val: string | null | undefined): string {
  if (!val) return '-'
  const d = new Date(val)
  if (isNaN(d.getTime())) return '-'
  const pad = (n: number) => String(n).padStart(2, '0')
  return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()) + ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes()) + ':' + pad(d.getSeconds())
}

function formatLabel(f: string): string {
  const map: Record<string, string> = { pdf: 'PDF', html: 'HTML', xlsx: 'Excel', docx: 'Word' }
  return map[f] || f || '-'
}

// ── Data Loading ───────────────────────────────────────────────────
async function loadPreview() {
  if (!taskId.value) return
  loading.value = true
  try {
    const { data } = await reportService.getPreview(taskId.value)
    if (data.code === 0) {
      previewData.value = data.data || null
    } else {
      ElMessage.error(data.message || '加载报表预览失败')
    }
  } catch (err: any) {
    ElMessage.error(err.message || '加载报表预览失败')
  } finally {
    loading.value = false
  }
}

// ── Actions ────────────────────────────────────────────────────────
async function handleDownload() {
  if (!taskId.value) return
  downloading.value = true
  try {
    const { data } = await reportService.download(taskId.value)
    if (data instanceof Blob) {
      const url = URL.createObjectURL(data)
      const link = document.createElement('a')
      link.href = url
      const ext = previewData.value?.format || 'pdf'
      link.download = previewData.value?.title || 'report' + '.' + ext
      link.click()
      URL.revokeObjectURL(url)
      ElMessage.success('下载成功')
    } else {
      ElMessage.warning('下载内容格式异常')
    }
  } catch (err: any) {
    ElMessage.error(err.message || '下载失败')
  } finally {
    downloading.value = false
  }
}

function goBack() {
  router.back()
}

// ── Lifecycle ──────────────────────────────────────────────────────
onMounted(() => {
  taskId.value = (route.query.taskId as string) || (route.query.id as string) || ''
  if (taskId.value) {
    loadPreview()
  }
})
</script>

<style scoped>
.report-preview-page {
  padding: var(--autops-space-xl);
}
.loading-wrapper {
  padding: 24px;
}



.mt-md {
  margin-top: 12px;
}

.report-header {
  margin-bottom: var(--autops-space-md);
}

.report-title {
  font-size: var(--autops-font-20);
  font-weight: 600;
  color: var(--autops-text-1);
  margin: 0 0 8px;
}

.report-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.meta-text {
  font-size: var(--autops-font-13);
  color: var(--autops-info);
}

.section-table {
  width: 100%;
}

.section-text {
  font-size: var(--autops-font-14);
  color: var(--autops-text-2);
  line-height: 1.8;
  white-space: pre-wrap;
}

.empty-state {
  display: flex;
  justify-content: center;
  padding: 60px 0;
}
</style>
