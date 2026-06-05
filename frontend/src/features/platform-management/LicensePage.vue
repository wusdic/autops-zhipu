<template>
  <div class="autops-page-container">
    <!-- 后端不可用时的引导页面 -->
    <div v-if="backendUnavailable" class="autops-card guide-card">
      <el-empty description="授权许可功能需要配置后端许可服务">
        <el-button type="primary" @click="retryLoadLicense">重新检测</el-button>
      </el-empty>
      <div class="guide-info">
        <div class="guide-title">配置说明</div>
        <ul class="guide-list">
          <li>请确保后端许可服务已正确部署并启动</li>
          <li>检查后端 API 端点 /api/v1/platform/license 是否可访问</li>
          <li>如需帮助，请联系平台管理员</li>
        </ul>
      </div>
    </div>

    <!-- 正常页面内容 -->
    <div v-if="!backendUnavailable">
    <div class="autops-page-header">
      <div>
        <div class="autops-page-title">授权许可</div>
        <div class="autops-page-desc">查看与管理平台授权信息</div>
      </div>
      <el-button @click="loadLicense" :loading="loading">
        <el-icon><Refresh /></el-icon> 刷新
      </el-button>
    </div>

    <el-row :gutter="16">
      <!-- ── License Info Card ────────────────────────────── -->
      <el-col :span="14">
        <div class="autops-card">
          <div class="autops-card-header">
            <span class="card-title">当前授权</span>
            <el-tag
              :type="license.expired ? 'danger' : 'success'"
              effect="dark"
              size="small"
            >
              {{ license.expired ? '已过期' : '有效' }}
            </el-tag>
          </div>
          <div class="card-body">
            <el-descriptions :column="2" border size="small">
              <el-descriptions-item label="授权类型">
                <el-tag size="small">{{ license.type || '-' }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="授权对象">
                {{ license.holder || '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="有效期至">
                <span :class="{ 'text-danger': license.expired, 'text-success': !license.expired }">
                  {{ license.expires_at || '-' }}
                </span>
              </el-descriptions-item>
              <el-descriptions-item label="序列号">
                <span class="text-secondary">{{ license.serial || '-' }}</span>
              </el-descriptions-item>
              <el-descriptions-item label="资产上限">
                {{ license.max_assets ?? '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="当前资产数">
                <span :class="{ 'text-danger': assetUsageExceeded }">
                  {{ license.current_assets ?? 0 }}
                  <span v-if="license.max_assets" class="usage-hint">
                    / {{ license.max_assets }}
                    ({{ assetUsagePercent }}%)
                  </span>
                </span>
              </el-descriptions-item>
              <el-descriptions-item label="节点上限">
                {{ license.max_nodes ?? '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="当前节点数">
                <span :class="{ 'text-danger': nodeUsageExceeded }">
                  {{ license.current_nodes ?? 0 }}
                  <span v-if="license.max_nodes" class="usage-hint">
                    / {{ license.max_nodes }}
                    ({{ nodeUsagePercent }}%)
                  </span>
                </span>
              </el-descriptions-item>
              <el-descriptions-item label="用户上限">
                {{ license.max_users ?? '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="授权时间">
                {{ license.issued_at || '-' }}
              </el-descriptions-item>
            </el-descriptions>

            <!-- Module List -->
            <div class="module-section">
              <div class="module-title">授权模块</div>
              <div class="module-list" v-if="licenseModules.length > 0">
                <el-tag
                  v-for="mod in licenseModules"
                  :key="mod"
                  size="small"
                  type="success"
                  class="module-tag"
                >
                  <el-icon style="margin-right: 2px"><CircleCheck /></el-icon>
                  {{ mod }}
                </el-tag>
              </div>
              <div v-else class="text-secondary">未获取到模块信息</div>
            </div>

            <!-- Usage Progress -->
            <div class="usage-section" v-if="license.max_assets || license.max_nodes">
              <div class="module-title">资源使用情况</div>
              <div class="usage-item" v-if="license.max_assets">
                <div class="usage-label">资产</div>
                <el-progress
                  :percentage="assetUsagePercent"
                  :color="usageColor(assetUsagePercent)"
                  :stroke-width="16"
                  :format="() => (license.current_assets ?? 0) + ' / ' + license.max_assets"
                />
              </div>
              <div class="usage-item" v-if="license.max_nodes">
                <div class="usage-label">节点</div>
                <el-progress
                  :percentage="nodeUsagePercent"
                  :color="usageColor(nodeUsagePercent)"
                  :stroke-width="16"
                  :format="() => (license.current_nodes ?? 0) + ' / ' + license.max_nodes"
                />
              </div>
            </div>
          </div>
        </div>
      </el-col>

      <!-- ── Update License Card ──────────────────────────── -->
      <el-col :span="10">
        <div class="autops-card">
          <div class="autops-card-header">
            <span class="card-title">更新授权</span>
          </div>
          <div class="card-body">
            <el-form label-width="80px" label-position="right">
              <el-form-item label="授权文件">
                <el-upload
                  action=""
                  :auto-upload="false"
                  :limit="1"
                  accept=".lic,.key"
                  :on-change="handleFileChange"
                  :file-list="fileList"
                >
                  <el-button>选择文件</el-button>
                </el-upload>
              </el-form-item>
              <el-form-item label="授权密钥">
                <el-input
                  v-model="licenseKey"
                  type="textarea"
                  :rows="5"
                  placeholder="粘贴授权密钥内容"
                />
              </el-form-item>
              <el-form-item>
                <el-button
                  type="primary"
                  :loading="activating"
                  @click="activateLicense"
                >
                  激活授权
                </el-button>
                <el-button @click="offlineActivate">离线激活</el-button>
              </el-form-item>
            </el-form>

            <el-divider />

            <div class="info-section">
              <div class="info-title">授权说明</div>
              <ul class="info-list">
                <li>社区版：免费使用，最多支持 100 资产和 3 节点</li>
                <li>专业版：适用于中小型团队，支持全部功能模块</li>
                <li>企业版：不限资产数和节点数，提供专属技术支持</li>
              </ul>
            </div>

            <div class="info-section" class="mt-lg">
              <div class="info-title">联系授权</div>
              <div class="text-secondary">
                如需获取或更新授权，请联系商务团队：
                <br />
                邮箱：license@autops.example.com
              </div>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, CircleCheck } from '@element-plus/icons-vue'
import client from '@/shared/api/client'
import { API } from '@/shared/api/routes'

// ── State ────────────────────────────────────────────────
const loading = ref(false)
const activating = ref(false)
const backendUnavailable = ref(false)
const licenseKey = ref('')
const fileList = ref<any[]>([])

const license = reactive({
  type: 'primary',
  holder: 'primary',
  expires_at: 'primary',
  expired: false,
  serial: 'primary',
  max_assets: 0,
  current_assets: 0,
  max_nodes: 0,
  current_nodes: 0,
  max_users: 0,
  modules: '' as string | string[],
  issued_at: 'primary',
})

// ── Computed ─────────────────────────────────────────────
const licenseModules = computed(() => {
  if (Array.isArray(license.modules)) return license.modules
  if (typeof license.modules === 'string' && license.modules) {
    return license.modules.split(',').map((s) => s.trim()).filter(Boolean)
  }
  return []
})

const assetUsagePercent = computed(() => {
  if (!license.max_assets) return 0
  return Math.min(Math.round(((license.current_assets ?? 0) / license.max_assets) * 100), 100)
})

const nodeUsagePercent = computed(() => {
  if (!license.max_nodes) return 0
  return Math.min(Math.round(((license.current_nodes ?? 0) / license.max_nodes) * 100), 100)
})

const assetUsageExceeded = computed(() => {
  return license.max_assets > 0 && (license.current_assets ?? 0) >= license.max_assets * 0.9
})

const nodeUsageExceeded = computed(() => {
  return license.max_nodes > 0 && (license.current_nodes ?? 0) >= license.max_nodes * 0.9
})

function usageColor(pct: number): string {
  if (pct >= 90) return '#f53f3f'
  if (pct >= 70) return '#ff7d00'
  return '#00b42a'
}

// ── Data Loading ─────────────────────────────────────────
async function loadLicense() {
  loading.value = true
  backendUnavailable.value = false
  try {
    const res = await client.get(API.PLATFORM.LICENSE)
    const data = res.data?.data ?? res.data
    if (data && typeof data === 'object') {
      Object.assign(license, {
        type: data.type ?? data.license_type ?? '',
        holder: data.holder ?? data.organization ?? '',
        expires_at: data.expires_at ?? data.expiry ?? '',
        expired: data.expired ?? data.is_expired ?? false,
        serial: data.serial ?? data.serial_number ?? '',
        max_assets: data.max_assets ?? 0,
        current_assets: data.current_assets ?? data.asset_count ?? 0,
        max_nodes: data.max_nodes ?? 0,
        current_nodes: data.current_nodes ?? data.node_count ?? 0,
        max_users: data.max_users ?? 0,
        modules: data.modules ?? data.features ?? '',
        issued_at: data.issued_at ?? data.created_at ?? '',
      })
    }
  } catch {
    backendUnavailable.value = true
  } finally {
    loading.value = false
  }
}

function retryLoadLicense() {
  loadLicense()
}

// ── File Handling ────────────────────────────────────────
function handleFileChange(file: any) {
  fileList.value = [file]
}

// ── Activate ─────────────────────────────────────────────
async function activateLicense() {
  if (!licenseKey.value && fileList.value.length === 0) {
    ElMessage.warning('请输入授权密钥或选择授权文件')
    return
  }

  activating.value = true
  try {
    const payload: Record<string, any> = {}
    if (licenseKey.value) payload.license_key = licenseKey.value
    if (fileList.value.length > 0) payload.has_file = true

    await client.post(API.PLATFORM.LICENSE, payload)
    ElMessage.success('授权已激活')
    licenseKey.value = ''
    fileList.value = []
    loadLicense()
  } catch (err: any) {
    ElMessage.error(err.message || '激活失败')
  } finally {
    activating.value = false
  }
}

function offlineActivate() {
  ElMessage.info('请联系商务团队获取离线激活文件')
}

// ── Init ─────────────────────────────────────────────────
onMounted(() => {
  loadLicense()
})
</script>

<style scoped>

.autops-page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--autops-space-lg);
}


.autops-card {
  background: var(--autops-bg-1);
  border: 1px solid var(--autops-bg-4);
  border-radius: var(--autops-radius-md);
  overflow: hidden;
}


.card-body {
  padding: var(--autops-space-lg);
}

.text-secondary {
  color: var(--autops-info);
  font-size: var(--autops-font-12);
}
.text-danger {
  color: var(--autops-danger);
}
.text-success {
  color: var(--autops-success);
}

.usage-hint {
  color: var(--autops-info);
  font-size: var(--autops-font-12);
}

/* Module section */
.module-section {
  margin-top: var(--autops-space-lg);
}
.module-title {
  font-size: var(--autops-font-13);
  font-weight: 600;
  color: var(--autops-text-2);
  margin-bottom: var(--autops-space-sm);
}
.module-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.module-tag {
  font-size: var(--autops-font-12);
}

/* Usage section */
.usage-section {
  margin-top: var(--autops-space-lg);
}
.usage-item {
  margin-bottom: 10px;
}
.usage-label {
  font-size: var(--autops-font-12);
  color: var(--autops-info);
  margin-bottom: 4px;
}

/* Info section */
.info-section {
  font-size: var(--autops-font-13);
}
.info-title {
  font-weight: 600;
  color: var(--autops-text-2);
  margin-bottom: 6px;
}
.info-list {
  margin: 0;
  padding-left: 18px;
  color: var(--autops-info);
  font-size: var(--autops-font-12);
  line-height: 1.8;
}

/* Guide card */
.guide-card {
  max-width: 600px;
  margin: 40px auto;
  padding: 40px 32px;
  text-align: center;
}

.guide-info {
  text-align: left;
  margin-top: 24px;
}

.guide-title {
  font-size: var(--autops-font-14);
  font-weight: 600;
  color: var(--autops-text-2);
  margin-bottom: var(--autops-space-sm);
}

.guide-list {
  margin: 0;
  padding-left: 18px;
  color: var(--autops-info);
  font-size: var(--autops-font-13);
  line-height: 2;
}
</style>
