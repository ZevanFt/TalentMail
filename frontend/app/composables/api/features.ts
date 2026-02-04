/**
 * 其他功能 API（邮件模板、标签、联系人、外部账号、网盘等）
 */
import { useApiBase } from './base'

export const useFeaturesApi = () => {
  const { api, API_BASE, token } = useApiBase()

  // ========== 邮件模板 ==========
  const getEmailTemplates = () => api<any[]>('/email-templates/')
  const getEmailTemplate = (id: number) => api<any>(`/email-templates/${id}`)
  const createEmailTemplate = (data: any) => api<any>('/email-templates/', 'POST', data)
  const updateEmailTemplate = (id: number, data: any) => api<any>(`/email-templates/${id}`, 'PUT', data)
  const deleteEmailTemplate = (id: number) => api<any>(`/email-templates/${id}`, 'DELETE')
  const previewEmailTemplate = (id: number, variables?: Record<string, any>) =>
    api<{ subject: string; body_html: string }>(`/email-templates/${id}/preview`, 'POST', { variables })
  const sendTestEmail = (id: number, toEmail: string, variables?: Record<string, any>) =>
    api<{ message: string }>(`/email-templates/${id}/test`, 'POST', { to_email: toEmail, variables })
  const getTemplateMetadataList = () => api<any[]>('/email-templates/metadata')
  const getTemplateMetadata = (code: string) => api<any>(`/email-templates/metadata/${code}`)
  const getGlobalVariables = () => api<Record<string, any>>('/email-templates/variables')
  const updateGlobalVariable = (key: string, value: any) =>
    api<any>('/email-templates/variables', 'PUT', { key, value })
  const resetTemplateToDefault = (code: string) => api<any>(`/email-templates/reset/${code}`, 'POST')
  const sendTemplateEmail = (templateCode: string, toEmail: string, variables?: Record<string, any>) =>
    api<{ message: string }>('/email-templates/send', 'POST', { template_code: templateCode, to_email: toEmail, variables })

  // 模板触发规则
  const getAvailableEvents = () => api<any[]>('/template-triggers/events')
  const getTemplateTriggerRules = () => api<any[]>('/template-triggers/')
  const createTemplateTriggerRule = (data: any) => api<any>('/template-triggers/', 'POST', data)
  const deleteTemplateTriggerRule = (id: number) => api<any>(`/template-triggers/${id}`, 'DELETE')
  const toggleTemplateTriggerRule = (id: number, isEnabled: boolean) =>
    api<any>(`/template-triggers/${id}/toggle`, 'PATCH', { is_enabled: isEnabled })

  // ========== 标签 ==========
  const getTags = () => api<any[]>('/tags/')
  const createTag = (data: { name: string; color?: string }) => api<any>('/tags/', 'POST', data)
  const updateTag = (id: number, data: { name?: string; color?: string }) => api<any>(`/tags/${id}`, 'PUT', data)
  const deleteTag = (id: number) => api<any>(`/tags/${id}`, 'DELETE')
  const addTagToEmail = (emailId: number, tagId: number) =>
    api<any>(`/emails/${emailId}/tags/${tagId}`, 'POST')
  const removeTagFromEmail = (emailId: number, tagId: number) =>
    api<any>(`/emails/${emailId}/tags/${tagId}`, 'DELETE')
  const getEmailsByTag = (tagId: number, page = 1, limit = 50) =>
    api<{ items: any[]; total: number }>(`/tags/${tagId}/emails?page=${page}&limit=${limit}`)

  // ========== 联系人 ==========
  const getContacts = (q?: string, page = 1, limit = 50) => {
    let url = `/contacts/?page=${page}&limit=${limit}`
    if (q) url += `&q=${encodeURIComponent(q)}`
    return api<{ items: any[]; total: number }>(url)
  }
  const createContact = (data: { email: string; name?: string; company?: string; phone?: string; notes?: string }) =>
    api<any>('/contacts/', 'POST', data)
  const updateContact = (id: number, data: { name?: string; company?: string; phone?: string; notes?: string }) =>
    api<any>(`/contacts/${id}`, 'PUT', data)
  const deleteContact = (id: number) => api<any>(`/contacts/${id}`, 'DELETE')

  // ========== 外部账号 ==========
  interface ExternalAccount {
    id: number
    email: string
    provider: string
    imap_host: string
    imap_port: number
    smtp_host: string
    smtp_port: number
    is_active: boolean
    last_sync_at: string | null
  }
  interface ProviderPreset {
    name: string
    imap_host: string
    imap_port: number
    imap_ssl: boolean
    smtp_host: string
    smtp_port: number
    smtp_ssl: boolean
    smtp_starttls: boolean
  }

  const getExternalAccounts = () => api<ExternalAccount[]>('/external-accounts/')
  const createExternalAccount = (data: { email: string; password: string; provider?: string; imap_host?: string; imap_port?: number; imap_ssl?: boolean; smtp_host?: string; smtp_port?: number; smtp_ssl?: boolean; smtp_starttls?: boolean }) =>
    api<ExternalAccount>('/external-accounts/', 'POST', data)
  const updateExternalAccount = (id: number, data: { password?: string; is_active?: boolean }) =>
    api<ExternalAccount>(`/external-accounts/${id}`, 'PUT', data)
  const deleteExternalAccount = (id: number) => api<any>(`/external-accounts/${id}`, 'DELETE')
  const testExternalAccount = (id: number) =>
    api<{ success: boolean; message: string }>(`/external-accounts/${id}/test`, 'POST')
  const getProviderPresets = () => api<Record<string, ProviderPreset>>('/external-accounts/providers')

  // ========== 网盘 ==========
  interface DriveFile {
    id: number
    filename: string
    original_filename: string
    content_type: string | null
    size: number
    share_code: string | null
    is_public: boolean
    download_count: number
    share_expires_at: string | null
    created_at: string
  }

  const getDriveFiles = () => api<DriveFile[]>('/drive')
  const uploadDriveFile = async (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return await $fetch<DriveFile>(`${API_BASE}/drive/upload`, {
      method: 'POST',
      headers: token.value ? { Authorization: `Bearer ${token.value}` } : {},
      body: formData
    })
  }
  const deleteDriveFile = (id: number) => api<any>(`/drive/${id}`, 'DELETE')
  const createDriveShare = (id: number, data: { is_public?: boolean; password?: string; expires_days?: number }) =>
    api<DriveFile>(`/drive/${id}/share`, 'POST', data)
  const removeDriveShare = (id: number) => api<any>(`/drive/${id}/share`, 'DELETE')
  const downloadDriveFileUrl = (id: number) => `${API_BASE}/drive/${id}/download`
  const getShareInfo = (shareCode: string, password?: string) =>
    api<{ original_filename: string; size: number; content_type: string; has_password: boolean; download_count: number }>(`/drive/share/${shareCode}${password ? `?password=${encodeURIComponent(password)}` : ''}`)
  const downloadSharedFileUrl = (shareCode: string, password?: string) =>
    `${API_BASE}/drive/share/${shareCode}/download${password ? `?password=${encodeURIComponent(password)}` : ''}`

  // ========== 公共邮箱池 ==========
  const getPoolMailboxes = () => api<any[]>('/pool/mailboxes')
  const createPoolMailbox = (data: { prefix: string; description?: string }) =>
    api<any>('/pool/mailboxes', 'POST', data)
  const deletePoolMailbox = (id: number) => api<any>(`/pool/mailboxes/${id}`, 'DELETE')
  const getPoolMailboxEmails = (mailboxId: number, page = 1, limit = 50) =>
    api<{ items: any[]; total: number }>(`/pool/mailboxes/${mailboxId}/emails?page=${page}&limit=${limit}`)
  const getPoolStats = () => api<any>('/pool/stats')
  const getPoolActivityLogs = (limit = 50) => api<any[]>(`/pool/activity?limit=${limit}`)
  const markPoolEmailRead = (emailId: number) => api<any>(`/pool/emails/${emailId}/read`, 'PATCH')

  // ========== 订阅 ==========
  const getSubscriptionStatus = () => api<any>('/billing/subscription')
  const redeemCode = (code: string) => api<any>('/billing/redeem', 'POST', { code })
  const getRedemptionHistory = () => api<any[]>('/billing/redemption-history')

  return {
    // 邮件模板
    getEmailTemplates, getEmailTemplate, createEmailTemplate, updateEmailTemplate, deleteEmailTemplate,
    previewEmailTemplate, sendTestEmail, getTemplateMetadataList, getTemplateMetadata,
    getGlobalVariables, updateGlobalVariable, resetTemplateToDefault, sendTemplateEmail,
    getAvailableEvents, getTemplateTriggerRules, createTemplateTriggerRule, deleteTemplateTriggerRule, toggleTemplateTriggerRule,
    // 标签
    getTags, createTag, updateTag, deleteTag, addTagToEmail, removeTagFromEmail, getEmailsByTag,
    // 联系人
    getContacts, createContact, updateContact, deleteContact,
    // 外部账号
    getExternalAccounts, createExternalAccount, updateExternalAccount, deleteExternalAccount,
    testExternalAccount, getProviderPresets,
    // 网盘
    getDriveFiles, uploadDriveFile, deleteDriveFile, createDriveShare, removeDriveShare,
    downloadDriveFileUrl, getShareInfo, downloadSharedFileUrl,
    // 公共邮箱池
    getPoolMailboxes, createPoolMailbox, deletePoolMailbox, getPoolMailboxEmails,
    getPoolStats, getPoolActivityLogs, markPoolEmailRead,
    // 订阅
    getSubscriptionStatus, redeemCode, getRedemptionHistory
  }
}
