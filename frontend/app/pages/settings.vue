<script setup lang="ts">
import { User, Shield, Palette, LogOut, ArrowLeft, Mail, Bell, Lock, HardDrive, Users } from 'lucide-vue-next'
const router = useRouter()
// 当前激活的 Tab
const activeTab = ref('profile')

// 使用无侧边栏布局
definePageMeta({ layout: 'pool' })
</script>

<template>
  <div class="flex w-full h-full bg-gray-50 dark:bg-bg-dark overflow-hidden">

    <!-- 1. 设置导航栏 (固定宽度 w-64) -->
    <div
      class="w-64 bg-white dark:bg-bg-panelDark border-r border-gray-200 dark:border-border-dark flex flex-col shrink-0 h-full">

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
          <button @click="activeTab = 'profile'" :class="['tab-btn', activeTab === 'profile' ? 'active' : '']">
            <User class="w-4 h-4" /> 账号信息
          </button>
          <button @click="activeTab = 'accounts'" :class="['tab-btn', activeTab === 'accounts' ? 'active' : '']">
            <Users class="w-4 h-4" /> 多账号管理
          </button>
          <button @click="activeTab = 'theme'" :class="['tab-btn', activeTab === 'theme' ? 'active' : '']">
            <Palette class="w-4 h-4" /> 外观主题
          </button>
        </div>

        <!-- 分组：邮件 -->
        <div class="space-y-1">
          <div class="px-4 text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">邮件服务</div>
          <button @click="activeTab = 'mail'" :class="['tab-btn', activeTab === 'mail' ? 'active' : '']">
            <Mail class="w-4 h-4" /> 邮件设置
          </button>
          <button @click="activeTab = 'notifications'"
            :class="['tab-btn', activeTab === 'notifications' ? 'active' : '']">
            <Bell class="w-4 h-4" /> 通知偏好
          </button>
          <button @click="activeTab = 'privacy'" :class="['tab-btn', activeTab === 'privacy' ? 'active' : '']">
            <Lock class="w-4 h-4" /> 隐私与安全
          </button>
        </div>

        <!-- 分组：数据 -->
        <div class="space-y-1">
          <div class="px-4 text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">数据</div>
          <button @click="activeTab = 'security'" :class="['tab-btn', activeTab === 'security' ? 'active' : '']">
            <Shield class="w-4 h-4" /> 登录与安全
          </button>
          <button @click="activeTab = 'storage'" :class="['tab-btn', activeTab === 'storage' ? 'active' : '']">
            <HardDrive class="w-4 h-4" /> 存储与配额
          </button>
        </div>

      </nav>

      <!-- 底部退出 -->
      <div class="p-4 border-t border-gray-100 dark:border-gray-800">
        <button
          class="tab-btn text-red-500 hover:bg-red-50 dark:hover:bg-red-900/10 hover:text-red-600 w-full justify-start">
          <LogOut class="w-4 h-4" /> 退出登录
        </button>
      </div>
    </div>

    <!-- 2. 内容主区域 -->
    <div class="flex-1 overflow-y-auto p-8 md:p-12 relative bg-gray-50 dark:bg-bg-dark">
      <div class="max-w-4xl mx-auto min-h-[600px] pb-20">

        <!-- 动态组件切换 -->
        <Transition name="fade" mode="out-in">
          <SettingsProfile v-if="activeTab === 'profile'" />
          <SettingsAccounts v-else-if="activeTab === 'accounts'" />
          <SettingsTheme v-else-if="activeTab === 'theme'" />
          <SettingsMail v-else-if="activeTab === 'mail'" />
          <SettingsNotifications v-else-if="activeTab === 'notifications'" />
          <SettingsPrivacy v-else-if="activeTab === 'privacy'" />
          <SettingsSecurity v-else-if="activeTab === 'security'" />
          <SettingsStorage v-else-if="activeTab === 'storage'" />
        </Transition>

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
</style>