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

  // User APIs
  const getMe = () => api<any>('/users/me')
  
  const updateMe = (data: {
    display_name?: string
    avatar_url?: string
    theme?: string
    enable_desktop_notifications?: boolean
    enable_sound_notifications?: boolean
    enable_pool_notifications?: boolean
    auto_reply_enabled?: boolean
    auto_reply_start_date?: string | null
    auto_reply_end_date?: string | null
    auto_reply_message?: string | null
  }) => api<any>('/users/me', 'PATCH', data)
  
  const changePassword = (currentPassword: string, newPassword: string) =>
    api<any>('/users/me/password', 'POST', { current_password: currentPassword, new_password: newPassword })
  
  const getStorageStats = () =>
    api<{ storage_used_bytes: number; storage_limit_bytes: number; email_count: number; email_bytes: number }>('/users/me/storage')

  // Invite APIs (admin only)
  const getInviteCodes = () => api<any[]>('/invite/')
  
  const createInviteCode = (maxUses: number = 1, expiresDays?: number) =>
    api<any>('/invite/', 'POST', { max_uses: maxUses, expires_days: expiresDays })
  
  const deleteInviteCode = (id: number) =>
    api<any>(`/invite/${id}`, 'DELETE')

  // Admin User APIs
  const getUsers = (q?: string, page = 1, limit = 20) => {
    let url = `/users/admin/list?page=${page}&limit=${limit}`
    if (q) url += `&q=${encodeURIComponent(q)}`
    return api<{ items: any[]; total: number }>(url)
  }
  
  const updateUserPermissions = (userId: number, data: { role?: string; pool_enabled?: boolean }) =>
    api<any>(`/users/admin/${userId}/permissions`, 'PATCH', data)

  // Pool APIs (临时邮箱)
  const getPoolMailboxes = (page = 1, limit = 20) =>
    api<{ items: any[]; total: number }>(`/pool/?page=${page}&limit=${limit}`)
  
  const createPoolMailbox = (data: { prefix?: string; purpose?: string; auto_verify_codes?: boolean }) =>
    api<any>('/pool/', 'POST', data)
  
  const deletePoolMailbox = (id: number) =>
    api<any>(`/pool/${id}`, 'DELETE')
  
  const getPoolMailboxEmails = (mailboxId: number, page = 1, limit = 20) =>
    api<{ items: any[]; total: number }>(`/pool/${mailboxId}/emails?page=${page}&limit=${limit}`)
  
  const getPoolStats = () =>
    api<{ total_mailboxes: number; active_mailboxes: number; total_emails: number; unread_emails: number; today_emails: number; recent_emails: Array<{ id: number; mailbox: string; sender: string; subject: string; received_at: string | null }> }>('/pool/stats')
  
  const getPoolActivityLogs = (page = 1, limit = 20) =>
    api<{ items: Array<{ id: number; action: string; mailbox_email: string; details: string | null; created_at: string | null }>; total: number }>(`/pool/activity?page=${page}&limit=${limit}`)
  
  const markPoolEmailRead = (emailId: number) =>
    api<any>(`/emails/${emailId}/read?is_read=true`, 'PATCH')

  // Draft APIs
  const saveDraft = (data: { to?: string; cc?: string; subject?: string; body_text?: string }) =>
    api<{ status: string; data: { id: number } }>('/emails/drafts', 'POST', data)
  
  const updateDraft = (id: number, data: { to?: string; cc?: string; subject?: string; body_text?: string }) =>
    api<{ status: string; data: { id: number } }>(`/emails/drafts/${id}`, 'PUT', data)
  
  const deleteDraft = (id: number) =>
    api<any>(`/emails/drafts/${id}`, 'DELETE')

  // Signature APIs
  const getSignatures = () => api<Array<{ id: number; name: string; content_html: string; is_default: boolean }>>('/signatures/')
  const createSignature = (data: { name: string; content_html: string; is_default?: boolean }) =>
    api<{ id: number; name: string; content_html: string; is_default: boolean }>('/signatures/', 'POST', data)
  const updateSignature = (id: number, data: { name?: string; content_html?: string; is_default?: boolean }) =>
    api<{ id: number; name: string; content_html: string; is_default: boolean }>(`/signatures/${id}`, 'PUT', data)
  const deleteSignature = (id: number) => api<any>(`/signatures/${id}`, 'DELETE')
  const getDefaultSignature = () => api<{ signature: string | null }>('/signatures/default')

  return { login, logout, getFolders, getEmails, getEmail, sendEmail, syncEmails, markEmailRead, deleteEmail, markEmailStarred, snoozeEmail, getAllEmails, getSnoozedEmails, searchEmails, getTrackingStats, resendEmail, getMe, updateMe, changePassword, getStorageStats, getInviteCodes, createInviteCode, deleteInviteCode, getUsers, updateUserPermissions, getPoolMailboxes, createPoolMailbox, deletePoolMailbox, getPoolMailboxEmails, getPoolStats, getPoolActivityLogs, markPoolEmailRead, saveDraft, updateDraft, deleteDraft, getSignatures, createSignature, updateSignature, deleteSignature, getDefaultSignature, token }
}