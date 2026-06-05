<template>
  <div class="config-inheritance">
    <el-divider content-position="left">
      <el-icon><Connection /></el-icon> 配置继承层级
    </el-divider>

    <div class="inheritance-chain">
      <div v-for="(level, idx) in levels" :key="idx" class="inheritance-level" :class="{ active: activeLevel === idx, overridden: level.overridden }">
        <div class="level-indicator">
          <div class="level-dot" :style="{ background: levelColor(idx) }" />
          <div v-if="idx < levels.length - 1" class="level-line" />
        </div>
        <div class="level-content">
          <div class="level-header">
            <span class="level-name">{{ level.label }}</span>
            <el-tag v-if="level.overridden" size="small" type="warning">已覆盖</el-tag>
            <el-tag v-else-if="level.source === 'inherited'" size="small" type="info">继承</el-tag>
            <el-tag v-else size="small" type="success">当前</el-tag>
          </div>
          <el-descriptions :column="2" size="small" border class="level-values">
            <el-descriptions-item v-for="(val, key) in level.values" :key="key" :label="key">
              <template v-if="level.overridden && getOverriddenValue(key) !== undefined">
                <del class="old-value">{{ val }}</del>
                <span class="new-value">{{ getOverriddenValue(key) }}</span>
              </template>
              <template v-else>{{ val }}</template>
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </div>
    </div>

    <div class="merged-view" style="margin-top:16px">
      <h4>合并后有效配置</h4>
      <el-table :data="mergedConfig" stripe size="small" border>
        <el-table-column prop="key" label="配置项" width="200" />
        <el-table-column prop="value" label="有效值" min-width="180" />
        <el-table-column prop="source" label="来源" width="120">
          <template #default="{ row }"><el-tag size="small">{{ row.source }}</el-tag></template>
        </el-table-column>
        <el-table-column label="覆盖链" min-width="200">
          <template #default="{ row }">
            <span v-for="(s,i) in row.chain" :key="i">
              {{ s }}<span v-if="i < row.chain.length - 1" style="color:#86909c"> → </span>
            </span>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { Connection } from '@element-plus/icons-vue'
import api from '@/shared/api/client'
import { API } from '@/shared/api/routes'

const props = defineProps<{
  assetId?: string
  groupId?: string
  configType?: string
}>()

interface InheritLevel {
  label: string
  source: 'global' | 'organization' | 'system' | 'group' | 'asset'
  values: Record<string, any>
  overridden: boolean
}

const levels = ref<InheritLevel[]>([])
const activeLevel = ref(-1)
const overrides = ref<Record<string, any>>({})

const levelColor = (idx: number) => {
  const colors = ['#165dff', '#00b42a', '#ff7d00', '#f53f3f', '#722ed1']
  return colors[idx] || '#86909c'
}

function getOverriddenValue(key: string) {
  return overrides.value[key]
}

const mergedConfig = computed(() => {
  const merged: Record<string, { value: any; source: string; chain: string[] }> = {}
  for (const level of levels.value) {
    for (const [key, value] of Object.entries(level.values)) {
      if (!merged[key]) merged[key] = { value, source: level.label, chain: [level.label] }
      else { merged[key].value = value; merged[key].source = level.label; merged[key].chain.push(level.label) }
    }
  }
  return Object.entries(merged).map(([key, data]) => ({ key, ...data }))
})

async function loadInheritance() {
  try {
    const params: any = {}
    if (props.assetId) params.asset_id = props.assetId
    if (props.groupId) params.group_id = props.groupId
    if (props.configType) params.config_type = props.configType

    const { data } = await api.get(API.CONFIG_INHERITANCE, { params })
    if (data?.code === 0 && data.data?.levels) {
      levels.value = data.data.levels
      overrides.value = data.data.overrides || {}
    } else {
      // Fallback: show example hierarchy
      levels.value = [
        { label: '全局默认', source: 'global', values: { '采集间隔': '60s', '超时': '30s', '重试次数': '3' }, overridden: false },
        { label: '组织策略', source: 'organization', values: { '采集间隔': '30s', '超时': '30s' }, overridden: false },
        { label: '系统模板', source: 'system', values: { '采集间隔': '30s', '超时': '60s', 'SNMP版本': 'v2c' }, overridden: false },
        { label: '资产分组', source: 'group', values: { '采集间隔': '15s', '超时': '60s' }, overridden: false },
        { label: '资产级别', source: 'asset', values: { '采集间隔': '10s' }, overridden: false },
      ]
    }
  } catch {
    levels.value = [
      { label: '全局默认', source: 'global', values: { '采集间隔': '60s', '超时': '30s' }, overridden: false },
      { label: '资产级别', source: 'asset', values: { '采集间隔': '10s' }, overridden: false },
    ]
  }
}

onMounted(() => { loadInheritance() })
watch(() => [props.assetId, props.groupId, props.configType], () => { loadInheritance() })
</script>

<style scoped>
.config-inheritance { margin-top: 12px; }
.inheritance-chain { padding-left: 8px; }
.inheritance-level { display: flex; gap: 12px; margin-bottom: 0; }
.inheritance-level.active .level-content { border-color: var(--autops-primary); }
.level-indicator { display: flex; flex-direction: column; align-items: center; width: 20px; flex-shrink: 0; }
.level-dot { width: 12px; height: 12px; border-radius: 50%; border: 2px solid var(--autops-bg-1); box-shadow: 0 0 0 1px var(--autops-bg-4); }
.level-line { width: 2px; flex: 1; background: var(--autops-bg-4); margin: 4px 0; min-height: 20px; }
.level-content { flex: 1; padding: var(--autops-space-sm) 12px; border: 1px solid var(--autops-bg-4); border-radius: var(--autops-radius-sm); margin-bottom: var(--autops-space-sm); background: var(--autops-bg-1); }
.level-header { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.level-name { font-weight: 500; font-size: var(--autops-font-13); }
.level-values { margin-top: 4px; }
.old-value { color: var(--autops-danger); text-decoration: line-through; margin-right: 6px; }
.new-value { color: var(--autops-success); font-weight: 500; }
</style>
