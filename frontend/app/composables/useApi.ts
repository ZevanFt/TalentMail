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
  interface LoginResponse {
    access_token?: string
    refresh_token?: string
    token_type?: string
    requires_2fa?: boolean
    temp_token?: string
    message?: string
  }
  
  const login = async (email: string, password: string): Promise<LoginResponse> => {
    const formData = new URLSearchParams()
    formData.append('username', email)
    formData.append('password', password)
    
    const res = await $fetch<LoginResponse>(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData.toString()
    })
    
    // 如果不需要 2FA，直接保存 token
    if (res.access_token && !res.requires_2fa) {
      token.value = res.access_token
    }
    
    return res
  }
  
  const login2FA = async (tempToken: string, code: string) => {
    const res = await $fetch<{ access_token: string; refresh_token: string; token_type: string }>(`${API_BASE}/auth/login-2fa`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ temp_token: tempToken, code })
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

  const sendEmail = (data: { to: string; cc?: string; subject: string; body_text?: string; body_html?: string; reply_to_id?: number; is_tracked?: boolean; attachment_ids?: number[] }) => {
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
      is_tracked: data.is_tracked || false,
      attachment_ids: data.attachment_ids || []
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
    spam_filter_level?: string
    block_external_images?: boolean
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
  
  const getInviteCodeUsages = (id: number) =>
    api<Array<{ id: number; user_email: string; used_at: string }>>(`/invite/${id}/usages`)

  // Admin User APIs
  const getUsers = (q?: string, page = 1, limit = 20) => {
    let url = `/users/admin/list?page=${page}&limit=${limit}`
    if (q) url += `&q=${encodeURIComponent(q)}`
    return api<{ items: any[]; total: number }>(url)
  }
  
  const updateUserPermissions = (userId: number, data: { role?: string; pool_enabled?: boolean; plan_id?: number; subscription_days?: number }) =>
    api<any>(`/users/admin/${userId}/permissions`, 'PATCH', data)
  
  const adminCreateUser = (data: { email_prefix: string; password: string; display_name?: string; role?: string; pool_enabled?: boolean; plan_id?: number; subscription_days?: number }) =>
    api<{ status: string; user: any }>('/users/admin/create', 'POST', data)
  
  const adminDeleteUser = (userId: number) =>
    api<any>(`/users/admin/${userId}`, 'DELETE')

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

  // Attachment APIs
  const uploadAttachment = async (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return await $fetch<{ id: number; filename: string; content_type: string; size: number }>(`${API_BASE}/attachments/upload`, {
      method: 'POST',
      headers: token.value ? { Authorization: `Bearer ${token.value}` } : {},
      body: formData
    })
  }
  const deleteAttachment = (id: number) => api<any>(`/attachments/${id}`, 'DELETE')
  const downloadAttachmentUrl = (id: number) => `${API_BASE}/attachments/${id}/download`

  // Billing APIs (会员订阅)
  const getPlans = () => api<any[]>('/billing/plans')
  const createPlan = (data: any) => api<any>('/billing/plans', 'POST', data)
  const updatePlan = (id: number, data: any) => api<any>(`/billing/plans/${id}`, 'PUT', data)
  const deletePlan = (id: number) => api<any>(`/billing/plans/${id}`, 'DELETE')
  
  const getRedemptionCodes = (status?: string, planId?: number, page = 1, limit = 50) => {
    let url = `/billing/codes?page=${page}&limit=${limit}`
    if (status) url += `&status=${status}`
    if (planId) url += `&plan_id=${planId}`
    return api<any[]>(url)
  }
  const generateRedemptionCodes = (data: { plan_id: number; duration_days: number; count: number; prefix?: string }) =>
    api<{ codes: string[]; count: number }>('/billing/codes', 'POST', data)
  const getRedemptionCodeStats = () => api<{ total: number; unused: number; used: number; expired: number }>('/billing/codes/stats')
  const revokeRedemptionCode = (id: number) => api<any>(`/billing/codes/${id}`, 'DELETE')
  
  const getSubscriptionStatus = () => api<any>('/billing/subscription')
  const redeemCode = (code: string) => api<any>('/billing/redeem', 'POST', { code })
  const getRedemptionHistory = () => api<any[]>('/billing/history')

  // Login Sessions APIs (登录会话)
  interface LoginSession {
    id: number
    device_info: string | null
    browser: string | null
    os: string | null
    ip_address: string | null
    location: string | null
    is_active: boolean
    created_at: string | null
    last_active_at: string | null
    is_current: boolean
  }
  const getLoginSessions = (limit = 10) => api<LoginSession[]>(`/users/me/sessions?limit=${limit}`)
  const revokeSession = (sessionId: number) => api<any>(`/users/me/sessions/${sessionId}`, 'DELETE')
  const revokeAllSessions = () => api<any>('/users/me/sessions', 'DELETE')

  // Reserved Prefixes APIs (保留前缀)
  interface ReservedPrefix {
    id: number
    prefix: string
    category: string
    description: string | null
    is_active: boolean
    created_at: string | null
    updated_at: string | null
  }
  const getReservedPrefixes = (category?: string, isActive?: boolean, q?: string, page = 1, limit = 50) => {
    let url = `/prefixes/?page=${page}&limit=${limit}`
    if (category) url += `&category=${category}`
    if (isActive !== undefined) url += `&is_active=${isActive}`
    if (q) url += `&q=${encodeURIComponent(q)}`
    return api<{ items: ReservedPrefix[]; total: number }>(url)
  }
  const createReservedPrefix = (data: { prefix: string; category?: string; description?: string }) =>
    api<ReservedPrefix>('/prefixes/', 'POST', data)
  const updateReservedPrefix = (id: number, data: { prefix?: string; category?: string; description?: string; is_active?: boolean }) =>
    api<ReservedPrefix>(`/prefixes/${id}`, 'PUT', data)
  const deleteReservedPrefix = (id: number) => api<any>(`/prefixes/${id}`, 'DELETE')
  const getReservedPrefixCategories = () => api<string[]>('/prefixes/categories')
  const checkPrefixAvailability = (prefix: string) => api<{ available: boolean; reason: string | null; message: string }>(`/prefixes/check/${prefix}`)

  // Verification Code APIs (验证码)
  const sendVerificationCode = (email: string, purpose: string = 'register') =>
    api<{ status: string; message: string }>('/auth/send-verification-code', 'POST', { email, purpose })
  const verifyCode = (email: string, code: string, purpose: string = 'register') =>
    api<{ status: string; message: string }>('/auth/verify-code', 'POST', { email, code, purpose })
  const registerWithVerification = (data: { email: string; password: string; invite_code: string; verification_email: string; verification_code: string }) =>
    api<{ status: string; user_id: number; email: string }>('/auth/register-with-verification', 'POST', data)

  // Password Reset APIs (密码重置)
  const forgotPassword = (email: string) =>
    api<{ status: string; message: string }>('/auth/forgot-password', 'POST', { email })
  const resetPassword = (email: string, code: string, newPassword: string) =>
    api<{ status: string; message: string }>('/auth/reset-password', 'POST', { email, code, new_password: newPassword })

  // Recovery Email APIs (辅助邮箱)
  const sendRecoveryEmailCode = (email: string) =>
    api<{ status: string; message: string }>('/auth/send-recovery-email-code', 'POST', { email, purpose: 'update_recovery_email' })
  const updateRecoveryEmail = (newEmail: string, code: string) =>
    api<{ status: string; message: string; recovery_email: string }>('/auth/update-recovery-email', 'POST', { new_email: newEmail, code })

  // Email Templates APIs (邮件模板管理)
  interface EmailTemplate {
    id: number
    code: string
    name: string
    category: string
    description: string | null
    subject: string
    body_html: string
    body_text: string | null
    variables: string[] | null
    is_active: boolean
    created_at: string
    updated_at: string
  }
  const getEmailTemplates = (category?: string) => {
    let url = '/email-templates/'
    if (category) url += `?category=${category}`
    return api<EmailTemplate[]>(url)
  }
  const getEmailTemplate = (id: number) => api<EmailTemplate>(`/email-templates/${id}`)
  const createEmailTemplate = (data: { code: string; name: string; category: string; description?: string; subject: string; body_html: string; body_text?: string; variables?: string[]; is_active?: boolean }) =>
    api<EmailTemplate>('/email-templates/', 'POST', data)
  const updateEmailTemplate = (id: number, data: { name?: string; category?: string; description?: string; subject?: string; body_html?: string; body_text?: string; variables?: string[]; is_active?: boolean }) =>
    api<EmailTemplate>(`/email-templates/${id}`, 'PUT', data)
  const deleteEmailTemplate = (id: number) => api<any>(`/email-templates/${id}`, 'DELETE')
  const previewEmailTemplate = (id: number, variables: Record<string, string>) =>
    api<{ subject: string; body_html: string; body_text: string }>(`/email-templates/${id}/preview`, 'POST', variables)

  // 2FA APIs (两步验证)
  interface TwoFactorStatus {
    enabled: boolean
    has_secret: boolean
  }
  interface TwoFactorSetupResponse {
    secret: string
    qr_code: string
    provisioning_uri: string
  }
  const get2FAStatus = () => api<TwoFactorStatus>('/2fa/status')
  const setup2FA = () => api<TwoFactorSetupResponse>('/2fa/setup', 'POST')
  const enable2FA = (code: string) => api<{ status: string; message: string }>('/2fa/enable', 'POST', { code })
  const disable2FA = (code: string, password: string) => api<{ status: string; message: string }>('/2fa/disable', 'POST', { code, password })
  const verify2FA = (code: string) => api<{ status: string; message: string }>('/2fa/verify', 'POST', { code })

  return { login, login2FA, logout, getFolders, getEmails, getEmail, sendEmail, syncEmails, markEmailRead, deleteEmail, markEmailStarred, snoozeEmail, getAllEmails, getSnoozedEmails, searchEmails, getTrackingStats, resendEmail, getMe, updateMe, changePassword, getStorageStats, getInviteCodes, createInviteCode, deleteInviteCode, getInviteCodeUsages, getUsers, updateUserPermissions, adminCreateUser, adminDeleteUser, getPoolMailboxes, createPoolMailbox, deletePoolMailbox, getPoolMailboxEmails, getPoolStats, getPoolActivityLogs, markPoolEmailRead, saveDraft, updateDraft, deleteDraft, getSignatures, createSignature, updateSignature, deleteSignature, getDefaultSignature, uploadAttachment, deleteAttachment, downloadAttachmentUrl, getPlans, createPlan, updatePlan, deletePlan, getRedemptionCodes, generateRedemptionCodes, getRedemptionCodeStats, revokeRedemptionCode, getSubscriptionStatus, redeemCode, getRedemptionHistory, getLoginSessions, revokeSession, revokeAllSessions, getReservedPrefixes, createReservedPrefix, updateReservedPrefix, deleteReservedPrefix, getReservedPrefixCategories, checkPrefixAvailability, sendVerificationCode, verifyCode, registerWithVerification, forgotPassword, resetPassword, sendRecoveryEmailCode, updateRecoveryEmail, getEmailTemplates, getEmailTemplate, createEmailTemplate, updateEmailTemplate, deleteEmailTemplate, previewEmailTemplate, get2FAStatus, setup2FA, enable2FA, disable2FA, verify2FA, token }
}