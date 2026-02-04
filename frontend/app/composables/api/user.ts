/**
 * 用户相关 API
 */
import { useApiBase } from './base'

export const useUserApi = () => {
  const { api } = useApiBase()

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
    auto_clean_trash?: boolean
    auto_archive_old?: boolean
  }) => api<any>('/users/me', 'PATCH', data)

  const changePassword = (currentPassword: string, newPassword: string) =>
    api<any>('/users/me/password', 'POST', { current_password: currentPassword, new_password: newPassword })

  const getStorageStats = () =>
    api<{ storage_used_bytes: number; storage_limit_bytes: number; email_count: number; email_bytes: number }>('/users/me/storage')

  // 恢复邮箱
  const sendRecoveryEmailCode = (newRecoveryEmail: string) =>
    api<{ message: string }>('/users/me/recovery-email/send-code', 'POST', { new_recovery_email: newRecoveryEmail })

  const updateRecoveryEmail = (newRecoveryEmail: string, code: string) =>
    api<{ message: string }>('/users/me/recovery-email', 'PUT', { new_recovery_email: newRecoveryEmail, code })

  // 登录会话
  const getLoginSessions = () => api<any[]>('/users/me/sessions')
  const revokeSession = (sessionId: number) => api<any>(`/users/me/sessions/${sessionId}`, 'DELETE')
  const revokeAllSessions = () => api<any>('/users/me/sessions', 'DELETE')

  // 黑名单
  const getBlockedSenders = () => api<any[]>('/users/me/blocked-senders')
  const addBlockedSender = (email: string) => api<any>('/users/me/blocked-senders', 'POST', { email })
  const removeBlockedSender = (id: number) => api<any>(`/users/me/blocked-senders/${id}`, 'DELETE')

  // 别名
  const getAliases = () => api<any[]>('/aliases/')
  const createAlias = (prefix: string, name?: string) => api<any>('/aliases/', 'POST', { prefix, name })
  const updateAlias = (id: number, data: { name?: string; is_active?: boolean }) => api<any>(`/aliases/${id}`, 'PUT', data)
  const deleteAlias = (id: number) => api<any>(`/aliases/${id}`, 'DELETE')

  // 签名
  const getSignatures = () => api<any[]>('/signatures/')
  const createSignature = (data: { name: string; content: string; is_default?: boolean }) => api<any>('/signatures/', 'POST', data)
  const updateSignature = (id: number, data: { name?: string; content?: string; is_default?: boolean }) => api<any>(`/signatures/${id}`, 'PUT', data)
  const deleteSignature = (id: number) => api<any>(`/signatures/${id}`, 'DELETE')
  const getDefaultSignature = () => api<any>('/signatures/default')

  return {
    getMe, updateMe, changePassword, getStorageStats,
    sendRecoveryEmailCode, updateRecoveryEmail,
    getLoginSessions, revokeSession, revokeAllSessions,
    getBlockedSenders, addBlockedSender, removeBlockedSender,
    getAliases, createAlias, updateAlias, deleteAlias,
    getSignatures, createSignature, updateSignature, deleteSignature, getDefaultSignature
  }
}
