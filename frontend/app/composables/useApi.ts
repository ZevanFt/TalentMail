const API_BASE = '/api'

interface ApiResponse<T> {
  status: string
  data: T
}

type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH'

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
  const getEmails = (folderId: number, page = 1, limit = 50, isRead?: boolean, isStarred?: boolean) => {
    let url = `/emails?folder_id=${folderId}&page=${page}&limit=${limit}`
    if (isRead !== undefined) url += `&is_read=${isRead}`
    if (isStarred !== undefined) url += `&is_starred=${isStarred}`
    return api<ApiResponse<{ items: any[]; total: number }>>(url)
  }

  const getEmail = (id: number) => api<ApiResponse<any>>(`/emails/${id}`)

  const sendEmail = (data: { to: string; cc?: string; subject: string; body_text?: string; body_html?: string; reply_to_id?: number; is_tracked?: boolean }) => {
    // 将逗号分隔的收件人转换为 EmailRecipient 数组
    const toRecipients = data.to.split(',').filter(e => e.trim()).map(email => ({ email: email.trim() }))
    const ccRecipients = data.cc ? data.cc.split(',').filter(e => e.trim()).map(email => ({ email: email.trim() })) : []
    return api<any>('/emails/send', 'POST', {
      to: toRecipients,
      cc: ccRecipients,
      subject: data.subject,
      body_text: data.body_text,
      body_html: data.body_html || '',
      reply_to_id: data.reply_to_id,
      is_tracked: data.is_tracked || false
    })
  }

  const syncEmails = () => api<ApiResponse<{ new_emails: number }>>('/emails/sync', 'POST')

  const markEmailRead = (id: number, isRead: boolean) =>
    api<ApiResponse<{ id: number; is_read: boolean }>>(`/emails/${id}/read?is_read=${isRead}`, 'PATCH')

  const deleteEmail = (id: number) =>
    api<ApiResponse<{ id: number }>>(`/emails/${id}`, 'DELETE')

  const markEmailStarred = (id: number, isStarred: boolean) =>
    api<ApiResponse<{ id: number; is_starred: boolean }>>(`/emails/${id}/star?is_starred=${isStarred}`, 'PATCH')

  const snoozeEmail = (id: number, snoozeUntil: string | null) => {
    const url = snoozeUntil ? `/emails/${id}/snooze?snooze_until=${encodeURIComponent(snoozeUntil)}` : `/emails/${id}/snooze`
    return api<ApiResponse<{ id: number; snoozed_until: string | null }>>(url, 'PATCH')
  }

  const getAllEmails = (page = 1, limit = 50, isRead?: boolean, isStarred?: boolean, inboxOnly = false) => {
    let url = `/emails/all?page=${page}&limit=${limit}`
    if (isRead !== undefined) url += `&is_read=${isRead}`
    if (isStarred !== undefined) url += `&is_starred=${isStarred}`
    if (inboxOnly) url += `&inbox_only=true`
    return api<ApiResponse<{ items: any[]; total: number }>>(url)
  }

  const getSnoozedEmails = (page = 1, limit = 50) =>
    api<ApiResponse<{ items: any[]; total: number }>>(`/emails/snoozed?page=${page}&limit=${limit}`)

  const searchEmails = (q: string, page = 1, limit = 50) =>
    api<ApiResponse<{ items: any[]; total: number }>>(`/emails/search?q=${encodeURIComponent(q)}&page=${page}&limit=${limit}`)

  const getTrackingStats = (emailId: number) =>
    api<ApiResponse<any>>(`/track/stats/${emailId}`)

  const resendEmail = (emailId: number) =>
    api<ApiResponse<any>>(`/emails/${emailId}/resend`, 'POST')

  return { login, logout, getFolders, getEmails, getEmail, sendEmail, syncEmails, markEmailRead, deleteEmail, markEmailStarred, snoozeEmail, getAllEmails, getSnoozedEmails, searchEmails, getTrackingStats, resendEmail, token }
}