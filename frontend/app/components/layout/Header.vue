<script setup lang="ts">
import { Search, Moon, Sun, Settings, Mail } from 'lucide-vue-next'
const router = useRouter()
const { isDark, toggleTheme } = useTheme()
</script>

<template>
    <header
        class="h-14 bg-white dark:bg-bg-panelDark border-b border-gray-200 dark:border-border-dark flex items-center justify-between px-4 shrink-0 transition-colors duration-200 z-20 relative">

        <!-- 左侧 Logo -->
        <!-- 修改点：去掉了 bg-primary 的 div，图标直接变大、变紫 -->
        <NuxtLink to="/" class="w-64 flex items-center gap-2 shrink-0 hover:opacity-80 transition-opacity">

            <!-- 纯图标：更极简，更现代 -->
            <Mail class="w-6 h-6 text-primary fill-primary/10" stroke-width="2.5" />

            <span class="font-bold text-xl text-gray-900 dark:text-white tracking-tight font-sans">TalentMail</span>
        </NuxtLink>

        <!-- ... 中间和右侧代码保持不变 ... -->
        <div class="flex-1 flex justify-center max-w-xl px-4">
            <div class="relative w-full group">
                <Search
                    class="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-primary transition-colors" />
                <input type="text" placeholder="搜索邮件、联系人..."
                    class="w-full bg-gray-100 dark:bg-gray-800 border-transparent focus:bg-white dark:focus:bg-gray-900 border border-transparent focus:border-primary/20 rounded-lg py-1.5 pl-9 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-primary/10 transition-all text-gray-900 dark:text-white placeholder-gray-400">
            </div>
        </div>

        <div class="flex items-center gap-1.5 justify-end shrink-0 w-64">
            <button @click="toggleTheme"
                class="p-2 text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white transition-colors rounded-md hover:bg-gray-100 dark:hover:bg-gray-800">
                <Sun v-if="isDark" class="w-4 h-4" />
                <Moon v-else class="w-4 h-4" />
            </button>
            <button @click="router.push('/settings')"
                class="p-2 text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white transition-colors rounded-md hover:bg-gray-100 dark:hover:bg-gray-800">
                <Settings class="w-4 h-4" />
            </button>
            <div @click="router.push('/settings')"
                class="w-7 h-7 rounded-full bg-gradient-to-tr from-blue-500 to-purple-500 ml-3 border border-gray-100 dark:border-gray-700 cursor-pointer shadow-sm hover:ring-2 hover:ring-primary/20 transition-all">
            </div>
        </div>
    </header>
</template>