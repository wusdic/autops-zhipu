import { ref } from 'vue'

export function useDialog<T = any>() {
  const visible = ref(false)
  const mode = ref<'create' | 'edit' | 'view'>('create')
  const editingRow = ref<T | null>(null)

  function openCreate() { mode.value = 'create'; editingRow.value = null; visible.value = true }
  function openEdit(row: T) { mode.value = 'edit'; editingRow.value = row; visible.value = true }
  function openView(row: T) { mode.value = 'view'; editingRow.value = row; visible.value = true }
  function close() { visible.value = false; editingRow.value = null }

  return { visible, mode, editingRow, openCreate, openEdit, openView, close }
}
