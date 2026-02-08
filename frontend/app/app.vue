<!-- <template>
  <div>
    <NuxtRouteAnnouncer />
    <NuxtWelcome />
  </div>
</template> -->

<script setup lang="ts">
const { initTheme } = useTheme()
const { initBackground, settings: bgSettings } = useBackground()
const token = useCookie('token')
const { register, unregister } = useKeyboardShortcuts()
const route = useRoute()

// 计算是否显示背景 - 只要设置中启用了就显示，权限检查在保存时进行
const showBackground = computed(() => {
  return bgSettings.value.enabled && !!bgSettings.value.imageUrl
})

// 登录/注册页面不显示自定义背景
const isAuthPage = computed(() => {
  const path = route.path
  return path === '/login' || path === '/register' || path === '/forgot-password'
})

onMounted(async () => {
  initTheme()
  await initBackground()
  // 注册键盘快捷键
  if (token.value) {
    register()
  }
})

// 监听背景设置变化，实时更新 CSS 变量
watch([() => bgSettings.value, isAuthPage], ([newSettings, authPage]) => {
  if (!import.meta.client) return
  
  const root = document.documentElement
  
  // 登录/注册页面不显示背景
  if (authPage) {
    root.classList.add('auth-page')
    root.classList.remove('has-custom-bg', 'bg-area-sidebar', 'bg-area-header', 'bg-area-main', 'bg-area-panels')
    return
  } else {
    root.classList.remove('auth-page')
  }
  
  if (newSettings.enabled && newSettings.imageUrl) {
    root.style.setProperty('--bg-custom-image', `url(${newSettings.imageUrl})`)
    root.style.setProperty('--bg-custom-opacity', `${newSettings.opacity / 100}`)
    root.style.setProperty('--bg-custom-blur', `${newSettings.blur}px`)
    root.style.setProperty('--bg-custom-overlay', `${newSettings.overlayOpacity / 100}`)
    root.classList.add('has-custom-bg')
    root.classList.toggle('bg-area-sidebar', newSettings.areas.sidebar)
    root.classList.toggle('bg-area-header', newSettings.areas.header)
    root.classList.toggle('bg-area-main', newSettings.areas.main)
    root.classList.toggle('bg-area-panels', newSettings.areas.panels)
  } else {
    // 清除背景
    root.style.removeProperty('--bg-custom-image')
    root.style.removeProperty('--bg-custom-opacity')
    root.style.removeProperty('--bg-custom-blur')
    root.style.removeProperty('--bg-custom-overlay')
    root.classList.remove('has-custom-bg', 'bg-area-sidebar', 'bg-area-header', 'bg-area-main', 'bg-area-panels')
  }
}, { deep: true, immediate: true })

onUnmounted(() => {
  unregister()
})

// 监听登录状态变化
watch(() => token.value, (newToken) => {
  if (newToken) {
    register()
  } else {
    unregister()
  }
})
</script>

<template>
  <!-- 全局背景层 - 始终渲染，由 CSS 控制显示 -->
  <div class="global-bg-layer" />
  
  <NuxtLayout>
    <NuxtPage />

    <!-- 全局挂载弹窗 - 仅登录后显示 -->
    <EmailComposeModal v-if="token" />
    
    <!-- 键盘快捷键帮助弹窗 -->
    <CommonKeyboardShortcutsHelp v-if="token" />
  </NuxtLayout>
</template>

<style>
/* ========================================
   TalentMail 统一磨砂玻璃效果设计系统
   ======================================== */

/* === CSS 变量定义 === */
:root {
  /* 磨砂玻璃效果参数 */
  --glass-blur: 16px;
  --glass-saturate: 180%;
  
  /* 浅色模式磨砂玻璃 */
  --glass-light-bg: rgba(255, 255, 255, 0.78);
  --glass-light-border: rgba(229, 231, 235, 0.6);
  
  /* 暗色模式磨砂玻璃 - 使用 panelDark 颜色 #18181b = rgb(24,24,27) */
  --glass-dark-bg: rgba(24, 24, 27, 0.82);
  --glass-dark-border: rgba(63, 63, 70, 0.5);
}

/* ========== 登录/注册页面：不显示自定义背景 ========== */
html.auth-page .global-bg-layer {
  display: none !important;
}

/* ========== 全局背景层 ========== */
.global-bg-layer {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  width: 100vw;
  height: 100vh;
  z-index: -1;
  background-image: var(--bg-custom-image);
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  opacity: 0;
  filter: blur(var(--bg-custom-blur, 0px));
  pointer-events: none;
  transition: opacity 0.3s ease;
  display: none;
}

/* 启用背景时显示背景层 - 浅色和暗色模式都生效 */
html.has-custom-bg .global-bg-layer {
  display: block;
  opacity: var(--bg-custom-opacity, 0.3);
}

/* ========================================
   核心修复：让所有页面容器透明以显示背景
   这是让背景可见的关键！
   ======================================== */

/* 浅色模式 - 让所有容器透明 */
html.has-custom-bg.bg-area-main body,
html.has-custom-bg.bg-area-main #__nuxt {
  background: transparent !important;
}

/* 暗色模式 - 同样让容器透明 */
html.has-custom-bg.dark.bg-area-main body,
html.has-custom-bg.dark.bg-area-main #__nuxt {
  background: transparent !important;
}

/* Layout 最外层容器透明 - 使用具体的 layout class */
html.has-custom-bg.bg-area-main .layout-default,
html.has-custom-bg.bg-area-main .layout-pool {
  background: transparent !important;
}

html.has-custom-bg.dark.bg-area-main .layout-default,
html.has-custom-bg.dark.bg-area-main .layout-pool {
  background: transparent !important;
}

/* settings.vue 页面容器透明 - 主内容区 */
html.has-custom-bg.bg-area-main .settings-page {
  background: transparent !important;
}

html.has-custom-bg.dark.bg-area-main .settings-page {
  background: transparent !important;
}

/* 设置页面内容区域磨砂效果 - 浅色模式 */
html.has-custom-bg.bg-area-main .settings-content {
  background: var(--glass-light-bg) !important;
  backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate)) !important;
  -webkit-backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate)) !important;
}

/* 设置页面内容区域磨砂效果 - 暗色模式 */
html.has-custom-bg.dark.bg-area-main .settings-content {
  background: var(--glass-dark-bg) !important;
  backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate)) !important;
  -webkit-backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate)) !important;
}

/* 首页主容器透明 */
html.has-custom-bg.bg-area-main .main-container {
  background: transparent !important;
}

html.has-custom-bg.dark.bg-area-main .main-container {
  background: transparent !important;
}

/* 账号池页面 pool.vue 容器透明 */
html.has-custom-bg.bg-area-main .pool-page,
html.has-custom-bg.bg-area-main .flex.w-full.h-full.bg-white {
  background: transparent !important;
}

html.has-custom-bg.dark.bg-area-main .pool-page,
html.has-custom-bg.dark.bg-area-main .flex.w-full.h-full.dark\:bg-bg-dark {
  background: transparent !important;
}

/* ========== Header 磨砂玻璃效果 ========== */
/* 浅色模式 */
html.has-custom-bg.bg-area-header .header-glass,
html.has-custom-bg.bg-area-header header {
  background: var(--glass-light-bg) !important;
  backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate));
  -webkit-backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate));
  border-bottom: 1px solid var(--glass-light-border) !important;
}

/* 暗色模式 */
html.has-custom-bg.dark.bg-area-header .header-glass,
html.has-custom-bg.dark.bg-area-header header {
  background: var(--glass-dark-bg) !important;
  backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate));
  -webkit-backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate));
  border-bottom: 1px solid var(--glass-dark-border) !important;
}

/* 搜索框样式 */
html.has-custom-bg.bg-area-header .header-glass input,
html.has-custom-bg.bg-area-header header input {
  background: rgba(243, 244, 246, 0.85) !important;
}

html.has-custom-bg.dark.bg-area-header .header-glass input,
html.has-custom-bg.dark.bg-area-header header input {
  background: rgba(39, 39, 42, 0.85) !important;
}

/* ========== 侧边栏磨砂玻璃效果 ========== */
/* 浅色模式 - 主页和设置页面侧边栏 */
html.has-custom-bg.bg-area-sidebar .sidebar-glass {
  background: var(--glass-light-bg) !important;
  backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate));
  -webkit-backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate));
}

/* 暗色模式 */
html.has-custom-bg.dark.bg-area-sidebar .sidebar-glass {
  background: var(--glass-dark-bg) !important;
  backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate));
  -webkit-backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate));
}

/* 设置页面左侧导航栏 - 浅色模式 */
html.has-custom-bg.bg-area-sidebar .settings-sidebar {
  background: var(--glass-light-bg) !important;
  backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate));
  -webkit-backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate));
}

/* 设置页面左侧导航栏 - 暗色模式 */
html.has-custom-bg.dark.bg-area-sidebar .settings-sidebar {
  background: var(--glass-dark-bg) !important;
  backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate));
  -webkit-backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate));
}

/* 账号池页面第一栏 - 浅色模式 */
html.has-custom-bg.bg-area-sidebar .pool-sidebar {
  background: var(--glass-light-bg) !important;
  backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate));
  -webkit-backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate));
}

/* 账号池页面第一栏 - 暗色模式 */
html.has-custom-bg.dark.bg-area-sidebar .pool-sidebar {
  background: var(--glass-dark-bg) !important;
  backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate));
  -webkit-backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate));
}

/* 账号池页面第二栏 - 浅色模式 - 不使用 backdrop-filter，让子元素可以正常使用 */
html.has-custom-bg.bg-area-main .pool-email-list {
  background: transparent !important;
}

/* 账号池页面第二栏 - 暗色模式 */
html.has-custom-bg.dark.bg-area-main .pool-email-list {
  background: transparent !important;
}

/* 账号池页面第二栏内容区 - 浅色模式 */
html.has-custom-bg.bg-area-main .pool-email-list > .flex-1 {
  background: var(--glass-light-bg) !important;
  backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate)) !important;
  -webkit-backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate)) !important;
}

/* 账号池页面第二栏内容区 - 暗色模式 */
html.has-custom-bg.dark.bg-area-main .pool-email-list > .flex-1 {
  background: var(--glass-dark-bg) !important;
  backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate)) !important;
  -webkit-backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate)) !important;
}

/* 账号池页面第三栏 - 浅色模式 - 不使用 backdrop-filter，让子元素可以正常使用 */
html.has-custom-bg.bg-area-main .pool-detail {
  background: transparent !important;
}

/* 账号池页面第三栏 - 暗色模式 */
html.has-custom-bg.dark.bg-area-main .pool-detail {
  background: transparent !important;
}

/* 账号池页面第三栏内容区 - 浅色模式 */
html.has-custom-bg.bg-area-main .pool-detail > .flex-1 {
  background: var(--glass-light-bg) !important;
  backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate)) !important;
  -webkit-backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate)) !important;
}

/* 账号池页面第三栏内容区 - 暗色模式 */
html.has-custom-bg.dark.bg-area-main .pool-detail > .flex-1 {
  background: var(--glass-dark-bg) !important;
  backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate)) !important;
  -webkit-backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate)) !important;
}

/* 账号池页面第三栏顶部栏 - 浅色模式 */
html.has-custom-bg.bg-area-main .pool-detail-header,
html.has-custom-bg.bg-area-main .pool-page .pool-detail-header,
html.has-custom-bg.bg-area-main .pool-detail .pool-detail-header {
  background: var(--glass-light-bg) !important;
  backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate)) !important;
  -webkit-backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate)) !important;
}

/* 账号池页面第三栏顶部栏 - 暗色模式 */
html.has-custom-bg.dark.bg-area-main .pool-detail-header,
html.has-custom-bg.dark.bg-area-main .pool-page .pool-detail-header,
html.has-custom-bg.dark.bg-area-main .pool-detail .pool-detail-header {
  background: var(--glass-dark-bg) !important;
  backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate)) !important;
  -webkit-backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate)) !important;
}

/* 账号池页面第二栏顶部栏 - 浅色模式 */
html.has-custom-bg.bg-area-main .pool-email-header,
html.has-custom-bg.bg-area-main .pool-page .pool-email-header,
html.has-custom-bg.bg-area-main .pool-email-list .pool-email-header {
  background: var(--glass-light-bg) !important;
  backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate)) !important;
  -webkit-backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate)) !important;
}

/* 账号池页面第二栏顶部栏 - 暗色模式 */
html.has-custom-bg.dark.bg-area-main .pool-email-header,
html.has-custom-bg.dark.bg-area-main .pool-page .pool-email-header,
html.has-custom-bg.dark.bg-area-main .pool-email-list .pool-email-header {
  background: var(--glass-dark-bg) !important;
  backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate)) !important;
  -webkit-backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate)) !important;
}

/* ========== 统一卡片磨砂玻璃效果 - 核心样式 ========== */
/* 使用 .card 类的统一样式 - 浅色模式 */
html.has-custom-bg.bg-area-main .card {
  background: var(--glass-light-bg) !important;
  backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate)) !important;
  -webkit-backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate)) !important;
  border-color: var(--glass-light-border) !important;
}

/* 使用 .card 类的统一样式 - 暗色模式 */
html.has-custom-bg.dark.bg-area-main .card {
  background: var(--glass-dark-bg) !important;
  backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate)) !important;
  -webkit-backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate)) !important;
  border-color: var(--glass-dark-border) !important;
}

/* ========== 设置页面内所有卡片统一磨砂效果 ========== */
/* 浅色模式 - 覆盖所有可能的卡片背景 */
html.has-custom-bg.bg-area-main .settings-content .card,
html.has-custom-bg.bg-area-main .settings-content .rounded-xl.border,
html.has-custom-bg.bg-area-main .settings-content .rounded-2xl.border,
html.has-custom-bg.bg-area-main .settings-content [class*="bg-white"],
html.has-custom-bg.bg-area-main .settings-content [class*="rounded-xl"][class*="border"],
html.has-custom-bg.bg-area-main .settings-content [class*="rounded-2xl"][class*="border"] {
  background: var(--glass-light-bg) !important;
  backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate)) !important;
  -webkit-backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate)) !important;
}

/* 暗色模式 - 覆盖所有可能的卡片背景 */
html.has-custom-bg.dark.bg-area-main .settings-content .card,
html.has-custom-bg.dark.bg-area-main .settings-content .rounded-xl.border,
html.has-custom-bg.dark.bg-area-main .settings-content .rounded-2xl.border,
html.has-custom-bg.dark.bg-area-main .settings-content [class*="dark:bg-bg-panelDark"],
html.has-custom-bg.dark.bg-area-main .settings-content [class*="dark:bg-gray-800"],
html.has-custom-bg.dark.bg-area-main .settings-content [class*="dark:bg-gray-900"],
html.has-custom-bg.dark.bg-area-main .settings-content [class*="rounded-xl"][class*="border"],
html.has-custom-bg.dark.bg-area-main .settings-content [class*="rounded-2xl"][class*="border"] {
  background: var(--glass-dark-bg) !important;
  backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate)) !important;
  -webkit-backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate)) !important;
}

/* 设置页面内的 stat-box 和内部小卡片也统一 */
html.has-custom-bg.bg-area-main .settings-content .stat-box {
  background: rgba(255, 255, 255, 0.5) !important;
  backdrop-filter: blur(8px) !important;
  -webkit-backdrop-filter: blur(8px) !important;
}

html.has-custom-bg.dark.bg-area-main .settings-content .stat-box {
  background: rgba(39, 39, 42, 0.5) !important;
  backdrop-filter: blur(8px) !important;
  -webkit-backdrop-filter: blur(8px) !important;
}

/* ========== 邮件列表和详情容器 ========== */
html.has-custom-bg.bg-area-main .email-list-container,
html.has-custom-bg.bg-area-main .email-detail-container {
  background: var(--glass-light-bg) !important;
  backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate));
  -webkit-backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate));
}

html.has-custom-bg.dark.bg-area-main .email-list-container,
html.has-custom-bg.dark.bg-area-main .email-detail-container {
  background: var(--glass-dark-bg) !important;
  backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate));
  -webkit-backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate));
}

/* ========== 边框透明化 ========== */
html.has-custom-bg.bg-area-main .border-gray-200,
html.has-custom-bg.bg-area-main .border-gray-100 {
  border-color: var(--glass-light-border) !important;
}

html.has-custom-bg.dark.bg-area-main .border-gray-700,
html.has-custom-bg.dark.bg-area-main .dark\:border-gray-700,
html.has-custom-bg.dark.bg-area-main .dark\:border-border-dark {
  border-color: var(--glass-dark-border) !important;
}

/* ========== 保护设置页面的背景图片预览区域 ========== */
html.has-custom-bg [data-bg-preview],
html.has-custom-bg [data-bg-preview] * {
  background: revert !important;
  backdrop-filter: none !important;
  -webkit-backdrop-filter: none !important;
}

/* ========== 面板透明效果 ========== */
html.has-custom-bg.bg-area-panels .panel-glass {
  background: var(--glass-light-bg) !important;
  backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate));
  -webkit-backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate));
}

html.has-custom-bg.dark.bg-area-panels .panel-glass {
  background: var(--glass-dark-bg) !important;
  backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate));
  -webkit-backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate));
}

/* ========== 模态框保护：始终使用实心背景 ========== */
.modal-solid-bg {
  background: rgb(255, 255, 255) !important;
  backdrop-filter: none !important;
  -webkit-backdrop-filter: none !important;
}

html.dark .modal-solid-bg {
  background: rgb(24, 24, 27) !important;
  backdrop-filter: none !important;
  -webkit-backdrop-filter: none !important;
}

/* 模态框内的内容也保持实心背景 */
.modal-solid-bg .bg-white,
.modal-solid-bg .bg-gray-50,
.modal-solid-bg .bg-gray-100 {
  background: rgb(255, 255, 255) !important;
  backdrop-filter: none !important;
}

html.dark .modal-solid-bg .dark\:bg-gray-800,
html.dark .modal-solid-bg .dark\:bg-gray-900,
html.dark .modal-solid-bg .dark\:bg-bg-panelDark {
  background: rgb(24, 24, 27) !important;
  backdrop-filter: none !important;
}

/* ========== 弹窗/对话框保护 ========== */
html.has-custom-bg .fixed.inset-0.z-50 > div.bg-white,
html.has-custom-bg .fixed.inset-0.z-50 > div[class*="dark:bg-gray-800"],
html.has-custom-bg .fixed.inset-0.z-50 > div[class*="rounded-xl"],
html.has-custom-bg .fixed.inset-0.z-50 > div[class*="rounded-2xl"] {
  background: rgb(255, 255, 255) !important;
  backdrop-filter: none !important;
  -webkit-backdrop-filter: none !important;
}

html.has-custom-bg.dark .fixed.inset-0.z-50 > div.bg-white,
html.has-custom-bg.dark .fixed.inset-0.z-50 > div[class*="dark:bg-gray-800"],
html.has-custom-bg.dark .fixed.inset-0.z-50 > div[class*="rounded-xl"],
html.has-custom-bg.dark .fixed.inset-0.z-50 > div[class*="rounded-2xl"] {
  background: rgb(24, 24, 27) !important;
  backdrop-filter: none !important;
  -webkit-backdrop-filter: none !important;
}

/* ========== 模态框内 kbd 元素专用样式 ========== */
/* 防止 kbd 元素被上面的通用规则覆盖 */
.modal-solid-bg kbd {
  background: rgb(243, 244, 246) !important; /* gray-100 */
  color: rgb(55, 65, 81) !important; /* gray-700 */
}

html.dark .modal-solid-bg kbd {
  background: rgb(75, 85, 99) !important; /* gray-600 */
  color: rgb(255, 255, 255) !important; /* white */
}
</style>