     1|<template>
     2|  <div class="page-container">
     3|    <div class="autops-page-header">
     4|      <div>
     5|        <div class="autops-page-title">编辑知识</div>
     6|        <div class="autops-page-desc">编辑知识条目内容</div>
     7|      </div>
     8|    </div>
     9|
    10|    <div class="autops-toolbar">
    11|      <el-button @click="goBack"><el-icon><ArrowLeft /></el-icon> 返回</el-button>
    12|      <div style="flex:1" />
    13|      <el-button type="primary" @click="save" :loading="saving"><el-icon><Check /></el-icon> 保存</el-button>
    14|      <el-button @click="saveAndPublish" :loading="saving">保存并发布</el-button>
    15|    </div>
    16|
    17|    <el-tabs v-model="activeTab">
    18|      <!-- 结构化编辑 -->
    19|      <el-tab-pane label="结构化编辑" name="structured">
    20|        <el-form :model="form" label-width="120px">
    21|          <el-row :gutter="16">
    22|            <el-col :span="12"><el-form-item label="标题" required><el-input v-model="form.title" placeholder="知识标题" /></el-form-item></el-col>
    23|            <el-col :span="12"><el-form-item label="分类">
    24|              <el-select v-model="form.category" style="width:100%">
    25|                <el-option label="故障处置" value="incident_response" /><el-option label="巡检方案" value="inspection" />
    26|                <el-option label="最佳实践" value="best_practice" /><el-option label="配置指南" value="configuration" />
    27|                <el-option label="安全合规" value="security" /><el-option label="性能优化" value="optimization" />
    28|              </el-select>
    29|            </el-form-item></el-col>
    30|          </el-row>
    31|
    32|          <el-form-item label="标签"><el-select v-model="form.tags" multiple filterable allow-create default-first-option style="width:100%" placeholder="添加标签">
    33|            <el-option label="Linux" value="linux" /><el-option label="Windows" value="windows" /><el-option label="数据库" value="database" />
    34|            <el-option label="Web" value="web" /><el-option label="网络" value="network" /><el-option label="安全" value="security" />
    35|          </el-select></el-form-item>
    36|
    37|          <el-row :gutter="16">
    38|            <el-col :span="8"><el-form-item label="适用资产类型">
    39|              <el-select v-model="form.applicable_asset_types" multiple style="width:100%">
    40|                <el-option label="Linux" value="linux_server" /><el-option label="Windows" value="windows_server" />
    41|                <el-option label="数据库" value="database" /><el-option label="Web服务" value="web_service" />
    42|              </el-select>
    43|            </el-form-item></el-col>
    44|            <el-col :span="8"><el-form-item label="风险等级">
    45|              <el-select v-model="form.risk_level" style="width:100%">
    46|                <el-option label="低" value="low" /><el-option label="中" value="medium" /><el-option label="高" value="high" />
    47|              </el-select>
    48|            </el-form-item></el-col>
    49|            <el-col :span="8"><el-form-item label="可自动执行">
    50|              <el-switch v-model="form.auto_executable" />
    51|            </el-form-item></el-col>
    52|          </el-row>
    53|
    54|          <el-divider content-position="left">触发条件</el-divider>
    55|          <div v-for="(trig, idx) in form.trigger_events" :key="'t'+idx" style="display:flex;gap:8px;margin-bottom:8px;align-items:center">
    56|            <el-input v-model="trig.event" placeholder="事件类型" style="width:200px" />
    57|            <el-input v-model="trig.condition" placeholder="条件描述" style="width:300px" />
    58|            <el-button size="small" type="danger" @click="form.trigger_events.splice(idx,1)"><el-icon><Delete /></el-icon></el-button>
    59|          </div>
    60|          <el-button size="small" @click="form.trigger_events.push({event:'',condition:''})">+ 添加触发条件</el-button>
    61|
    62|          <el-divider content-position="left">诊断步骤</el-divider>
    63|          <div v-for="(step, idx) in form.diagnosis_steps" :key="'d'+idx" class="step-block">
    64|            <div style="display:flex;gap:8px;align-items:center;margin-bottom:4px">
    65|              <span class="step-num">{{ idx+1 }}</span>
    66|              <el-input v-model="step.name" placeholder="步骤名称" style="width:200px" />
    67|              <el-input v-model="step.command" placeholder="命令/操作" style="width:300px" />
    68|              <el-button size="small" @click="moveItem(form.diagnosis_steps, idx, -1)">↑</el-button>
    69|              <el-button size="small" @click="moveItem(form.diagnosis_steps, idx, 1)">↓</el-button>
    70|              <el-button size="small" type="danger" @click="form.diagnosis_steps.splice(idx,1)"><el-icon><Delete /></el-icon></el-button>
    71|            </div>
    72|            <el-input v-model="step.description" type="textarea" :rows="2" placeholder="详细说明" />
    73|          </div>
    74|          <el-button size="small" @click="form.diagnosis_steps.push({name:'',command:'',description:''})">+ 添加诊断步骤</el-button>
    75|
    76|          <el-divider content-position="left">处置步骤</el-divider>
    77|          <div v-for="(step, idx) in form.action_steps" :key="'a'+idx" class="step-block">
    78|            <div style="display:flex;gap:8px;align-items:center;margin-bottom:4px">
    79|              <span class="step-num action-num">{{ idx+1 }}</span>
    80|              <el-input v-model="step.name" placeholder="步骤名称" style="width:200px" />
    81|              <el-select v-model="step.type" style="width:120px">
    82|                <el-option label="脚本" value="script" /><el-option label="命令" value="command" />
    83|                <el-option label="人工" value="manual" /><el-option label="审批" value="approval" />
    84|              </el-select>
    85|              <el-input v-model="step.target" placeholder="目标脚本/命令" style="width:250px" />
    86|              <el-button size="small" @click="moveItem(form.action_steps, idx, -1)">↑</el-button>
    87|              <el-button size="small" @click="moveItem(form.action_steps, idx, 1)">↓</el-button>
    88|              <el-button size="small" type="danger" @click="form.action_steps.splice(idx,1)"><el-icon><Delete /></el-icon></el-button>
    89|            </div>
    90|            <el-input v-model="step.description" type="textarea" :rows="2" placeholder="详细说明" />
    91|          </div>
    92|          <el-button size="small" @click="form.action_steps.push({name:'',type:'command',target:'',description:''})">+ 添加处置步骤</el-button>
    93|
    94|          <el-divider content-position="left">验证步骤</el-divider>
    95|          <div v-for="(step, idx) in form.verification_steps" :key="'v'+idx" style="display:flex;gap:8px;margin-bottom:8px;align-items:center">
    96|            <span class="step-num verify-num">{{ idx+1 }}</span>
    97|            <el-input v-model="step.name" placeholder="验证项" style="width:200px" />
    98|            <el-input v-model="step.expected" placeholder="期望结果" style="width:300px" />
    99|            <el-button size="small" type="danger" @click="form.verification_steps.splice(idx,1)"><el-icon><Delete /></el-icon></el-button>
   100|          </div>
   101|          <el-button size="small" @click="form.verification_steps.push({name:'',expected:''})">+ 添加验证步骤</el-button>
   102|
   103|          <el-divider content-position="left">关联资源</el-divider>
   104|          <el-row :gutter="16">
   105|            <el-col :span="8"><el-form-item label="关联策略">
   106|              <el-input v-model="form.related_policy_id" placeholder="策略ID (可选)" />
   107|            </el-form-item></el-col>
   108|            <el-col :span="8"><el-form-item label="关联Playbook">
   109|              <el-input v-model="form.related_playbook_id" placeholder="Playbook ID (可选)" />
   110|            </el-form-item></el-col>
   111|            <el-col :span="8"><el-form-item label="关联脚本">
   112|              <el-input v-model="form.related_script_id" placeholder="脚本ID (可选)" />
   113|            </el-form-item></el-col>
   114|          </el-row>
   115|        </el-form>
   116|      </el-tab-pane>
   117|
   118|      <!-- 富文本编辑 -->
   119|      <el-tab-pane label="富文本编辑" name="richtext">
   120|        <div class="richtext-toolbar">
   121|          <el-button-group>
   122|            <el-button size="small" @click="execCmd('bold')" title="加粗"><strong>B</strong></el-button>
   123|            <el-button size="small" @click="execCmd('italic')" title="斜体"><em>I</em></el-button>
   124|            <el-button size="small" @click="execCmd('underline')" title="下划线"><u>U</u></el-button>
   125|          </el-button-group>
   126|          <el-button-group style="margin-left:8px">
   127|            <el-button size="small" @click="execCmd('insertUnorderedList')" title="无序列表">• 列表</el-button>
   128|            <el-button size="small" @click="execCmd('insertOrderedList')" title="有序列表">1. 列表</el-button>
   129|          </el-button-group>
   130|          <el-button-group style="margin-left:8px">
   131|            <el-button size="small" @click="execCmd('formatBlock','<h2>')" title="标题2">H2</el-button>
   132|            <el-button size="small" @click="execCmd('formatBlock','<h3>')" title="标题3">H3</el-button>
   133|            <el-button size="small" @click="execCmd('formatBlock','<p>')" title="正文">P</el-button>
   134|          </el-button-group>
   135|          <el-button-group style="margin-left:8px">
   136|            <el-button size="small" @click="execCmd('insertHorizontalRule')">分割线</el-button>
   137|            <el-button size="small" @click="insertCodeBlock">代码块</el-button>
   138|          </el-button-group>
   139|        </div>
   140|        <div ref="editorRef" class="richtext-editor" contenteditable="true" @input="onEditorInput" v-html="form.content" />
   141|      </el-tab-pane>
   142|
   143|      <!-- 预览 -->
   144|      <el-tab-pane label="预览" name="preview">
   145|        <div class="autops-card">
   146|          <h2>{{ form.title || '(未命名)' }}</h2>
   147|          <div style="margin:8px 0">
   148|            <el-tag v-for="t in form.tags" :key="t" size="small" style="margin-right:4px">{{ t }}</el-tag>
   149|          </div>
   150|          <el-descriptions :column="3" size="small" border style="margin-bottom:16px">
   151|            <el-descriptions-item label="分类">{{ form.category }}</el-descriptions-item>
   152|            <el-descriptions-item label="风险">{{ form.risk_level }}</el-descriptions-item>
   153|            <el-descriptions-item label="可自动执行">{{ form.auto_executable ? '是' : '否' }}</el-descriptions-item>
   154|          </el-descriptions>
   155|
   156|          <template v-if="form.trigger_events.length">
   157|            <h3>触发条件</h3>
   158|            <ul><li v-for="(t,i) in form.trigger_events" :key="i">{{ t.event }}: {{ t.condition }}</li></ul>
   159|          </template>
   160|
   161|          <template v-if="form.diagnosis_steps.length">
   162|            <h3>诊断步骤</h3>
   163|            <ol><li v-for="(s,i) in form.diagnosis_steps" :key="i"><strong>{{ s.name }}</strong> <code v-if="s.command">{{ s.command }}</code><p>{{ s.description }}</p></li></ol>
   164|          </template>
   165|
   166|          <template v-if="form.action_steps.length">
   167|            <h3>处置步骤</h3>
   168|            <ol><li v-for="(s,i) in form.action_steps" :key="i"><strong>{{ s.name }}</strong> [{{ s.type }}] <code v-if="s.target">{{ s.target }}</code><p>{{ s.description }}</p></li></ol>
   169|          </template>
   170|
   171|          <template v-if="form.verification_steps.length">
   172|            <h3>验证步骤</h3>
   173|            <ul><li v-for="(s,i) in form.verification_steps" :key="i">{{ s.name }} → 期望: {{ s.expected }}</li></ul>
   174|          </template>
   175|
   176|          <div v-if="form.content" v-html="form.content" style="margin-top:16px" />
   177|        </div>
   178|      </el-tab-pane>
   179|    </el-tabs>
   180|  </div>
   181|</template>
   182|
   183|<script setup lang="ts">
   184|import { ref, reactive, onMounted } from 'vue'
   185|import { useRouter, useRoute } from 'vue-router'
   186|import { ElMessage } from 'element-plus'
   187|import { ArrowLeft, Check, Delete } from '@element-plus/icons-vue'
   188|import api from '@/shared/api/client'
   189|import { API } from '@/shared/api/routes'
   190|
   191|const router = useRouter()
   192|const route = useRoute()
   193|const saving = ref(false)
   194|const activeTab = ref('structured')
   195|const editorRef = ref<HTMLElement>()
   196|
   197|const form = reactive({
   198|  title: '', category: 'incident_response', tags: [] as string[],
   199|  applicable_asset_types: [] as string[], risk_level: 'low', auto_executable: false,
   200|  trigger_events: [] as { event: string; condition: string }[],
   201|  diagnosis_steps: [] as { name: string; command: string; description: string }[],
   202|  action_steps: [] as { name: string; type: string; target: string; description: string }[],
   203|  verification_steps: [] as { name: string; expected: string }[],
   204|  related_policy_id: '', related_playbook_id: '', related_script_id: '',
   205|  content: '',
   206|})
   207|
   208|function goBack() { router.push('/knowledge') }
   209|function moveItem(arr: any[], idx: number, dir: number) { if (arr[idx+dir]) { const t=arr[idx]; arr[idx]=arr[idx+dir]; arr[idx+dir]=t } }
   210|
   211|function execCmd(cmd: string, val?: string) { document.execCommand(cmd, false, val) }
   212|function insertCodeBlock() { document.execCommand('insertHTML', false, '<pre style="background:#f5f5f5;padding:8px;border-radius:4px;font-family:monospace">code here</pre>') }
   213|function onEditorInput() { if (editorRef.value) form.content = editorRef.value.innerHTML }
   214|
   215|async function loadKnowledge(id: string) {
   216|  try {
   217|    const res = await api.get(API.KNOWLEDGE_DETAIL(id))
   218|    if (res.data?.code === 0) {
   219|      const d = res.data.data
   220|      form.title = d.title || ''; form.category = d.category || 'incident_response'; form.tags = d.tags || []
   221|      form.applicable_asset_types = d.applicable_asset_types || []; form.risk_level = d.risk_level || 'low'
   222|      form.auto_executable = !!d.auto_executable; form.content = d.content || ''
   223|      form.trigger_events = d.trigger_events || []; form.diagnosis_steps = d.diagnosis_steps || []
   224|      form.action_steps = d.action_steps || []; form.verification_steps = d.verification_steps || []
   225|      form.related_policy_id = d.related_policy_id || ''; form.related_playbook_id = d.related_playbook_id || ''
   226|      form.related_script_id = d.related_script_id || ''
   227|    }
   228|  } catch {}
   229|}
   230|
   231|async function save() {
   232|  if (!form.title) return ElMessage.warning('请输入标题')
   233|  saving.value = true
   234|  try {
   235|    const id = route.params.id as string
   236|    const payload = { ...form }
   237|    if (id) await api.put(API.KNOWLEDGE_DETAIL(id), payload)
   238|    else await api.post(API.KNOWLEDGE, payload)
   239|    ElMessage.success('保存成功'); goBack()
   240|  } catch (e: any) { ElMessage.error(e?.message || '保存失败') }
   241|  finally { saving.value = false }
   242|}
   243|
   244|async function saveAndPublish() {
   245|  if (!form.title) return ElMessage.warning('请输入标题')
   246|  saving.value = true
   247|  try {
   248|    const id = route.params.id as string
   249|    const payload = { ...form, status: 'published' }
   250|    if (id) { await api.put(API.KNOWLEDGE_DETAIL(id), payload); await api.post(API.KNOWLEDGE_PUBLISH(id)) }
   251|    else { const res = await api.post(API.KNOWLEDGE, payload); const newId = res.data?.data?.id; if (newId) await api.post(API.KNOWLEDGE_PUBLISH(newId)) }
   252|    ElMessage.success('保存并发布成功'); goBack()
   253|  } catch (e: any) { ElMessage.error(e?.message || '操作失败') }
   254|  finally { saving.value = false }
   255|}
   256|
   257|onMounted(() => { const id = route.params.id as string; if (id) loadKnowledge(id) })
   258|</script>
   259|
   260|<style scoped>
   261|
   262|.toolbar { margin-bottom: 16px; display: flex; gap: 8px; align-items: center; }
   263|.step-block { background: #f7f8fa; padding: 8px; border-radius: 4px; margin-bottom: 8px; }
   264|.step-num { width: 22px; height: 22px; background: #165dff; color: #fff; border-radius: 50%; text-align: center; line-height: 22px; font-size: 11px; display: inline-block; }
   265|.action-num { background: #ff7d00; }
   266|.verify-num { background: #00b42a; }
   267|.richtext-toolbar { padding: 8px; border: 1px solid #dcdfe6; border-bottom: none; border-radius: 4px 4px 0 0; background: #f7f8fa; }
   268|.richtext-editor { min-height: 400px; border: 1px solid #dcdfe6; border-radius: 0 0 4px 4px; padding: 12px; outline: none; font-size: 14px; line-height: 1.8; }
   269|.richtext-editor:focus { border-color: #165dff; }
   270|</style>
   271|