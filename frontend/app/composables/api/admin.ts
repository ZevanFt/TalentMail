/**
 * 管理员相关 API
 */
import { useApiBase } from './base'

export const useAdminApi = () => {
  const { api } = useApiBase()

  // ========== 用户管理 ==========
  const getUsers = (q?: string, page = 1, limit = 20) => {
    let url = `/users/admin/list?page=${page}&limit=${limit}`
    if (q) url += `&q=${encodeURIComponent(q)}`
    return api<{ items: any[]; total: number }>(url)
  }

  const updateUserPermissions = (userId: number, data: { role?: string; is_active?: boolean; storage_limit_bytes?: number }) =>
    api<any>(`/users/admin/${userId}/permissions`, 'PUT', data)

  const adminCreateUser = (data: { email: string; password: string; display_name?: string; role?: string }) =>
    api<any>('/users/admin/create', 'POST', data)

  const adminDeleteUser = (userId: number) =>
    api<any>(`/users/admin/${userId}`, 'DELETE')

  // ========== 邀请码 ==========
  const getInviteCodes = () => api<any[]>('/invite/')
  const createInviteCode = (maxUses: number = 1, expiresDays?: number) =>
    api<any>('/invite/', 'POST', { max_uses: maxUses, expires_days: expiresDays })
  const deleteInviteCode = (id: number) => api<any>(`/invite/${id}`, 'DELETE')
  const getInviteCodeUsages = (id: number) =>
    api<Array<{ id: number; user_email: string; used_at: string }>>(`/invite/${id}/usages`)

  // ========== 保留前缀 ==========
  const getReservedPrefixes = () => api<any[]>('/reserved-prefixes/')
  const createReservedPrefix = (data: { prefix: string; category?: string; reason?: string }) =>
    api<any>('/reserved-prefixes/', 'POST', data)
  const updateReservedPrefix = (id: number, data: { category?: string; reason?: string }) =>
    api<any>(`/reserved-prefixes/${id}`, 'PUT', data)
  const deleteReservedPrefix = (id: number) => api<any>(`/reserved-prefixes/${id}`, 'DELETE')
  const getReservedPrefixCategories = () => api<string[]>('/reserved-prefixes/categories')
  const checkPrefixAvailability = (prefix: string) =>
    api<{ available: boolean; reason?: string }>(`/reserved-prefixes/check/${prefix}`)

  // ========== 订阅计划 ==========
  const getPlans = () => api<any[]>('/billing/plans')
  const createPlan = (data: any) => api<any>('/billing/plans', 'POST', data)
  const updatePlan = (id: number, data: any) => api<any>(`/billing/plans/${id}`, 'PUT', data)
  const deletePlan = (id: number) => api<any>(`/billing/plans/${id}`, 'DELETE')

  // ========== 兑换码 ==========
  const getRedemptionCodes = (page = 1, limit = 50, status?: string) => {
    let url = `/billing/redemption-codes?page=${page}&limit=${limit}`
    if (status) url += `&status=${status}`
    return api<{ items: any[]; total: number }>(url)
  }
  const generateRedemptionCodes = (data: { plan_id: number; count: number; prefix?: string; expires_days?: number }) =>
    api<{ codes: string[] }>('/billing/redemption-codes/generate', 'POST', data)
  const getRedemptionCodeStats = () => api<any>('/billing/redemption-codes/stats')
  const revokeRedemptionCode = (code: string) =>
    api<any>(`/billing/redemption-codes/${code}/revoke`, 'POST')

  // ========== 更新日志 ==========
  interface Changelog {
    id: number
    version: string
    title: string
    content: string
    is_major: boolean
    is_published: boolean
    published_at: string | null
    created_at: string
  }

  const getChangelogs = (page = 1, limit = 20, published_only = false) => {
    let url = `/changelogs/?page=${page}&limit=${limit}`
    if (published_only) url += '&published_only=true'
    return api<{ items: Changelog[]; total: number }>(url)
  }
  const getLatestChangelog = () => api<Changelog | null>('/changelogs/latest')
  const getChangelog = (id: number) => api<Changelog>(`/changelogs/${id}`)
  const createChangelog = (data: { version: string; title: string; content: string; is_major?: boolean }) =>
    api<Changelog>('/changelogs/', 'POST', data)
  const updateChangelog = (id: number, data: { version?: string; title?: string; content?: string; is_major?: boolean }) =>
    api<Changelog>(`/changelogs/${id}`, 'PUT', data)
  const deleteChangelog = (id: number) => api<{ message: string }>(`/changelogs/${id}`, 'DELETE')
  const publishChangelog = (id: number) => api<Changelog>(`/changelogs/${id}/publish`, 'POST')
  const unpublishChangelog = (id: number) => api<Changelog>(`/changelogs/${id}/unpublish`, 'POST')

  return {
    // 用户管理
    getUsers, updateUserPermissions, adminCreateUser, adminDeleteUser,
    // 邀请码
    getInviteCodes, createInviteCode, deleteInviteCode, getInviteCodeUsages,
    // 保留前缀
    getReservedPrefixes, createReservedPrefix, updateReservedPrefix, deleteReservedPrefix,
    getReservedPrefixCategories, checkPrefixAvailability,
    // 订阅计划
    getPlans, createPlan, updatePlan, deletePlan,
    // 兑换码
    getRedemptionCodes, generateRedemptionCodes, getRedemptionCodeStats, revokeRedemptionCode,
    // 更新日志
    getChangelogs, getLatestChangelog, getChangelog, createChangelog, updateChangelog,
    deleteChangelog, publishChangelog, unpublishChangelog
  }
}
