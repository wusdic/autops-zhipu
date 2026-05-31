<template>
  <div class="asset-topology">
    <!-- 顶部导航 -->
    <div class="topology-header">
      <el-button :icon="ArrowLeft" @click="$router.back()">返回</el-button>
      <h2 style="margin: 0 0 0 12px">{{ asset?.hostname || '资产拓扑' }} - 关系拓扑图</h2>
      <div style="margin-left: auto; display: flex; gap: 8px">
        <el-button size="small" @click="refreshTopology" :loading="loading">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
      </div>
    </div>

    <div v-loading="loading" style="margin-top: 16px">
      <!-- 拓扑图区域 -->
      <div class="topology-container">
        <div v-if="nodes.length === 0 && !loading" class="empty-topology">
          <el-empty description="暂无拓扑关系数据">
            <el-button type="primary" @click="showAddRelation = true">添加关系</el-button>
          </el-empty>
        </div>
        <div v-else class="topology-canvas" ref="canvasRef">
          <!-- SVG拓扑图 -->
          <svg width="100%" height="100%" class="topology-svg">
            <!-- 连线 -->
            <g v-for="(edge, idx) in edges" :key="'e-' + idx">
              <line
                :x1="getNodePosition(edge.source).x"
                :y1="getNodePosition(edge.source).y"
                :x2="getNodePosition(edge.target).x"
                :y2="getNodePosition(edge.target).y"
                :stroke="edge.relation_type === 'depends_on' ? '#E6A23C' : '#409EFF'"
                stroke-width="2"
                stroke-dasharray="5,5"
              />
              <text
                :x="(getNodePosition(edge.source).x + getNodePosition(edge.target).x) / 2"
                :y="(getNodePosition(edge.source).y + getNodePosition(edge.target).y) / 2 - 8"
                text-anchor="middle"
                fill="#999"
                font-size="12"
              >{{ edge.relation_type }}</text>
            </g>
            <!-- 节点 -->
            <g v-for="node in nodes" :key="node.id" class="topology-node" @click="onNodeClick(node)">
              <rect
                :x="node.x - 50" :y="node.y - 20"
                width="100" height="40" rx="8"
                :fill="node.id === assetId ? '#409EFF' : '#fff'"
                :stroke="node.id === assetId ? '#409EFF' : '#ddd'"
                stroke-width="2"
              />
              <text
                :x="node.x" :y="node.y + 5"
                text-anchor="middle"
                :fill="node.id === assetId ? '#fff' : '#333'"
                font-size="13"
              >{{ node.label }}</text>
            </g>
          </svg>
        </div>
      </div>

      <!-- 节点详情面板 -->
      <el-drawer v-model="nodeDrawerVisible" title="节点详情" size="400px">
        <el-descriptions :column="1" border v-if="selectedNode">
          <el-descriptions-item label="名称">{{ selectedNode.label }}</el-descriptions-item>
          <el-descriptions-item label="类型">{{ selectedNode.asset_type }}</el-descriptions-item>
          <el-descriptions-item label="IP">{{ selectedNode.ip }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <StatusBadge :status="selectedNode.status" size="small" show-icon />
          </el-descriptions-item>
        </el-descriptions>
        <div style="margin-top: 16px">
          <el-button type="primary" @click="goToAsset(selectedNode?.id)">查看资产详情</el-button>
        </div>
      </el-drawer>

      <!-- 关系列表 -->
      <div style="margin-top: 16px">
        <el-divider content-position="left">关系列表</el-divider>
        <el-table :data="relations" stripe>
          <el-table-column label="源资产" min-width="140">
            <template #default="{ row }">{{ row.source_asset?.hostname || row.source_asset_id }}</template>
          </el-table-column>
          <el-table-column prop="relation_type" label="关系类型" width="140" />
          <el-table-column label="目标资产" min-width="140">
            <template #default="{ row }">{{ row.target_asset?.hostname || row.target_asset_id }}</template>
          </el-table-column>
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-popconfirm title="确认删除该关系？" @confirm="deleteRelation(row.id)">
                <template #reference>
                  <el-button text type="danger" size="small">删除</el-button>
                </template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <!-- 添加关系对话框 -->
    <el-dialog v-model="showAddRelation" title="添加资产关系" width="500px">
      <el-form :model="newRelation" label-width="100px">
        <el-form-item label="关系类型">
          <el-select v-model="newRelation.relation_type" style="width: 100%">
            <el-option label="依赖 (depends_on)" value="depends_on" />
            <el-option label="连接 (connected_to)" value="connected_to" />
            <el-option label="包含 (contains)" value="contains" />
            <el-option label="运行于 (runs_on)" value="runs_on" />
          </el-select>
        </el-form-item>
        <el-form-item label="目标资产">
          <el-select v-model="newRelation.target_asset_id" filterable style="width: 100%" placeholder="选择目标资产">
            <el-option v-for="a in allAssets" :key="a.id" :label="`${a.hostname} (${a.ip})`" :value="a.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddRelation = false">取消</el-button>
        <el-button type="primary" @click="addRelation" :loading="submitting">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Refresh } from '@element-plus/icons-vue'
import api from '@/shared/api/client'
import { API as R } from '@/shared/api/routes'
import StatusBadge from '@/shared/components/StatusBadge.vue'

const route = useRoute()
const router = useRouter()
const assetId = computed(() => route.params.id as string)

const loading = ref(false)
const asset = ref<any>(null)
const relations = ref<any[]>([])
const allAssets = ref<any[]>([])
const showAddRelation = ref(false)
const submitting = ref(false)
const nodeDrawerVisible = ref(false)
const selectedNode = ref<any>(null)

const newRelation = ref({ relation_type: 'depends_on', target_asset_id: '' })

// 拓扑节点和边
const nodes = ref<any[]>([])
const edges = ref<any[]>([])

function computeLayout(rels: any[], currentAsset: any, allAssetsMap: Record<string, any>) {
  const nodeMap = new Map<string, { id: string; label: string; x: number; y: number; asset_type: string; ip: string; status: string }>()
  // 中心节点
  const cx = 500, cy = 300
  nodeMap.set(currentAsset.id, {
    id: currentAsset.id,
    label: currentAsset.hostname || currentAsset.ip,
    x: cx, y: cy,
    asset_type: currentAsset.asset_type,
    ip: currentAsset.ip,
    status: currentAsset.status,
  })

  // 周围节点
  let angle = 0
  const radius = 180
  for (const rel of rels) {
    const otherId = rel.source_asset_id === currentAsset.id ? rel.target_asset_id : rel.source_asset_id
    const other = allAssetsMap[otherId]
    if (!nodeMap.has(otherId)) {
      const a = allAssetsMap[otherId]
      nodeMap.set(otherId, {
        id: otherId,
        label: a?.hostname || a?.ip || otherId.slice(0, 8),
        x: cx + radius * Math.cos(angle),
        y: cy + radius * Math.sin(angle),
        asset_type: a?.asset_type || '',
        ip: a?.ip || '',
        status: a?.status || '',
      })
      angle += (2 * Math.PI) / Math.max(rels.length, 6)
    }
  }
  nodes.value = Array.from(nodeMap.values())
  edges.value = rels.map(r => ({
    source: r.source_asset_id,
    target: r.target_asset_id,
    relation_type: r.relation_type,
  }))
}

function getNodePosition(id: string) {
  const n = nodes.value.find(n => n.id === id)
  return n ? { x: n.x, y: n.y } : { x: 0, y: 0 }
}

async function loadAsset() {
  const id = assetId.value
  if (!id) return
  loading.value = true
  try {
    const [assetRes, relRes, allRes] = await Promise.all([
      api.get(R.ASSET_DETAIL(id)),
      api.get(R.ASSET_RELATIONS(id)),
      api.get(R.ASSETS, { params: { page: 1, page_size: 200 } }),
    ])
    if (assetRes.data.code === 0) asset.value = assetRes.data.data
    const relData = relRes.data.code === 0 ? (relRes.data.data?.items || relRes.data.data || []) : []
    relations.value = Array.isArray(relData) ? relData : []

    const allItems = allRes.data.code === 0 ? (allRes.data.data?.items || allRes.data.data || []) : []
    allAssets.value = allItems
    const assetsMap: Record<string, any> = {}
    for (const a of allItems) assetsMap[a.id] = a

    computeLayout(relations.value, asset.value || { id }, assetsMap)
  } catch {
    ElMessage.error('加载拓扑数据失败')
  } finally {
    loading.value = false
  }
}

function refreshTopology() { loadAsset() }

function onNodeClick(node: any) {
  selectedNode.value = node
  nodeDrawerVisible.value = true
}

function goToAsset(id?: string) {
  if (id) router.push(`/assets/${id}`)
}

async function addRelation() {
  if (!newRelation.value.target_asset_id) {
    ElMessage.warning('请选择目标资产')
    return
  }
  submitting.value = true
  try {
    const { data } = await api.post(R.ASSET_RELATIONS(assetId.value), {
      source_asset_id: assetId.value,
      target_asset_id: newRelation.value.target_asset_id,
      relation_type: newRelation.value.relation_type,
    })
    if (data.code === 0) {
      ElMessage.success('关系已添加')
      showAddRelation.value = false
      newRelation.value = { relation_type: 'depends_on', target_asset_id: '' }
      loadAsset()
    }
  } catch {
    ElMessage.error('添加关系失败')
  } finally {
    submitting.value = false
  }
}

async function deleteRelation(id: string) {
  try {
    await api.delete(R.ASSET_RELATION_DELETE(assetId.value, id))
    ElMessage.success('关系已删除')
    loadAsset()
  } catch {
    ElMessage.error('删除失败')
  }
}

onMounted(() => loadAsset())
watch(() => route.params.id, () => { if (route.params.id) loadAsset() })
</script>

<style scoped>
.topology-header {
  display: flex;
  align-items: center;
}
.topology-container {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  min-height: 500px;
  position: relative;
  background: #fafafa;
}
.topology-canvas {
  width: 100%;
  height: 500px;
}
.topology-svg {
  width: 100%;
  height: 100%;
}
.topology-node {
  cursor: pointer;
}
.topology-node:hover rect {
  filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));
}
.empty-topology {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 400px;
}
</style>
