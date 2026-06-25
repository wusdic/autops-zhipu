<template>
  <div class="knowledge-import">
    <div class="autops-page-header">
      <div>
        <div class="autops-page-title">知识导入</div>
        <div class="autops-page-desc">批量导入知识条目</div>
      </div>
      <div class="top-actions">
        <el-button :icon="ArrowLeft" @click="$router.push({ name: 'knowledge' })">返回知识库</el-button>
      </div>
    </div>

    <div class="mt-lg">
      <el-tabs v-model="activeTab" type="border-card">
        <!-- YAML / JSON 文件导入 (with validation preview) -->
        <el-tab-pane label="文件导入" name="upload">
          <el-upload
            ref="uploadRef"
            drag
            :auto-upload="false"
            :limit="10"
            accept=".yaml,.yml,.json,.md"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
            :file-list="fileList"
            multiple
          >
            <el-icon style="font-size: 48px; color: #c9cdd4"><UploadFilled /></el-icon>
            <div>拖拽文件到此处，或<em>点击上传</em></div>
            <template #tip>
              <div class="el-upload__tip">
                支持 YAML、JSON、Markdown 格式，单个文件不超过 5MB，最多 10 个文件
              </div>
            </template>
          </el-upload>

          <!-- Validation Preview -->
          <div v-if="parsedFiles.length > 0" class="preview-section">
            <el-divider content-position="left">文件解析预览</el-divider>
            <el-table stripe :data="parsedFiles"size="small">
              <el-table-column type="index" label="#" width="50" />
              <el-table-column label="文件名" prop="filename" min-width="180" show-overflow-tooltip />
              <el-table-column label="标题" min-width="200">
                <template #default="{ row }">
                  <span v-if="row.valid">{{ row.title || '(无标题)' }}</span>
                  <span v-else class="text-danger">{{ row.error || '解析失败' }}</span>
                </template>
              </el-table-column>
              <el-table-column label="类型" width="120">
                <template #default="{ row }">
                  <el-tag v-if="row.valid" size="small">{{ row.article_type || '-' }}</el-tag>
                  <el-tag v-else type="danger" size="small">错误</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="分类" width="120">
                <template #default="{ row }">
                  <span v-if="row.valid">{{ row.category || '-' }}</span>
                </template>
              </el-table-column>
              <el-table-column label="校验" width="80" align="center">
                <template #default="{ row }">
                  <el-icon v-if="row.valid" color="#00b42a" :size="18"><CircleCheck /></el-icon>
                  <el-icon v-else color="#f53f3f" :size="18"><CircleClose /></el-icon>
                </template>
              </el-table-column>
            </el-table>
            <div class="preview-summary">
              <el-tag type="success" size="small">{{ validFileCount }} 个有效</el-tag>
              <el-tag v-if="invalidFileCount > 0" type="danger" size="small" style="margin-left: 8px">
                {{ invalidFileCount }} 个无效
              </el-tag>
            </div>
          </div>

          <el-button
            type="primary"
            class="mt-lg"
            @click="startBatchImport"
            :loading="importing"
            :disabled="!validFileCount"
          >
            开始导入（{{ validFileCount }} 个有效文件）
          </el-button>
        </el-tab-pane>

        <!-- 粘贴导入 -->
        <el-tab-pane label="粘贴导入" name="paste">
          <el-form :model="pasteForm" label-width="100px">
            <el-form-item label="标题">
              <el-input v-model="pasteForm.title" placeholder="知识标题" />
            </el-form-item>
            <el-form-item label="类型">
              <el-select v-model="pasteForm.article_type" style="width: 100%">
                <el-option label="事件总结" value="incident_summary" />
                <el-option label="Runbook" value="runbook" />
                <el-option label="标准方案" value="standard_solution" />
                <el-option label="FAQ" value="faq" />
                <el-option label="最佳实践" value="best_practice" />
              </el-select>
            </el-form-item>
            <el-form-item label="分类">
              <el-select v-model="pasteForm.category" style="width: 100%">
                <el-option label="故障处置" value="troubleshooting" />
                <el-option label="操作指南" value="operation_guide" />
                <el-option label="最佳实践" value="best_practice" />
                <el-option label="配置参考" value="config_reference" />
                <el-option label="安全基线" value="security_baseline" />
              </el-select>
            </el-form-item>
            <el-form-item label="标签">
              <el-select v-model="pasteForm.tags" multiple filterable allow-create style="width: 100%" placeholder="输入标签">
                <el-option label="linux" value="linux" />
                <el-option label="windows" value="windows" />
                <el-option label="database" value="database" />
                <el-option label="web" value="web" />
                <el-option label="network" value="network" />
              </el-select>
            </el-form-item>
            <el-form-item label="风险等级">
              <el-select v-model="pasteForm.risk_level" style="width: 100%">
                <el-option label="高" value="high" />
                <el-option label="中" value="medium" />
                <el-option label="低" value="low" />
              </el-select>
            </el-form-item>
            <el-form-item label="内容">
              <el-input v-model="pasteForm.content" type="textarea" :rows="10" placeholder="Markdown 格式内容" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="submitPaste" :loading="importing">导入</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 标准处置方案（8 大场景） -->
        <el-tab-pane label="标准知识库模板" name="standard">
          <el-alert
            type="info"
            :closable="false"
            class="mb-lg"
          >
            <template #title>
              以下 8 大标准场景处置方案将批量导入知识库，每个方案包含完整的触发条件、诊断步骤、处置动作和验证方法，并关联对应的告警规则和自动化策略。
            </template>
          </el-alert>

          <el-table stripe
 ref="standardTableRef"
 :data="standardSchemes"@selection-change="onStandardSelectionChange"
 >
            <el-table-column type="selection" width="55" :selectable="(row: any) => !row.imported" />
            <el-table-column prop="title" label="方案名称" min-width="220" show-overflow-tooltip />
            <el-table-column prop="scenario" label="场景" width="140" />
            <el-table-column prop="category" label="分类" width="120" />
            <el-table-column label="风险等级" width="100">
              <template #default="{ row }">
                <el-tag
                  :type="row.risk_level === 'high' ? 'danger' : row.risk_level === 'medium' ? 'warning' : 'success'"
                  size="small"
                >
                  {{ row.risk_level === 'high' ? '高' : row.risk_level === 'medium' ? '中' : '低' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="包含步骤" width="100" align="center">
              <template #default="{ row }">
                <span>{{ row.step_count }} 步</span>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag v-if="row.imported" type="success" size="small">已导入</el-tag>
                <el-tag v-else type="info" size="small">待导入</el-tag>
              </template>
            </el-table-column>
          </el-table>

          <div class="standard-actions">
            <el-button
              type="primary"
              @click="importSelectedStandardSchemes"
              :loading="importing"
              :disabled="!selectedStandardSchemes.length"
            >
              导入选中（{{ selectedStandardSchemes.length }} 个）
            </el-button>
            <el-button @click="importAllStandardSchemes" :loading="importing">
              导入全部未导入
            </el-button>
          </div>
        </el-tab-pane>

        <!-- 导入历史 -->
        <el-tab-pane label="导入历史" name="history">
          <el-table stripe :data="importHistory" v-loading="loadingHistory" size="small">
            <el-table-column type="index" label="#" width="50" />
            <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
            <el-table-column prop="article_type" label="类型" width="120">
              <template #default="{ row }">
                <el-tag size="small">{{ articleTypeLabel(row.article_type) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="source" label="来源" width="100">
              <template #default="{ row }">
                <el-tag :type="row.source === 'standard' ? 'warning' : row.source === 'import' ? 'info' : 'success'" size="small">
                  {{ sourceLabel(row.source) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="row.status === 'published' ? 'success' : 'info'" size="small">
                  {{ row.status === 'published' ? '已发布' : '草稿' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="导入时间" width="170">
              <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
            </el-table-column>
          </el-table>
          <div style="display: flex; justify-content: flex-end; margin-top: 12px">
            <el-pagination
              v-model:current-page="historyPagination.page"
              v-model:page-size="historyPagination.pageSize"
              :total="historyPagination.total"
              :page-sizes="[10, 20, 50]"
              layout="total, sizes, prev, pager, next"
              background
              small
              @change="loadImportHistory"
            />
          </div>
        </el-tab-pane>
      </el-tabs>

      <!-- Import Progress Dialog -->
      <el-dialog v-model="showProgress" title="导入进度" width="600px" :close-on-click-modal="false" :close-on-press-escape="false">
        <div class="progress-container">
          <el-progress
            :percentage="progressPercent"
            :status="progressStatus"
            :stroke-width="20"
            :text-inside="true"
          />
          <div class="progress-stats">
            <el-tag type="success">成功: {{ importResult.success }}</el-tag>
            <el-tag type="danger" style="margin-left: 8px">失败: {{ importResult.failed }}</el-tag>
            <el-tag type="info" style="margin-left: 8px">总计: {{ importResult.total }}</el-tag>
          </div>
          <div v-if="importResult.errors.length" class="progress-errors">
            <h4>错误详情：</h4>
            <el-scrollbar max-height="200px">
              <div v-for="(err, idx) in importResult.errors" :key="idx" class="error-item">
                <el-icon color="#f53f3f"><CircleClose /></el-icon>
                <span>{{ err }}</span>
              </div>
            </el-scrollbar>
          </div>
        </div>
        <template #footer>
          <el-button @click="showProgress = false" :disabled="importing">关闭</el-button>
          <el-button type="primary" @click="goToKnowledgeList" :disabled="importing">返回知识库</el-button>
        </template>
      </el-dialog>

      <!-- Legacy Result Dialog (kept for paste import) -->
      <el-dialog v-model="showResult" title="导入结果" width="600px">
        <el-result
          :icon="importResult.success > 0 ? 'success' : 'error'"
          :title="'成功 ' + importResult.success + ' 条，失败 ' + importResult.failed + ' 条'"
        >
          <template #extra>
            <div v-if="importResult.errors.length">
              <h4>错误详情：</h4>
              <ul>
                <li v-for="(err, idx) in importResult.errors" :key="idx" class="text-danger">
                  {{ err }}
                </li>
              </ul>
            </div>
            <el-button type="primary" @click="showResult = false">确定</el-button>
          </template>
        </el-result>
      </el-dialog>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, UploadFilled, CircleCheck, CircleClose } from '@element-plus/icons-vue'
import api from '@/shared/api/client'
import { API as R } from '@/shared/api/routes'
import type { UploadFile } from 'element-plus'

const router = useRouter()

const activeTab = ref('upload')
const fileList = ref<UploadFile[]>([])
const importing = ref(false)
const showResult = ref(false)
const showProgress = ref(false)
const uploadRef = ref()
const standardTableRef = ref()

// ─── Parsed file preview data ────────────────────────────────────────
interface ParsedFile {
  filename: string
  valid: boolean
  error?: string
  title?: string
  article_type?: string
  category?: string
  tags?: string[]
  content?: string
  raw?: any
  file?: File
}

const parsedFiles = ref<ParsedFile[]>([])

const validFileCount = computed(() => parsedFiles.value.filter(f => f.valid).length)
const invalidFileCount = computed(() => parsedFiles.value.filter(f => !f.valid).length)

// ─── Import history state ──────────────────────────────────────────
const importHistory = ref<any[]>([])
const loadingHistory = ref(false)
const historyPagination = reactive({ page: 1, pageSize: 20, total: 0 })

// ─── Import result ───────────────────────────────────────────────────
const importResult = reactive({
  success: 0,
  failed: 0,
  total: 0,
  errors: [] as string[],
})

const progressPercent = computed(() => {
  if (importResult.total === 0) return 0
  return Math.round(((importResult.success + importResult.failed) / importResult.total) * 100)
})

const progressStatus = computed(() => {
  if (importing.value) return ''
  if (importResult.failed > 0 && importResult.success === 0) return 'exception'
  if (importResult.success + importResult.failed >= importResult.total) return 'success'
  return ''
})

// ─── Paste form ──────────────────────────────────────────────────────
const pasteForm = reactive({
  title: '',
  article_type: 'standard_solution',
  category: 'troubleshooting',
  content: '',
  tags: [] as string[],
  risk_level: 'medium',
})

// ─── Standard Schemes (8 scenarios from design doc) ──────────────────
const standardSchemes = ref([
  {
    id: 'kb-linux-disk-high',
    title: 'Linux 磁盘空间使用率过高处置',
    scenario: '磁盘空间异常',
    category: 'troubleshooting',
    risk_level: 'low',
    step_count: 5,
    imported: false,
    template: {
      diagnosis_steps: '1. 检查磁盘使用率: `df -h`\n2. 查看大文件: `du -sh /* | sort -rh | head -20`\n3. 检查日志文件大小: `find /var/log -type f -size +100M`\n4. 检查已删除但未释放的文件: `lsof | grep deleted`',
      resolution_steps: '1. 清理临时文件: `rm -rf /tmp/*`\n2. 轮转日志: `logrotate -f /etc/logrotate.conf`\n3. 清理包管理器缓存: `yum clean all` 或 `apt-get clean`\n4. 清理已删除文件: 重启占用进程或 `> /proc/PID/fd/FD`\n5. 扩容磁盘（如上述步骤无效）',
      verification_steps: '1. 确认磁盘使用率已降至阈值以下: `df -h`\n2. 验证服务运行正常\n3. 检查监控告警是否消除',
    },
  },
  {
    id: 'kb-windows-service-down',
    title: 'Windows 关键服务停止运行处置',
    scenario: '服务异常',
    category: 'troubleshooting',
    risk_level: 'low',
    step_count: 4,
    imported: false,
    template: {
      diagnosis_steps: '1. 检查服务状态: `Get-Service -Name <ServiceName>`\n2. 查看系统事件日志: `Get-EventLog -LogName System -Newest 50`\n3. 查看应用事件日志: `Get-EventLog -LogName Application -Newest 50`\n4. 检查服务依赖项是否正常',
      resolution_steps: '1. 重启服务: `Restart-Service -Name <ServiceName>`\n2. 如重启失败，检查服务配置和依赖\n3. 检查端口占用: `netstat -ano | findstr :<Port>`\n4. 必要时重启服务器',
      verification_steps: '1. 确认服务状态为 Running\n2. 验证服务端口可访问\n3. 检查相关功能是否恢复正常',
    },
  },
  {
    id: 'kb-web-port-unreachable',
    title: 'Web 服务端口不可达处置',
    scenario: '网络/服务不可达',
    category: 'troubleshooting',
    risk_level: 'medium',
    step_count: 6,
    imported: false,
    template: {
      diagnosis_steps: '1. 检查本机端口监听: `netstat -tlnp | grep <Port>`\n2. 检查服务进程: `ps aux | grep <ProcessName>`\n3. 测试本机连接: `curl -I http://localhost:<Port>`\n4. 检查防火墙规则: `iptables -L -n` 或 `firewall-cmd --list-all`\n5. 检查网络连通性: `ping <TargetIP>`\n6. 检查负载均衡器配置',
      resolution_steps: '1. 重启 Web 服务: `systemctl restart <ServiceName>`\n2. 修正防火墙规则开放端口\n3. 修复服务配置文件\n4. 重启负载均衡器或更新后端列表\n5. 通知网络团队排查网络问题',
      verification_steps: '1. 从外部访问 Web 端口确认可达\n2. 验证 HTTP 状态码正常 (200)\n3. 确认监控告警已恢复',
    },
  },
  {
    id: 'kb-db-conn-high',
    title: '数据库连接数过高处置',
    scenario: '数据库性能',
    category: 'troubleshooting',
    risk_level: 'medium',
    step_count: 5,
    imported: false,
    template: {
      diagnosis_steps: '1. 检查当前连接数: `SHOW PROCESSLIST` 或 `SELECT COUNT(*) FROM pg_stat_activity`\n2. 查看最大连接数配置: `SHOW VARIABLES LIKE \'max_connections\'`\n3. 识别长连接和锁等待\n4. 检查慢查询日志\n5. 检查连接池配置',
      resolution_steps: '1. 终止空闲长连接: `KILL CONNECTION <ID>`\n2. 优化慢查询\n3. 调整 max_connections 参数\n4. 检查应用连接池配置\n5. 实施连接数限制策略',
      verification_steps: '1. 确认连接数已降至正常水平\n2. 验证数据库响应时间正常\n3. 确认应用连接正常',
    },
  },
  {
    id: 'kb-db-conn-failed',
    title: '数据库连接失败处置',
    scenario: '数据库故障',
    category: 'troubleshooting',
    risk_level: 'high',
    step_count: 6,
    imported: false,
    template: {
      diagnosis_steps: '1. 检查数据库进程状态: `systemctl status <db_service>`\n2. 检查数据库监听端口\n3. 测试本地连接: `mysql -u root -p` 或 `psql -U postgres`\n4. 检查数据库错误日志\n5. 检查磁盘空间: `df -h`\n6. 检查数据库认证配置',
      resolution_steps: '1. 重启数据库服务\n2. 如磁盘满，先清理磁盘空间\n3. 修复损坏的数据文件\n4. 恢复认证配置\n5. 如需从备份恢复，启动数据恢复流程\n6. 通知应用团队重连',
      verification_steps: '1. 确认数据库服务状态为 running\n2. 验证应用连接成功\n3. 执行简单查询确认数据完整性\n4. 确认监控告警已恢复',
    },
  },
  {
    id: 'kb-ssl-cert-expiring',
    title: 'SSL 证书即将过期处置',
    scenario: '证书/安全',
    category: 'troubleshooting',
    risk_level: 'low',
    step_count: 4,
    imported: false,
    template: {
      diagnosis_steps: '1. 检查证书过期时间: `openssl x509 -in cert.pem -noout -dates`\n2. 列出所有证书文件及过期时间\n3. 确认证书颁发机构 (CA) 信息\n4. 检查证书链完整性',
      resolution_steps: '1. 申请新证书（续签或重新申请）\n2. 下载并部署新证书\n3. 重载 Web 服务: `nginx -s reload` 或 `systemctl reload apache2`\n4. 验证新证书生效',
      verification_steps: '1. 确认新证书过期时间正确\n2. 验证 HTTPS 访问正常\n3. 确认证书链完整\n4. 检查 SSL Labs 评分',
    },
  },
  {
    id: 'kb-collector-offline',
    title: '采集器离线处置',
    scenario: '监控异常',
    category: 'troubleshooting',
    risk_level: 'medium',
    step_count: 5,
    imported: false,
    template: {
      diagnosis_steps: '1. 检查采集器进程: `systemctl status collector`\n2. 查看采集器日志: `journalctl -u collector --since "1 hour ago"`\n3. 检查网络连通性（采集器到服务端）\n4. 检查采集器配置文件\n5. 检查系统资源（CPU/内存/磁盘）',
      resolution_steps: '1. 重启采集器: `systemctl restart collector`\n2. 修正配置文件错误\n3. 修复网络问题\n4. 清理磁盘空间\n5. 如版本过旧，升级采集器',
      verification_steps: '1. 确认采集器状态为在线\n2. 验证数据正常上报\n3. 检查服务端数据接收正常\n4. 确认告警已恢复',
    },
  },
  {
    id: 'kb-automation-failed',
    title: '自动化执行失败处置',
    scenario: '自动化异常',
    category: 'troubleshooting',
    risk_level: 'high',
    step_count: 6,
    imported: false,
    template: {
      diagnosis_steps: '1. 查看执行日志，定位失败步骤\n2. 检查目标资产连通性\n3. 验证执行凭证是否有效\n4. 检查脚本/Playbook 内容\n5. 检查执行权限\n6. 检查目标资产状态（资源、服务）',
      resolution_steps: '1. 修正脚本/Playbook 错误\n2. 更新过期凭证\n3. 修复目标资产连通性\n4. 调整执行权限\n5. 重新执行失败的自动化任务\n6. 如无法自动修复，升级为人工处置',
      verification_steps: '1. 确认自动化任务执行成功\n2. 验证执行结果符合预期\n3. 检查目标资产状态正常\n4. 确认告警已消除或工单已关闭',
    },
  },
])

const selectedStandardSchemes = ref<any[]>([])

// ─── File Handling ───────────────────────────────────────────────────
function handleFileChange(file: UploadFile, files: UploadFile[]) {
  fileList.value = files
  parseFile(file)
}

function handleFileRemove(file: UploadFile) {
  parsedFiles.value = parsedFiles.value.filter(p => p.filename !== file.name)
}

/** Parse and validate uploaded files */
async function parseFile(file: UploadFile) {
  const raw = file.raw
  if (!raw) return

  const entry: ParsedFile = {
    filename: raw.name,
    valid: false,
    file: raw,
  }

  try {
    const text = await raw.text()

    if (raw.name.endsWith('.json')) {
      try {
        const parsed = JSON.parse(text)
        entry.valid = true
        entry.title = parsed.title || ''
        entry.article_type = parsed.article_type || 'standard_solution'
        entry.category = parsed.category || 'troubleshooting'
        entry.tags = parsed.tags || []
        entry.content = parsed.content || text
        entry.raw = parsed
        // Validate required fields
        if (!entry.title) {
          entry.title = raw.name.replace(/\.json$/, '')
        }
      } catch (e: any) {
        entry.valid = false
        entry.error = 'JSON 解析失败: ' + e.message
      }
    } else if (raw.name.endsWith('.yaml') || raw.name.endsWith('.yml')) {
      // Basic YAML parsing (key: value lines)
      entry.valid = true
      entry.title = raw.name.replace(/\.(yaml|yml)$/, '')
      entry.article_type = 'standard_solution'
      entry.category = 'troubleshooting'
      entry.content = text

      // Extract simple key: value pairs
      const titleMatch = text.match(/^title:\s*(.+)$/m)
      if (titleMatch) entry.title = titleMatch[1].trim().replace(/^['"]|['"]$/g, '')
      const typeMatch = text.match(/^article_type:\s*(.+)$/m)
      if (typeMatch) entry.article_type = typeMatch[1].trim()
      const catMatch = text.match(/^category:\s*(.+)$/m)
      if (catMatch) entry.category = catMatch[1].trim()
    } else if (raw.name.endsWith('.md')) {
      entry.valid = true
      const titleMatch = text.match(/^#\s+(.+)/m)
      entry.title = titleMatch ? titleMatch[1] : raw.name.replace(/\.md$/, '')
      entry.content = text
      entry.article_type = 'standard_solution'
      entry.category = 'troubleshooting'
    } else {
      entry.valid = false
      entry.error = '不支持的文件格式'
    }

    // Validate title exists for valid files
    if (entry.valid && !entry.title) {
      entry.title = raw.name.replace(/\.\w+$/, '')
    }
  } catch (e: any) {
    entry.valid = false
    entry.error = '文件读取失败: ' + e.message
  }

  // Update or add the parsed entry
  const idx = parsedFiles.value.findIndex(p => p.filename === raw.name)
  if (idx >= 0) {
    parsedFiles.value[idx] = entry
  } else {
    parsedFiles.value.push(entry)
  }
}

// ─── Batch Import ────────────────────────────────────────────────────
async function startBatchImport() {
  const validFiles = parsedFiles.value.filter(f => f.valid)
  if (!validFiles.length) return

  importing.value = true
  showProgress.value = true
  importResult.success = 0
  importResult.failed = 0
  importResult.total = validFiles.length
  importResult.errors = []

  for (const file of validFiles) {
    try {
      const payload: any = {
        title: file.title,
        content: file.content,
        article_type: file.article_type || 'standard_solution',
        category: file.category || 'troubleshooting',
        tags: file.tags || [],
        source: 'import',
        status: 'published',
      }

      const { data } = await api.post(R.KNOWLEDGE, payload)
      if (data.code === 0) {
        importResult.success++
      } else {
        importResult.failed++
        importResult.errors.push(file.filename + ': ' + data.message)
      }
    } catch (e: any) {
      importResult.failed++
      importResult.errors.push(file.filename + ': ' + (e.message || '未知错误'))
    }
  }

  importing.value = false
  if (importResult.success > 0) {
    ElMessage.success('成功导入 ' + importResult.success + ' 条知识')
  }
  // Reset file list
  fileList.value = []
  parsedFiles.value = []
}

// ─── Paste Import ────────────────────────────────────────────────────
async function submitPaste() {
  if (!pasteForm.title || !pasteForm.content) {
    ElMessage.warning('请填写标题和内容')
    return
  }
  importing.value = true
  try {
    const { data } = await api.post(R.KNOWLEDGE, {
      title: pasteForm.title,
      content: pasteForm.content,
      article_type: pasteForm.article_type,
      category: pasteForm.category,
      tags: pasteForm.tags,
      risk_level: pasteForm.risk_level,
      source: 'manual',
      status: 'published',
    })
    if (data.code === 0) {
      ElMessage.success('导入成功')
      pasteForm.title = ''
      pasteForm.content = ''
      pasteForm.tags = []
    } else {
      ElMessage.error(data.message || '导入失败')
    }
  } catch {
    ElMessage.error('导入失败')
  } finally {
    importing.value = false
  }
}

// ─── Standard Scheme Selection ───────────────────────────────────────
function onStandardSelectionChange(selection: any[]) {
  selectedStandardSchemes.value = selection
}

async function importSelectedStandardSchemes() {
  const schemes = selectedStandardSchemes.value.filter(s => !s.imported)
  if (!schemes.length) {
    ElMessage.warning('请选择要导入的方案')
    return
  }
  await doStandardImport(schemes)
}

async function importAllStandardSchemes() {
  const schemes = standardSchemes.value.filter(s => !s.imported)
  if (!schemes.length) {
    ElMessage.info('所有方案已导入')
    return
  }
  await doStandardImport(schemes)
}

async function doStandardImport(schemes: any[]) {
  importing.value = true
  showProgress.value = true
  importResult.success = 0
  importResult.failed = 0
  importResult.total = schemes.length
  importResult.errors = []

  for (const scheme of schemes) {
    try {
      const template = scheme.template || {}
      const { data } = await api.post(R.KNOWLEDGE, {
        title: scheme.title,
        content: '# ' + scheme.title + '\n\n## 场景\n' + scheme.scenario + '\n\n## 分类\n' + scheme.category,
        article_type: 'runbook',
        category: scheme.category,
        risk_level: scheme.risk_level,
        source: 'standard',
        status: 'published',
        tags: ['standard', scheme.id, scheme.scenario],
        diagnosis_steps: template.diagnosis_steps || '待补充',
        resolution_steps: template.resolution_steps || '待补充',
        verification_steps: template.verification_steps || '待补充',
      })
      if (data.code === 0) {
        importResult.success++
        scheme.imported = true
      } else {
        importResult.failed++
        importResult.errors.push(scheme.title + ': ' + data.message)
      }
    } catch (e: any) {
      importResult.failed++
      importResult.errors.push(scheme.title + ': ' + (e.message || '未知错误'))
    }
  }

  importing.value = false
  if (importResult.success > 0) {
    ElMessage.success('成功导入 ' + importResult.success + ' 条标准方案')
  }
  selectedStandardSchemes.value = []
}

// ─── Navigation ──────────────────────────────────────────────────────
function goToKnowledgeList() {
  showProgress.value = false
  router.push({ name: 'knowledge' })
}

// ─── Import History ─────────────────────────────────────────────────
function formatTime(val: string | null | undefined): string {
  if (!val) return '-'
  const d = new Date(val)
  if (isNaN(d.getTime())) return '-'
  const pad = (n: number) => String(n).padStart(2, '0')
  return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()) + ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes()) + ':' + pad(d.getSeconds())
}

function articleTypeLabel(t: string): string {
  var map: Record<string, string> = {
    incident_summary: '事件总结',
    runbook: 'Runbook',
    standard_solution: '标准方案',
    faq: 'FAQ',
    best_practice: '最佳实践',
  }
  return map[t] || t || '-'
}

function sourceLabel(s: string): string {
  var map: Record<string, string> = {
    import: '文件导入',
    manual: '手动导入',
    standard: '标准模板',
    api: 'API导入',
  }
  return map[s] || s || '-'
}

async function loadImportHistory() {
  loadingHistory.value = true
  try {
    var params = {
      page: historyPagination.page,
      page_size: historyPagination.pageSize,
      source: 'import,standard,manual',
    }
    var response = await api.get(R.KNOWLEDGE, { params: params })
    var data = response.data
    if (data.code === 0) {
      importHistory.value = data.data?.items || data.data?.list || []
      historyPagination.total = data.data?.total || 0
    }
  } catch {
    importHistory.value = []
  } finally {
    loadingHistory.value = false
  }
}

// ─── Init ────────────────────────────────────────────────────────────
onMounted(() => {
  checkExisting()
  loadImportHistory()
})

async function checkExisting() {
  try {
    const { data } = await api.get(R.KNOWLEDGE, { params: { source: 'standard', page_size: 100 } })
    if (data.code === 0) {
      const items = data.data?.items || data.data || []
      const existingTags = new Set(items.flatMap((i: any) => i.tags || []))
      for (const scheme of standardSchemes.value) {
        scheme.imported = existingTags.has(scheme.id)
      }
    }
  } catch { /* ignore */ }
}
</script>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
}

.preview-section {
  margin-top: var(--autops-space-lg);
  padding: var(--autops-space-md);
  background: var(--autops-bg-2);
  border-radius: var(--autops-radius-sm);
}
.preview-summary {
  margin-top: 8px;
  display: flex;
  align-items: center;
}

.progress-container {
  padding: var(--autops-space-sm) 0;
}
.progress-stats {
  margin-top: var(--autops-space-lg);
  display: flex;
  align-items: center;
}
.progress-errors {
  margin-top: var(--autops-space-lg);
}
.error-item {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--autops-danger);
  font-size: var(--autops-font-13);
  padding: 2px 0;
}

.standard-actions {
  margin-top: var(--autops-space-lg);
  display: flex;
  gap: 8px;
}
</style>
