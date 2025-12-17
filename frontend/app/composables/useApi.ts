const API_BASE = '/api'

interface ApiResponse<T> {
  status: string
  data: T
}

type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE'

export const useApi = () => {
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

  // Auth
  const login = async (email: string, password: string) => {
    const formData = new URLSearchParams()
    formData.append('username', email)
    formData.append('password', password)
    
    const res = await $fetch<{ access_token: string }>(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData.toString()
    })
    token.value = res.access_token
    return res
  }

  const logout = () => {
    token.value = null
  }

  // Folders
  const getFolders = () => api<ApiResponse<any[]>>('/folders')

  // Emails
  const getEmails = (folderId: number, page = 1, limit = 50) =>
    api<ApiResponse<{ items: any[]; total: number }>>(`/emails?folder_id=${folderId}&page=${page}&limit=${limit}`)

  const getEmail = (id: number) => api<ApiResponse<any>>(`/emails/${id}`)

  const sendEmail = (data: { to: string; subject: string; body_text?: string; body_html?: string }) => {
    // 将逗号分隔的收件人转换为 EmailRecipient 数组
    const recipients = data.to.split(',').map(email => ({ email: email.trim() }))
    return api<any>('/emails/send', 'POST', { to: recipients, subject: data.subject, body_text: data.body_text, body_html: data.body_html || '' })
  }

  const syncEmails = () => api<ApiResponse<{ new_emails: number }>>('/emails/sync', 'POST')

  return { login, logout, getFolders, getEmails, getEmail, sendEmail, syncEmails, token }
}