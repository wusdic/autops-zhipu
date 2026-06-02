import { ref } from 'vue'
import { ElMessage } from 'element-plus'

export function useFormSubmit(
  submitFn: (data: any) => Promise<any>,
  options?: { successMsg?: string; errorMsg?: string }
) {
  const submitting = ref(false)

  async function submit(data: any) {
    submitting.value = true
    try {
      const res = await submitFn(data)
      ElMessage.success(options?.successMsg || '操作成功')
      return res
    } catch (e: any) {
      const msg = e?.response?.data?.detail || options?.errorMsg || '操作失败'
      if (Array.isArray(msg)) {
        ElMessage.error(msg.map((m: any) => m.msg || m.message || m).join('; '))
      } else {
        ElMessage.error(String(msg))
      }
      throw e
    } finally {
      submitting.value = false
    }
  }

  return { submitting, submit }
}
