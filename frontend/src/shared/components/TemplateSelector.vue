<template>
  <el-select
    v-model="selected"
    :placeholder="placeholder"
    :multiple="multiple"
    filterable
    :loading="loading"
    @change="handleChange"
    style="width: 100%"
  >
    <el-option-group v-for="group in groupedTemplates" :key="group.label" :label="group.label">
      <el-option v-for="tpl in group.items" :key="tpl.id" :label="tpl.name" :value="tpl.id">
        <div style="display: flex; justify-content: space-between; align-items: center">
          <span>{{ tpl.name }}</span>
          <el-tag v-if="tpl.asset_type" size="small" type="info" style="margin-left: 8px">{{ tpl.asset_type }}</el-tag>
        </div>
        <div v-if="tpl.description" style="font-size: 12px; color: #999">{{ tpl.description }}</div>
      </el-option>
    </el-option-group>
    <template #empty>
      <div style="padding: 10px; color: #999; text-align: center">
        {{ emptyText }}
      </div>
    </template>
  </el-select>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import api from '@/shared/api/client'
import { API } from '@/shared/api/routes'

const props = withDefaults(defineProps<{
  modelValue: string | string[]
  templateType?: 'inspection' | 'collection' | 'notification' | 'report' | 'discovery' | ''
  assetType?: string
  multiple?: boolean
  placeholder?: string
  emptyText?: string
}>(), {
  templateType: '',
  multiple: false,
  placeholder: '选择模板',
  emptyText: '暂无模板',
})

const emit = defineEmits(['update:modelValue', 'change'])
const selected = ref(props.modelValue) as any
const templates = ref<any[]>([])
const loading = ref(false)

// Map template type to API route
const typeApiMap: Record<string, string> = {
  inspection: API.INSPECTION_TEMPLATES || '/api/v1/inspection/templates',
  collection: API.COLLECTORS || '/api/v1/collectors',
  notification: API.NOTIFICATION_RULES || '/api/v1/notification-rules',
  report: API.REPORT_TEMPLATES || '/api/v1/report/templates',
  discovery: API.DISCOVERY_TEMPLATES || '/api/v1/discovery-templates',
}

const groupedTemplates = computed(() => {
  if (!templates.value.length) return []
  const groups: Record<string, any[]> = {}
  templates.value.forEach(tpl => {
    const key = tpl.asset_type || tpl.category || '默认'
    if (!groups[key]) groups[key] = []
    groups[key].push(tpl)
  })
  return Object.entries(groups).map(([label, items]) => ({ label, items }))
})

watch(() => props.modelValue, (val) => { selected.value = val })

function handleChange(val: any) {
  emit('update:modelValue', val)
  emit('change', val)
}

async function loadTemplates() {
  loading.value = true
  try {
    const endpoint = props.templateType ? typeApiMap[props.templateType] : API.INSPECTION_TEMPLATES || '/api/v1/inspection/templates'
    const params: any = { page: 1, page_size: 100 }
    if (props.assetType) params.asset_type = props.assetType
    const res = await api.get(endpoint, { params })
    templates.value = res.data?.data?.items || res.data?.data || []
  } catch { templates.value = [] }
  finally { loading.value = false }
}

onMounted(loadTemplates)
</script>
