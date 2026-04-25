/**
 * TalentMail 前端共享类型定义
 * Nuxt 3 自动从 types/ 目录导入
 */

/** 用户信息（getMe 返回） */
export interface AppUser {
  id: number
  email: string
  display_name: string | null
  avatar_url: string | null
  role: string
  theme: string | null
  recovery_email: string | null
  pool_enabled: boolean | null
  plan_name: string | null
  plan_id: number | null
  created_at: string
  [key: string]: unknown // 允许动态字段访问（如 Storage.vue 中的 user[key]）
}

/** 订阅状态 */
export interface Subscription {
  plan_name: string
  plan_id: number | null
  expires_at: string | null
  is_active: boolean
  max_aliases: number
  max_storage: number
  max_external_accounts: number
  features: Record<string, boolean>
}

/** 共享文件信息 */
export interface SharedFile {
  original_filename: string
  size: number
  content_type: string | null
  download_count: number
}

/** 外部邮箱账号 */
export interface ExternalAccountForm {
  email: string
  password: string
  provider: string
  imap_host: string
  imap_port: number
  smtp_host: string
  smtp_port: number
}
