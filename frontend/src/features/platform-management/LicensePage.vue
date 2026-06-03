     1|<template>
     2|  <div class="page-container">
     3|    <!-- 后端不可用时的引导页面 -->
     4|    <div v-if="backendUnavailable" class="autops-card guide-card">
     5|      <el-empty description="授权许可功能需要配置后端许可服务">
     6|        <el-button type="primary" @click="retryLoadLicense">重新检测</el-button>
     7|      </el-empty>
     8|      <div class="guide-info">
     9|        <div class="guide-title">配置说明</div>
    10|        <ul class="guide-list">
    11|          <li>请确保后端许可服务已正确部署并启动</li>
    12|          <li>检查后端 API 端点 /api/v1/platform/license 是否可访问</li>
    13|          <li>如需帮助，请联系平台管理员</li>
    14|        </ul>
    15|      </div>
    16|    </div>
    17|
    18|    <!-- 正常页面内容 -->
    19|    <div v-if="!backendUnavailable">
    20|    <div class="autops-page-header">
    21|      <div>
    22|        <div class="autops-page-title">授权许可</div>
    23|        <div class="autops-page-desc">查看与管理平台授权信息</div>
    24|      </div>
    25|      <el-button @click="loadLicense" :loading="loading">
    26|        <el-icon><Refresh /></el-icon> 刷新
    27|      </el-button>
    28|    </div>
    29|
    30|    <el-row :gutter="16">
    31|      <!-- ── License Info Card ────────────────────────────── -->
    32|      <el-col :span="14">
    33|        <div class="autops-card">
    34|          <div class="card-header">
    35|            <span class="card-title">当前授权</span>
    36|            <el-tag
    37|              :type="license.expired ? 'danger' : 'success'"
    38|              effect="dark"
    39|              size="small"
    40|            >
    41|              {{ license.expired ? '已过期' : '有效' }}
    42|            </el-tag>
    43|          </div>
    44|          <div class="card-body">
    45|            <el-descriptions :column="2" border size="small">
    46|              <el-descriptions-item label="授权类型">
    47|                <el-tag size="small">{{ license.type || '-' }}</el-tag>
    48|              </el-descriptions-item>
    49|              <el-descriptions-item label="授权对象">
    50|                {{ license.holder || '-' }}
    51|              </el-descriptions-item>
    52|              <el-descriptions-item label="有效期至">
    53|                <span :class="{ 'text-danger': license.expired, 'text-success': !license.expired }">
    54|                  {{ license.expires_at || '-' }}
    55|                </span>
    56|              </el-descriptions-item>
    57|              <el-descriptions-item label="序列号">
    58|                <span class="text-secondary">{{ license.serial || '-' }}</span>
    59|              </el-descriptions-item>
    60|              <el-descriptions-item label="资产上限">
    61|                {{ license.max_assets ?? '-' }}
    62|              </el-descriptions-item>
    63|              <el-descriptions-item label="当前资产数">
    64|                <span :class="{ 'text-danger': assetUsageExceeded }">
    65|                  {{ license.current_assets ?? 0 }}
    66|                  <span v-if="license.max_assets" class="usage-hint">
    67|                    / {{ license.max_assets }}
    68|                    ({{ assetUsagePercent }}%)
    69|                  </span>
    70|                </span>
    71|              </el-descriptions-item>
    72|              <el-descriptions-item label="节点上限">
    73|                {{ license.max_nodes ?? '-' }}
    74|              </el-descriptions-item>
    75|              <el-descriptions-item label="当前节点数">
    76|                <span :class="{ 'text-danger': nodeUsageExceeded }">
    77|                  {{ license.current_nodes ?? 0 }}
    78|                  <span v-if="license.max_nodes" class="usage-hint">
    79|                    / {{ license.max_nodes }}
    80|                    ({{ nodeUsagePercent }}%)
    81|                  </span>
    82|                </span>
    83|              </el-descriptions-item>
    84|              <el-descriptions-item label="用户上限">
    85|                {{ license.max_users ?? '-' }}
    86|              </el-descriptions-item>
    87|              <el-descriptions-item label="授权时间">
    88|                {{ license.issued_at || '-' }}
    89|              </el-descriptions-item>
    90|            </el-descriptions>
    91|
    92|            <!-- Module List -->
    93|            <div class="module-section">
    94|              <div class="module-title">授权模块</div>
    95|              <div class="module-list" v-if="licenseModules.length > 0">
    96|                <el-tag
    97|                  v-for="mod in licenseModules"
    98|                  :key="mod"
    99|                  size="small"
   100|                  type="success"
   101|                  class="module-tag"
   102|                >
   103|                  <el-icon style="margin-right: 2px"><CircleCheck /></el-icon>
   104|                  {{ mod }}
   105|                </el-tag>
   106|              </div>
   107|              <div v-else class="text-secondary">未获取到模块信息</div>
   108|            </div>
   109|
   110|            <!-- Usage Progress -->
   111|            <div class="usage-section" v-if="license.max_assets || license.max_nodes">
   112|              <div class="module-title">资源使用情况</div>
   113|              <div class="usage-item" v-if="license.max_assets">
   114|                <div class="usage-label">资产</div>
   115|                <el-progress
   116|                  :percentage="assetUsagePercent"
   117|                  :color="usageColor(assetUsagePercent)"
   118|                  :stroke-width="16"
   119|                  :format="() => (license.current_assets ?? 0) + ' / ' + license.max_assets"
   120|                />
   121|              </div>
   122|              <div class="usage-item" v-if="license.max_nodes">
   123|                <div class="usage-label">节点</div>
   124|                <el-progress
   125|                  :percentage="nodeUsagePercent"
   126|                  :color="usageColor(nodeUsagePercent)"
   127|                  :stroke-width="16"
   128|                  :format="() => (license.current_nodes ?? 0) + ' / ' + license.max_nodes"
   129|                />
   130|              </div>
   131|            </div>
   132|          </div>
   133|        </div>
   134|      </el-col>
   135|
   136|      <!-- ── Update License Card ──────────────────────────── -->
   137|      <el-col :span="10">
   138|        <div class="autops-card">
   139|          <div class="card-header">
   140|            <span class="card-title">更新授权</span>
   141|          </div>
   142|          <div class="card-body">
   143|            <el-form label-width="80px" label-position="right">
   144|              <el-form-item label="授权文件">
   145|                <el-upload
   146|                  action=""
   147|                  :auto-upload="false"
   148|                  :limit="1"
   149|                  accept=".lic,.key"
   150|                  :on-change="handleFileChange"
   151|                  :file-list="fileList"
   152|                >
   153|                  <el-button>选择文件</el-button>
   154|                </el-upload>
   155|              </el-form-item>
   156|              <el-form-item label="授权密钥">
   157|                <el-input
   158|                  v-model="licenseKey"
   159|                  type="textarea"
   160|                  :rows="5"
   161|                  placeholder="粘贴授权密钥内容"
   162|                />
   163|              </el-form-item>
   164|              <el-form-item>
   165|                <el-button
   166|                  type="primary"
   167|                  :loading="activating"
   168|                  @click="activateLicense"
   169|                >
   170|                  激活授权
   171|                </el-button>
   172|                <el-button @click="offlineActivate">离线激活</el-button>
   173|              </el-form-item>
   174|            </el-form>
   175|
   176|            <el-divider />
   177|
   178|            <div class="info-section">
   179|              <div class="info-title">授权说明</div>
   180|              <ul class="info-list">
   181|                <li>社区版：免费使用，最多支持 100 资产和 3 节点</li>
   182|                <li>专业版：适用于中小型团队，支持全部功能模块</li>
   183|                <li>企业版：不限资产数和节点数，提供专属技术支持</li>
   184|              </ul>
   185|            </div>
   186|
   187|            <div class="info-section" style="margin-top: 16px">
   188|              <div class="info-title">联系授权</div>
   189|              <div class="text-secondary">
   190|                如需获取或更新授权，请联系商务团队：
   191|                <br />
   192|                邮箱：license@autops.example.com
   193|              </div>
   194|            </div>
   195|          </div>
   196|        </div>
   197|      </el-col>
   198|    </el-row>
   199|    </div>
   200|  </div>
   201|</template>
   202|
   203|<script setup lang="ts">
   204|import { ref, reactive, computed, onMounted } from 'vue'
   205|import { ElMessage } from 'element-plus'
   206|import { Refresh, CircleCheck } from '@element-plus/icons-vue'
   207|import client from '@/shared/api/client'
   208|
   209|// ── State ────────────────────────────────────────────────
   210|const loading = ref(false)
   211|const activating = ref(false)
   212|const backendUnavailable = ref(false)
   213|const licenseKey = ref('')
   214|const fileList = ref<any[]>([])
   215|
   216|const license = reactive({
   217|  type: '',
   218|  holder: '',
   219|  expires_at: '',
   220|  expired: false,
   221|  serial: '',
   222|  max_assets: 0,
   223|  current_assets: 0,
   224|  max_nodes: 0,
   225|  current_nodes: 0,
   226|  max_users: 0,
   227|  modules: '' as string | string[],
   228|  issued_at: '',
   229|})
   230|
   231|// ── Computed ─────────────────────────────────────────────
   232|const licenseModules = computed(() => {
   233|  if (Array.isArray(license.modules)) return license.modules
   234|  if (typeof license.modules === 'string' && license.modules) {
   235|    return license.modules.split(',').map((s) => s.trim()).filter(Boolean)
   236|  }
   237|  return []
   238|})
   239|
   240|const assetUsagePercent = computed(() => {
   241|  if (!license.max_assets) return 0
   242|  return Math.min(Math.round(((license.current_assets ?? 0) / license.max_assets) * 100), 100)
   243|})
   244|
   245|const nodeUsagePercent = computed(() => {
   246|  if (!license.max_nodes) return 0
   247|  return Math.min(Math.round(((license.current_nodes ?? 0) / license.max_nodes) * 100), 100)
   248|})
   249|
   250|const assetUsageExceeded = computed(() => {
   251|  return license.max_assets > 0 && (license.current_assets ?? 0) >= license.max_assets * 0.9
   252|})
   253|
   254|const nodeUsageExceeded = computed(() => {
   255|  return license.max_nodes > 0 && (license.current_nodes ?? 0) >= license.max_nodes * 0.9
   256|})
   257|
   258|function usageColor(pct: number): string {
   259|  if (pct >= 90) return '#f53f3f'
   260|  if (pct >= 70) return '#ff7d00'
   261|  return '#00b42a'
   262|}
   263|
   264|// ── Data Loading ─────────────────────────────────────────
   265|async function loadLicense() {
   266|  loading.value = true
   267|  backendUnavailable.value = false
   268|  try {
   269|    const res = await client.get('/api/v1/platform/license')
   270|    const data = res.data?.data ?? res.data
   271|    if (data && typeof data === 'object') {
   272|      Object.assign(license, {
   273|        type: data.type ?? data.license_type ?? '',
   274|        holder: data.holder ?? data.organization ?? '',
   275|        expires_at: data.expires_at ?? data.expiry ?? '',
   276|        expired: data.expired ?? data.is_expired ?? false,
   277|        serial: data.serial ?? data.serial_number ?? '',
   278|        max_assets: data.max_assets ?? 0,
   279|        current_assets: data.current_assets ?? data.asset_count ?? 0,
   280|        max_nodes: data.max_nodes ?? 0,
   281|        current_nodes: data.current_nodes ?? data.node_count ?? 0,
   282|        max_users: data.max_users ?? 0,
   283|        modules: data.modules ?? data.features ?? '',
   284|        issued_at: data.issued_at ?? data.created_at ?? '',
   285|      })
   286|    }
   287|  } catch {
   288|    backendUnavailable.value = true
   289|  } finally {
   290|    loading.value = false
   291|  }
   292|}
   293|
   294|function retryLoadLicense() {
   295|  loadLicense()
   296|}
   297|
   298|// ── File Handling ────────────────────────────────────────
   299|function handleFileChange(file: any) {
   300|  fileList.value = [file]
   301|}
   302|
   303|// ── Activate ─────────────────────────────────────────────
   304|async function activateLicense() {
   305|  if (!licenseKey.value && fileList.value.length === 0) {
   306|    ElMessage.warning('请输入授权密钥或选择授权文件')
   307|    return
   308|  }
   309|
   310|  activating.value = true
   311|  try {
   312|    const payload: Record<string, any> = {}
   313|    if (licenseKey.value) payload.license_key = licenseKey.value
   314|    if (fileList.value.length > 0) payload.has_file = true
   315|
   316|    await client.post('/api/v1/platform/license', payload)
   317|    ElMessage.success('授权已激活')
   318|    licenseKey.value = ''
   319|    fileList.value = []
   320|    loadLicense()
   321|  } catch (err: any) {
   322|    ElMessage.error(err.message || '激活失败')
   323|  } finally {
   324|    activating.value = false
   325|  }
   326|}
   327|
   328|function offlineActivate() {
   329|  ElMessage.info('请联系商务团队获取离线激活文件')
   330|}
   331|
   332|// ── Init ─────────────────────────────────────────────────
   333|onMounted(() => {
   334|  loadLicense()
   335|})
   336|</script>
   337|
   338|<style scoped>
   339|
   342|.autops-page-header {
   343|  display: flex;
   344|  justify-content: space-between;
   345|  align-items: center;
   346|  margin-bottom: 16px;
   347|}
   348|.autops-page-title {
   349|  font-size: 18px;
   350|  font-weight: 600;
   351|  color: #1d2129;
   352|}
   353|
   354|.autops-card {
   355|  background: #fff;
   356|  border: 1px solid #e5e6eb;
   357|  border-radius: 8px;
   358|  overflow: hidden;
   359|}
   360|
   367|
   372|.card-body {
   373|  padding: 16px;
   374|}
   375|
   376|.text-secondary {
   377|  color: #86909c;
   378|  font-size: 12px;
   379|}
   380|.text-danger {
   381|  color: #f53f3f;
   382|}
   383|.text-success {
   384|  color: #00b42a;
   385|}
   386|
   387|.usage-hint {
   388|  color: #86909c;
   389|  font-size: 12px;
   390|}
   391|
   392|/* Module section */
   393|.module-section {
   394|  margin-top: 16px;
   395|}
   396|.module-title {
   397|  font-size: 13px;
   398|  font-weight: 600;
   399|  color: #4e5969;
   400|  margin-bottom: 8px;
   401|}
   402|.module-list {
   403|  display: flex;
   404|  flex-wrap: wrap;
   405|  gap: 6px;
   406|}
   407|.module-tag {
   408|  font-size: 12px;
   409|}
   410|
   411|/* Usage section */
   412|.usage-section {
   413|  margin-top: 16px;
   414|}
   415|.usage-item {
   416|  margin-bottom: 10px;
   417|}
   418|.usage-label {
   419|  font-size: 12px;
   420|  color: #86909c;
   421|  margin-bottom: 4px;
   422|}
   423|
   424|/* Info section */
   425|.info-section {
   426|  font-size: 13px;
   427|}
   428|.info-title {
   429|  font-weight: 600;
   430|  color: #4e5969;
   431|  margin-bottom: 6px;
   432|}
   433|.info-list {
   434|  margin: 0;
   435|  padding-left: 18px;
   436|  color: #86909c;
   437|  font-size: 12px;
   438|  line-height: 1.8;
   439|}
   440|
   441|/* Guide card */
   442|.guide-card {
   443|  max-width: 600px;
   444|  margin: 40px auto;
   445|  padding: 40px 32px;
   446|  text-align: center;
   447|}
   448|
   449|.guide-info {
   450|  text-align: left;
   451|  margin-top: 24px;
   452|}
   453|
   454|.guide-title {
   455|  font-size: 14px;
   456|  font-weight: 600;
   457|  color: #4e5969;
   458|  margin-bottom: 8px;
   459|}
   460|
   461|.guide-list {
   462|  margin: 0;
   463|  padding-left: 18px;
   464|  color: #86909c;
   465|  font-size: 13px;
   466|  line-height: 2;
   467|}
   468|</style>
   469|