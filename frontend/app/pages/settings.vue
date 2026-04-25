<script setup lang="ts">
import { User, Shield, Palette, LogOut, ArrowLeft, Mail, Bell, Lock, HardDrive, Users, Ticket, UserCog, CreditCard, AtSign, FileText, Info, Zap, Workflow, ScrollText, Box, ChevronDown } from 'lucide-vue-next'
const router = useRouter()
const route = useRoute()
const { logout, getMe } = useApi()
const { isMobile, initResponsive } = useResponsive()

const activeTab = ref('profile')
const isAdmin = ref(false)
const mobileMenuOpen = ref(false)

definePageMeta({ layout: 'pool' })

// 从 URL 参数读取 tab
const initTabFromQuery = () => {
  const tabFromQuery = route.query.tab as string
  if (tabFromQuery) {
    activeTab.value = tabFromQuery
  }
}

// 切换 tab 并更新 URL
const setTab = (tab: string) => {
  activeTab.value = tab
  // 更新 URL query 参数，不触发页面刷新
  // 默认 tab (profile) 不需要带参数，保持 URL 干净
  if (tab === 'profile') {
    router.replace({ path: '/settings' })
  } else {
    router.replace({ path: '/settings', query: { tab } })
  }
}

// 检查是否是管理员
// Tab 配置（label 用于移动端显示）
const tabGroups = computed(() => {
  const groups = [
    { label: '通用', tabs: [
      { key: 'profile', label: '账号信息', icon: 'User' },
      { key: 'accounts', label: '多账号管理', icon: 'Users' },
      { key: 'theme', label: '外观主题', icon: 'Palette' },
    ]},
    { label: '邮件服务', tabs: [
      { key: 'mail', label: '邮件设置', icon: 'Mail' },
      { key: 'my-workflows', label: '我的工作流', icon: 'Workflow' },
      { key: 'notifications', label: '通知偏好', icon: 'Bell' },
      { key: 'privacy', label: '隐私与安全', icon: 'Lock' },
    ]},
    { label: '数据', tabs: [
      { key: 'security', label: '登录与安全', icon: 'Shield' },
      { key: 'storage', label: '存储与配额', icon: 'HardDrive' },
    ]},
    { label: '其他', tabs: [
      { key: 'changelog', label: '更新日志', icon: 'ScrollText' },
      { key: 'about', label: '关于', icon: 'Info' },
    ]},
  ]
  if (isAdmin.value) {
    groups.push({ label: '管理', tabs: [
      { key: 'billing', label: '会员订阅管理', icon: 'CreditCard' },
      { key: 'invites', label: '邀请码管理', icon: 'Ticket' },
      { key: 'prefixes', label: '保留前缀管理', icon: 'AtSign' },
      { key: 'email-templates', label: '邮件模板管理', icon: 'FileText' },
      { key: 'system-workflows', label: '系统工作流', icon: 'Workflow' },
      { key: 'temp-mail-policy', label: '临时邮箱策略', icon: 'Box' },
      { key: 'user-mgmt', label: '用户权限管理', icon: 'UserCog' },
    ]})
  }
  return groups
})

const activeTabLabel = computed(() => {
  for (const group of tabGroups.value) {
    const found = group.tabs.find(t => t.key === activeTab.value)
    if (found) return found.label
  }
  return '设置'
})

const setTabMobile = (tab: string) => {
  setTab(tab)
  mobileMenuOpen.value = false
}

onMounted(async () => {
  initResponsive()
  initTabFromQuery()
  try {
    const user = await getMe()
    isAdmin.value = user.role === 'admin'
  } catch (e) { console.warn('获取用户信息失败:', e) }
})

// 监听路由变化（用于浏览器前进/后退）
watch(() => route.query.tab, (newTab) => {
  if (newTab && typeof newTab === 'string' && newTab !== activeTab.value) {
    activeTab.value = newTab
  }
})

const handleLogout = () => {
  logout()
  router.push('/login')
}

// 动态 tab 组件映射 — 使用 defineAsyncComponent 懒加载
// Nuxt 自动导入的组件不在 Vue 全局注册表里，字符串方式不可用。
// 这里显式用 defineAsyncComponent + import() 构建组件对象映射。
const settingsTabMap: Record<string, Component> = {
  'profile': defineAsyncComponent(() => import('~/components/settings/Profile.vue')),
  'accounts': defineAsyncComponent(() => import('~/components/settings/Accounts.vue')),
  'theme': defineAsyncComponent(() => import('~/components/settings/Theme.vue')),
  'mail': defineAsyncComponent(() => import('~/components/settings/Mail.vue')),
  'my-workflows': defineAsyncComponent(() => import('~/components/settings/MyWorkflows.vue')),
  'notifications': defineAsyncComponent(() => import('~/components/settings/Notifications.vue')),
  'privacy': defineAsyncComponent(() => import('~/components/settings/Privacy.vue')),
  'security': defineAsyncComponent(() => import('~/components/settings/Security.vue')),
  'storage': defineAsyncComponent(() => import('~/components/settings/Storage.vue')),
  'billing': defineAsyncComponent(() => import('~/components/settings/Billing.vue')),
  'invites': defineAsyncComponent(() => import('~/components/settings/InviteCodes.vue')),
  'prefixes': defineAsyncComponent(() => import('~/components/settings/ReservedPrefixes.vue')),
  'email-templates': defineAsyncComponent(() => import('~/components/settings/EmailTemplates.vue')),
  'system-workflows': defineAsyncComponent(() => import('~/components/settings/SystemWorkflows.vue')),
  'temp-mail-policy': defineAsyncComponent(() => import('~/components/settings/TempMailboxPolicy.vue')),
  'changelog': defineAsyncComponent(() => import('~/components/settings/Changelog.vue')),
  'about': defineAsyncComponent(() => import('~/components/settings/About.vue')),
  'user-mgmt': defineAsyncComponent(() => import('~/components/settings/UserManagement.vue')),
}

// user-mgmt 使用全高度布局（overflow-hidden），其他 tab 使用滚动布局
const isFullHeightTab = computed(() => activeTab.value === 'user-mgmt')

// 当前活跃组件
const activeComponent = computed(() => {
  const comp = settingsTabMap[activeTab.value]
  if (!comp) {
    console.warn(`[Settings] 未知 tab: ${activeTab.value}, 回退到 profile`)
  }
  return comp || settingsTabMap['profile']
})
</script>

<template>
  <div class="settings-page flex flex-col lg:flex-row w-full h-full bg-gray-50 dark:bg-bg-dark overflow-hidden">

    <!-- 移动端 tab 选择器 -->
    <div v-if="isMobile" class="shrink-0 bg-white dark:bg-bg-panelDark border-b border-gray-200 dark:border-border-dark">
      <div class="flex items-center px-4 h-12 gap-2">
        <button @click="router.push('/')" class="p-2 -ml-2 text-gray-500 hover:text-gray-900 dark:hover:text-white rounded-lg transition-colors">
          <ArrowLeft class="w-5 h-5" />
        </button>
        <button @click="mobileMenuOpen = !mobileMenuOpen" class="flex-1 flex items-center justify-between py-2 px-3 bg-gray-50 dark:bg-gray-800 rounded-lg text-sm font-bold text-gray-900 dark:text-white">
          {{ activeTabLabel }}
          <ChevronDown class="w-4 h-4 text-gray-400 transition-transform" :class="{ 'rotate-180': mobileMenuOpen }" />
        </button>
      </div>
      <!-- 下拉菜单 -->
      <Transition name="slide-down">
        <div v-if="mobileMenuOpen" class="px-4 pb-3 max-h-[60vh] overflow-y-auto space-y-3">
          <div v-for="group in tabGroups" :key="group.label">
            <div class="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-1 px-2">{{ group.label }}</div>
            <button v-for="tab in group.tabs" :key="tab.key" @click="setTabMobile(tab.key)"
              :class="['w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors text-left', activeTab === tab.key ? 'bg-primary/10 text-primary font-bold' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800']">
              {{ tab.label }}
            </button>
          </div>
          <button @click="handleLogout" class="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-red-500 hover:bg-red-50 dark:hover:bg-red-900/10 text-left">
            <LogOut class="w-4 h-4" /> 退出登录
          </button>
        </div>
      </Transition>
    </div>

    <!-- 1. 设置导航栏 (固定宽度 w-64，移动端隐藏) -->
    <div
      class="settings-sidebar w-64 bg-white dark:bg-bg-panelDark border-r border-gray-200 dark:border-border-dark flex-col shrink-0 h-full hidden lg:flex">

      <!-- 顶部返回 -->
      <div class="h-14 flex items-center px-6 gap-2 border-b border-gray-100 dark:border-gray-800 shrink-0">
        <button @click="router.push('/')"
          class="flex items-center gap-2 text-gray-500 hover:text-gray-900 dark:hover:text-white font-bold transition-colors">
          <ArrowLeft class="w-5 h-5" /> 设置
        </button>
      </div>

      <!-- 导航菜单 -->
      <nav class="p-4 flex-1 overflow-y-auto custom-scrollbar space-y-6">

        <!-- 分组：通用 -->
        <div class="space-y-1">
          <div class="px-4 text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">通用</div>
          <button @click="setTab('profile')" :class="['tab-btn', activeTab === 'profile' ? 'active' : '']">
            <User class="w-4 h-4" /> 账号信息
          </button>
          <button @click="setTab('accounts')" :class="['tab-btn', activeTab === 'accounts' ? 'active' : '']">
            <Users class="w-4 h-4" /> 多账号管理
          </button>
          <button @click="setTab('theme')" :class="['tab-btn', activeTab === 'theme' ? 'active' : '']">
            <Palette class="w-4 h-4" /> 外观主题
          </button>
        </div>

        <!-- 分组：邮件 -->
        <div class="space-y-1">
          <div class="px-4 text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">邮件服务</div>
          <button @click="setTab('mail')" :class="['tab-btn', activeTab === 'mail' ? 'active' : '']">
            <Mail class="w-4 h-4" /> 邮件设置
          </button>
          <button @click="setTab('my-workflows')" :class="['tab-btn', activeTab === 'my-workflows' ? 'active' : '']">
            <Workflow class="w-4 h-4" /> 我的工作流
          </button>
          <button @click="setTab('notifications')"
            :class="['tab-btn', activeTab === 'notifications' ? 'active' : '']">
            <Bell class="w-4 h-4" /> 通知偏好
          </button>
          <button @click="setTab('privacy')" :class="['tab-btn', activeTab === 'privacy' ? 'active' : '']">
            <Lock class="w-4 h-4" /> 隐私与安全
          </button>
        </div>

        <!-- 分组：数据 -->
        <div class="space-y-1">
          <div class="px-4 text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">数据</div>
          <button @click="setTab('security')" :class="['tab-btn', activeTab === 'security' ? 'active' : '']">
            <Shield class="w-4 h-4" /> 登录与安全
          </button>
          <button @click="setTab('storage')" :class="['tab-btn', activeTab === 'storage' ? 'active' : '']">
            <HardDrive class="w-4 h-4" /> 存储与配额
          </button>
        </div>

        <!-- 分组：其他 -->
        <div class="space-y-1">
          <div class="px-4 text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">其他</div>
          <button @click="setTab('changelog')" :class="['tab-btn', activeTab === 'changelog' ? 'active' : '']">
            <ScrollText class="w-4 h-4" /> 更新日志
          </button>
          <button @click="setTab('about')" :class="['tab-btn', activeTab === 'about' ? 'active' : '']">
            <Info class="w-4 h-4" /> 关于
          </button>
        </div>

        <!-- 分组：管理（仅管理员可见） -->
        <div v-if="isAdmin" class="space-y-1">
          <div class="px-4 text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">管理</div>
          <button @click="setTab('billing')" :class="['tab-btn', activeTab === 'billing' ? 'active' : '']">
            <CreditCard class="w-4 h-4" /> 会员订阅管理
          </button>
          <button @click="setTab('invites')" :class="['tab-btn', activeTab === 'invites' ? 'active' : '']">
            <Ticket class="w-4 h-4" /> 邀请码管理
          </button>
          <button @click="setTab('prefixes')" :class="['tab-btn', activeTab === 'prefixes' ? 'active' : '']">
            <AtSign class="w-4 h-4" /> 保留前缀管理
          </button>
          <button @click="setTab('email-templates')" :class="['tab-btn', activeTab === 'email-templates' ? 'active' : '']">
            <FileText class="w-4 h-4" /> 邮件模板管理
          </button>
          <button @click="setTab('system-workflows')" :class="['tab-btn', activeTab === 'system-workflows' ? 'active' : '']">
            <Workflow class="w-4 h-4" /> 系统工作流
          </button>
          <button @click="setTab('temp-mail-policy')" :class="['tab-btn', activeTab === 'temp-mail-policy' ? 'active' : '']">
            <Box class="w-4 h-4" /> 临时邮箱策略
          </button>
          <button @click="setTab('user-mgmt')" :class="['tab-btn', activeTab === 'user-mgmt' ? 'active' : '']">
            <UserCog class="w-4 h-4" /> 用户权限管理
          </button>
        </div>

      </nav>

      <!-- 底部退出 -->
      <div class="p-4 border-t border-gray-100 dark:border-gray-800">
        <button @click="handleLogout"
          class="tab-btn text-red-500 hover:bg-red-50 dark:hover:bg-red-900/10 hover:text-red-600 w-full justify-start">
          <LogOut class="w-4 h-4" /> 退出登录
        </button>
      </div>
    </div>

    <!-- 2. 内容主区域（动态组件替代 17 个 v-if/v-else-if） -->
    <div class="settings-content flex-1 flex flex-col overflow-hidden bg-gray-50 dark:bg-bg-dark">
      <div
        class="flex-1 p-4 lg:p-8 xl:p-12"
        :class="isFullHeightTab ? 'overflow-hidden' : 'overflow-y-auto'"
      >
        <div :class="isFullHeightTab ? 'max-w-5xl mx-auto h-full' : 'max-w-4xl mx-auto min-h-[600px] pb-20'">
          <Transition name="fade" mode="out-in">
            <component :is="activeComponent" :key="activeTab" />
          </Transition>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.tab-btn {
  @apply w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm text-gray-600 dark:text-gray-400 font-medium hover:bg-gray-100 dark:hover:bg-gray-800 transition-all text-left;
}

.tab-btn.active {
  @apply bg-primary/10 text-primary dark:bg-primary/20 dark:text-primary font-bold;
}

/* 简单的淡入淡出动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 移动端下拉菜单动画 */
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.2s ease;
  overflow: hidden;
}
.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  max-height: 0;
}
.slide-down-enter-to,
.slide-down-leave-from {
  opacity: 1;
  max-height: 60vh;
}
</style>
