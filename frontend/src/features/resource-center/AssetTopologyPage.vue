<template>
  <div class="autops-page-container">
    <PageHeader title="拓扑视图" />

    <!-- 统计卡片 -->
    <el-row :gutter="12" class="stat-row mb-md">
      <el-col :span="4"><el-card shadow="hover" class="autops-metric-card"><div class="stat-value">{{ nodes.length }}</div><div class="stat-label">节点总数</div></el-card></el-col>
      <el-col :span="4"><el-card shadow="hover" class="stat-card success"><div class="stat-value">{{ edges.length }}</div><div class="stat-label">关系总数</div></el-card></el-col>
      <el-col :span="4"><el-card shadow="hover" class="stat-card primary"><div class="stat-value">{{ healthyCount }}</div><div class="stat-label">健康节点</div></el-card></el-col>
      <el-col :span="4"><el-card shadow="hover" class="stat-card warning"><div class="stat-value">{{ warningCount }}</div><div class="stat-label">告警节点</div></el-card></el-col>
      <el-col :span="4"><el-card shadow="hover" class="stat-card danger"><div class="stat-value">{{ criticalCount }}</div><div class="stat-label">故障节点</div></el-card></el-col>
      <el-col :span="4"><el-card shadow="hover" class="autops-metric-card"><div class="stat-value">{{ typeCount }}</div><div class="stat-label">资产类型</div></el-card></el-col>
    </el-row>

    <!-- 工具栏 -->
    <div class="autops-toolbar">
      <el-select v-model="relationFilter" placeholder="关系类型" clearable style="width:150px;margin-right:8px">
        <el-option label="依赖" value="depends_on" /><el-option label="包含" value="contains" />
        <el-option label="连接" value="connected_to" /><el-option label="承载" value="hosts" />
        <el-option label="备份" value="backs_up" />
      </el-select>
      <el-select v-model="typeFilter" placeholder="资产类型" clearable style="width:150px;margin-right:8px">
        <el-option label="Linux" value="linux_server" /><el-option label="Windows" value="windows_server" />
        <el-option label="数据库" value="database" /><el-option label="Web服务" value="web_service" />
        <el-option label="网络设备" value="network_device" /><el-option label="安全设备" value="security_device" />
      </el-select>
      <el-input v-model="searchKeyword" placeholder="搜索节点名称/IP" clearable style="width:180px;margin-right:8px" @input="onSearch" />
      <el-button type="primary" @click="loadTopology"><el-icon><Search /></el-icon> 加载拓扑</el-button>
      <el-button @click="autoLayout"><el-icon><Grid /></el-icon> 自动布局</el-button>
      <el-button @click="toggleImpactMode" :type="impactMode?'warning':''">
        <el-icon><Warning /></el-icon> {{ impactMode ? '退出影响分析' : '影响分析' }}
      </el-button>
      <div style="flex:1" />
      <el-button-group>
        <el-button @click="zoomIn" title="放大"><el-icon><ZoomIn /></el-icon></el-button>
        <el-button @click="zoomOut" title="缩小"><el-icon><ZoomOut /></el-icon></el-button>
        <el-button @click="fitView" title="适应画布"><el-icon><FullScreen /></el-icon></el-button>
        <el-button @click="resetView" title="重置">1:1</el-button>
      </el-button-group>
    </div>

    <!-- 影响分析面板 -->
    <el-alert v-if="impactMode && selectedNode" type="warning" :closable="false" style="margin-bottom:12px">
      <template #title>
        <span style="font-weight:bold">影响分析: {{ selectedNode.name }} ({{ selectedNode.asset_type }})</span>
      </template>
      <div style="display:flex;gap:24px;margin-top:4px">
        <span>直接依赖: <strong style="color:#f53f3f">{{ impactAnalysis.directDeps }}</strong></span>
        <span>间接依赖: <strong style="color:#ff7d00">{{ impactAnalysis.indirectDeps }}</strong></span>
        <span>影响服务: <strong style="color:#f53f3f">{{ impactAnalysis.affectedServices }}</strong></span>
        <span>影响路径: <strong>{{ impactAnalysis.totalPaths }}</strong> 条</span>
      </div>
      <div v-if="impactAffectedList.length" style="margin-top:8px">
        <span style="color:#86909c;font-size:13px">受影响节点：</span>
        <el-tag v-for="n in impactAffectedList" :key="n.id" :type="n.health_status==='healthy'?'info':'danger'" size="small" style="margin:2px">{{ n.name }}</el-tag>
      </div>
    </el-alert>

    <el-row :gutter="12">
      <!-- 拓扑画布 -->
      <el-col :span="18">
        <div class="topology-canvas" ref="canvasRef" @mousedown="startDrag" @mousemove="onDrag" @mouseup="endDrag" @mouseleave="endDrag" @wheel.prevent="onWheel">
          <svg :width="canvasW" :height="canvasH" :viewBox="viewX + ' ' + viewY + ' ' + canvasW/zoom + ' ' + canvasH/zoom" style="background:#fafbfc">
            <defs>
              <marker id="arrow" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto"><polygon points="0 0, 10 3.5, 0 7" fill="#c9cdd4" /></marker>
              <marker id="arrow-red" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto"><polygon points="0 0, 10 3.5, 0 7" fill="#f53f3f" /></marker>
              <marker id="arrow-highlight" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto"><polygon points="0 0, 10 3.5, 0 7" fill="#165dff" /></marker>
              <filter id="glow"><feGaussianBlur stdDeviation="3" result="blur" /><feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge></filter>
              <filter id="shadow"><feDropShadow dx="1" dy="1" stdDeviation="2" flood-color="#00000020" /></filter>
            </defs>

            <!-- Grid background -->
            <pattern id="grid" width="50" height="50" patternUnits="userSpaceOnUse">
              <path d="M 50 0 L 0 0 0 50" fill="none" stroke="#f0f0f0" stroke-width="0.5"/>
            </pattern>
            <rect :x="viewX - 500" :y="viewY - 500" :width="canvasW/zoom + 1000" :height="canvasH/zoom + 1000" fill="url(#grid)" />

            <!-- 连线 -->
            <g v-for="(edge, i) in filteredEdges" :key="'e'+i">
              <line :x1="getNode(edge.source_id)?.x||0" :y1="getNode(edge.source_id)?.y||0"
                    :x2="getNode(edge.target_id)?.x||0" :y2="getNode(edge.target_id)?.y||0"
                    :stroke="getEdgeColor(edge)" :stroke-width="isImpactEdge(edge)?3:isSearchEdge(edge)?2.5:1.5"
                    :stroke-dasharray="edge.relation_type==='backs_up'?'6,3':''"
                    :marker-end="isImpactEdge(edge)?'url(#arrow-red)':isSearchEdge(edge)?'url(#arrow-highlight)':'url(#arrow)'" />
              <text :x="(getNode(edge.source_id)?.x+getNode(edge.target_id)?.x)/2"
                    :y="(getNode(edge.source_id)?.y+getNode(edge.target_id)?.y)/2 - 6"
                    font-size="9" :fill="isImpactEdge(edge)?'#f53f3f':'#b0b0b0'" text-anchor="middle">
                {{ relationLabel(edge.relation_type) }}
              </text>
            </g>

            <!-- 节点 -->
            <g v-for="node in filteredNodes" :key="node.id" :transform="'translate(' + node.x + ',' + node.y + ')'" @click.stop="selectNode(node)" style="cursor:pointer">
              <rect :x="-65" :y="-28" width="130" height="56" rx="10"
                    :fill="getNodeFill(node)" :stroke="getNodeStroke(node)"
                    :stroke-width="isHighlighted(node)?3:node.id===selectedNode?.id?2.5:1.5"
                    :filter="isHighlighted(node)?'url(#glow)':'url(#shadow)'" />
              <!-- 健康状态指示灯 -->
              <circle cx="-50" cy="-14" r="4" :fill="healthColor(node.health_status || node.status)" />
              <text x="0" y="-6" text-anchor="middle" fill="#fff" font-size="11" font-weight="bold">{{ truncate(node.name, 10) }}</text>
              <text x="0" y="10" text-anchor="middle" fill="rgba(255,255,255,0.75)" font-size="9">{{ typeLabel(node.asset_type) }}</text>
              <text x="0" y="22" text-anchor="middle" fill="rgba(255,255,255,0.6)" font-size="8">{{ node.ip || node.ip_address || '' }}</text>
            </g>
          </svg>

          <!-- 缩放指示器 -->
          <div class="zoom-indicator">{{ Math.round(zoom * 100) }}%</div>
        </div>
      </el-col>

      <!-- 右侧面板 -->
      <el-col :span="6">
        <!-- 图例 -->
        <div class="autops-card">
          <div class="autops-card-header">
            <span class="autops-card-title">图例</span>
          </div>
          <div class="autops-card-body legend-card">
          <div class="legend-section">
            <div class="legend-title">资产类型</div>
            <div v-for="(color, type) in typeColors" :key="type" class="legend-item">
              <span class="legend-dot" :style="{background:color}"></span> {{ typeLabel(type as string) }}
            </div>
          </div>
          <div class="legend-section">
            <div class="legend-title">健康状态</div>
            <div class="legend-item"><span class="legend-dot" style="background:#00b42a"></span> 健康</div>
            <div class="legend-item"><span class="legend-dot" style="background:#ff7d00"></span> 告警</div>
            <div class="legend-item"><span class="legend-dot" style="background:#f53f3f"></span> 故障</div>
            <div class="legend-item"><span class="legend-dot" style="background:#86909c"></span> 未知</div>
          </div>
          <div class="legend-section">
            <div class="legend-title">关系类型</div>
            <div class="legend-item"><span class="legend-line"></span> 依赖</div>
            <div class="legend-item"><span class="legend-line" style="border-top:2px dashed #c9cdd4"></span> 备份</div>
            <div class="legend-item"><span class="legend-line" style="border-top:2px solid #f53f3f"></span> 影响路径</div>
          </div>
          </div>
        </div>

        <!-- 节点快速信息 -->
        <div v-if="selectedNode" class="autops-card" style="margin-top:12px">
          <div class="autops-card-header">
            <span class="autops-card-title">{{ selectedNode.name }}</span>
            <el-tag :type="(healthTagType(selectedNode.health_status || selectedNode.status)) as TagType" size="small">{{ selectedNode.health_status || selectedNode.status || 'unknown' }}</el-tag>
          </div>
          <div class="autops-card-body">
          <el-descriptions :column="1" size="small" border>
            <el-descriptions-item label="类型">{{ typeLabel(selectedNode.asset_type) }}</el-descriptions-item>
            <el-descriptions-item label="IP">{{ selectedNode.ip_address || '-' }}</el-descriptions-item>
            <el-descriptions-item label="关联数">{{ nodeRelations.length }}</el-descriptions-item>
          </el-descriptions>

          <h4 style="margin:10px 0 6px;font-size:13px">关联关系</h4>
          <el-table stripe :data="nodeRelations"size="small" max-height="200">
            <el-table-column prop="relation_type" label="类型" width="70">
              <template #default="{ row }">{{ relationLabel(row.relation_type) }}</template>
            </el-table-column>
            <el-table-column label="目标" min-width="100">
              <template #default="{ row }">
                <el-link type="primary" @click="jumpToNode(row.source_id===selectedNode.id?row.target_id:row.source_id)">
                  {{ getTargetName(row.source_id===selectedNode.id?row.target_id:row.source_id) }}
                </el-link>
              </template>
            </el-table-column>
            <el-table-column label="方向" width="40">
              <template #default="{ row }">{{ row.source_id===selectedNode.id ? '→' : '←' }}</template>
            </el-table-column>
          </el-table>

          <div style="margin-top:10px;display:flex;gap:6px">
            <el-button size="small" type="primary" @click="viewAsset">查看详情</el-button>
            <el-button size="small" type="warning" @click="startImpact">影响分析</el-button>
          </div>
          </div>
        </div>

        <!-- 小地图 -->
        <div class="autops-card" style="margin-top:12px">
          <div class="autops-card-header">
            <span class="autops-card-title">导航</span>
          </div>
          <div class="autops-card-body">
          <div class="minimap" ref="minimapRef">
            <svg width="100%" height="120" :viewBox="String(minimapViewBox)">
              <g v-for="node in filteredNodes" :key="'m'+node.id">
                <circle :cx="node.x" :cy="node.y" r="4"
                  :fill="node.id===selectedNode?.id?'#165dff':isImpactNode(node)?'#f53f3f':typeColor(node.asset_type)" />
              </g>
              <g v-for="(edge, i) in filteredEdges" :key="'me'+i">
                <line :x1="getNode(edge.source_id)?.x||0" :y1="getNode(edge.source_id)?.y||0"
                      :x2="getNode(edge.target_id)?.x||0" :y2="getNode(edge.target_id)?.y||0"
                      stroke="#ddd" stroke-width="0.5" />
              </g>
            </svg>
          </div>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import type { TagType } from '@/shared/types'
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search, Warning, ZoomIn, ZoomOut, FullScreen, Grid } from '@element-plus/icons-vue'
import PageHeader from '@/shared/components/PageHeader.vue'
import api from '@/shared/api/client'
import { API } from '@/shared/api/routes'

const router = useRouter()
const route = useRoute()

const nodes = ref<any[]>([])
const edges = ref<any[]>([])
const selectedNode = ref<any>(null)
const relationFilter = ref('')
const typeFilter = ref('')
const searchKeyword = ref('')
const impactMode = ref(false)

const canvasRef = ref<HTMLElement>()
const minimapRef = ref<HTMLElement>()
const canvasW = ref(900)
const canvasH = ref(550)
const viewX = ref(-100)
const viewY = ref(-50)
const zoom = ref(1)
const dragging = ref(false)
const dragStart = reactive({ x: 0, y: 0 })
const impactAnalysis = reactive({ directDeps: 0, indirectDeps: 0, affectedServices: 0, totalPaths: 0 })
const impactNodes = ref<Set<string>>(new Set())
const impactEdges = ref<Set<number>>(new Set())
const searchMatchNodes = ref<Set<string>>(new Set())

const typeColors: Record<string, string> = {
  linux_server: '#00b42a', windows_server: '#165dff', database: '#ff7d00',
  web_service: '#86909c', network_device: '#9b59b6', security_device: '#f53f3f',
}

const healthyCount = computed(() => nodes.value.filter(n => (n.health_status || n.status) === 'healthy').length)
const warningCount = computed(() => nodes.value.filter(n => (n.health_status || n.status) === 'warning').length)
const criticalCount = computed(() => nodes.value.filter(n => (n.health_status || n.status) === 'critical').length)
const typeCount = computed(() => new Set(nodes.value.map(n => n.asset_type)).size)
const impactAffectedList = computed(() => nodes.value.filter(n => impactNodes.value.has(n.id) && n.id !== selectedNode.value?.id))

const filteredNodes = computed(() => {
  let result = nodes.value
  if (typeFilter.value) result = result.filter(n => n.asset_type === typeFilter.value)
  if (impactMode.value && impactNodes.value.size) result = result.filter(n => impactNodes.value.has(n.id) || n.id === selectedNode.value?.id)
  return result
})

const filteredEdges = computed(() => {
  let result = edges.value
  if (relationFilter.value) result = result.filter(e => e.relation_type === relationFilter.value)
  if (impactMode.value && impactNodes.value.size) result = result.filter(e => impactNodes.value.has(e.source_id) && impactNodes.value.has(e.target_id))
  return result
})

const nodeRelations = computed(() => {
  if (!selectedNode.value) return []
  return edges.value.filter(e => e.source_id === selectedNode.value.id || e.target_id === selectedNode.value.id)
})

const minimapViewBox = computed(() => {
  if (!nodes.value.length) return '0 0 100 100'
  const xs = nodes.value.map(n => n.x)
  const ys = nodes.value.map(n => n.y)
  const minX = Math.min(...xs) - 20, maxX = Math.max(...xs) + 20
  const minY = Math.min(...ys) - 20, maxY = Math.max(...ys) + 20
  return `${minX} ${minY} ${maxX - minX} ${maxY - minY}`
})

function getNode(id: string) { return nodes.value.find(n => n.id === id) }
function getTargetName(id: string) { const n = getNode(id); return n?.name || id.substring(0, 8) }
function isImpactEdge(edge: any) { return impactMode.value && impactEdges.value.has(edges.value.indexOf(edge)) }
function isImpactNode(node: any) { return impactMode.value && impactNodes.value.has(node.id) && node.id !== selectedNode.value?.id }
function isHighlighted(node: any) { return searchMatchNodes.value.has(node.id) || node.id === selectedNode?.value?.id }
function isSearchEdge(edge: any) { return searchMatchNodes.value.has(edge.source_id) && searchMatchNodes.value.has(edge.target_id) }

function typeColor(t: string) { return typeColors[t] || '#4e5969' }
function typeLabel(t: string) { return ({ linux_server:'Linux', windows_server:'Windows', database:'数据库', web_service:'Web服务', network_device:'网络设备', security_device:'安全设备' })[t] || t }
function relationLabel(r: string) { return ({ depends_on:'依赖', contains:'包含', connected_to:'连接', hosts:'承载', backs_up:'备份' })[r] || r }
function healthColor(s: string) { return ({ healthy:'#00b42a', warning:'#ff7d00', critical:'#f53f3f' })[s] || '#86909c' }
function healthTagType(s: string): TagType { return (({ healthy:'success', warning:'warning', critical:'danger' })[s] ?? 'info') as TagType }
function truncate(s: string, n: number) { return s?.length > n ? s.substring(0, n) + '…' : s || '' }

function getNodeFill(node: any) {
  if (node.id === selectedNode.value?.id) return '#165dff'
  if (isImpactNode(node)) return '#f53f3f'
  if (searchMatchNodes.value.has(node.id)) return '#3399ff'
  return typeColor(node.asset_type)
}

function getNodeStroke(node: any) {
  if (node.id === selectedNode.value?.id) return '#2d7de6'
  if (searchMatchNodes.value.has(node.id)) return '#1a8cff'
  return '#ddd'
}

function getEdgeColor(edge: any) {
  if (isImpactEdge(edge)) return '#f53f3f'
  if (isSearchEdge(edge)) return '#165dff'
  return '#d0d0d0'
}

function onSearch() {
  if (!searchKeyword.value) { searchMatchNodes.value = new Set(); return }
  const kw = searchKeyword.value.toLowerCase()
  searchMatchNodes.value = new Set(
    nodes.value.filter(n => n.name?.toLowerCase().includes(kw) || (n.ip || n.ip_address)?.includes(kw)).map(n => n.id)
  )
}

function jumpToNode(id: string) {
  const node = getNode(id)
  if (node) {
    selectedNode.value = node
    viewX.value = node.x - canvasW.value / zoom.value / 2
    viewY.value = node.y - canvasH.value / zoom.value / 2
  }
}

async function loadTopology() {
  try {
    const assetId = route.params.id as string
    const res = await api.get(assetId ? API.ASSET_RELATIONS(assetId) : API.ASSETS, { params: { page_size: 100 } })
    if (res.data?.code === 0) {
      const data = res.data.data
      if (assetId && data?.relations) {
        edges.value = data.relations || []
        const nodeIds = new Set<string>()
        edges.value.forEach((e: any) => { nodeIds.add(e.source_id); nodeIds.add(e.target_id) })
        const assetsRes = await api.get(API.ASSETS, { params: { page_size: 100 } })
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
          const key = e.source_id + '-' + e.target_id + '-' + e.relation_type
          if (seen.has(key)) return false; seen.add(key); return true
        })
      }
      ElMessage.success('加载 ' + nodes.value.length + ' 个节点, ' + edges.value.length + ' 条关系')
    }
  } catch { ElMessage.error('加载拓扑失败') }
}

function autoLayout() {
  const centerX = nodes.value.reduce((a, n) => a + n.x, 0) / (nodes.value.length || 1)
  const centerY = nodes.value.reduce((a, n) => a + n.y, 0) / (nodes.value.length || 1)
  // Simple force-directed layout: push connected nodes apart
  for (let iter = 0; iter < 50; iter++) {
    const positions = nodes.value.map(n => ({ x: n.x, y: n.y, fx: 0, fy: 0 }))
    // Repulsion between all pairs
    for (let i = 0; i < positions.length; i++) {
      for (let j = i + 1; j < positions.length; j++) {
        const dx = positions[i].x - positions[j].x
        const dy = positions[i].y - positions[j].y
        const dist = Math.sqrt(dx * dx + dy * dy) || 1
        const force = 2000 / (dist * dist)
        const fx = (dx / dist) * force, fy = (dy / dist) * force
        positions[i].fx += fx; positions[i].fy += fy
        positions[j].fx -= fx; positions[j].fy -= fy
      }
    }
    // Attraction along edges
    edges.value.forEach(e => {
      const si = nodes.value.findIndex(n => n.id === e.source_id)
      const ti = nodes.value.findIndex(n => n.id === e.target_id)
      if (si >= 0 && ti >= 0) {
        const dx = positions[ti].x - positions[si].x
        const dy = positions[ti].y - positions[si].y
        const dist = Math.sqrt(dx * dx + dy * dy) || 1
        const force = (dist - 200) * 0.05
        positions[si].fx += (dx / dist) * force; positions[si].fy += (dy / dist) * force
        positions[ti].fx -= (dx / dist) * force; positions[ti].fy -= (dy / dist) * force
      }
    })
    positions.forEach((p, i) => {
      nodes.value[i].x += Math.max(-20, Math.min(20, p.fx))
      nodes.value[i].y += Math.max(-20, Math.min(20, p.fy))
    })
  }
  ElMessage.success('自动布局完成')
}

function selectNode(node: any) {
  selectedNode.value = node
}

function viewAsset() {
  if (selectedNode.value?.id) router.push('/assets/' + selectedNode.value.id)
}

function startImpact() {
  impactMode.value = true
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
  let pathCount = 0
  while (queue.length) {
    const current = queue.shift()!
    edges.value.forEach((e: any, idx: number) => {
      if (e.source_id === current && !visited.has(e.target_id)) {
        visited.add(e.target_id); queue.push(e.target_id); impactedEdges.add(idx); pathCount++
      } else if (e.target_id === current && !visited.has(e.source_id)) {
        visited.add(e.source_id); queue.push(e.source_id); impactedEdges.add(idx); pathCount++
      }
    })
  }
  impactNodes.value = visited
  impactEdges.value = impactedEdges
  impactAnalysis.directDeps = edges.value.filter((e: any) => e.source_id === selectedNode.value.id || e.target_id === selectedNode.value.id).length
  impactAnalysis.indirectDeps = visited.size - 1 - impactAnalysis.directDeps
  impactAnalysis.affectedServices = nodes.value.filter(n => visited.has(n.id) && ['web_service', 'database'].includes(n.asset_type)).length
  impactAnalysis.totalPaths = pathCount
}

function startDrag(e: MouseEvent) { dragging.value = true; dragStart.x = e.clientX; dragStart.y = e.clientY }
function onDrag(e: MouseEvent) {
  if (!dragging.value) return
  viewX.value -= (e.clientX - dragStart.x) / zoom.value
  viewY.value -= (e.clientY - dragStart.y) / zoom.value
  dragStart.x = e.clientX; dragStart.y = e.clientY
}
function endDrag() { dragging.value = false }
function onWheel(e: WheelEvent) { zoom.value = Math.max(0.3, Math.min(3, zoom.value + (e.deltaY > 0 ? -0.1 : 0.1))) }
function zoomIn() { zoom.value = Math.min(3, zoom.value + 0.2) }
function zoomOut() { zoom.value = Math.max(0.3, zoom.value - 0.2) }
function resetView() { zoom.value = 1; viewX.value = -100; viewY.value = -50 }
function fitView() {
  if (!nodes.value.length) return
  const xs = nodes.value.map(n => n.x), ys = nodes.value.map(n => n.y)
  const minX = Math.min(...xs) - 100, maxX = Math.max(...xs) + 100
  const minY = Math.min(...ys) - 80, maxY = Math.max(...ys) + 80
  const scaleX = canvasW.value / (maxX - minX), scaleY = canvasH.value / (maxY - minY)
  zoom.value = Math.min(scaleX, scaleY, 2)
  viewX.value = minX; viewY.value = minY
}

onMounted(() => {
  if (canvasRef.value) { canvasW.value = canvasRef.value.clientWidth; canvasH.value = 550 }
  loadTopology()
})
</script>

<style scoped>
.stat-row { margin-bottom: var(--autops-space-lg); }
.autops-metric-card 
.autops-metric-card.success .stat-value { color: var(--autops-success); }
.autops-metric-card.primary .stat-value { color: var(--autops-primary); }
.autops-metric-card.warning .stat-value { color: var(--autops-warning); }
.autops-metric-card.danger .stat-value { color: var(--autops-danger); }
.autops-metric-card 
.toolbar { margin-bottom: var(--autops-space-md); display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.topology-canvas { border: 1px solid var(--autops-bg-4); border-radius: var(--autops-radius-md); overflow: hidden; cursor: grab; user-select: none; position: relative; }
.topology-canvas:active { cursor: grabbing; }
.zoom-indicator { position: absolute; bottom: 8px; right: 8px; background: rgba(0,0,0,0.5); color: var(--autops-bg-1); padding: 2px 8px; border-radius: var(--autops-radius-sm); font-size: var(--autops-font-12); }

.legend-card { font-size: var(--autops-font-13); }
.legend-section { margin-bottom: 10px; }
.legend-section:last-child { margin-bottom: 0; }
.legend-title { font-weight: bold; color: var(--autops-text-2); margin-bottom: 4px; font-size: var(--autops-font-12); }
.legend-item { display: flex; align-items: center; gap: 6px; padding: 2px 0; font-size: var(--autops-font-12); color: var(--autops-text-2); }
.legend-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
.legend-line { width: 20px; border-top: 2px solid var(--autops-text-4); display: inline-block; }

.minimap { background: var(--autops-bg-2); border-radius: var(--autops-radius-sm); border: 1px solid var(--autops-bg-4); }
</style>
