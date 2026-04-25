/**
 * 响应式断点检测 & 移动端状态管理
 * 使用 matchMedia 监听，SSR 安全，useState 跨组件共享
 */
export const useResponsive = () => {
  const isMobile = useState('isMobile', () => false)       // < 768px
  const isDesktop = useState('isDesktop', () => true)       // >= 1024px

  // 移动端侧边栏抽屉状态
  const isSidebarOpen = useState('sidebarOpen', () => false)

  // 移动端邮件列表↔详情切换
  const mobileShowDetail = useState('mobileShowDetail', () => false)

  // 防止重复注册 listener
  const initialized = useState('responsiveInit', () => false)

  // 存储 mediaQuery 引用和 handler 用于清理
  let mqMobile: MediaQueryList | null = null
  let mqDesktop: MediaQueryList | null = null
  let updateHandler: (() => void) | null = null

  const initResponsive = () => {
    if (!import.meta.client || initialized.value) return
    initialized.value = true

    mqMobile = window.matchMedia('(max-width: 767px)')
    mqDesktop = window.matchMedia('(min-width: 1024px)')

    updateHandler = () => {
      isMobile.value = mqMobile!.matches
      isDesktop.value = mqDesktop!.matches

      // 切换到桌面端时，自动关闭抽屉、重置列表/详情切换
      if (isDesktop.value) {
        isSidebarOpen.value = false
        mobileShowDetail.value = false
      }
    }

    // 初始值
    updateHandler()

    // 监听变化
    mqMobile.addEventListener('change', updateHandler)
    mqDesktop.addEventListener('change', updateHandler)
  }

  // 清理监听器
  if (import.meta.client) {
    onScopeDispose(() => {
      if (mqMobile && updateHandler) mqMobile.removeEventListener('change', updateHandler)
      if (mqDesktop && updateHandler) mqDesktop.removeEventListener('change', updateHandler)
      mqMobile = null
      mqDesktop = null
      updateHandler = null
    })
  }

  // 侧边栏控制
  const toggleSidebar = () => { isSidebarOpen.value = !isSidebarOpen.value }
  const closeSidebar = () => { isSidebarOpen.value = false }

  // 移动端列表↔详情切换
  const showEmailDetail = () => { mobileShowDetail.value = true }
  const showEmailList = () => { mobileShowDetail.value = false }

  return {
    isMobile,
    isDesktop,
    isSidebarOpen,
    mobileShowDetail,
    initResponsive,
    toggleSidebar,
    closeSidebar,
    showEmailDetail,
    showEmailList,
  }
}
