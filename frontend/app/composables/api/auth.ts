/**
 * 认证相关 API
 */
import { useApiBase } from './base'

export const useAuthApi = () => {
  const { api, token, API_BASE } = useApiBase()

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

  // 验证码
  const sendVerificationCode = (email: string) =>
    api<{ message: string }>('/auth/send-code', 'POST', { email })

  const verifyCode = (email: string, code: string) =>
    api<{ verified: boolean }>('/auth/verify-code', 'POST', { email, code })

  const registerWithVerification = (email: string, password: string, code: string, inviteCode?: string, displayName?: string) =>
    api<{ access_token: string }>('/auth/register', 'POST', { email, password, code, invite_code: inviteCode, display_name: displayName })

  // 密码重置
  const forgotPassword = (email: string) =>
    api<{ message: string }>('/auth/forgot-password', 'POST', { email })

  const resetPassword = (email: string, code: string, newPassword: string) =>
    api<{ message: string }>('/auth/reset-password', 'POST', { email, code, new_password: newPassword })

  // 2FA
  const get2FAStatus = () => api<{ enabled: boolean; backup_codes_count: number }>('/auth/2fa/status')
  const setup2FA = () => api<{ secret: string; qr_code: string }>('/auth/2fa/setup', 'POST')
  const enable2FA = (code: string) => api<{ message: string; backup_codes: string[] }>('/auth/2fa/enable', 'POST', { code })
  const disable2FA = (code: string) => api<{ message: string }>('/auth/2fa/disable', 'POST', { code })
  const verify2FA = (code: string) => api<{ valid: boolean }>('/auth/2fa/verify', 'POST', { code })

  return {
    login, login2FA, logout,
    sendVerificationCode, verifyCode, registerWithVerification,
    forgotPassword, resetPassword,
    get2FAStatus, setup2FA, enable2FA, disable2FA, verify2FA,
    token
  }
}
