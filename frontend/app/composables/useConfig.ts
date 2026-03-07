// 配置 - 优先从运行时和当前访问域名推断，避免域名写死
export const useConfig = () => {
  const runtimeConfig = useRuntimeConfig()
  const rawBaseDomain = runtimeConfig.public.baseDomain
  const configuredDomain = typeof rawBaseDomain === 'string' && rawBaseDomain.trim()
    ? rawBaseDomain.trim()
    : ''

  const requestUrl = useRequestURL()
  const hostname = (requestUrl.hostname || '').toLowerCase()

  // 从 mail.talenting.vip 推断 talenting.vip；localhost 不参与推断。
  const inferredDomain = (() => {
    if (!hostname || hostname === 'localhost' || /^\d+\.\d+\.\d+\.\d+$/.test(hostname)) return ''
    const parts = hostname.split('.')
    if (parts.length < 2) return ''
    return parts.slice(-2).join('.')
  })()

  const baseDomain = inferredDomain || configuredDomain || 'talenting.vip'
  
  return {
    appName: 'TalentMail',
    appIcon: '/logo.svg',
    baseDomain,
    emailDomain: `@${baseDomain}`,
  }
}
