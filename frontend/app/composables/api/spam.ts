/**
 * 垃圾邮件管理 API
 */
import { useApiBase } from './base'

export const useSpamApi = () => {
  const { api } = useApiBase()

  interface TrustedSender {
    id: number
    email: string
    sender_type: string
    note: string | null
    created_at: string | null
  }

  interface BulkActionResult {
    status: string
    message: string
    moved_count: number
  }

  // 白名单
  const getWhitelist = () => api<TrustedSender[]>('/spam/whitelist')
  const addToWhitelist = (email: string, note?: string) =>
    api<TrustedSender>('/spam/whitelist', 'POST', { email, note })
  const removeFromWhitelist = (id: number) => api<any>(`/spam/whitelist/${id}`, 'DELETE')

  // 垃圾邮件标记
  const markAsSpam = (emailIds: number[]) =>
    api<BulkActionResult>('/spam/mark-spam', 'POST', { email_ids: emailIds })
  const markAsNotSpam = (emailIds: number[]) =>
    api<BulkActionResult>('/spam/mark-not-spam', 'POST', { email_ids: emailIds })

  return {
    getWhitelist, addToWhitelist, removeFromWhitelist,
    markAsSpam, markAsNotSpam
  }
}
