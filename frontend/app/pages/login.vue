<script setup lang="ts">
import { Mail, Eye, EyeOff, Moon, Sun } from 'lucide-vue-next'
const { isDark, toggleTheme } = useTheme() // 复用之前的 hook

// 禁用默认布局 (不显示侧边栏和Header)
definePageMeta({
    layout: false
})

const showPassword = ref(false)
const form = reactive({
    email: '',
    password: ''
})

const handleLogin = () => {
    // 这里写登录逻辑
    console.log('Login:', form)
    // 登录成功后跳转
    useRouter().push('/')
}
</script>

<template>
    <div
        class="min-h-screen w-full flex items-center justify-center bg-gray-50 dark:bg-bg-dark transition-colors duration-300 p-4">

        <!-- 登录卡片 -->
        <div
            class="w-full max-w-[400px] bg-white dark:bg-bg-panelDark rounded-2xl shadow-xl p-8 md:p-10 transition-colors duration-300 relative overflow-hidden">

            <!-- 顶部 Logo -->
            <div class="flex flex-col items-center mb-8">
                <div
                    class="w-12 h-12 bg-gradient-to-tr from-primary to-purple-400 rounded-xl flex items-center justify-center text-white shadow-lg shadow-primary/30 mb-4">
                    <Mail class="w-6 h-6" />
                </div>
                <h1 class="text-2xl font-bold text-gray-900 dark:text-white">TalentMail</h1>
                <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">登录你的邮箱</p>
            </div>

            <!-- 表单区域 -->
            <form @submit.prevent="handleLogin" class="space-y-5">

                <!-- 邮箱 -->
                <div class="space-y-1.5">
                    <input v-model="form.email" type="email" placeholder="邮箱地址" class="input-field" required>
                </div>

                <!-- 密码 -->
                <div class="space-y-1.5 relative">
                    <input v-model="form.password" :type="showPassword ? 'text' : 'password'" placeholder="密码"
                        class="input-field pr-10" required>
                    <!-- 眼睛图标 -->
                    <button type="button" @click="showPassword = !showPassword"
                        class="absolute right-3 top-3.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors">
                        <EyeOff v-if="showPassword" class="w-5 h-5" />
                        <Eye v-else class="w-5 h-5" />
                    </button>
                </div>

                <!-- 登录按钮 -->
                <button type="submit"
                    class="w-full bg-primary hover:bg-primary-hover text-white font-bold py-3 rounded-xl shadow-lg shadow-primary/25 transition-all active:scale-[0.98] mt-2">
                    登录
                </button>

            </form>

            <!-- 底部链接 -->
            <div class="mt-8 flex items-center justify-between">
                <!-- 暗黑模式开关 -->
                <button @click="toggleTheme"
                    class="p-2 text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800">
                    <Sun v-if="isDark" class="w-5 h-5" />
                    <Moon v-else class="w-5 h-5" />
                </button>

                <div class="text-sm text-gray-500">
                    没有账号？
                    <NuxtLink to="/register" class="text-primary hover:text-primary-hover font-bold hover:underline">
                        注册
                    </NuxtLink>
                </div>
            </div>

        </div>
    </div>
</template>

<style scoped>
/* 输入框通用样式 */
.input-field {
    @apply w-full px-4 py-3 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all text-gray-900 dark:text-white placeholder-gray-400;
}
</style>