import client from './client'
import { API } from './routes'

export const inspectionService = {
  listTemplates: (params?: Record<string, any>) => client.get(API.INSPECTION.TEMPLATES, { params }),
  getTemplate: (id: string) => client.get(API.INSPECTION.TEMPLATE_DETAIL(id)),
  createTemplate: (data: Record<string, any>) => client.post(API.INSPECTION.TEMPLATES, data),
  updateTemplate: (id: string, data: Record<string, any>) => client.put(API.INSPECTION.TEMPLATE_DETAIL(id), data),
  deleteTemplate: (id: string) => client.delete(API.INSPECTION.TEMPLATE_DETAIL(id)),
  listPlans: (params?: Record<string, any>) => client.get(API.INSPECTION.PLANS, { params }),
  getPlan: (id: string) => client.get(API.INSPECTION.PLAN_DETAIL(id)),
  createPlan: (data: Record<string, any>) => client.post(API.INSPECTION.PLANS, data),
  updatePlan: (id: string, data: Record<string, any>) => client.put(API.INSPECTION.PLAN_DETAIL(id), data),
  deletePlan: (id: string) => client.delete(API.INSPECTION.PLAN_DETAIL(id)),
  listTasks: (params?: Record<string, any>) => client.get(API.INSPECTION.TASKS, { params }),
  getTask: (id: string) => client.get(API.INSPECTION.TASK_DETAIL(id)),
  triggerTask: (data: Record<string, any>) => client.post(API.INSPECTION.TASKS, data),
  listResults: (params?: Record<string, any>) => client.get(API.INSPECTION.RESULTS, { params }),
  getResult: (id: string) => client.get(API.INSPECTION.RESULT_DETAIL(id)),
  listReports: (params?: Record<string, any>) => client.get(API.INSPECTION.REPORTS, { params }),
  getReport: (id: string) => client.get(API.INSPECTION.REPORT_DETAIL(id)),
  overview: () => client.get(API.INSPECTION.STATS),
}
