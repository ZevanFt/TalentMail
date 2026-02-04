/**
 * API 基础模块
 * 提供通用的 API 请求方法和 Token 管理
 */

const API_BASE = '/api'

export interface ApiResponse<T> {
  status: string
  data: T
}

export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH'

export const useApiBase = () => {
  const token = useCookie('token')

  const api = async <T>(url: string, method: HttpMethod = 'GET', body?: any): Promise<T> => {
    return await $fetch<T>(`${API_BASE}${url}`, {
      method,
      headers: {
        'Content-Type': 'application/json',
        ...(token.value ? { Authorization: `Bearer ${token.value}` } : {})
      },
      body: body ? JSON.stringify(body) : undefined
    })
  }

  const apiFormData = async <T>(url: string, formData: FormData): Promise<T> => {
    return await $fetch<T>(`${API_BASE}${url}`, {
      method: 'POST',
      headers: token.value ? { Authorization: `Bearer ${token.value}` } : {},
      body: formData
    })
  }

  return { api, apiFormData, token, API_BASE }
}
