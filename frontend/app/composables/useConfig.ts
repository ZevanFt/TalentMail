// 配置 - 从 runtimeConfig 获取，默认 undefined.test 便于调试
export const useConfig = () => {
  const runtimeConfig = useRuntimeConfig()
  const baseDomain = runtimeConfig.public.baseDomain || 'undefined.test'
  
  return {
    appName: 'TalentMail',
    appIcon: '/logo.svg',
    baseDomain,
    emailDomain: `@${baseDomain}`,
  }
}