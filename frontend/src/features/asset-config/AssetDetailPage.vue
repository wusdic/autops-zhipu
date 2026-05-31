<template>
  <div class="asset-detail">
    <!-- 顶部导航 -->
    <div class="page-top">
      <el-button @click="goBack" :icon="ArrowLeft">返回资产列表</el-button>
      <el-button v-if="asset" type="primary" link @click="$router.push(`/assets/${asset.id}/topology`)">
        <el-icon><Connection /></el-icon> 拓扑图
      </el-button>
      <div class="asset-title" v-if="asset">
        <span class="name">{{ asset.name }}</span>
        <el-tag :type="statusType(asset.status)" size="small" style="margin-left: 8px">{{ asset.status }}</el-tag>
        <el-tag :type="healthType(asset.health_status)" size="small" style="margin-left: 4px">{{ asset.health_status }}</el-tag>
      </div>
    </div>

    <div v-loading="loading" class="detail-body">
      <!-- 空状态 -->
      <el-empty v-if="!loading && !asset" description="资产不存在或已被删除">
        <el-button type="primary" @click="goBack">返回列表</el-button>
      </el-empty>

      <template v-if="asset">
        <!-- 顶部摘要卡片 -->
        <el-card class="summary-card" shadow="hover">
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
        </el-card>

        <!-- Tab 切换 -->
        <el-card style="margin-top: 16px">
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
                  <el-tag :type="statusType(asset.status)" size="small">{{ asset.status }}</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="健康状态">
                  <el-tag :type="healthType(asset.health_status)" size="small">{{ asset.health_status }}</el-tag>
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
                <el-table :data="asset.ips" size="small" stripe>
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
                <el-table v-else :data="relations" stripe>
                  <el-table-column prop="relation_type" label="关系类型" width="140">
                    <template #default="{ row }">
                      <el-tag size="small">{{ formatRelationType(row.relation_type) }}</el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="target_name" label="关联资产" min-width="160">
                    <template #default="{ row }">
                      <el-button link type="primary" @click="navigateToAsset(row.target_id)">
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
          </el-tabs>
        </el-card>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Plus, Connection } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import api from '@/shared/api/client'
import { API as R } from '@/shared/api/routes'
import TimelineView from '@/shared/components/TimelineView.vue'

const route = useRoute()
const router = useRouter()

const assetId = ref(route.params.id as string)
const loading = ref(false)
const relationsLoading = ref(false)
const timelineLoading = ref(false)
const asset = ref<any>(null)
const relations = ref<any[]>([])
const timeline = ref<any[]>([])
const activeTab = ref('info')
const newTag = ref('')

function formatType(t: string) {
  const map: Record<string, string> = {
    linux_server: 'Linux', windows_server: 'Windows', database: '数据库',
    network_device: '网络设备', web_service: 'Web服务',
  }
  return map[t] || t || '-'
}

function formatRelationType(t: string) {
  const map: Record<string, string> = {
    depends: '依赖', connected: '连接', hosted_on: '部署于', contains: '包含',
    parent: '父级', child: '子级',
  }
  return map[t] || t
}

function statusType(s: string) {
  return s === 'active' ? 'success' : s === 'inactive' ? 'danger' : 'warning'
}

function healthType(h: string) {
  return h === 'healthy' ? 'success' : h === 'warning' ? 'warning' : h === 'critical' ? 'danger' : 'info'
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

onMounted(async () => {
  await loadAsset()
  loadRelations()
  loadTimeline()
})
</script>

<style scoped>
.page-top {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
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
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e7ed 100%);
}
.summary-item {
  text-align: center;
}
.summary-item .label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}
.summary-item .value {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}
.section-block {
  margin-top: 24px;
}
.section-block h4 {
  margin-bottom: 12px;
  font-size: 14px;
  color: #303133;
  border-left: 3px solid #409eff;
  padding-left: 8px;
}
</style>
