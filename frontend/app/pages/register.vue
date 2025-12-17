<script setup lang="ts">
import { Mail } from 'lucide-vue-next'

// 禁用默认布局
definePageMeta({
    layout: false
})

const form = reactive({
    username: '',
    emailPrefix: '',
    password: ''
})

const handleRegister = () => {
    console.log('Register:', form.emailPrefix + '@talenting.vip')
    // 注册成功跳转
    useRouter().push('/')
}
</script>

<template>
    <div
        class="min-h-screen w-full flex items-center justify-center bg-gray-50 dark:bg-bg-dark transition-colors duration-300 p-4">

        <div
            class="w-full max-w-[400px] bg-white dark:bg-bg-panelDark rounded-2xl shadow-xl p-8 md:p-10 transition-colors duration-300">

            <!-- 顶部 Logo -->
            <div class="flex flex-col items-center mb-8">
                <div
                    class="w-12 h-12 bg-gradient-to-tr from-primary to-purple-400 rounded-xl flex items-center justify-center text-white shadow-lg shadow-primary/30 mb-4">
                    <Mail class="w-6 h-6" />
                </div>
                <h1 class="text-2xl font-bold text-gray-900 dark:text-white">创建账号</h1>
                <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">开始使用 TalentMail</p>
            </div>

            <form @submit.prevent="handleRegister" class="space-y-5">

                <!-- 用户名 -->
                <input v-model="form.username" type="text" placeholder="用户名" class="input-field" required>

                <!-- 邮箱 (组合输入框) -->
                <div class="flex">
                    <input v-model="form.emailPrefix" type="text" placeholder="邮箱"
                        class="input-field rounded-r-none border-r-0 z-10" required>
                    <div
                        class="px-4 py-3 bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-r-xl text-gray-500 text-sm flex items-center font-medium whitespace-nowrap">
                        @talenting.vip
                    </div>
                </div>

                <!-- 密码 -->
                <input v-model="form.password" type="password" placeholder="密码" class="input-field" required>

                <!-- 注册按钮 -->
                <button type="submit"
                    class="w-full bg-gradient-to-r from-primary to-purple-600 hover:from-primary-hover hover:to-purple-700 text-white font-bold py-3 rounded-xl shadow-lg shadow-primary/25 transition-all active:scale-[0.98] mt-2">
                    注册
                </button>

            </form>

            <!-- 底部链接 -->
            <div class="mt-8 text-center text-sm text-gray-500">
                已有账号？
                <NuxtLink to="/login" class="text-primary hover:text-primary-hover font-bold hover:underline">
                    登录
                </NuxtLink>
            </div>

        </div>
    </div>
</template>

<style scoped>
.input-field {
    @apply w-full px-4 py-3 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all text-gray-900 dark:text-white placeholder-gray-400;
}
</style>