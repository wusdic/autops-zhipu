<template>
  <div ref="chartRef" :style="{ width: '100%', height: height }"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onUnmounted } from 'vue'
import * as echarts from 'echarts'

const props = withDefaults(defineProps<{
  data: Array<{ time: string; value: number }>
  title?: string
  color?: string
  height?: string
  unit?: string
}>(), {
  height: '300px',
  color: '#409EFF',
  unit: '',
})

const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

onMounted(() => {
  if (chartRef.value) {
    chart = echarts.init(chartRef.value)
    renderChart()
  }
})

watch(() => props.data, renderChart, { deep: true })

onUnmounted(() => chart?.dispose())

function renderChart() {
  if (!chart) return
  chart.setOption({
    title: { text: props.title, left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'axis', formatter: (p: any) => `${p[0]?.axisValue}<br/>${p[0]?.value}${props.unit}` },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: props.data.map(d => d.time), boundaryGap: false },
    yAxis: { type: 'value' },
    series: [{ type: 'line', data: props.data.map(d => d.value), smooth: true, areaStyle: { opacity: 0.15 }, itemStyle: { color: props.color } }],
  })
}
</script>
