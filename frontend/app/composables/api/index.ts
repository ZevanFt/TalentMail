/**
 * API 模块统一导出
 *
 * 模块化结构：
 * - base.ts    - 基础 API 请求方法
 * - auth.ts    - 认证相关（登录、注册、2FA）
 * - email.ts   - 邮件相关（收发、批量操作）
 * - spam.ts    - 垃圾邮件管理（白名单、黑名单）
 * - user.ts    - 用户相关（个人信息、会话、别名）
 * - workflow.ts - 工作流相关
 * - admin.ts   - 管理员功能
 * - features.ts - 其他功能（模板、标签、联系人等）
 */

export { useApiBase } from './base'
export { useAuthApi } from './auth'
export { useEmailApi } from './email'
export { useSpamApi } from './spam'
export { useUserApi } from './user'
export { useWorkflowApi } from './workflow'
export { useAdminApi } from './admin'
export { useFeaturesApi } from './features'

/**
 * 组合所有 API（用于需要全部功能的场景）
 */
export const useAllApis = () => {
  const auth = useAuthApi()
  const email = useEmailApi()
  const spam = useSpamApi()
  const user = useUserApi()
  const workflow = useWorkflowApi()
  const admin = useAdminApi()
  const features = useFeaturesApi()

  return {
    ...auth,
    ...email,
    ...spam,
    ...user,
    ...workflow,
    ...admin,
    ...features
  }
}
