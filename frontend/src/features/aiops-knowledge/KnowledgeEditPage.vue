<template>
  <div class="knowledge-edit">
    <!-- 顶部导航 -->
    <div class="page-top">
      <el-button @click="goBack" :icon="ArrowLeft">返回详情</el-button>
      <span class="page-title">编辑知识文章</span>
    </div>

    <div v-loading="loading" class="edit-body">
      <!-- 空状态 -->
      <el-empty v-if="!loading && !formData" description="知识文章不存在或已被删除">
        <el-button type="primary" @click="goBack">返回列表</el-button>
      </el-empty>

      <el-card v-if="formData" shadow="hover">
        <el-form
          ref="formRef"
          :model="formData"
          :rules="rules"
          label-width="100px"
          label-position="right"
        >
          <!-- 标题 -->
          <el-form-item label="标题" prop="title">
            <el-input v-model="formData.title" placeholder="请输入知识文章标题" maxlength="200" show-word-limit />
          </el-form-item>

          <!-- 类型 + 风险等级 -->
          <el-row :gutter="24">
            <el-col :span="12">
              <el-form-item label="类型" prop="article_type">
                <el-select v-model="formData.article_type" placeholder="请选择文章类型" style="width: 100%">
                  <el-option label="标准方案" value="standard_solution" />
                  <el-option label="事件总结" value="incident_summary" />
                  <el-option label="最佳实践" value="best_practice" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="风险等级" prop="risk_level">
                <el-select v-model="formData.risk_level" placeholder="请选择风险等级" style="width: 100%">
                  <el-option label="高" value="high" />
                  <el-option label="中" value="medium" />
                  <el-option label="低" value="low" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>

          <!-- 正文内容 -->
          <el-form-item label="内容" prop="content">
            <el-input
              v-model="formData.content"
              type="textarea"
              placeholder="请输入文章正文内容（支持 Markdown 格式）"
              :autosize="{ minRows: 6, maxRows: 20 }"
            />
          </el-form-item>

          <!-- 诊断步骤 -->
          <el-form-item label="诊断步骤" prop="diagnosis_steps">
            <el-input
              v-model="formData.diagnosis_steps"
              type="textarea"
              placeholder="请输入诊断步骤（支持 Markdown 格式）"
              :autosize="{ minRows: 4, maxRows: 16 }"
            />
          </el-form-item>

          <!-- 处置步骤 -->
          <el-form-item label="处置步骤" prop="resolution_steps">
            <el-input
              v-model="formData.resolution_steps"
              type="textarea"
              placeholder="请输入处置步骤（支持 Markdown 格式）"
              :autosize="{ minRows: 4, maxRows: 16 }"
            />
          </el-form-item>

          <!-- 验证步骤 -->
          <el-form-item label="验证步骤" prop="verification_steps">
            <el-input
              v-model="formData.verification_steps"
              type="textarea"
              placeholder="请输入验证步骤（支持 Markdown 格式）"
              :autosize="{ minRows: 4, maxRows: 16 }"
            />
          </el-form-item>

          <!-- 操作按钮 -->
          <el-form-item>
            <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
            <el-button @click="goBack">取消</el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import api from '@/shared/api/client'
import { API } from '@/shared/api/routes'

const route = useRoute()
const router = useRouter()

const knowledgeId = route.params.id as string
const loading = ref(false)
const saving = ref(false)
const formRef = ref<FormInstance>()

/** 表单数据 */
const formData = ref<{
  title: string
  article_type: string
  risk_level: string
  content: string
  diagnosis_steps: string
  resolution_steps: string
  verification_steps: string
} | null>(null)

/** 表单校验规则 */
const rules: FormRules = {
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
  article_type: [{ required: true, message: '请选择文章类型', trigger: 'change' }],
  risk_level: [{ required: true, message: '请选择风险等级', trigger: 'change' }],
}

/** 返回详情页 */
function goBack() {
  router.push({ name: 'knowledge-detail', params: { id: knowledgeId } })
}

/** 加载知识详情以填充编辑表单 */
async function loadArticle() {
  loading.value = true
  try {
    const { data } = await api.get(API.KNOWLEDGE_DETAIL(knowledgeId))
    if (data.code === 0) {
      const d = data.data
      formData.value = {
        title: d.title || '',
        article_type: d.article_type || '',
        risk_level: d.risk_level || '',
        content: d.content || '',
        diagnosis_steps: d.diagnosis_steps || '',
        resolution_steps: d.resolution_steps || '',
        verification_steps: d.verification_steps || '',
      }
    }
  } catch (e: any) {
    ElMessage.error('加载知识详情失败: ' + (e.message || e))
  } finally {
    loading.value = false
  }
}

/** 保存编辑 */
async function handleSave() {
  if (!formRef.value || !formData.value) return

  try {
    const valid = await formRef.value.validate()
    if (!valid) return
  } catch {
    return // 校验不通过
  }

  saving.value = true
  try {
    const { data } = await api.put(API.KNOWLEDGE_DETAIL(knowledgeId), {
      title: formData.value.title,
      article_type: formData.value.article_type,
      risk_level: formData.value.risk_level,
      content: formData.value.content,
      diagnosis_steps: formData.value.diagnosis_steps,
      resolution_steps: formData.value.resolution_steps,
      verification_steps: formData.value.verification_steps,
    })
    if (data.code === 0) {
      ElMessage.success('保存成功')
      router.push({ name: 'knowledge-detail', params: { id: knowledgeId } })
    }
  } catch (e: any) {
    ElMessage.error('保存失败: ' + (e.message || e))
  } finally {
    saving.value = false
  }
}

onMounted(() => loadArticle())
</script>

<style scoped>
.page-top {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}
.page-title {
  margin-left: 16px;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}
.edit-body {
  max-width: 900px;
}
</style>
