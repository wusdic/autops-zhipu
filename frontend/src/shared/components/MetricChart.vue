<template>
  <div class="metric-chart" ref="chartRef" :style="{ height: height + 'px' }" />
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

type Point = { time: string; value: number }
type Series = { name: string; data: Point[]; color?: string }

const props = withDefaults(defineProps<{
  data?: Point[]
  multiple?: Series[]
  chartType?: 'line' | 'bar' | 'pie'
  title?: string
  height?: number
  color?: string
  unit?: string
}>(), {
  data: () => [],
  multiple: () => [],
  chartType: 'line',
  height: 240,
  color: '#165dff',
  unit: '',
})

const chartRef = ref<HTMLElement | null>(null)
let chart: echarts.ECharts | null = null

const PALETTE = ['#165dff', '#00b42a', '#ff7d00', '#f53f3f', '#722ed1', '#14c9c9', '#eb0aa4', '#7bc616']

function hasData(): boolean {
  if (props.chartType === 'pie') return (props.data?.length ?? 0) > 0
  if (props.multiple && props.multiple.length) return props.multiple.some(s => s.data && s.data.length)
  return (props.data?.length ?? 0) > 0
}

function buildOption(): echarts.EChartsOption {
  const title = props.title
    ? { text: props.title, left: 'center', textStyle: { fontSize: 13, color: '#4e5969', fontWeight: 600 as const } }
    : undefined

  // 空态
  if (!hasData()) {
    return {
      title: { text: '暂无数据', left: 'center', top: 'middle', textStyle: { color: '#c9cdd4', fontSize: 13, fontWeight: 'normal' as const } },
    }
  }

  // 饼图（data[].time 作为名称，data[].value 作为数值）
  if (props.chartType === 'pie') {
    return {
      title,
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      legend: { bottom: 0, type: 'scroll' },
      series: [{
        type: 'pie',
        radius: ['40%', '68%'],
        center: ['50%', title ? '48%' : '45%'],
        avoidLabelOverlap: true,
        itemStyle: { borderRadius: 4, borderColor: '#fff', borderWidth: 2 },
        label: { formatter: '{b}\n{c}' },
        data: (props.data || []).map(d => ({ name: d.time, value: d.value })),
      }],
    }
  }

  // 折线/柱状（单或多系列）
  const seriesList: Series[] = (props.multiple && props.multiple.length)
    ? props.multiple
    : [{ name: props.title || '数值', data: props.data || [], color: props.color }]
  const xData = (seriesList[0]?.data || []).map(p => p.time)
  const multi = seriesList.length > 1

  return {
    title,
    tooltip: { trigger: 'axis', valueFormatter: (v) => `${v}${props.unit}` },
    legend: multi ? { bottom: 0, type: 'scroll' } : undefined,
    grid: { left: 48, right: 16, top: title ? 36 : 16, bottom: multi ? 36 : 28 },
    xAxis: { type: 'category', boundaryGap: props.chartType === 'bar', data: xData, axisLabel: { color: '#86909c', fontSize: 11 } },
    yAxis: { type: 'value', axisLabel: { color: '#86909c', fontSize: 11, formatter: (v: number) => `${v}${props.unit}` }, splitLine: { lineStyle: { color: '#e5e6eb' } } },
    series: seriesList.map((s, i) => ({
      name: s.name,
      type: props.chartType === 'bar' ? 'bar' : 'line',
      smooth: props.chartType !== 'bar',
      showSymbol: false,
      data: (s.data || []).map(p => p.value),
      itemStyle: { color: s.color || PALETTE[i % PALETTE.length] },
      areaStyle: (!multi && props.chartType === 'line')
        ? { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: (s.color || props.color) + '40' },
            { offset: 1, color: (s.color || props.color) + '05' },
          ]) }
        : undefined,
    })),
  }
}

function render() {
  const el = chartRef.value
  if (!el) return
  if (!chart) chart = echarts.init(el)
  chart.setOption(buildOption(), true)
}

function onResize() { chart?.resize() }

onMounted(() => { nextTick(render); window.addEventListener('resize', onResize) })
onBeforeUnmount(() => { window.removeEventListener('resize', onResize); chart?.dispose(); chart = null })

watch(() => [props.data, props.multiple, props.chartType], () => nextTick(render), { deep: true })
</script>

<style scoped>
.metric-chart {
  width: 100%;
  min-height: 120px;
}
</style>
