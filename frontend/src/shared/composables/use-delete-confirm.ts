import { ElMessageBox, ElMessage } from 'element-plus'

export function useDeleteConfirm(
  deleteFn: (id: string) => Promise<any>,
  options?: { title?: string; message?: string; successMsg?: string }
) {
  async function confirmDelete(id: string, name?: string) {
    await ElMessageBox.confirm(
      options?.message || `确定要删除${name ? ' ' + name : '该项'}吗？此操作不可撤销。`,
      options?.title || '删除确认',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' }
    )
    await deleteFn(id)
    ElMessage.success(options?.successMsg || '删除成功')
  }

  return { confirmDelete }
}
