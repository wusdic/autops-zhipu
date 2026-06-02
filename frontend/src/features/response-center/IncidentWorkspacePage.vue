<template>
  <div class="p-6 incident-workspace">
    <el-page-header @back="$router.back()" title="返回异常列表">
      <template #content>
        <span class="page-title">故障工作台</span>
        <el-tag v-if="incident.id" :type="statusType(incident.status)" size="small" style="margin-left:8px">{{ statusLabel(incident.status) }}</el-tag>
      </template>
      <template #extra>
        <el-button-group>
          <el-button @click="refreshData"><el-icon><Refresh /></el-icon> 刷新</el-button>
          <el-button type="primary" @click="triggerAIAnalysis" :loading="aiLoading">AI 分析</el-button>
          <el-button @click="escalateTicket">转工单</el-button>
        </el-button-group>
      </template>
    </el-page-header>

    <el-row :gutter="16" style="margin-top:16px">
      <!-- 左栏：时间线 + 证据 -->
      <el-col :span="16">
        <!-- 异常信息 -->
        <div class="autops-card">
          <div class="autops-card-header"><div class="autops-card-title">异常信息</div></div>
          <div class="autops-card-body">
            <el-descriptions :column="2" border size="small">
              <el-descriptions-item label="异常标题">{{ incident.title || "-" }}</el-descriptions-item>
              <el-descriptions-item label="严重级别">
                <span class="autops-status-tag" :class="severityClass(incident.severity)">{{ incident.severity || "-" }}</span>
              </el-descriptions-item>
              <el-descriptions-item label="来源">{{ incident.source || "-" }}</el-descriptions-item>
              <el-descriptions-item label="关联资产">{{ incident.asset_name || "-" }}</el-descriptions-item>
              <el-descriptions-item label="发现时间">{{ incident.created_at || "-" }}</el-descriptions-item>
              <el-descriptions-item label="持续时长">{{ incident.duration || "-" }}</el-descriptions-item>
            </el-descriptions>
          </div>
        </div>

        <!-- 时间线 -->
        <div class="autops-card" style="margin-top:16px">
          <div class="autops-card-header"><div class="autops-card-title">故障时间线</div></div>
          <div class="autops-card-body">
            <el-timeline>
              <el-timeline-item v-for="(event, idx) in timeline" :key="idx"
                :timestamp="event.time" :type="event.type" placement="top">
                <div class="timeline-content">
                  <span class="timeline-title">{{ event.title }}</span>
                  <span v-if="event.detail" class="text-tertiary font-12">{{ event.detail }}</span>
                </div>
              </el-timeline-item>
              <el-timeline-item v-if="!timeline.length" timestamp="暂无时间线数据" type="info" />
            </el-timeline>
          </div>
        </div>

        <!-- 证据面板 -->
        <div class="autops-card" style="margin-top:16px">
          <div class="autops-card-header">
            <div class="autops-card-title">证据链</div>
            <el-button text type="primary" size="small" @click="collectEvidence">收集证据</el-button>
          </div>
          <div class="autops-card-body">
            <el-table :data="evidences" stripe size="small" empty-text="暂无证据">
              <el-table-column prop="type" label="类型" width="100">
                <template #default="{ row }"><el-tag size="small">{{ row.type }}</el-tag></template>
              </el-table-column>
              <el-table-column prop="source" label="来源" width="120" />
              <el-table-column prop="summary" label="摘要" min-width="200" show-overflow-tooltip />
              <el-table-column prop="collected_at" label="采集时间" width="150">
                <template #default="{ row }"><span class="text-tertiary font-12">{{ row.collected_at }}</span></template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </el-col>

      <!-- 右栏：AI分析 + 处置建议 + 操作 -->
      <el-col :span="8">
        <!-- AI分析结果 -->
        <div class="autops-card">
          <div class="autops-card-header"><div class="autops-card-title">AI 分析</div></div>
          <div class="autops-card-body">
            <div v-if="aiResult">
              <div class="mb-sm"><strong>根因分析：</strong>{{ aiResult.root_cause }}</div>
              <div class="mb-sm"><strong>置信度：</strong>
                <el-progress :percentage="aiResult.confidence" :stroke-width="8"
                  :color="aiResult.confidence >= 80 ? '#00b42a' : aiResult.confidence >= 50 ? '#ff7d00' : '#f53f3f'" style="display:inline-block;width:120px" />
              </div>
              <div class="mb-sm"><strong>建议动作：</strong></div>
              <div v-for="(action, idx) in aiResult.suggested_actions" :key="idx" class="action-item">
                <el-tag size="small" :type="action.risk === 'low' ? 'success' : action.risk === 'medium' ? 'warning' : 'danger'">{{ action.risk }}</el-tag>
                <span>{{ action.description }}</span>
              </div>
            </div>
            <el-empty v-else description="点击右上角AI分析按钮" :image-size="60" />
          </div>
        </div>

        <!-- 处置建议 -->
        <div class="autops-card" style="margin-top:16px">
          <div class="autops-card-header"><div class="autops-card-title">处置建议</div></div>
          <div class="autops-card-body">
            <div v-if="aiResult?.suggested_actions?.length">
              <div v-for="(action, idx) in aiResult.suggested_actions" :key="idx" class="remediation-option">
                <el-radio :value="idx" v-model="selectedAction">
                  {{ action.description }}
                </el-radio>
                <div class="text-tertiary font-12">风险: {{ action.risk }} | {{ action.estimated_time }}</div>
              </div>
            </div>
            <el-empty v-else description="等待AI分析" :image-size="60" />
          </div>
        </div>

        <!-- 操作面板 -->
        <div class="autops-card" style="margin-top:16px">
          <div class="autops-card-header"><div class="autops-card-title">操作</div></div>
          <div class="autops-card-body" style="display:flex;flex-direction:column;gap:8px">
            <el-button type="primary" :disabled="selectedAction === null">执行选中方案</el-button>
            <el-button>Dry-run 预演</el-button>
            <el-button>手动处置</el-button>
            <el-button @click="escalateTicket">升级工单</el-button>
            <el-button @click="closeIncident">关闭故障</el-button>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from "vue"
import { Refresh } from "@element-plus/icons-vue"
import { ElMessage } from "element-plus"

const incident = reactive({
  id: "", title: "", severity: "medium", source: "-", asset_name: "-",
  status: "open", created_at: "-", duration: "-",
})

const timeline = ref<any[]>([])
const evidences = ref<any[]>([])
const aiLoading = ref(false)
const aiResult = ref<any>(null)
const selectedAction = ref<number | null>(null)

function statusType(s: string) { return ({ open: "danger", investigating: "warning", resolving: "", closed: "success" } as any)[s] || "info" }
function statusLabel(s: string) { return ({ open: "打开", investigating: "调查中", resolving: "处置中", closed: "已关闭" } as any)[s] || s }
function severityClass(s: string) { return ({ critical: "status-failed", high: "status-warning", medium: "status-info", low: "status-info" } as any)[s] || "status-info" }

function refreshData() { ElMessage.info("刷新数据") }

async function triggerAIAnalysis() {
  aiLoading.value = true
  try {
    await new Promise(r => setTimeout(r, 2000))
    aiResult.value = {
      root_cause: "磁盘空间不足导致服务异常",
      confidence: 72,
      suggested_actions: [
        { description: "清理临时文件和过期日志", risk: "low", estimated_time: "~5分钟" },
        { description: "扩容磁盘分区", risk: "medium", estimated_time: "~30分钟" },
      ],
    }
  } finally { aiLoading.value = false }
}

function collectEvidence() { ElMessage.info("证据收集任务已提交") }
function escalateTicket() { ElMessage.info("升级工单功能开发中") }
function closeIncident() { ElMessage.info("关闭故障需要验证") }
</script>

<style scoped>
.page-title { font-size: 18px; font-weight: 600; color: #1d2129; }
.text-tertiary { color: #86909c; } .font-12 { font-size: 12px; } .mb-sm { margin-bottom: 8px; }
.autops-status-tag { padding: 2px 8px; border-radius: 4px; font-size: 12px; }
.status-failed { background: #ffece8; color: #f53f3f; }
.status-warning { background: #fff7e8; color: #ff7d00; }
.status-info { background: #f2f3f5; color: #86909c; }
.timeline-title { font-weight: 500; }
.action-item { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.remediation-option { padding: 8px; border: 1px solid #e5e6eb; border-radius: 6px; margin-bottom: 8px; }
</style>
