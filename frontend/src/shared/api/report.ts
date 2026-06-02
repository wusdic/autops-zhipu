import client from './client'
import { API } from './routes'

export const reportService = {
  listTemplates: (params?: Record<string, any>) => client.get(API.REPORT.TEMPLATES, { params }),
  getTemplate: (id: string) => client.get(API.REPORT.TEMPLATE_DETAIL(id)),
  createTemplate: (data: Record<string, any>) => client.post(API.REPORT.TEMPLATES, data),
  updateTemplate: (id: string, data: Record<string, any>) => client.put(API.REPORT.TEMPLATE_DETAIL(id), data),
  deleteTemplate: (id: string) => client.delete(API.REPORT.TEMPLATE_DETAIL(id)),
  generate: (data: Record<string, any>) => client.post(API.REPORT.GENERATE, data),
  listTasks: (params?: Record<string, any>) => client.get(API.REPORT.TASKS, { params }),
  getTask: (id: string) => client.get(API.REPORT.TASK_DETAIL(id)),
  getPreview: (id: string) => client.get(API.REPORT.PREVIEW(id)),
  download: (id: string) => client.get(API.REPORT.DOWNLOAD(id), { responseType: 'blob' }),
  listArchive: (params?: Record<string, any>) => client.get(API.REPORT.ARCHIVE, { params }),
  getArchiveDetail: (id: string) => client.get(API.REPORT.ARCHIVE_DETAIL(id)),
  overview: () => client.get(API.REPORT.STATS),
}
