/**
 * 邮件相关 API
 */
import { useApiBase, type ApiResponse } from './base'

export const useEmailApi = () => {
  const { api, API_BASE, token } = useApiBase()

  // 文件夹
  const getFolders = () => api<ApiResponse<any[]>>('/folders')

  // 邮件列表
  const getEmails = (folderId: number, page = 1, limit = 50, isRead?: boolean, isStarred?: boolean) => {
    let url = `/emails?folder_id=${folderId}&page=${page}&limit=${limit}`
    if (isRead !== undefined) url += `&is_read=${isRead}`
    if (isStarred !== undefined) url += `&is_starred=${isStarred}`
    return api<ApiResponse<{ items: any[]; total: number }>>(url)
  }

  const getEmail = (id: number) => api<ApiResponse<any>>(`/emails/${id}`)

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

  // 发送邮件
  const sendEmail = (data: { to: string; cc?: string; subject: string; body_text?: string; body_html?: string; reply_to_id?: number; is_tracked?: boolean; attachment_ids?: number[] }) => {
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

  // 同步
  const syncEmails = () => api<ApiResponse<{ new_emails: number }>>('/emails/sync', 'POST')

  // 单个邮件操作
  const markEmailRead = (id: number, isRead: boolean) =>
    api<ApiResponse<{ id: number; is_read: boolean }>>(`/emails/${id}/read?is_read=${isRead}`, 'PATCH')

  const markEmailStarred = (id: number, isStarred: boolean) =>
    api<ApiResponse<{ id: number; is_starred: boolean }>>(`/emails/${id}/star?is_starred=${isStarred}`, 'PATCH')

  const deleteEmail = (id: number) =>
    api<ApiResponse<{ id: number }>>(`/emails/${id}`, 'DELETE')

  const snoozeEmail = (id: number, snoozeUntil: string | null) => {
    const url = snoozeUntil ? `/emails/${id}/snooze?snooze_until=${encodeURIComponent(snoozeUntil)}` : `/emails/${id}/snooze`
    return api<ApiResponse<{ id: number; snoozed_until: string | null }>>(url, 'PATCH')
  }

  const resendEmail = (emailId: number) =>
    api<ApiResponse<any>>(`/emails/${emailId}/resend`, 'POST')

  // 批量操作
  interface BulkActionResult {
    status: string
    success_count: number
    failed_count: number
    failed_ids: number[]
  }

  const bulkMarkRead = (emailIds: number[], isRead: boolean) =>
    api<BulkActionResult>(`/emails/bulk/read?is_read=${isRead}`, 'POST', { email_ids: emailIds })

  const bulkMarkStarred = (emailIds: number[], isStarred: boolean) =>
    api<BulkActionResult>(`/emails/bulk/star?is_starred=${isStarred}`, 'POST', { email_ids: emailIds })

  const bulkMoveEmails = (emailIds: number[], targetFolderId: number) =>
    api<BulkActionResult>('/emails/bulk/move', 'POST', { email_ids: emailIds, target_folder_id: targetFolderId })

  const bulkDeleteEmails = (emailIds: number[]) =>
    api<BulkActionResult>('/emails/bulk/delete', 'POST', { email_ids: emailIds })

  const bulkArchiveEmails = (emailIds: number[]) =>
    api<BulkActionResult>('/emails/bulk/archive', 'POST', { email_ids: emailIds })

  // 追踪
  const getTrackingStats = (emailId: number) =>
    api<ApiResponse<any>>(`/track/stats/${emailId}`)

  // 草稿
  const saveDraft = (data: any) => api<any>('/emails/draft', 'POST', data)
  const updateDraft = (id: number, data: any) => api<any>(`/emails/draft/${id}`, 'PUT', data)
  const deleteDraft = (id: number) => api<any>(`/emails/draft/${id}`, 'DELETE')

  // 附件
  const uploadAttachment = async (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return await $fetch<{ id: number; filename: string; content_type: string; size_bytes: number }>(`${API_BASE}/attachments/upload`, {
      method: 'POST',
      headers: token.value ? { Authorization: `Bearer ${token.value}` } : {},
      body: formData
    })
  }
  const deleteAttachment = (id: number) => api<any>(`/attachments/${id}`, 'DELETE')
  const downloadAttachmentUrl = (id: number) => `${API_BASE}/attachments/${id}/download`

  return {
    getFolders, getEmails, getEmail, getAllEmails, getSnoozedEmails, searchEmails,
    sendEmail, syncEmails,
    markEmailRead, markEmailStarred, deleteEmail, snoozeEmail, resendEmail,
    bulkMarkRead, bulkMarkStarred, bulkMoveEmails, bulkDeleteEmails, bulkArchiveEmails,
    getTrackingStats,
    saveDraft, updateDraft, deleteDraft,
    uploadAttachment, deleteAttachment, downloadAttachmentUrl
  }
}
