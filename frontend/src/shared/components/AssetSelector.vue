<template>
  <el-select
    v-model="selected"
    :placeholder="placeholder"
    :multiple="multiple"
    filterable
    remote
    :remote-method="searchAssets"
    :loading="loading"
    @change="$emit('update:modelValue', selected)"
    style="width: 100%"
  >
    <el-option v-for="asset in options" :key="asset.id" :label="`${asset.name} (${asset.ip || asset.id})`" :value="asset.id">
      <span>{{ asset.name }}</span>
      <span style="color: #999; margin-left: 8px; font-size: 12px">{{ asset.ip }}</span>
    </el-option>
  </el-select>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '@/shared/api/client'
import { API } from '@/shared/api/routes'

const props = withDefaults(defineProps<{
  modelValue: string | string[]
  multiple?: boolean
  placeholder?: string
  assetType?: string
}>(), { placeholder: '选择资产', multiple: false })

const emit = defineEmits(['update:modelValue'])
const selected = ref(props.modelValue) as any
const options = ref<any[]>([])
const loading = ref(false)

onMounted(() => searchAssets(''))

async function searchAssets(query: string) {
  loading.value = true
  try {
    const params: any = { page: 1, page_size: 20 }
    if (query) params.keyword = query
    if (props.assetType) params.asset_type = props.assetType
    const res = await api.get(API.ASSETS, { params })
    options.value = res.data?.data?.items || res.data?.data || []
  } catch { options.value = [] }
  finally { loading.value = false }
}
</script>
