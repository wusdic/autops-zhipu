<template>
  <div>
    <el-card>
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span>🤖 AI 智能诊断</span>
          <el-tag :type="llmAvailable ? 'success' : 'danger'">{{ llmAvailable ? 'LLM 在线' : 'LLM 离线' }}</el-tag>
        </div>
      </template>

      <el-row :gutter="16">
        <el-col :span="12">
          <h4>输入诊断请求</h4>
          <el-form :model="form" label-width="80px">
            <el-form-item label="问题描述">
              <el-input type="textarea" v-model="form.question" :rows="4" placeholder="描述运维问题，如：服务器磁盘空间不足怎么办？" />
            </el-form-item>
            <el-form-item label="上下文">
              <el-input type="textarea" v-model="form.context" :rows="3" placeholder="可选：相关日志、指标数据等" />
            </el-form-item>
            <el-form-item label="资产类型">
              <el-select v-model="form.asset_type" placeholder="选择资产类型" clearable>
                <el-option label="Linux 服务器" value="linux_server" />
                <el-option label="Windows 服务器" value="windows_server" />
                <el-option label="数据库" value="database" />
                <el-option label="Web 服务" value="web_service" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="diagnose" :loading="loading" :disabled="!form.question">
                开始诊断
              </el-button>
              <el-button @click="resetForm">清空</el-button>
            </el-form-item>
          </el-form>
        </el-col>

        <el-col :span="12">
          <h4>诊断结果</h4>
          <div v-if="loading" style="text-align:center;padding:40px">
            <el-icon class="is-loading" :size="32"><Loading /></el-icon>
            <p>AI 正在分析中...</p>
          </div>
          <div v-else-if="result" class="ai-result">
            <el-alert v-if="result.error" :title="result.error" type="error" show-icon :closable="false" />
            <template v-else>
              <el-descriptions :column="1" border>
                <el-descriptions-item label="根因分析">
                  <div class="result-text">{{ result.root_cause || result.analysis || '无分析结果' }}</div>
                </el-descriptions-item>
                <el-descriptions-item v-if="result.recommendations" label="处置建议">
                  <div v-for="(r, i) in result.recommendations" :key="i" style="margin:4px 0">
                    <el-tag size="small" type="primary">{{ i + 1 }}</el-tag>
                    <span style="margin-left:8px">{{ typeof r === 'string' ? r : r.action || JSON.stringify(r) }}</span>
                  </div>
                </el-descriptions-item>
                <el-descriptions-item v-if="result.confidence" label="置信度">
                  <el-progress :percentage="result.confidence" />
                </el-descriptions-item>
              </el-descriptions>
              <div v-if="result.raw_response" style="margin-top:12px">
                <el-collapse>
                  <el-collapse-item title="原始 LLM 响应">
                    <pre class="raw-response">{{ result.raw_response }}</pre>
                  </el-collapse-item>
                </el-collapse>
              </div>
            </template>
          </div>
          <el-empty v-else description="提交诊断请求后查看结果" />
        </el-col>
      </el-row>
    </el-card>

    <!-- 历史诊断记录 -->
    <el-card style="margin-top:16px">
      <template #header><span>历史诊断记录</span></template>
      <el-table :data="history" stripe size="small" max-height="300">
        <el-table-column prop="question" label="问题" min-width="250" show-overflow-tooltip />
        <el-table-column prop="asset_type" label="资产类型" width="120" />
        <el-table-column prop="created_at" label="时间" width="170">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="80">
          <template #default="{ row }">
            <el-button size="small" @click="viewHistory(row)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import api from '@/shared/api/client'
import { API as R } from '@/shared/api/routes'

const loading = ref(false)
const result = ref<any>(null)
const llmAvailable = ref(false)
const history = ref<any[]>([])
const form = reactive({ question: '', context: '', asset_type: '' })

function formatTime(t: string) { return t ? new Date(t).toLocaleString('zh-CN') : '' }

function resetForm() {
  form.question = ''
  form.context = ''
  form.asset_type = ''
}

async function checkLLM() {
  try {
    const { data } = await api.get(R.AIOPS.HEALTH)
    llmAvailable.value = data.code === 0
  } catch { llmAvailable.value = false }
}

async function diagnose() {
  if (!form.question) return
  loading.value = true
  result.value = null
  try {
    const { data } = await api.post(R.AIOPS.DIAGNOSE, form)
    if (data.code === 0) {
      result.value = data.data
    } else {
      result.value = { error: data.message || '诊断失败' }
    }
  } catch (e: any) {
    result.value = { error: 'AI 服务连接失败: ' + (e.message || '未知错误') }
  } finally { loading.value = false }
}

async function loadHistory() {
  try {
    const { data } = await api.get(R.AIOPS.ANALYSES, { params: { page: 1, page_size: 20 } })
    if (data.code === 0) history.value = data.data.items || []
  } catch { /* ignore */ }
}

function viewHistory(row: any) { result.value = row }

onMounted(() => { checkLLM(); loadHistory() })
</script>

<style scoped>
.ai-result { padding: 8px; }
.result-text { line-height: 1.6; white-space: pre-wrap; }
.raw-response { background: #f5f7fa; padding: 12px; border-radius: 4px; font-size: 12px; max-height: 300px; overflow: auto; }
</style>
