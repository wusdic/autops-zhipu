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
  chartType?: 'line' | 'bar' | 'pie'
  multiple?: Array<{ name: string; data: Array<{ time: string; value: number }>; color: string }>
}>(), {
  height: '300px',
  color: '#409EFF',
  unit: '',
  chartType: 'line',
})

const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

function initChart() {
  if (chartRef.value) {
    chart = echarts.init(chartRef.value)
    renderChart()
  }
}

onMounted(() => {
  initChart()
  window.addEventListener('resize', handleResize)
})

watch(() => [props.data, props.multiple], renderChart, { deep: true })

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chart?.dispose()
})

function handleResize() {
  chart?.resize()
}

function renderChart() {
  if (!chart) return

  if (props.chartType === 'pie') {
    renderPieChart()
    return
  }

  // Line or Bar chart
  const series: any[] = []
  if (props.multiple && props.multiple.length > 0) {
    // Multiple series
    const allTimes = new Set<string>()
    props.multiple.forEach(s => s.data.forEach(d => allTimes.add(d.time)))
    const times = Array.from(allTimes).sort()
    props.multiple.forEach(s => {
      const dataMap = new Map(s.data.map(d => [d.time, d.value]))
      series.push({
        name: s.name,
        type: props.chartType,
        data: times.map(t => dataMap.get(t) ?? null),
        smooth: props.chartType === 'line',
        areaStyle: props.chartType === 'line' ? { opacity: 0.15 } : undefined,
        itemStyle: { color: s.color },
      })
    })
    chart.setOption({
      title: { text: props.title, left: 'center', textStyle: { fontSize: 14 } },
      tooltip: { trigger: 'axis' },
      legend: { bottom: 0 },
      grid: { left: '3%', right: '4%', bottom: '12%', top: '14%', containLabel: true },
      xAxis: { type: 'category', data: times, boundaryGap: props.chartType === 'bar' },
      yAxis: { type: 'value' },
      series,
    }, true)
  } else {
    // Single series
    chart.setOption({
      title: { text: props.title, left: 'center', textStyle: { fontSize: 14 } },
      tooltip: {
        trigger: 'axis',
        formatter: (p: any) => `${p[0]?.axisValue}<br/>${p[0]?.value}${props.unit}`
      },
      grid: { left: '3%', right: '4%', bottom: '3%', top: '14%', containLabel: true },
      xAxis: { type: 'category', data: props.data.map(d => d.time), boundaryGap: false },
      yAxis: { type: 'value' },
      series: [{
        type: props.chartType,
        data: props.data.map(d => d.value),
        smooth: props.chartType === 'line',
        areaStyle: props.chartType === 'line' ? { opacity: 0.15 } : undefined,
        itemStyle: { color: props.color },
      }],
    }, true)
  }
}

function renderPieChart() {
  if (!chart) return
  chart.setOption({
    title: { text: props.title, left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'item' },
    legend: { bottom: 0 },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: false,
      itemStyle: { borderRadius: 4, borderColor: '#fff', borderWidth: 2 },
      label: { show: true, formatter: '{b}: {c}' },
      data: props.data.map(d => ({ name: d.time, value: d.value })),
    }],
  }, true)
}
</script>
