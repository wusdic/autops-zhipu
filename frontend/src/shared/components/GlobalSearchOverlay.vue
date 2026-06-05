<template>
  <Teleport to="body">
    <Transition name="overlay">
      <div v-if="visible" class="search-overlay" @click.self="close">
        <div class="search-panel">
          <div class="search-input-wrapper">
            <el-icon size="20" color="#86909c"><Search /></el-icon>
            <input
              ref="inputRef"
              v-model="keyword"
              class="search-input"
              placeholder="搜索页面、资产、告警、工单... (ESC 关闭)"
              @input="handleSearch"
              @keydown.enter="selectFirst"
              @keydown.escape="close"
              @keydown.down.prevent="moveDown"
              @keydown.up.prevent="moveUp"
            />
            <el-tag size="small" type="info" class="search-shortcut">ESC</el-tag>
          </div>

          <div v-if="results.length > 0" class="search-results">
            <div
              v-for="(item, idx) in results"
              :key="item.path + item.title"
              class="search-result-item"
              :class="{ active: idx === activeIndex }"
              @click="navigateTo(item)"
              @mouseenter="activeIndex = idx"
            >
              <div class="result-icon">
                <el-icon :size="16">
                  <component :is="getIcon(item.module)" />
                </el-icon>
              </div>
              <div class="result-content">
                <div class="result-title" v-html="highlightKeyword(item.title)" />
                <div class="result-meta">
                  <el-tag size="small" :type="moduleTagType(item.module)">{{ item.module }}</el-tag>
                  <span class="result-group">{{ item.group }}</span>
                </div>
              </div>
            </div>
          </div>

          <div v-else-if="keyword && !loading" class="search-empty">
            <el-empty description="未找到匹配结果" :image-size="60" />
          </div>

          <div v-else-if="!keyword" class="search-hint">
            <div class="hint-title">快速跳转</div>
            <div class="hint-items">
              <div v-for="item in recentPages" :key="item.path" class="hint-item" @click="navigateTo(item)">
                <el-icon size="14"><Clock /></el-icon>
                <span>{{ item.title }}</span>
                <span class="hint-path">{{ item.path }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Search, Clock, DataBoard, Box, Checked, TrendCharts, Warning, Cpu, MagicStick, Tickets, Document, Tools } from '@element-plus/icons-vue'

const props = defineProps<{ visible: boolean }>()
const emit = defineEmits<{ (e: 'update:visible', v: boolean): void }>()

const router = useRouter()
const keyword = ref('')
const results = ref<any[]>([])
const activeIndex = ref(0)
const loading = ref(false)
const inputRef = ref<HTMLInputElement>()

const allPages = [
  { path: '/', title: '首页指挥台', module: 'M1', group: '首页指挥台' },
  { path: '/business-health-map', title: '业务健康地图', module: 'M1', group: '首页指挥台' },
  { path: '/daily-summary', title: '今日摘要', module: 'M1', group: '首页指挥台' },
  { path: '/resources', title: '资源总览', module: 'M2', group: '资源中心' },
  { path: '/assets', title: '资源列表', module: 'M2', group: '资源中心' },
  { path: '/lifecycle', title: '生命周期', module: 'M2', group: '资源中心' },
  { path: '/credentials', title: '凭证管理', module: 'M2', group: '资源中心' },
  { path: '/inspections', title: '巡检总览', module: 'M3', group: '巡检中心' },
  { path: '/inspection/templates', title: '巡检模板', module: 'M3', group: '巡检中心' },
  { path: '/monitoring', title: '监控总览', module: 'M4', group: '监控中心' },
  { path: '/events', title: '事件流', module: 'M4', group: '监控中心' },
  { path: '/anomalies', title: '异常总览', module: 'M5', group: '处置中心' },
  { path: '/alerts', title: '告警列表', module: 'M5', group: '处置中心' },
  { path: '/incident', title: '故障工作台', module: 'M5', group: '处置中心' },
  { path: '/policies', title: '策略列表', module: 'M6', group: '自动化中心' },
  { path: '/scripts', title: '脚本库', module: 'M6', group: '自动化中心' },
  { path: '/knowledge', title: '知识列表', module: 'M7', group: '智能知识库' },
  { path: '/aiops', title: 'AI 诊断', module: 'M7', group: '智能知识库' },
  { path: '/tickets', title: '工单列表', module: 'M8', group: '工单中心' },
  { path: '/reports', title: '报表总览', module: 'M9', group: '报表审计' },
  { path: '/audit', title: '审计查询', module: 'M9', group: '报表审计' },
  { path: '/users', title: '用户管理', module: 'M10', group: '平台管理' },
  { path: '/system-config', title: '系统配置', module: 'M10', group: '平台管理' },
]

const recentPages = ref(allPages.slice(0, 5))

const iconMap: Record<string, any> = { M1: DataBoard, M2: Box, M3: Checked, M4: TrendCharts, M5: Warning, M6: Cpu, M7: MagicStick, M8: Tickets, M9: Document, M10: Tools }
const getIcon = (m: string) => iconMap[m] || Document
const moduleTagType = (m: string) => {
  const map: Record<string, string> = { M1: '', M2: 'success', M3: 'info', M4: 'warning', M5: 'danger', M6: '', M7: 'success', M8: 'info', M9: 'warning', M10: 'danger' }
  return map[m] || 'info'
}

function handleSearch() {
  if (!keyword.value.trim()) { results.value = []; return }
  const kw = keyword.value.toLowerCase().trim()
  results.value = allPages.filter(p => p.title.toLowerCase().includes(kw) || p.path.toLowerCase().includes(kw) || p.group.toLowerCase().includes(kw))
  activeIndex.value = 0
}

function highlightKeyword(text: string) {
  if (!keyword.value) return text
  const escaped = keyword.value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const regex = new RegExp('(' + escaped + ')', 'gi')
  return text.replace(regex, '<mark>$1</mark>')
}

function navigateTo(item: any) {
  router.push(item.path).catch(() => {})
  close()
}

function selectFirst() {
  if (results.value.length > 0) navigateTo(results.value[activeIndex.value])
}

function moveDown() {
  if (activeIndex.value < results.value.length - 1) activeIndex.value++
}
function moveUp() {
  if (activeIndex.value > 0) activeIndex.value--
}

function close() {
  emit('update:visible', false)
  keyword.value = ''
  results.value = []
}

watch(() => props.visible, (v) => {
  if (v) {
    nextTick(() => { inputRef.value?.focus() })
  }
})
</script>

<style scoped>
.search-overlay {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.5); z-index: 9999;
  display: flex; justify-content: center; padding-top: 120px;
}
.search-panel {
  width: 600px; max-height: 500px; background: var(--autops-bg-1); border-radius: var(--autops-radius-lg);
  box-shadow: 0 12px 40px rgba(0,0,0,0.2); overflow: hidden;
}
.search-input-wrapper {
  display: flex; align-items: center; padding: var(--autops-space-lg) 20px;
  border-bottom: 1px solid var(--autops-bg-4); gap: 12px;
}
.search-input {
  flex: 1; border: none; outline: none; font-size: var(--autops-font-16); color: var(--autops-text-1);
}
.search-shortcut { flex-shrink: 0; }
.search-results { max-height: 400px; overflow-y: auto; padding: var(--autops-space-sm); }
.search-result-item {
  display: flex; align-items: center; gap: 12px; padding: 10px 12px;
  border-radius: var(--autops-radius-md); cursor: pointer; transition: background 0.15s;
}
.search-result-item:hover, .search-result-item.active { background: var(--autops-bg-3); }
.result-icon { width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; background: var(--autops-bg-3); border-radius: 6px; }
.result-title { font-size: var(--autops-font-14); color: var(--autops-text-1); }
.result-meta { display: flex; align-items: center; gap: 8px; margin-top: 4px; }
.result-group { font-size: var(--autops-font-12); color: var(--autops-info); }
.search-empty { padding: 40px 0; }
.search-hint { padding: var(--autops-space-md) 20px; }
.hint-title { font-size: var(--autops-font-12); color: var(--autops-info); margin-bottom: var(--autops-space-sm); }
.hint-item {
  display: flex; align-items: center; gap: 8px; padding: var(--autops-space-sm) 0;
  cursor: pointer; color: var(--autops-text-2); font-size: var(--autops-font-14);
}
.hint-item:hover { color: var(--autops-primary); }
.hint-path { margin-left: auto; font-size: var(--autops-font-12); color: var(--autops-text-4); }
.overlay-enter-active, .overlay-leave-active { transition: opacity 0.2s ease; }
.overlay-enter-from, .overlay-leave-to { opacity: 0; }
mark { background: var(--autops-warning-light); color: inherit; padding: 0 2px; border-radius: 2px; }
</style>
