<template>
  <div class="asset-detail">
    <!-- 页面头部 -->
    <div class="autops-page-header">
      <div class="autops-page-title" v-if="asset">
        <el-button @click="goBack" :icon="ArrowLeft">返回资产列表</el-button>
        <span style="margin-left: 12px">{{ asset.name }}</span>
        <el-tag :type="(statusType(asset.status)) as TagType" size="small" style="margin-left: 8px">{{ asset.status }}</el-tag>
        <el-tag :type="(healthType(asset.health_status)) as TagType" size="small" style="margin-left: 4px">{{ asset.health_status }}</el-tag>
      </div>
      <div class="autops-toolbar-right" v-if="asset">
        <el-button type="primary" plain @click="$router.push('/assets/' + asset.id + '/topology')">
          <el-icon><Connection /></el-icon> 拓扑图
        </el-button>
        <el-button type="primary" @click="navToInspectionFromAsset(assetId)">
          <el-icon><Setting /></el-icon> 绑定巡检模板
        </el-button>
      </div>
    </div>

    <div v-loading="loading" class="detail-body">
      <!-- 空状态 -->
      <el-empty v-if="!loading && !asset" description="资产不存在或已被删除">
        <el-button type="primary" @click="goBack">返回列表</el-button>
      </el-empty>

      <template v-if="asset">
        <!-- 顶部摘要卡片 -->
        <div class="autops-card mb-lg">
          <div class="autops-card-body">
          <el-row :gutter="24">
            <el-col :span="6">
              <div class="summary-item">
                <div class="label">IP 地址</div>
                <div class="value">{{ asset.ip }}</div>
              </div>
            </el-col>
            <el-col :span="4">
              <div class="summary-item">
                <div class="label">端口</div>
                <div class="value">{{ asset.port || '-' }}</div>
              </div>
            </el-col>
            <el-col :span="4">
              <div class="summary-item">
                <div class="label">类型</div>
                <div class="value">{{ formatType(asset.asset_type) }}</div>
              </div>
            </el-col>
            <el-col :span="4">
              <div class="summary-item">
                <div class="label">操作系统</div>
                <div class="value">{{ asset.os_type || '-' }}</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="summary-item">
                <div class="label">环境</div>
                <div class="value">{{ asset.environment || '-' }}</div>
              </div>
            </el-col>
          </el-row>
          </div>
        </div>

        <!-- Tab 切换 -->
        <div class="autops-card">
          <div class="autops-card-body">
          <el-tabs v-model="activeTab">
            <!-- 基本信息 -->
            <el-tab-pane label="基本信息" name="info">
              <el-descriptions :column="2" border>
                <el-descriptions-item label="ID">{{ asset.id }}</el-descriptions-item>
                <el-descriptions-item label="名称">{{ asset.name }}</el-descriptions-item>
                <el-descriptions-item label="类型">{{ formatType(asset.asset_type) }}</el-descriptions-item>
                <el-descriptions-item label="IP">{{ asset.ip }}</el-descriptions-item>
                <el-descriptions-item label="端口">{{ asset.port || '-' }}</el-descriptions-item>
                <el-descriptions-item label="状态">
                  <el-tag :type="(statusType(asset.status)) as TagType" size="small">{{ asset.status }}</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="健康状态">
                  <el-tag :type="(healthType(asset.health_status)) as TagType" size="small">{{ asset.health_status }}</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="操作系统">{{ asset.os_type || '-' }}</el-descriptions-item>
                <el-descriptions-item label="环境">{{ asset.environment || '-' }}</el-descriptions-item>
                <el-descriptions-item label="描述" :span="2">{{ asset.description || '-' }}</el-descriptions-item>
              </el-descriptions>

              <!-- 标签 -->
              <div class="section-block">
                <h4>标签</h4>
                <div class="tags-area" v-if="asset.tags && asset.tags.length">
                  <el-tag
                    v-for="tag in asset.tags"
                    :key="tag"
                    closable
                    style="margin-right: 6px; margin-bottom: 4px"
                    @close="removeTag(tag)"
                  >{{ tag }}</el-tag>
                </div>
                <el-empty v-else description="暂无标签" :image-size="40" />
                <div style="margin-top: 8px">
                  <el-input
                    v-model="newTag"
                    placeholder="输入标签后回车"
                    size="small"
                    style="width: 200px"
                    @keyup.enter="addTag"
                  >
                    <template #append>
                      <el-button @click="addTag" :icon="Plus" />
                    </template>
                  </el-input>
                </div>
              </div>

              <!-- IP 列表 -->
              <div class="section-block" v-if="asset.ips && asset.ips.length">
                <h4>关联 IP</h4>
                <el-table stripe :data="asset.ips" size="small">
                  <el-table-column prop="ip" label="IP" />
                  <el-table-column prop="type" label="类型" width="120" />
                  <el-table-column prop="is_primary" label="主IP" width="80">
                    <template #default="{ row }">
                      <el-tag :type="row.is_primary ? 'success' : 'info'" size="small">
                        {{ row.is_primary ? '是' : '否' }}
                      </el-tag>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </el-tab-pane>

            <!-- 关系 -->
            <el-tab-pane label="关系" name="relations">
              <div v-loading="relationsLoading">
                <el-empty v-if="!relationsLoading && !relations.length" description="暂无关联关系" />
                <el-table stripe v-else :data="relations">
                  <el-table-column prop="relation_type" label="关系类型" width="140">
                    <template #default="{ row }">
                      <el-tag size="small">{{ formatRelationType(row.relation_type) }}</el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="target_name" label="关联资产" min-width="160">
                    <template #default="{ row }">
                      <el-button plain type="primary" @click="navigateToAsset(row.target_id)">
                        {{ row.target_name || row.target_id }}
                      </el-button>
                    </template>
                  </el-table-column>
                  <el-table-column prop="target_ip" label="IP" width="140" />
                  <el-table-column prop="target_type" label="类型" width="120">
                    <template #default="{ row }">
                      <el-tag size="small">{{ formatType(row.target_type) }}</el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="description" label="描述" min-width="160" show-overflow-tooltip />
                  <el-table-column prop="created_at" label="建立时间" width="160">
                    <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
                  </el-table-column>
                </el-table>
              </div>
            </el-tab-pane>

            <!-- 时间线 -->
            <el-tab-pane label="时间线" name="timeline">
              <div v-loading="timelineLoading">
                <el-empty v-if="!timelineLoading && !timeline.length" description="暂无时间线记录" />
                <TimelineView v-else :items="timeline" />
              </div>
            </el-tab-pane>

            <!-- 凭证绑定 -->
            <el-tab-pane label="凭证绑定" name="credentials">
              <div class="tab-toolbar">
                <el-button type="primary" size="small" @click="showCredentialDialog = true">绑定凭证</el-button>
              </div>
              <div v-loading="credentialsLoading">
                <el-empty v-if="!credentialsLoading && !boundCredentials.length" description="暂无绑定凭证" />
                <el-table stripe v-else :data="boundCredentials"size="small">
                  <el-table-column prop="name" label="凭证名称" min-width="140" />
                  <el-table-column prop="type" label="类型" width="120">
                    <template #default="{ row }">
                      <el-tag size="small">{{ row.type || '-' }}</el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="username" label="用户名" width="140" />
                  <el-table-column prop="bound_at" label="绑定时间" width="170">
                    <template #default="{ row }">{{ formatTime(row.bound_at) }}</template>
                  </el-table-column>
                  <el-table-column label="操作" width="100" fixed="right">
                    <template #default="{ row }">
                      <el-popconfirm title="确定解绑该凭证？" @confirm="unbindCredential(row.id)">
                        <template #reference>
                          <el-button type="danger" plain size="small">解绑</el-button>
                        </template>
                      </el-popconfirm>
                    </template>
                  </el-table-column>
                </el-table>
              </div>

              <!-- 绑定凭证对话框 -->
              <el-dialog v-model="showCredentialDialog" title="绑定凭证" width="480px" destroy-on-close>
                <el-form label-width="80px">
                  <el-form-item label="选择凭证">
                    <el-select
                      v-model="selectedCredentialId"
                      placeholder="请选择凭证"
                      filterable
                      style="width: 100%"
                      v-loading="allCredentialsLoading"
                    >
                      <el-option
                        v-for="c in allCredentials"
                        :key="c.id"
                        :label="c.name + '（' + c.username || c.type || '-' + '）'"
                        :value="c.id"
                      />
                    </el-select>
                  </el-form-item>
                </el-form>
                <template #footer>
                  <el-button @click="showCredentialDialog = false">取消</el-button>
                  <el-button type="primary" :disabled="!selectedCredentialId" @click="bindCredential">确定绑定</el-button>
                </template>
              </el-dialog>
            </el-tab-pane>

            <!-- 采集配置 -->
            <el-tab-pane label="采集配置" name="collection">
              <div class="tab-toolbar">
                <el-button type="primary" size="small" @click="showCollectionDialog = true">绑定采集模板</el-button>
              </div>
              <div v-loading="collectionLoading">
                <el-empty v-if="!collectionLoading && !collectionConfigs.length" description="暂无采集配置" />
                <el-table stripe v-else :data="collectionConfigs"size="small">
                  <el-table-column prop="config_name" label="配置名称" min-width="140" />
                  <el-table-column prop="type" label="类型" width="120">
                    <template #default="{ row }">
                      <el-tag size="small">{{ row.type || '-' }}</el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="interval" label="采集间隔" width="120">
                    <template #default="{ row }">{{ row.interval || '-' }}</template>
                  </el-table-column>
                  <el-table-column prop="last_collection_at" label="最近采集" width="170">
                    <template #default="{ row }">{{ formatTime(row.last_collection_at) }}</template>
                  </el-table-column>
                  <el-table-column prop="status" label="状态" width="100">
                    <template #default="{ row }">
                      <StatusBadge :status="row.status" />
                    </template>
                  </el-table-column>
                  <el-table-column label="操作" width="100" fixed="right">
                    <template #default="{ row }">
                      <el-button type="primary" plain size="small" @click="triggerCollection(row.id)">触发采集</el-button>
                    </template>
                  </el-table-column>
                </el-table>

                <!-- 最近采集结果预览 -->
                <div class="section-block" v-if="lastCollectionResult">
                  <h4>最近采集结果</h4>
                  <el-descriptions :column="2" border size="small">
                    <el-descriptions-item label="状态">
                      <StatusBadge :status="lastCollectionResult.status" />
                    </el-descriptions-item>
                    <el-descriptions-item label="采集时间">{{ formatTime(lastCollectionResult.collected_at) }}</el-descriptions-item>
                    <el-descriptions-item label="耗时">{{ lastCollectionResult.duration || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="数据条数">{{ lastCollectionResult.item_count ?? '-' }}</el-descriptions-item>
                    <el-descriptions-item label="摘要" :span="2">{{ lastCollectionResult.summary || '-' }}</el-descriptions-item>
                  </el-descriptions>
                </div>
              </div>

              <!-- 绑定采集模板对话框 -->
              <el-dialog v-model="showCollectionDialog" title="绑定采集模板" width="480px" destroy-on-close>
                <el-form label-width="100px">
                  <el-form-item label="选择配置">
                    <el-select
                      v-model="selectedCollectionId"
                      placeholder="请选择采集配置"
                      filterable
                      style="width: 100%"
                      v-loading="allCollectionConfigsLoading"
                    >
                      <el-option
                        v-for="c in allCollectionConfigs"
                        :key="c.id"
                        :label="c.name + '（' + c.type || '-' + '）'"
                        :value="c.id"
                      />
                    </el-select>
                  </el-form-item>
                </el-form>
                <template #footer>
                  <el-button @click="showCollectionDialog = false">取消</el-button>
                  <el-button type="primary" :disabled="!selectedCollectionId" @click="bindCollection">确定绑定</el-button>
                </template>
              </el-dialog>
            </el-tab-pane>

            <!-- 策略绑定 -->
            <el-tab-pane label="策略绑定" name="policies">
              <div class="tab-toolbar">
                <el-button type="primary" size="small" @click="showPolicyDialog = true">绑定策略</el-button>
              </div>
              <div v-loading="policiesLoading">
                <el-empty v-if="!policiesLoading && !boundPolicies.length" description="暂无绑定策略" />
                <el-table stripe v-else :data="boundPolicies"size="small">
                  <el-table-column prop="name" label="策略名称" min-width="140" />
                  <el-table-column prop="trigger_condition" label="触发条件" min-width="160" show-overflow-tooltip />
                  <el-table-column prop="risk_level" label="风险等级" width="100">
                    <template #default="{ row }">
                      <el-tag :type="(riskLevelType(row.risk_level)) as TagType" size="small">{{ row.risk_level || '-' }}</el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="enabled" label="启用状态" width="100">
                    <template #default="{ row }">
                      <el-switch
                        :model-value="row.enabled"
                        size="small"
                        @change="(val: string | number | boolean) => togglePolicyEnabled(row.id, val as boolean)"
                      />
                    </template>
                  </el-table-column>
                  <el-table-column label="操作" width="100" fixed="right">
                    <template #default="{ row }">
                      <el-popconfirm title="确定解绑该策略？" @confirm="unbindPolicy(row.id)">
                        <template #reference>
                          <el-button type="danger" plain size="small">解绑</el-button>
                        </template>
                      </el-popconfirm>
                    </template>
                  </el-table-column>
                </el-table>
              </div>

              <!-- 绑定策略对话框 -->
              <el-dialog v-model="showPolicyDialog" title="绑定策略" width="480px" destroy-on-close>
                <el-form label-width="80px">
                  <el-form-item label="选择策略">
                    <el-select
                      v-model="selectedPolicyId"
                      placeholder="请选择策略"
                      filterable
                      style="width: 100%"
                      v-loading="allPoliciesLoading"
                    >
                      <el-option
                        v-for="p in allPolicies"
                        :key="p.id"
                        :label="p.name + '（' + p.risk_level || '-' + '）'"
                        :value="p.id"
                      />
                    </el-select>
                  </el-form-item>
                </el-form>
                <template #footer>
                  <el-button @click="showPolicyDialog = false">取消</el-button>
                  <el-button type="primary" :disabled="!selectedPolicyId" @click="bindPolicy">确定绑定</el-button>
                </template>
              </el-dialog>
            </el-tab-pane>
          </el-tabs>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import type { TagType } from '@/shared/types'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Plus, Connection, Setting } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import api from '@/shared/api/client'
import { API as R } from '@/shared/api/routes'
import TimelineView from '@/shared/components/TimelineView.vue'
import { useWorkflowNav } from '@/shared/composables/useWorkflowNav'
import StatusBadge from '@/shared/components/StatusBadge.vue'

const route = useRoute()
const router = useRouter()

const { navToInspectionFromAsset } = useWorkflowNav()

const assetId = ref(route.params.id as string)
const loading = ref(false)
const relationsLoading = ref(false)
const timelineLoading = ref(false)
const asset = ref<any>(null)
const relations = ref<any[]>([])
const timeline = ref<any[]>([])
const activeTab = ref('info')
const newTag = ref('')

// ---- 凭证绑定 ----
const credentialsLoading = ref(false)
const boundCredentials = ref<any[]>([])
const showCredentialDialog = ref(false)
const selectedCredentialId = ref('')
const allCredentials = ref<any[]>([])
const allCredentialsLoading = ref(false)

// ---- 采集配置 ----
const collectionLoading = ref(false)
const collectionConfigs = ref<any[]>([])
const lastCollectionResult = ref<any>(null)
const showCollectionDialog = ref(false)
const selectedCollectionId = ref('')
const allCollectionConfigs = ref<any[]>([])
const allCollectionConfigsLoading = ref(false)

// ---- 策略绑定 ----
const policiesLoading = ref(false)
const boundPolicies = ref<any[]>([])
const showPolicyDialog = ref(false)
const selectedPolicyId = ref('')
const allPolicies = ref<any[]>([])
const allPoliciesLoading = ref(false)

function formatType(t: string): string {
  const map: Record<string, string> = {
    linux_server: 'Linux', windows_server: 'Windows', database: '数据库',
    network_device: '网络设备', web_service: 'Web服务',
  }
  return map[t] || t || '-'
}

function formatRelationType(t: string): string {
  const map: Record<string, string> = {
    depends: '依赖', connected: '连接', hosted_on: '部署于', contains: '包含',
    parent: '父级', child: '子级',
  }
  return map[t] || t
}

function statusType(s: string): TagType {
  return (s === 'active' ? 'success' : s === 'inactive' ? 'danger' : 'warning') as TagType
}

function healthType(h: string): TagType {
  return (h === 'healthy' ? 'success' : h === 'warning' ? 'warning' : h === 'critical' ? 'danger' : 'info') as TagType
}

function riskLevelType(level: string): TagType {
  const map: Record<string, string> = {
    critical: 'danger', high: 'danger', medium: 'warning', low: 'success', info: 'info',
  }
  return (map[level] || 'info') as TagType
}

function formatTime(t: string) {
  return t ? new Date(t).toLocaleString('zh-CN') : '-'
}

function goBack() {
  router.back()
}

function navigateToAsset(id: string) {
  router.push({ name: 'asset-detail', params: { id } })
}

async function loadAsset() {
  loading.value = true
  try {
    const { data } = await api.get(R.ASSET_DETAIL(assetId.value))
    if (data.code === 0) {
      asset.value = data.data
    }
  } catch (e: any) {
    ElMessage.error('加载资产详情失败: ' + (e.message || e))
  } finally {
    loading.value = false
  }
}

async function loadRelations() {
  relationsLoading.value = true
  try {
    const { data } = await api.get(R.ASSET_RELATIONS(assetId.value))
    if (data.code === 0) {
      relations.value = data.data?.items || data.data || []
    }
  } catch (e: any) {
    ElMessage.error('加载关系失败: ' + (e.message || e))
  } finally {
    relationsLoading.value = false
  }
}

async function loadTimeline() {
  timelineLoading.value = true
  try {
    const { data } = await api.get(R.ASSET_TIMELINE(assetId.value))
    if (data.code === 0) {
      timeline.value = data.data?.items || data.data || []
    }
  } catch (e: any) {
    ElMessage.error('加载时间线失败: ' + (e.message || e))
  } finally {
    timelineLoading.value = false
  }
}

async function addTag() {
  if (!newTag.value.trim()) return
  const tags = [...(asset.value.tags || []), newTag.value.trim()]
  try {
    const { data } = await api.put(R.ASSET_DETAIL(assetId.value), { tags })
    if (data.code === 0) {
      asset.value.tags = tags
      newTag.value = ''
      ElMessage.success('标签已添加')
    }
  } catch (e: any) {
    ElMessage.error('添加标签失败')
  }
}

async function removeTag(tag: string) {
  const tags = (asset.value.tags || []).filter((t: string) => t !== tag)
  try {
    const { data } = await api.put(R.ASSET_DETAIL(assetId.value), { tags })
    if (data.code === 0) {
      asset.value.tags = tags
      ElMessage.success('标签已移除')
    }
  } catch (e: any) {
    ElMessage.error('移除标签失败')
  }
}

// ==================== 凭证绑定 ====================

async function loadCredentials() {
  credentialsLoading.value = true
  try {
    const { data } = await api.get(R.ASSET_CREDENTIALS(assetId.value))
    if (data.code === 0) {
      boundCredentials.value = data.data?.items || data.data || []
    }
  } catch (e: any) {
    ElMessage.error('加载凭证列表失败: ' + (e.message || e))
  } finally {
    credentialsLoading.value = false
  }
}

async function loadAllCredentials() {
  allCredentialsLoading.value = true
  try {
    const { data } = await api.get(R.CREDENTIALS)
    if (data.code === 0) {
      allCredentials.value = data.data?.items || data.data || []
    }
  } catch (e: any) {
    ElMessage.error('加载凭证选择列表失败')
  } finally {
    allCredentialsLoading.value = false
  }
}

async function bindCredential() {
  if (!selectedCredentialId.value) return
  try {
    const { data } = await api.post(R.ASSET_CREDENTIALS(assetId.value), {
      credential_id: selectedCredentialId.value,
    })
    if (data.code === 0) {
      ElMessage.success('凭证绑定成功')
      showCredentialDialog.value = false
      selectedCredentialId.value = ''
      loadCredentials()
    }
  } catch (e: any) {
    ElMessage.error('绑定凭证失败: ' + (e.message || e))
  }
}

async function unbindCredential(credId: string) {
  try {
    const { data } = await api.delete(R.ASSET_CREDENTIAL_UNBIND(assetId.value, credId))
    if (data.code === 0) {
      ElMessage.success('凭证已解绑')
      loadCredentials()
    }
  } catch (e: any) {
    ElMessage.error('解绑凭证失败: ' + (e.message || e))
  }
}

// ==================== 采集配置 ====================

async function loadCollectionConfigs() {
  collectionLoading.value = true
  try {
    const { data } = await api.get(R.ASSET_COLLECTION_CONFIGS(assetId.value))
    if (data.code === 0) {
      collectionConfigs.value = data.data?.items || data.data || []
      lastCollectionResult.value = data.data?.last_result || null
    }
  } catch (e: any) {
    ElMessage.error('加载采集配置失败: ' + (e.message || e))
  } finally {
    collectionLoading.value = false
  }
}

async function loadAllCollectionConfigs() {
  allCollectionConfigsLoading.value = true
  try {
    const { data } = await api.get(R.COLLECTORS)
    if (data.code === 0) {
      allCollectionConfigs.value = data.data?.items || data.data || []
    }
  } catch (e: any) {
    ElMessage.error('加载采集模板列表失败')
  } finally {
    allCollectionConfigsLoading.value = false
  }
}

async function bindCollection() {
  if (!selectedCollectionId.value) return
  try {
    const { data } = await api.post(R.ASSET_COLLECTION_CONFIGS(assetId.value), {
      config_id: selectedCollectionId.value,
    })
    if (data.code === 0) {
      ElMessage.success('采集配置绑定成功')
      showCollectionDialog.value = false
      selectedCollectionId.value = ''
      loadCollectionConfigs()
    }
  } catch (e: any) {
    ElMessage.error('绑定采集配置失败: ' + (e.message || e))
  }
}

async function triggerCollection(configId: string) {
  try {
    const { data } = await api.post(R.ASSET_COLLECTION_TRIGGER(assetId.value), {
      config_id: configId,
    })
    if (data.code === 0) {
      ElMessage.success('采集任务已触发')
      loadCollectionConfigs()
    }
  } catch (e: any) {
    ElMessage.error('触发采集失败: ' + (e.message || e))
  }
}

// ==================== 策略绑定 ====================

async function loadPolicies() {
  policiesLoading.value = true
  try {
    const { data } = await api.get(R.ASSET_POLICIES(assetId.value))
    if (data.code === 0) {
      boundPolicies.value = data.data?.items || data.data || []
    }
  } catch (e: any) {
    ElMessage.error('加载策略列表失败: ' + (e.message || e))
  } finally {
    policiesLoading.value = false
  }
}

async function loadAllPolicies() {
  allPoliciesLoading.value = true
  try {
    const { data } = await api.get(R.POLICIES)
    if (data.code === 0) {
      allPolicies.value = data.data?.items || data.data || []
    }
  } catch (e: any) {
    ElMessage.error('加载策略选择列表失败')
  } finally {
    allPoliciesLoading.value = false
  }
}

async function bindPolicy() {
  if (!selectedPolicyId.value) return
  try {
    const { data } = await api.post(R.ASSET_POLICIES(assetId.value), {
      policy_id: selectedPolicyId.value,
    })
    if (data.code === 0) {
      ElMessage.success('策略绑定成功')
      showPolicyDialog.value = false
      selectedPolicyId.value = ''
      loadPolicies()
    }
  } catch (e: any) {
    ElMessage.error('绑定策略失败: ' + (e.message || e))
  }
}

async function unbindPolicy(policyId: string) {
  try {
    const { data } = await api.delete(R.ASSET_POLICY_UNBIND(assetId.value, policyId))
    if (data.code === 0) {
      ElMessage.success('策略已解绑')
      loadPolicies()
    }
  } catch (e: any) {
    ElMessage.error('解绑策略失败: ' + (e.message || e))
  }
}

async function togglePolicyEnabled(policyId: string, enabled: boolean) {
  try {
    const row = boundPolicies.value.find((p: any) => p.id === policyId)
    const { data } = await api.put(R.ASSET_POLICY_UNBIND(assetId.value, policyId), { enabled })
    if (data.code === 0) {
      if (row) row.enabled = enabled
      ElMessage.success(enabled ? '策略已启用' : '策略已禁用')
    }
  } catch (e: any) {
    ElMessage.error('更新策略状态失败')
  }
}

watch(showCredentialDialog, (val) => { if (val) loadAllCredentials() })
watch(showCollectionDialog, (val) => { if (val) loadAllCollectionConfigs() })
watch(showPolicyDialog, (val) => { if (val) loadAllPolicies() })

onMounted(async () => {
  await loadAsset()
  loadRelations()
  loadTimeline()
  loadCredentials()
  loadCollectionConfigs()
  loadPolicies()
})
</script>

<style scoped>
.page-top {
  display: flex;
  align-items: center;
  margin-bottom: var(--autops-space-lg);
}
.asset-title {
  margin-left: 16px;
  display: flex;
  align-items: center;
}
.asset-title .name {
  font-size: 18px;
  font-weight: 600;
}
.summary-card {
  background: linear-gradient(135deg, var(--autops-bg-2) 0%, var(--autops-bg-4) 100%);
}
.summary-item {
  text-align: center;
}
.summary-item .label {
  font-size: var(--autops-font-12);
  color: var(--autops-info);
  margin-bottom: 4px;
}
.summary-item .value {
  font-size: var(--autops-font-16);
  font-weight: 600;
  color: var(--autops-text-1);
}
.section-block {
  margin-top: 24px;
}
.section-block h4 {
  margin-bottom: var(--autops-space-md);
  font-size: var(--autops-font-14);
  color: var(--autops-text-1);
  border-left: 3px solid var(--autops-primary);
  padding-left: 8px;
}
.tab-toolbar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: var(--autops-space-md);
}
</style>
