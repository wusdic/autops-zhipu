<template>
  <div class="metric-chart" ref="chartRef" :style="{ height: height + 'px' }" />
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'

const props = withDefaults(defineProps<{
  data?: Array<{ time: string; value: number }>
  title?: string
  height?: number
  color?: string
  unit?: string
}>(), {
  height: 240,
  color: '#165dff',
  unit: 'primary',
})

const chartRef = ref<HTMLElement | null>(null)
let chartInstance: any = null

// Simple canvas-based chart (no echarts dependency)
function renderChart() {
  const el = chartRef.value
  if (!el || !props.data || props.data.length === 0) {
    // Draw empty state
    if (el) {
      const canvas = document.createElement('canvas')
      canvas.width = el.clientWidth * 2
      canvas.height = el.clientHeight * 2
      canvas.style.width = '100%'
      canvas.style.height = '100%'
      el.innerHTML = ''
      el.appendChild(canvas)
      const ctx = canvas.getContext('2d')
      if (ctx) {
        ctx.scale(2, 2)
        const w = el.clientWidth
        const h = el.clientHeight
        ctx.fillStyle = '#f2f3f5'
        ctx.fillRect(0, 0, w, h)
        ctx.fillStyle = '#c9cdd4'
        ctx.font = '13px sans-serif'
        ctx.textAlign = 'center'
        ctx.fillText('暂无数据', w / 2, h / 2)
      }
    }
    return
  }

  const canvas = document.createElement('canvas')
  canvas.width = el.clientWidth * 2
  canvas.height = el.clientHeight * 2
  canvas.style.width = '100%'
  canvas.style.height = '100%'
  el.innerHTML = ''
  el.appendChild(canvas)

  const ctx = canvas.getContext('2d')
  if (!ctx) return

  ctx.scale(2, 2)
  const w = el.clientWidth
  const h = el.clientHeight
  const pad = { top: 20, right: 20, bottom: 30, left: 50 }
  const cw = w - pad.left - pad.right
  const ch = h - pad.top - pad.bottom

  // Background
  ctx.fillStyle = '#fff'
  ctx.fillRect(0, 0, w, h)

  // Grid
  ctx.strokeStyle = '#e5e6eb'
  ctx.lineWidth = 0.5
  for (let i = 0; i <= 4; i++) {
    const y = pad.top + (ch / 4) * i
    ctx.beginPath()
    ctx.moveTo(pad.left, y)
    ctx.lineTo(w - pad.right, y)
    ctx.stroke()
  }

  // Data
  const values = props.data.map(d => d.value)
  const minVal = Math.min(...values)
  const maxVal = Math.max(...values)
  const range = maxVal - minVal || 1

  // Line
  ctx.strokeStyle = props.color
  ctx.lineWidth = 2
  ctx.beginPath()
  props.data.forEach((d, i) => {
    const x = pad.left + (cw / (props.data!.length - 1 || 1)) * i
    const y = pad.top + ch - ((d.value - minVal) / range) * ch
    if (i === 0) ctx.moveTo(x, y)
    else ctx.lineTo(x, y)
  })
  ctx.stroke()

  // Fill area
  ctx.lineTo(pad.left + cw, pad.top + ch)
  ctx.lineTo(pad.left, pad.top + ch)
  ctx.closePath()
  const grad = ctx.createLinearGradient(0, pad.top, 0, pad.top + ch)
  grad.addColorStop(0, props.color + '30')
  grad.addColorStop(1, props.color + '05')
  ctx.fillStyle = grad
  ctx.fill()

  // Y axis labels
  ctx.fillStyle = '#86909c'
  ctx.font = '11px sans-serif'
  ctx.textAlign = 'right'
  for (let i = 0; i <= 4; i++) {
    const val = maxVal - (range / 4) * i
    const y = pad.top + (ch / 4) * i + 4
    ctx.fillText(val.toFixed(0) + props.unit, pad.left - 6, y)
  }

  // X axis labels (first, middle, last)
  ctx.textAlign = 'center'
  const showLabels = props.data.filter((_, i) => {
    const step = Math.max(1, Math.floor(props.data!.length / 5))
    return i % step === 0 || i === props.data!.length - 1
  })
  showLabels.forEach(d => {
    const idx = props.data!.indexOf(d)
    const x = pad.left + (cw / (props.data!.length - 1 || 1)) * idx
    ctx.fillText(d.time.slice(-5), x, h - 6)
  })
}

onMounted(() => {
  nextTick(renderChart)
})

onBeforeUnmount(() => {
  chartInstance = null
})

watch(() => props.data, () => {
  nextTick(renderChart)
}, { deep: true })
</script>

<style scoped>
.metric-chart {
  width: 100%;
  min-height: 120px;
}
</style>
