export default defineNuxtRouteMiddleware((to) => {
  const token = useCookie('token')
  
  // 不需要登录的页面
  const publicPages = ['/login', '/register']
  
  if (!token.value && !publicPages.includes(to.path)) {
    return navigateTo('/login')
  }
  
  // 已登录用户访问登录页，跳转到首页
  if (token.value && to.path === '/login') {
    return navigateTo('/')
  }
})