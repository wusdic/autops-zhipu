<template>
  <div class="impact-scope-graph">
    <div class="isg-center" :style="{ borderColor: centerColor }">
      <div class="isg-center-name">{{ centerName }}</div>
      <div class="isg-center-status">{{ centerStatus }}</div>
    </div>
    <div class="isg-rings" v-if="layers.length">
      <div v-for="(layer, lIdx) in layers" :key="lIdx" class="isg-layer" :class="'layer-' + lIdx">
        <div v-for="(node, nIdx) in layer" :key="nIdx" class="isg-node" :class="'impact-' + node.level"
          :style="{ transform: 'rotate(' + (360/layer.length)*nIdx + 'deg) translateY(-' + 80*(lIdx+1) + 'px) rotate(-' + (360/layer.length)*nIdx + 'deg)' }">
          <div class="isg-node-name">{{ node.name }}</div>
          <div class="isg-node-type">{{ node.type }}</div>
        </div>
      </div>
    </div>
    <el-empty v-if="!layers.length" description="暂无影响范围数据" :image-size="60" />
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue"

const props = withDefaults(defineProps<{
  centerName?: string
  centerStatus?: string
  centerLevel?: string
  layers?: { name: string; type: string; level: string }[][]
}>(), { centerName: "故障源", centerStatus: "异常", centerLevel: "critical", layers: () => [] })

const centerColor = computed(() => ({ critical: "#f53f3f", high: "#ff7d00", medium: "#ffc40f", low: "#00b42a" } as any)[props.centerLevel] || "#86909c")
</script>

<style scoped>
.impact-scope-graph { position: relative; min-height: 300px; display: flex; align-items: center; justify-content: center; }
.isg-center { width: 80px; height: 80px; border-radius: 50%; border: 3px solid; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; z-index: 2; background: var(--autops-bg-1); }
.isg-center-name { font-size: var(--autops-font-12); font-weight: 600; color: var(--autops-text-1); }
.isg-center-status { font-size: 11px; color: var(--autops-info); }
.isg-rings { position: absolute; width: 100%; height: 100%; }
.isg-node { position: absolute; width: 70px; text-align: center; top: 50%; left: calc(50% - 35px); }
.isg-node-name { font-size: 11px; font-weight: 500; color: var(--autops-text-1); }
.isg-node-type { font-size: 10px; color: var(--autops-info); }
.isg-node.impact-critical { color: var(--autops-danger); } .isg-node.impact-high { color: var(--autops-warning); }
.isg-node.impact-medium { color: var(--autops-gold); } .isg-node.impact-low { color: var(--autops-success); }
</style>
