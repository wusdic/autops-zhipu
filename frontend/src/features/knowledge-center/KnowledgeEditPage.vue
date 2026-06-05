<template>
  <div class="autops-page-container">
    <div class="autops-page-header">
      <div>
        <div class="autops-page-title">编辑知识</div>
        <div class="autops-page-desc">编辑知识条目内容</div>
      </div>
    </div>

    <div class="autops-toolbar">
      <el-button @click="goBack"><el-icon><ArrowLeft /></el-icon> 返回</el-button>
      <div style="flex:1" />
      <el-button type="primary" @click="save" :loading="saving"><el-icon><Check /></el-icon> 保存</el-button>
      <el-button @click="saveAndPublish" :loading="saving">保存并发布</el-button>
    </div>

    <el-tabs v-model="activeTab">
      <!-- 结构化编辑 -->
      <el-tab-pane label="结构化编辑" name="structured">
        <el-form :model="form" label-width="120px">
          <el-row :gutter="16">
            <el-col :span="12"><el-form-item label="标题" required><el-input v-model="form.title" placeholder="知识标题" /></el-form-item></el-col>
            <el-col :span="12"><el-form-item label="分类">
              <el-select v-model="form.category" style="width:100%">
                <el-option label="故障处置" value="incident_response" /><el-option label="巡检方案" value="inspection" />
                <el-option label="最佳实践" value="best_practice" /><el-option label="配置指南" value="configuration" />
                <el-option label="安全合规" value="security" /><el-option label="性能优化" value="optimization" />
              </el-select>
            </el-form-item></el-col>
          </el-row>

          <el-form-item label="标签"><el-select v-model="form.tags" multiple filterable allow-create default-first-option style="width:100%" placeholder="添加标签">
            <el-option label="Linux" value="linux" /><el-option label="Windows" value="windows" /><el-option label="数据库" value="database" />
            <el-option label="Web" value="web" /><el-option label="网络" value="network" /><el-option label="安全" value="security" />
          </el-select></el-form-item>

          <el-row :gutter="16">
            <el-col :span="8"><el-form-item label="适用资产类型">
              <el-select v-model="form.applicable_asset_types" multiple style="width:100%">
                <el-option label="Linux" value="linux_server" /><el-option label="Windows" value="windows_server" />
                <el-option label="数据库" value="database" /><el-option label="Web服务" value="web_service" />
              </el-select>
            </el-form-item></el-col>
            <el-col :span="8"><el-form-item label="风险等级">
              <el-select v-model="form.risk_level" style="width:100%">
                <el-option label="低" value="low" /><el-option label="中" value="medium" /><el-option label="高" value="high" />
              </el-select>
            </el-form-item></el-col>
            <el-col :span="8"><el-form-item label="可自动执行">
              <el-switch v-model="form.auto_executable" />
            </el-form-item></el-col>
          </el-row>

          <el-divider content-position="left">触发条件</el-divider>
          <div v-for="(trig, idx) in form.trigger_events" :key="'t'+idx" style="display:flex;gap:8px;margin-bottom:8px;align-items:center">
            <el-input v-model="trig.event" placeholder="事件类型" style="width:200px" />
            <el-input v-model="trig.condition" placeholder="条件描述" style="width:300px" />
            <el-button size="small" type="danger" @click="form.trigger_events.splice(idx,1)"><el-icon><Delete /></el-icon></el-button>
          </div>
          <el-button size="small" @click="form.trigger_events.push({event:'',condition:''})">+ 添加触发条件</el-button>

          <el-divider content-position="left">诊断步骤</el-divider>
          <div v-for="(step, idx) in form.diagnosis_steps" :key="'d'+idx" class="step-block">
            <div style="display:flex;gap:8px;align-items:center;margin-bottom:4px">
              <span class="step-num">{{ idx+1 }}</span>
              <el-input v-model="step.name" placeholder="步骤名称" style="width:200px" />
              <el-input v-model="step.command" placeholder="命令/操作" style="width:300px" />
              <el-button size="small" @click="moveItem(form.diagnosis_steps, idx, -1)">↑</el-button>
              <el-button size="small" @click="moveItem(form.diagnosis_steps, idx, 1)">↓</el-button>
              <el-button size="small" type="danger" @click="form.diagnosis_steps.splice(idx,1)"><el-icon><Delete /></el-icon></el-button>
            </div>
            <el-input v-model="step.description" type="textarea" :rows="2" placeholder="详细说明" />
          </div>
          <el-button size="small" @click="form.diagnosis_steps.push({name:'',command:'',description:''})">+ 添加诊断步骤</el-button>

          <el-divider content-position="left">处置步骤</el-divider>
          <div v-for="(step, idx) in form.action_steps" :key="'a'+idx" class="step-block">
            <div style="display:flex;gap:8px;align-items:center;margin-bottom:4px">
              <span class="step-num action-num">{{ idx+1 }}</span>
              <el-input v-model="step.name" placeholder="步骤名称" style="width:200px" />
              <el-select v-model="step.type" style="width:120px">
                <el-option label="脚本" value="script" /><el-option label="命令" value="command" />
                <el-option label="人工" value="manual" /><el-option label="审批" value="approval" />
              </el-select>
              <el-input v-model="step.target" placeholder="目标脚本/命令" style="width:250px" />
              <el-button size="small" @click="moveItem(form.action_steps, idx, -1)">↑</el-button>
              <el-button size="small" @click="moveItem(form.action_steps, idx, 1)">↓</el-button>
              <el-button size="small" type="danger" @click="form.action_steps.splice(idx,1)"><el-icon><Delete /></el-icon></el-button>
            </div>
            <el-input v-model="step.description" type="textarea" :rows="2" placeholder="详细说明" />
          </div>
          <el-button size="small" @click="form.action_steps.push({name:'',type:'command',target:'',description:''})">+ 添加处置步骤</el-button>

          <el-divider content-position="left">验证步骤</el-divider>
          <div v-for="(step, idx) in form.verification_steps" :key="'v'+idx" style="display:flex;gap:8px;margin-bottom:8px;align-items:center">
            <span class="step-num verify-num">{{ idx+1 }}</span>
            <el-input v-model="step.name" placeholder="验证项" style="width:200px" />
            <el-input v-model="step.expected" placeholder="期望结果" style="width:300px" />
            <el-button size="small" type="danger" @click="form.verification_steps.splice(idx,1)"><el-icon><Delete /></el-icon></el-button>
          </div>
          <el-button size="small" @click="form.verification_steps.push({name:'',expected:''})">+ 添加验证步骤</el-button>

          <el-divider content-position="left">关联资源</el-divider>
          <el-row :gutter="16">
            <el-col :span="8"><el-form-item label="关联策略">
              <el-input v-model="form.related_policy_id" placeholder="策略ID (可选)" />
            </el-form-item></el-col>
            <el-col :span="8"><el-form-item label="关联Playbook">
              <el-input v-model="form.related_playbook_id" placeholder="Playbook ID (可选)" />
            </el-form-item></el-col>
            <el-col :span="8"><el-form-item label="关联脚本">
              <el-input v-model="form.related_script_id" placeholder="脚本ID (可选)" />
            </el-form-item></el-col>
          </el-row>
        </el-form>
      </el-tab-pane>

      <!-- 富文本编辑 -->
      <el-tab-pane label="富文本编辑" name="richtext">
        <div class="richtext-toolbar">
          <el-button-group>
            <el-button size="small" @click="execCmd('bold')" title="加粗"><strong>B</strong></el-button>
            <el-button size="small" @click="execCmd('italic')" title="斜体"><em>I</em></el-button>
            <el-button size="small" @click="execCmd('underline')" title="下划线"><u>U</u></el-button>
          </el-button-group>
          <el-button-group style="margin-left:8px">
            <el-button size="small" @click="execCmd('insertUnorderedList')" title="无序列表">• 列表</el-button>
            <el-button size="small" @click="execCmd('insertOrderedList')" title="有序列表">1. 列表</el-button>
          </el-button-group>
          <el-button-group style="margin-left:8px">
            <el-button size="small" @click="execCmd('formatBlock','<h2>')" title="标题2">H2</el-button>
            <el-button size="small" @click="execCmd('formatBlock','<h3>')" title="标题3">H3</el-button>
            <el-button size="small" @click="execCmd('formatBlock','<p>')" title="正文">P</el-button>
          </el-button-group>
          <el-button-group style="margin-left:8px">
            <el-button size="small" @click="execCmd('insertHorizontalRule')">分割线</el-button>
            <el-button size="small" @click="insertCodeBlock">代码块</el-button>
          </el-button-group>
        </div>
        <div ref="editorRef" class="richtext-editor" contenteditable="true" @input="onEditorInput" v-html="form.content" />
      </el-tab-pane>

      <!-- 预览 -->
      <el-tab-pane label="预览" name="preview">
        <div class="autops-card">
          <h2>{{ form.title || '(未命名)' }}</h2>
          <div style="margin:8px 0">
            <el-tag v-for="t in form.tags" :key="t" size="small" style="margin-right:4px">{{ t }}</el-tag>
          </div>
          <el-descriptions :column="3" size="small" border style="margin-bottom:16px">
            <el-descriptions-item label="分类">{{ form.category }}</el-descriptions-item>
            <el-descriptions-item label="风险">{{ form.risk_level }}</el-descriptions-item>
            <el-descriptions-item label="可自动执行">{{ form.auto_executable ? '是' : '否' }}</el-descriptions-item>
          </el-descriptions>

          <template v-if="form.trigger_events.length">
            <h3>触发条件</h3>
            <ul><li v-for="(t,i) in form.trigger_events" :key="i">{{ t.event }}: {{ t.condition }}</li></ul>
          </template>

          <template v-if="form.diagnosis_steps.length">
            <h3>诊断步骤</h3>
            <ol><li v-for="(s,i) in form.diagnosis_steps" :key="i"><strong>{{ s.name }}</strong> <code v-if="s.command">{{ s.command }}</code><p>{{ s.description }}</p></li></ol>
          </template>

          <template v-if="form.action_steps.length">
            <h3>处置步骤</h3>
            <ol><li v-for="(s,i) in form.action_steps" :key="i"><strong>{{ s.name }}</strong> [{{ s.type }}] <code v-if="s.target">{{ s.target }}</code><p>{{ s.description }}</p></li></ol>
          </template>

          <template v-if="form.verification_steps.length">
            <h3>验证步骤</h3>
            <ul><li v-for="(s,i) in form.verification_steps" :key="i">{{ s.name }} → 期望: {{ s.expected }}</li></ul>
          </template>

          <div v-if="form.content" v-html="form.content" style="margin-top:16px" />
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Check, Delete } from '@element-plus/icons-vue'
import api from '@/shared/api/client'
import { API } from '@/shared/api/routes'

const router = useRouter()
const route = useRoute()
const saving = ref(false)
const activeTab = ref('structured')
const editorRef = ref<HTMLElement>()

const form = reactive({
  title: 'primary', category: 'incident_response', tags: [] as string[],
  applicable_asset_types: [] as string[], risk_level: 'low', auto_executable: false,
  trigger_events: [] as { event: string; condition: string }[],
  diagnosis_steps: [] as { name: string; command: string; description: string }[],
  action_steps: [] as { name: string; type: string; target: string; description: string }[],
  verification_steps: [] as { name: string; expected: string }[],
  related_policy_id: 'primary', related_playbook_id: 'primary', related_script_id: 'primary',
  content: 'primary',
})

function goBack() { router.push('/knowledge') }
function moveItem(arr: any[], idx: number, dir: number) { if (arr[idx+dir]) { const t=arr[idx]; arr[idx]=arr[idx+dir]; arr[idx+dir]=t } }

function execCmd(cmd: string, val?: string) { document.execCommand(cmd, false, val) }
function insertCodeBlock() { document.execCommand('insertHTML', false, '<pre style="background:#f5f5f5;padding:8px;border-radius:4px;font-family:monospace">code here</pre>') }
function onEditorInput() { if (editorRef.value) form.content = editorRef.value.innerHTML }

async function loadKnowledge(id: string) {
  try {
    const res = await api.get(API.KNOWLEDGE_DETAIL(id))
    if (res.data?.code === 0) {
      const d = res.data.data
      form.title = d.title || ''; form.category = d.category || 'incident_response'; form.tags = d.tags || []
      form.applicable_asset_types = d.applicable_asset_types || []; form.risk_level = d.risk_level || 'low'
      form.auto_executable = !!d.auto_executable; form.content = d.content || ''
      form.trigger_events = d.trigger_events || []; form.diagnosis_steps = d.diagnosis_steps || []
      form.action_steps = d.action_steps || []; form.verification_steps = d.verification_steps || []
      form.related_policy_id = d.related_policy_id || ''; form.related_playbook_id = d.related_playbook_id || ''
      form.related_script_id = d.related_script_id || ''
    }
  } catch {}
}

async function save() {
  if (!form.title) return ElMessage.warning('请输入标题')
  saving.value = true
  try {
    const id = route.params.id as string
    const payload = { ...form }
    if (id) await api.put(API.KNOWLEDGE_DETAIL(id), payload)
    else await api.post(API.KNOWLEDGE, payload)
    ElMessage.success('保存成功'); goBack()
  } catch (e: any) { ElMessage.error(e?.message || '保存失败') }
  finally { saving.value = false }
}

async function saveAndPublish() {
  if (!form.title) return ElMessage.warning('请输入标题')
  saving.value = true
  try {
    const id = route.params.id as string
    const payload = { ...form, status: 'published' }
    if (id) { await api.put(API.KNOWLEDGE_DETAIL(id), payload); await api.post(API.KNOWLEDGE_PUBLISH(id)) }
    else { const res = await api.post(API.KNOWLEDGE, payload); const newId = res.data?.data?.id; if (newId) await api.post(API.KNOWLEDGE_PUBLISH(newId)) }
    ElMessage.success('保存并发布成功'); goBack()
  } catch (e: any) { ElMessage.error(e?.message || '操作失败') }
  finally { saving.value = false }
}

onMounted(() => { const id = route.params.id as string; if (id) loadKnowledge(id) })
</script>

<style scoped>

.toolbar { margin-bottom: var(--autops-space-lg); display: flex; gap: 8px; align-items: center; }
.step-block { background: var(--autops-bg-2); padding: var(--autops-space-sm); border-radius: var(--autops-radius-sm); margin-bottom: var(--autops-space-sm); }
.step-num { width: 22px; height: 22px; background: var(--autops-primary); color: var(--autops-bg-1); border-radius: 50%; text-align: center; line-height: 22px; font-size: 11px; display: inline-block; }
.action-num { background: var(--autops-warning); }
.verify-num { background: var(--autops-success); }
.richtext-toolbar { padding: var(--autops-space-sm); border: 1px solid var(--autops-bg-4); border-bottom: none; border-radius: var(--autops-radius-sm) 4px 0 0; background: var(--autops-bg-2); }
.richtext-editor { min-height: 400px; border: 1px solid var(--autops-bg-4); border-radius: 0 0 4px 4px; padding: var(--autops-space-md); outline: none; font-size: var(--autops-font-14); line-height: 1.8; }
.richtext-editor:focus { border-color: var(--autops-primary); }
</style>
