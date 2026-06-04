<template>
  <div class="topology-graph" :style="{ width: '100%', height: height, border: '1px solid #e5e6eb', borderRadius: '6px', position: 'relative' }">
    <div v-if="!nodes.length" :style="{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#999' }">暂无拓扑数据</div>
    <svg v-else :width="'100%'" :height="height" :viewBox="'0 0 ' + svgWidth + ' ' + svgHeight">
      <defs>
        <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto">
          <polygon points="0 0, 10 3.5, 0 7" fill="#c9cdd4" />
        </marker>
      </defs>
      <line v-for="edge in edges" :key="'e-' + edge.source + '-' + edge.target"
        :x1="getNodePos(edge.source).x" :y1="getNodePos(edge.source).y"
        :x2="getNodePos(edge.target).x" :y2="getNodePos(edge.target).y"
        stroke="#c9cdd4" stroke-width="2" marker-end="url(#arrowhead)" />
      <g v-for="(node, idx) in nodes" :key="'n-' + idx" @click="$emit('nodeClick', node)"
        style="cursor: pointer">
        <circle :cx="node.x" :cy="node.y" r="24" :fill="nodeColor(node.type)" stroke="#dcdfe6" stroke-width="2" />
        <text :x="node.x" :y="node.y + 5" text-anchor="middle" fill="white" font-size="12" font-weight="600">{{ node.icon || node.type?.[0]?.toUpperCase() || '?' }}</text>
        <text :x="node.x" :y="node.y + 44" text-anchor="middle" fill="#4e5969" font-size="12">{{ node.name }}</text>
      </g>
    </svg>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  nodes: Array<{ id: string; name: string; type?: string; icon?: string; x?: number; y?: number }>
  edges: Array<{ source: string; target: string }>
  height?: string
}>(), { height: '400px' })

defineEmits(['nodeClick'])

const svgWidth = computed(() => Math.max(800, props.nodes.length * 120))
const svgHeight = computed(() => parseInt(props.height) || 400)

const nodePositions = computed(() => {
  const cols = Math.ceil(Math.sqrt(props.nodes.length))
  return props.nodes.reduce((acc, node, idx) => {
    const row = Math.floor(idx / cols)
    const col = idx % cols
    acc[node.id] = { x: (col + 1) * (svgWidth.value / (cols + 1)), y: (row + 1) * 140 }
    return acc
  }, {} as Record<string, { x: number; y: number }>)
})

function getNodePos(id: string) { return nodePositions.value[id] || { x: 0, y: 0 } }

function nodeColor(type?: string): string {
  const colors: Record<string, string> = {
    server: '#165dff', database: '#ff7d00', web: '#00b42a', network: '#86909c', container: '#f53f3f',
  }
  return colors[type || ''] || '#165dff'
}
</script>
