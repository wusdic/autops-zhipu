<template>
  <div class="asset-range-selector">
    <el-radio-group v-model="rangeMode" size="small" @change="handleModeChange">
      <el-radio-button label="all">全部资产</el-radio-button>
      <el-radio-button label="type">按类型</el-radio-button>
      <el-radio-button label="group">按分组</el-radio-button>
      <el-radio-button label="tag">按标签</el-radio-button>
      <el-radio-button label="custom">自定义选择</el-radio-button>
    </el-radio-group>

    <!-- 按类型选择 -->
    <div v-if="rangeMode === 'type'" class="mt-2">
      <el-checkbox-group v-model="selectedTypes" @change="emitChange">
        <el-checkbox v-for="t in assetTypes" :key="t.value" :label="t.value">{{ t.label }}</el-checkbox>
      </el-checkbox-group>
    </div>

    <!-- 按分组选择 -->
    <div v-if="rangeMode === 'group'" class="mt-2">
      <el-select v-model="selectedGroups" multiple filterable placeholder="选择资产分组" style="width: 100%" @change="emitChange">
        <el-option v-for="g in groups" :key="g.id" :label="g.name" :value="g.id" />
      </el-select>
    </div>

    <!-- 按标签选择 -->
    <div v-if="rangeMode === 'tag'" class="mt-2">
      <el-select v-model="selectedTags" multiple filterable allow-create placeholder="选择或输入标签" style="width: 100%" @change="emitChange">
        <el-option v-for="tag in availableTags" :key="tag" :label="tag" :value="tag" />
      </el-select>
    </div>

    <!-- 自定义选择 -->
    <div v-if="rangeMode === 'custom'" class="mt-2">
      <el-select
        v-model="selectedAssets"
        multiple
        filterable
        remote
        :remote-method="searchAssets"
        :loading="searchLoading"
        placeholder="搜索并选择资产"
        style="width: 100%"
        @change="emitChange"
      >
        <el-option v-for="a in assetOptions" :key="a.id" :label="a.name + (a.ip ? ' (' + a.ip + ')' : '')" :value="a.id" />
      </el-select>
    </div>

    <!-- 范围预览 -->
    <div v-if="previewText" class="range-preview mt-2">
      <el-tag size="small" type="info">{{ previewText }}</el-tag>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import api from '@/shared/api/client'
import { API } from '@/shared/api/routes'

const props = withDefaults(defineProps<{
  modelValue?: any
}>(), { modelValue: () => ({ mode: 'all', types: [], groups: [], tags: [], asset_ids: [] }) })

const emit = defineEmits(['update:modelValue', 'change'])

const rangeMode = ref(props.modelValue?.mode || 'all')
const selectedTypes = ref<string[]>(props.modelValue?.types || [])
const selectedGroups = ref<string[]>(props.modelValue?.groups || [])
const selectedTags = ref<string[]>(props.modelValue?.tags || [])
const selectedAssets = ref<string[]>(props.modelValue?.asset_ids || [])
const searchLoading = ref(false)
const assetOptions = ref<any[]>([])
const groups = ref<any[]>([])
const availableTags = ref<string[]>([])

const assetTypes = [
  { label: 'Linux 服务器', value: 'linux_server' },
  { label: 'Windows 服务器', value: 'windows_server' },
  { label: 'MySQL 数据库', value: 'mysql' },
  { label: 'PostgreSQL 数据库', value: 'postgresql' },
  { label: 'Redis', value: 'redis' },
  { label: 'Nginx', value: 'nginx' },
  { label: 'Web 应用', value: 'web_app' },
  { label: '网络设备', value: 'network_device' },
]

const previewText = computed(() => {
  switch (rangeMode.value) {
    case 'all': return '全部资产'
    case 'type': return selectedTypes.value.length ? '类型: ' + selectedTypes.value.length + ' 种' : '未选择类型'
    case 'group': return selectedGroups.value.length ? '分组: ' + selectedGroups.value.length + ' 个' : '未选择分组'
    case 'tag': return selectedTags.value.length ? '标签: ' + selectedTags.value.length + ' 个' : '未选择标签'
    case 'custom': return selectedAssets.value.length ? '已选: ' + selectedAssets.value.length + ' 个资产' : '未选择资产'
    default: return ''
  }
})

function handleModeChange() {
  emitChange()
}

function emitChange() {
  const value = {
    mode: rangeMode.value,
    types: selectedTypes.value,
    groups: selectedGroups.value,
    tags: selectedTags.value,
    asset_ids: selectedAssets.value,
  }
  emit('update:modelValue', value)
  emit('change', value)
}

async function searchAssets(query: string) {
  searchLoading.value = true
  try {
    const params: any = { page: 1, page_size: 20 }
    if (query) params.keyword = query
    const res = await api.get(API.ASSETS, { params })
    assetOptions.value = res.data?.data?.items || res.data?.data || []
  } catch { assetOptions.value = [] }
  finally { searchLoading.value = false }
}

async function loadGroups() {
  try {
    const res = await api.get(API.ASSET_GROUPS)
    groups.value = res.data?.data?.items || res.data?.data || []
  } catch { groups.value = [] }
}

async function loadTags() {
  try {
    const res = await api.get(API.ASSETS, { params: { page: 1, page_size: 100 } })
    const items = res.data?.data?.items || []
    const tagSet = new Set<string>()
    items.forEach((a: any) => {
      if (Array.isArray(a.tags)) a.tags.forEach((t: string) => tagSet.add(t))
    })
    availableTags.value = Array.from(tagSet)
  } catch { /* ignore */ }
}

onMounted(() => {
  loadGroups()
  loadTags()
  searchAssets('')
})
</script>

<style scoped>
.asset-range-selector { width: 100%; }
.mt-2 { margin-top: 8px; }
.range-preview { display: flex; align-items: center; }
</style>
