import { ElMessage } from 'element-plus'

export function useDownload() {
  async function downloadBlob(blob: Blob, filename: string) {
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  }

  async function downloadFromApi(promise: Promise<{ data: Blob }>, filename: string) {
    try {
      const res = await promise
      downloadBlob(res.data, filename)
      ElMessage.success('下载成功')
    } catch (e: any) {
      ElMessage.error(e?.response?.data?.detail || '下载失败')
    }
  }

  return { downloadBlob, downloadFromApi }
}
