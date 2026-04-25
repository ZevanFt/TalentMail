export default defineNuxtRouteMiddleware((to) => {
  const token = useCookie('token')

  // 不需要登录的页面
  const publicPages = ['/login', '/register', '/forgot-password']
  const publicPrefixes = ['/share/']

  if (!token.value && !publicPages.includes(to.path) && !publicPrefixes.some(p => to.path.startsWith(p))) {
    return navigateTo('/login', { replace: true })
  }

  // 已登录用户访问登录页，跳转到首页
  if (token.value && to.path === '/login') {
    return navigateTo('/', { replace: true })
  }
})