<template>
  <div class="page-container">
    <div class="toolbar">
      <el-select v-model="relationFilter" placeholder="关系类型" clearable style="width:150px;margin-right:8px">
        <el-option label="依赖" value="depends_on" /><el-option label="包含" value="contains" />
        <el-option label="连接" value="connected_to" /><el-option label="承载" value="hosts" />
        <el-option label="备份" value="backs_up" />
      </el-select>
      <el-select v-model="typeFilter" placeholder="资产类型" clearable style="width:150px;margin-right:8px">
        <el-option label="Linux" value="linux_server" /><el-option label="Windows" value="windows_server" />
        <el-option label="数据库" value="database" /><el-option label="Web服务" value="web_service" />
        <el-option label="网络设备" value="network_device" />
      </el-select>
      <el-button type="primary" @click="loadTopology"><el-icon><Search /></el-icon> 加载拓扑</el-button>
      <el-button @click="toggleImpactMode" :type="impactMode?'warning':''">
        <el-icon><Warning /></el-icon> {{ impactMode ? '退出影响分析' : '影响分析模式' }}
      </el-button>
      <div style="flex:1" />
      <el-button @click="zoomIn">放大</el-button>
      <el-button @click="zoomOut">缩小</el-button>
      <el-button @click="resetView">重置</el-button>
    </div>

    <!-- 影响分析面板 -->
    <el-alert v-if="impactMode && selectedNode" type="warning" :closable="false" style="margin-bottom:12px">
      <template #title>影响分析: {{ selectedNode.name }} ({{ selectedNode.asset_type }})</template>
      <div>直接依赖: <strong>{{ impactAnalysis.directDeps }}</strong> 个 | 间接依赖: <strong>{{ impactAnalysis.indirectDeps }}</strong> 个 | 影响服务: <strong>{{ impactAnalysis.affectedServices }}</strong> 个</div>
    </el-alert>

    <!-- SVG 拓扑画布 -->
    <div class="topology-canvas" ref="canvasRef" @mousedown="startDrag" @mousemove="onDrag" @mouseup="endDrag" @mouseleave="endDrag" @wheel="onWheel">
      <svg :width="canvasW" :height="canvasH" :viewBox="`${viewX} ${viewY} ${canvasW/zoom} ${canvasH/zoom}`" style="background:#fafbfc">
        <defs>
          <marker id="arrow" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto"><polygon points="0 0, 10 3.5, 0 7" fill="#c0c4cc" /></marker>
          <marker id="arrow-red" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto"><polygon points="0 0, 10 3.5, 0 7" fill="#f56c6c" /></marker>
        </defs>

        <!-- 连线 -->
        <g v-for="(edge, i) in filteredEdges" :key="'e'+i">
          <line :x1="getNode(edge.source_id)?.x||0" :y1="getNode(edge.source_id)?.y||0"
                :x2="getNode(edge.target_id)?.x||0" :y2="getNode(edge.target_id)?.y||0"
                :stroke="isImpactEdge(edge)?'#f56c6c':'#c0c4cc'" stroke-width="2"
                :marker-end="isImpactEdge(edge)?'url(#arrow-red)':'url(#arrow)'" />
          <text :x="(getNode(edge.source_id)?.x+getNode(edge.target_id)?.x)/2"
                :y="(getNode(edge.source_id)?.y+getNode(edge.target_id)?.y)/2 - 5"
                font-size="10" fill="#909399" text-anchor="middle">{{ edge.relation_type }}</text>
        </g>

        <!-- 节点 -->
        <g v-for="node in filteredNodes" :key="node.id" :transform="`translate(${node.x},${node.y})`" @click.stop="selectNode(node)" style="cursor:pointer">
          <rect :x="-60" :y="-25" width="120" height="50" rx="8"
                :fill="node.id===selectedNode?.id?'#409eff':isImpactNode(node)?'#f56c6c':typeColor(node.asset_type)"
                :stroke="node.id===selectedNode?.id?'#2d7de6':'#ddd'" stroke-width="2" />
          <text x="0" y="-5" text-anchor="middle" fill="#fff" font-size="12" font-weight="bold">{{ node.name?.substring(0,10) }}</text>
          <text x="0" y="12" text-anchor="middle" fill="rgba(255,255,255,0.8)" font-size="9">{{ node.asset_type }}</text>
        </g>
      </svg>
    </div>

    <!-- 节点详情面板 -->
    <el-drawer v-model="showNodeDetail" :title="selectedNode?.name||'节点详情'" size="420px" direction="rtl">
      <template v-if="selectedNode">
        <el-descriptions :column="1" border size="small">
          <el-descriptions-item label="名称">{{ selectedNode.name }}</el-descriptions-item>
          <el-descriptions-item label="类型"><el-tag size="small">{{ selectedNode.asset_type }}</el-tag></el-descriptions-item>
          <el-descriptions-item label="IP">{{ selectedNode.ip_address || '-' }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="selectedNode.status==='healthy'?'success':selectedNode.status==='warning'?'warning':'danger'" size="small">
              {{ selectedNode.status || 'unknown' }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <h4 style="margin:12px 0 8px">关联关系 ({{ nodeRelations.length }})</h4>
        <el-table :data="nodeRelations" stripe size="small">
          <el-table-column prop="relation_type" label="类型" width="90" />
          <el-table-column label="目标" min-width="120">
            <template #default="{ row }">{{ row.source_id===selectedNode.id ? getTargetName(row.target_id) : getTargetName(row.source_id) }}</template>
          </el-table-column>
          <el-table-column label="方向" width="70">
            <template #default="{ row }">{{ row.source_id===selectedNode.id ? '→出' : '←入' }}</template>
          </el-table-column>
        </el-table>

        <div style="margin-top:12px;display:flex;gap:8px">
          <el-button size="small" type="primary" @click="viewAsset">查看资产详情</el-button>
          <el-button size="small" type="warning" @click="startImpact">影响分析</el-button>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search, Warning } from '@element-plus/icons-vue'
import api from '@/shared/api/client'
import { API } from '@/shared/api/routes'

const router = useRouter()
const route = useRoute()

const nodes = ref<any[]>([])
const edges = ref<any[]>([])
const selectedNode = ref<any>(null)
const showNodeDetail = ref(false)
const relationFilter = ref('')
const typeFilter = ref('')
const impactMode = ref(false)

const canvasRef = ref<HTMLElement>()
const canvasW = ref(1200)
const canvasH = ref(600)
const viewX = ref(-100)
const viewY = ref(-50)
const zoom = ref(1)
const dragging = ref(false)
const dragStart = reactive({ x: 0, y: 0 })
const impactAnalysis = reactive({ directDeps: 0, indirectDeps: 0, affectedServices: 0 })
const impactNodes = ref<Set<string>>(new Set())
const impactEdges = ref<Set<number>>(new Set())

const filteredNodes = computed(() => {
  let result = nodes.value
  if (typeFilter.value) result = result.filter(n => n.asset_type === typeFilter.value)
  if (impactMode.value && impactNodes.value.size) result = result.filter(n => impactNodes.value.has(n.id) || n.id === selectedNode.value?.id)
  return result
})

const filteredEdges = computed(() => {
  let result = edges.value
  if (relationFilter.value) result = result.filter(e => e.relation_type === relationFilter.value)
  if (impactMode.value && impactNodes.value.size) {
    result = result.filter(e => impactNodes.value.has(e.source_id) && impactNodes.value.has(e.target_id))
  }
  return result
})

const nodeRelations = computed(() => {
  if (!selectedNode.value) return []
  return edges.value.filter(e => e.source_id === selectedNode.value.id || e.target_id === selectedNode.value.id)
})

function getNode(id: string) { return nodes.value.find(n => n.id === id) }
function getTargetName(id: string) { const n = getNode(id); return n?.name || id }
function isImpactEdge(edge: any) { return impactMode.value && impactEdges.value.has(edges.value.indexOf(edge)) }
function isImpactNode(node: any) { return impactMode.value && impactNodes.value.has(node.id) && node.id !== selectedNode.value?.id }

function typeColor(t: string) {
  return ({ linux_server:'#67c23a', windows_server:'#409eff', database:'#e6a23c', web_service:'#909399', network_device:'#9b59b6', security_device:'#f56c6c' })[t] || '#606266'
}

async function loadTopology() {
  try {
    const assetId = route.params.id as string
    const res = await api.get(assetId ? API.ASSET_RELATIONS(assetId) : API.ASSETS, { params: { page_size: 200 } })
    if (res.data?.code === 0) {
      const data = res.data.data
      if (assetId && data?.relations) {
        edges.value = data.relations || []
        const nodeIds = new Set<string>()
        edges.value.forEach((e: any) => { nodeIds.add(e.source_id); nodeIds.add(e.target_id) })
        const assetsRes = await api.get(API.ASSETS, { params: { page_size: 200 } })
        const allAssets = assetsRes.data?.data?.items || assetsRes.data?.data || []
        nodes.value = allAssets.filter((a: any) => nodeIds.has(a.id)).map((a: any, i: number) => ({
          ...a, x: a.x || (200 + (i % 5) * 200), y: a.y || (150 + Math.floor(i / 5) * 120),
        }))
      } else {
        const items = data?.items || data || []
        nodes.value = items.map((a: any, i: number) => ({
          ...a, x: a.x || (150 + (i % 6) * 180), y: a.y || (120 + Math.floor(i / 6) * 110),
        }))
        const relPromises = items.slice(0, 30).map((a: any) => api.get(API.ASSET_RELATIONS(a.id)).catch(() => null))
        const relResults = await Promise.all(relPromises)
        edges.value = relResults.filter(Boolean).flatMap((r: any) => r.data?.data?.relations || r.data?.data || [])
        const seen = new Set<string>()
        edges.value = edges.value.filter((e: any) => {
          const key = `${e.source_id}-${e.target_id}-${e.relation_type}`
          if (seen.has(key)) return false; seen.add(key); return true
        })
      }
    }
  } catch { ElMessage.error('加载拓扑失败') }
}

function selectNode(node: any) {
  selectedNode.value = node
  showNodeDetail.value = true
}

function viewAsset() {
  if (selectedNode.value?.id) router.push(`/assets/${selectedNode.value.id}`)
}

function startImpact() {
  impactMode.value = true
  showNodeDetail.value = false
  computeImpact()
}

function toggleImpactMode() {
  impactMode.value = !impactMode.value
  if (impactMode.value && selectedNode.value) computeImpact()
  else { impactNodes.value = new Set(); impactEdges.value = new Set() }
}

function computeImpact() {
  if (!selectedNode.value) return
  const visited = new Set<string>()
  const queue = [selectedNode.value.id]
  visited.add(selectedNode.value.id)
  const impactedEdges = new Set<number>()
  while (queue.length) {
    const current = queue.shift()!
    edges.value.forEach((e: any, idx: number) => {
      if (e.source_id === current && !visited.has(e.target_id)) {
        visited.add(e.target_id); queue.push(e.target_id); impactedEdges.add(idx)
      } else if (e.target_id === current && !visited.has(e.source_id)) {
        visited.add(e.source_id); queue.push(e.source_id); impactedEdges.add(idx)
      }
    })
  }
  impactNodes.value = visited
  impactEdges.value = impactedEdges
  impactAnalysis.directDeps = edges.value.filter((e: any) => e.source_id === selectedNode.value.id || e.target_id === selectedNode.value.id).length
  impactAnalysis.indirectDeps = visited.size - 1 - impactAnalysis.directDeps
  impactAnalysis.affectedServices = nodes.value.filter(n => visited.has(n.id) && ['web_service','database'].includes(n.asset_type)).length
}

// Canvas interactions
function startDrag(e: MouseEvent) { dragging.value = true; dragStart.x = e.clientX; dragStart.y = e.clientY }
function onDrag(e: MouseEvent) {
  if (!dragging.value) return
  viewX.value -= (e.clientX - dragStart.x) / zoom.value
  viewY.value -= (e.clientY - dragStart.y) / zoom.value
  dragStart.x = e.clientX; dragStart.y = e.clientY
}
function endDrag() { dragging.value = false }
function onWheel(e: WheelEvent) { e.preventDefault(); zoom.value = Math.max(0.3, Math.min(3, zoom.value + (e.deltaY > 0 ? -0.1 : 0.1))) }
function zoomIn() { zoom.value = Math.min(3, zoom.value + 0.2) }
function zoomOut() { zoom.value = Math.max(0.3, zoom.value - 0.2) }
function resetView() { zoom.value = 1; viewX.value = -100; viewY.value = -50 }

onMounted(() => { loadTopology() })
</script>

<style scoped>
.page-container { padding: 20px; }
.toolbar { margin-bottom: 16px; display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.topology-canvas { border: 1px solid #e4e7ed; border-radius: 8px; overflow: hidden; cursor: grab; user-select: none; }
.topology-canvas:active { cursor: grabbing; }
</style>
