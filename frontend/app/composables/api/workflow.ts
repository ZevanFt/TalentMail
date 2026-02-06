/**
 * 工作流相关 API
 */
import { useApiBase } from './base'

export const useWorkflowApi = () => {
  const { api } = useApiBase()

  // ========== 系统工作流 ==========
  interface SystemWorkflow {
    id: number
    code: string
    name: string
    name_en: string | null
    description: string | null
    category: string
    nodes: any[]
    edges: any[]
    config_schema: any
    default_config: any
    version: number
    is_active: boolean
  }

  const getSystemWorkflows = (category?: string) => {
    let url = '/workflows/system'
    if (category) url += `?category=${category}`
    return api<SystemWorkflow[]>(url)
  }
  const getSystemWorkflow = (code: string) => api<SystemWorkflow>(`/workflows/system/${code}`)
  const getSystemWorkflowConfig = (code: string) =>
    api<{ workflow_id: number; workflow_code: string; config_schema: any; default_config: any; custom_config: any; effective_config: any }>(`/workflows/system/${code}/config`)
  const updateSystemWorkflowConfig = (code: string, config: any, nodeConfigs?: any) =>
    api<any>(`/workflows/system/${code}/config`, 'PUT', { config, node_configs: nodeConfigs })
  const executeSystemWorkflow = (code: string, triggerData: any) =>
    api<{ success: boolean; result: any }>(`/workflows/system/${code}/execute`, 'POST', { trigger_data: triggerData })

  // ========== 执行记录 ==========
  interface WorkflowExecution {
    id: number
    workflow_type: string
    workflow_id: number
    workflow_version: number | null
    user_id: number | null
    trigger_type: string | null
    status: string
    started_at: string | null
    finished_at: string | null
    result: any
    error_message: string | null
  }

  const getWorkflowExecutions = (workflowType?: string, workflowId?: number, status?: string, limit = 50) => {
    let url = `/workflows/executions?limit=${limit}`
    if (workflowType) url += `&workflow_type=${workflowType}`
    if (workflowId) url += `&workflow_id=${workflowId}`
    if (status) url += `&status=${status}`
    return api<WorkflowExecution[]>(url)
  }
  const getWorkflowExecutionDetail = (executionId: number) =>
    api<{ execution: WorkflowExecution; node_executions: any[] }>(`/workflows/executions/${executionId}`)

  // ========== 节点类型 ==========
  const getNodeTypes = (category?: string) => {
    let url = '/workflows/node-types'
    if (category) url += `?category=${category}`
    return api<any[]>(url)
  }

  // ========== 自定义工作流 ==========
  interface CustomWorkflow {
    id: number
    name: string
    description: string | null
    owner_id: number | null
    scope: string
    category: string | null
    status: string
    is_active: boolean
    version: number
    execution_count: number
  }

  const getWorkflows = (scope?: string, status?: string) => {
    let url = '/workflows/'
    const params: string[] = []
    if (scope) params.push(`scope=${scope}`)
    if (status) params.push(`status=${status}`)
    if (params.length > 0) url += '?' + params.join('&')
    return api<CustomWorkflow[]>(url)
  }
  const createWorkflow = (data: { name: string; description?: string; category?: string }) =>
    api<CustomWorkflow>('/workflows/', 'POST', data)
  interface WorkflowDetailInfo extends CustomWorkflow {
    config_schema: any
    default_config: any
    config: any
  }

  interface WorkflowDetailResponse {
    workflow: WorkflowDetailInfo
    nodes: any[]
    edges: any[]
  }

  const getWorkflow = (id: number) => api<WorkflowDetailResponse>(`/workflows/${id}`)
  const updateWorkflow = (id: number, data: { name?: string; description?: string; category?: string; is_active?: boolean; config_schema?: any; default_config?: any; config?: any }) =>
    api<CustomWorkflow>(`/workflows/${id}`, 'PUT', data)
  const saveWorkflowCanvas = (id: number, nodes: any[], edges: any[]) =>
    api<{ success: boolean; version: number; nodes_count: number; edges_count: number }>(`/workflows/${id}/canvas`, 'PUT', { nodes, edges })
  const publishWorkflow = (id: number) => api<CustomWorkflow>(`/workflows/${id}/publish`, 'POST')
  const deleteWorkflow = (id: number) => api<{ success: boolean }>(`/workflows/${id}`, 'DELETE')

  // ========== 工作流模板 ==========
  const getWorkflowTemplates = (options?: { category?: string; source_type?: string; tag?: string; q?: string; featured_only?: boolean; favorites_only?: boolean; page?: number; limit?: number }) => {
    let url = '/workflow-templates/'
    const params: string[] = []
    if (options?.category) params.push(`category=${options.category}`)
    if (options?.source_type) params.push(`source_type=${options.source_type}`)
    if (options?.tag) params.push(`tag=${encodeURIComponent(options.tag)}`)
    if (options?.q) params.push(`q=${encodeURIComponent(options.q)}`)
    if (options?.featured_only) params.push('featured_only=true')
    if (options?.favorites_only) params.push('favorites_only=true')
    if (options?.page) params.push(`page=${options.page}`)
    if (options?.limit) params.push(`limit=${options.limit}`)
    if (params.length > 0) url += '?' + params.join('&')
    return api<any[]>(url)
  }
  const getWorkflowTemplateCategories = () => api<string[]>('/workflow-templates/categories')
  const getWorkflowTemplateTags = () => api<string[]>('/workflow-templates/tags')
  const getWorkflowTemplate = (id: number) => api<any>(`/workflow-templates/${id}`)
  const useWorkflowTemplate = (id: number) => api<any>(`/workflow-templates/${id}/use`, 'POST')
  const toggleWorkflowTemplateFavorite = (id: number) => api<any>(`/workflow-templates/${id}/favorite`, 'POST')
  const createWorkflowTemplate = (data: any) => api<any>('/workflow-templates/', 'POST', data)
  const updateWorkflowTemplate = (id: number, data: any) => api<any>(`/workflow-templates/${id}`, 'PUT', data)
  const deleteWorkflowTemplate = (id: number) => api<any>(`/workflow-templates/${id}`, 'DELETE')
  const getPendingWorkflowTemplates = () => api<any[]>('/workflow-templates/pending')
  const reviewWorkflowTemplate = (id: number, data: { action: string; reason?: string }) => api<any>(`/workflow-templates/${id}/review`, 'POST', data)

  return {
    // 系统工作流
    getSystemWorkflows, getSystemWorkflow, getSystemWorkflowConfig, updateSystemWorkflowConfig, executeSystemWorkflow,
    // 执行记录
    getWorkflowExecutions, getWorkflowExecutionDetail,
    // 节点类型
    getNodeTypes,
    // 自定义工作流
    getWorkflows, createWorkflow, getWorkflow, updateWorkflow, saveWorkflowCanvas, publishWorkflow, deleteWorkflow,
    // 模板
    getWorkflowTemplates, getWorkflowTemplateCategories, getWorkflowTemplateTags, getWorkflowTemplate,
    useWorkflowTemplate, toggleWorkflowTemplateFavorite, createWorkflowTemplate, updateWorkflowTemplate,
    deleteWorkflowTemplate, getPendingWorkflowTemplates, reviewWorkflowTemplate
  }
}
