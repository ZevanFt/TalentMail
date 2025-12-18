<script setup lang="ts">
import { Mail } from 'lucide-vue-next'

definePageMeta({ layout: false })

const { login } = useApi()
const router = useRouter()
const config = useConfig()

const form = reactive({
    displayName: '',
    emailPrefix: '',
    password: '',
    inviteCode: ''
})

const loading = ref(false)
const error = ref('')

const handleRegister = async () => {
    error.value = ''
    loading.value = true
    
    try {
        const email = `${form.emailPrefix}@${config.baseDomain}`
        
        await $fetch('/api/auth/register', {
            method: 'POST',
            body: {
                email,
                password: form.password,
                display_name: form.displayName || form.emailPrefix,
                invite_code: form.inviteCode
            }
        })
        
        await login(email, form.password)
        router.push('/')
    } catch (e: any) {
        error.value = e.data?.detail || '注册失败，请重试'
    } finally {
        loading.value = false
    }
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
                <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">开始使用 {{ config.appName }}</p>
            </div>

            <!-- 错误提示 -->
            <div v-if="error" class="mb-4 p-3 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm rounded-lg">
                {{ error }}
            </div>

            <form @submit.prevent="handleRegister" class="space-y-5">

                <!-- 邀请码 -->
                <input v-model="form.inviteCode" type="text" placeholder="邀请码" class="input-field" required>

                <!-- 用户名 -->
                <input v-model="form.displayName" type="text" placeholder="显示名称（可选）" class="input-field">

                <!-- 邮箱 (组合输入框) -->
                <div class="space-y-2">
                    <label class="text-sm font-medium text-gray-700 dark:text-gray-300">邮箱地址</label>
                    <div class="flex">
                        <input v-model="form.emailPrefix" type="text" placeholder="输入邮箱前缀"
                            class="flex-1 min-w-0 px-4 py-3 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 border-r-0 rounded-l-xl text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all text-gray-900 dark:text-white placeholder-gray-400" required>
                        <div
                            class="px-3 py-3 bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-r-xl text-gray-500 text-xs sm:text-sm flex items-center font-medium shrink-0">
                            {{ config.emailDomain }}
                        </div>
                    </div>
                    <p class="text-xs text-gray-400">您的完整邮箱地址: {{ form.emailPrefix || 'example' }}{{ config.emailDomain }}</p>
                </div>

                <!-- 密码 -->
                <input v-model="form.password" type="password" placeholder="密码" class="input-field" required minlength="6">

                <!-- 注册按钮 -->
                <button type="submit" :disabled="loading"
                    class="w-full bg-gradient-to-r from-primary to-purple-600 hover:from-primary-hover hover:to-purple-700 text-white font-bold py-3 rounded-xl shadow-lg shadow-primary/25 transition-all active:scale-[0.98] mt-2 disabled:opacity-50">
                    {{ loading ? '注册中...' : '注册' }}
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