<script setup lang="ts">
import { Mail, ArrowLeft, Loader2, Eye, EyeOff, Moon, Sun, CheckCircle } from 'lucide-vue-next'
const { isDark, toggleTheme } = useTheme()
const { forgotPassword, resetPassword } = useApi()
const { appName, emailDomain } = useConfig()
const router = useRouter()

definePageMeta({
    layout: false
})

// 步骤：1=输入邮箱, 2=输入验证码和新密码, 3=完成
const step = ref(1)
const loading = ref(false)
const error = ref('')
const success = ref('')

const showPassword = ref(false)
const showConfirmPassword = ref(false)

const form = reactive({
    username: '',  // 只输入用户名部分
    code: '',
    newPassword: '',
    confirmPassword: ''
})

// 完整邮箱地址
const fullEmail = computed(() => `${form.username}${emailDomain}`)

// 倒计时
const countdown = ref(0)
let countdownTimer: ReturnType<typeof setInterval> | null = null

const startCountdown = () => {
    countdown.value = 60
    countdownTimer = setInterval(() => {
        countdown.value--
        if (countdown.value <= 0) {
            clearInterval(countdownTimer!)
            countdownTimer = null
        }
    }, 1000)
}

// 发送验证码
const handleSendCode = async () => {
    if (loading.value || !form.username || countdown.value > 0) return
    loading.value = true
    error.value = ''
    
    try {
        await forgotPassword(fullEmail.value)
        success.value = '验证码已发送到您的邮箱'
        step.value = 2
        startCountdown()
    } catch (e: any) {
        error.value = e.data?.detail || '发送验证码失败'
    } finally {
        loading.value = false
    }
}

// 重新发送验证码
const handleResendCode = async () => {
    if (loading.value || countdown.value > 0) return
    loading.value = true
    error.value = ''
    success.value = ''
    
    try {
        await forgotPassword(fullEmail.value)
        success.value = '验证码已重新发送'
        startCountdown()
    } catch (e: any) {
        error.value = e.data?.detail || '发送验证码失败'
    } finally {
        loading.value = false
    }
}

// 重置密码
const handleResetPassword = async () => {
    if (loading.value) return
    
    // 验证
    if (!form.code) {
        error.value = '请输入验证码'
        return
    }
    if (form.code.length !== 6) {
        error.value = '验证码为6位数字'
        return
    }
    if (!form.newPassword) {
        error.value = '请输入新密码'
        return
    }
    if (form.newPassword.length < 6) {
        error.value = '密码长度至少为6位'
        return
    }
    if (form.newPassword !== form.confirmPassword) {
        error.value = '两次输入的密码不一致'
        return
    }
    
    loading.value = true
    error.value = ''
    
    try {
        await resetPassword(fullEmail.value, form.code, form.newPassword)
        step.value = 3
    } catch (e: any) {
        error.value = e.data?.detail || '重置密码失败'
    } finally {
        loading.value = false
    }
}

// 返回上一步
const goBack = () => {
    if (step.value === 2) {
        step.value = 1
        form.code = ''
        form.newPassword = ''
        form.confirmPassword = ''
        error.value = ''
        success.value = ''
    }
}

onUnmounted(() => {
    if (countdownTimer) {
        clearInterval(countdownTimer)
    }
})
</script>

<template>
    <div
        class="min-h-screen w-full flex items-center justify-center bg-gray-50 dark:bg-bg-dark transition-colors duration-300 p-4">

        <!-- 卡片 -->
        <div
            class="w-full max-w-[400px] bg-white dark:bg-bg-panelDark rounded-2xl shadow-xl p-8 md:p-10 transition-colors duration-300 relative overflow-hidden">

            <!-- 顶部 Logo -->
            <div class="flex flex-col items-center mb-8">
                <div
                    class="w-12 h-12 bg-gradient-to-tr from-primary to-purple-400 rounded-xl flex items-center justify-center text-white shadow-lg shadow-primary/30 mb-4">
                    <Mail class="w-6 h-6" />
                </div>
                <h1 class="text-2xl font-bold text-gray-900 dark:text-white">{{ appName }}</h1>
                <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
                    {{ step === 3 ? '密码重置成功' : '重置密码' }}
                </p>
            </div>

            <!-- 步骤 1: 输入邮箱 -->
            <form v-if="step === 1" @submit.prevent="handleSendCode" class="space-y-5">
                <div class="space-y-1.5">
                    <label class="text-sm font-medium text-gray-700 dark:text-gray-300">TalentMail 邮箱</label>
                    <div class="flex items-stretch rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden focus-within:border-primary focus-within:ring-2 focus-within:ring-primary/20 transition-all">
                        <input v-model="form.username" type="text" placeholder="用户名"
                            class="flex-[6] min-w-0 px-4 py-3 bg-gray-50 dark:bg-gray-900 text-sm outline-none text-gray-900 dark:text-white placeholder-gray-400 border-none" required>
                        <span class="flex-[4] px-2 py-3 bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400 flex items-center justify-center border-l border-gray-200 dark:border-gray-700 domain-suffix">
                            {{ emailDomain }}
                        </span>
                    </div>
                    <p class="text-xs text-gray-500 dark:text-gray-400">验证码将发送到此邮箱</p>
                </div>

                <!-- 错误提示 -->
                <div v-if="error" class="text-red-500 text-sm text-center">{{ error }}</div>

                <!-- 发送验证码按钮 -->
                <button type="submit" :disabled="loading || !form.username"
                    class="w-full bg-primary hover:bg-primary-hover disabled:opacity-50 text-white font-bold py-3 rounded-xl shadow-lg shadow-primary/25 transition-all active:scale-[0.98] flex items-center justify-center gap-2">
                    <Loader2 v-if="loading" class="w-5 h-5 animate-spin" />
                    {{ loading ? '发送中...' : '发送验证码' }}
                </button>
            </form>

            <!-- 步骤 2: 输入验证码和新密码 -->
            <form v-else-if="step === 2" @submit.prevent="handleResetPassword" class="space-y-5">
                <!-- 返回按钮 -->
                <button type="button" @click="goBack"
                    class="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition-colors">
                    <ArrowLeft class="w-4 h-4" />
                    返回
                </button>

                <!-- 显示邮箱 -->
                <div class="text-center text-sm text-gray-600 dark:text-gray-400">
                    验证码已发送至 <span class="font-medium text-gray-900 dark:text-white">{{ fullEmail }}</span>
                </div>

                <!-- 验证码 -->
                <div class="space-y-1.5">
                    <label class="text-sm font-medium text-gray-700 dark:text-gray-300">验证码</label>
                    <div class="flex gap-2">
                        <input v-model="form.code" type="text" maxlength="6" placeholder="6位验证码"
                            class="input-field flex-1 text-center tracking-widest" required>
                        <button type="button" @click="handleResendCode" :disabled="countdown > 0 || loading"
                            class="px-4 py-3 text-sm font-medium text-primary hover:text-primary-hover disabled:text-gray-400 disabled:cursor-not-allowed transition-colors whitespace-nowrap">
                            {{ countdown > 0 ? `${countdown}s` : '重新发送' }}
                        </button>
                    </div>
                </div>

                <!-- 新密码 -->
                <div class="space-y-1.5 relative">
                    <label class="text-sm font-medium text-gray-700 dark:text-gray-300">新密码</label>
                    <input v-model="form.newPassword" :type="showPassword ? 'text' : 'password'" placeholder="至少6位"
                        class="input-field pr-10" required>
                    <button type="button" @click="showPassword = !showPassword"
                        class="absolute right-3 top-9 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors">
                        <EyeOff v-if="showPassword" class="w-5 h-5" />
                        <Eye v-else class="w-5 h-5" />
                    </button>
                </div>

                <!-- 确认密码 -->
                <div class="space-y-1.5 relative">
                    <label class="text-sm font-medium text-gray-700 dark:text-gray-300">确认密码</label>
                    <input v-model="form.confirmPassword" :type="showConfirmPassword ? 'text' : 'password'" placeholder="再次输入新密码"
                        class="input-field pr-10" required>
                    <button type="button" @click="showConfirmPassword = !showConfirmPassword"
                        class="absolute right-3 top-9 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors">
                        <EyeOff v-if="showConfirmPassword" class="w-5 h-5" />
                        <Eye v-else class="w-5 h-5" />
                    </button>
                </div>

                <!-- 成功提示 -->
                <div v-if="success" class="text-green-500 text-sm text-center">{{ success }}</div>

                <!-- 错误提示 -->
                <div v-if="error" class="text-red-500 text-sm text-center">{{ error }}</div>

                <!-- 重置密码按钮 -->
                <button type="submit" :disabled="loading"
                    class="w-full bg-primary hover:bg-primary-hover disabled:opacity-50 text-white font-bold py-3 rounded-xl shadow-lg shadow-primary/25 transition-all active:scale-[0.98] flex items-center justify-center gap-2">
                    <Loader2 v-if="loading" class="w-5 h-5 animate-spin" />
                    {{ loading ? '重置中...' : '重置密码' }}
                </button>
            </form>

            <!-- 步骤 3: 完成 -->
            <div v-else class="space-y-6 text-center">
                <div class="flex justify-center">
                    <div class="w-16 h-16 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center">
                        <CheckCircle class="w-8 h-8 text-green-500" />
                    </div>
                </div>
                <div>
                    <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">密码重置成功</h3>
                    <p class="text-sm text-gray-500 dark:text-gray-400">您现在可以使用新密码登录了</p>
                </div>
                <NuxtLink to="/login"
                    class="block w-full bg-primary hover:bg-primary-hover text-white font-bold py-3 rounded-xl shadow-lg shadow-primary/25 transition-all active:scale-[0.98] text-center">
                    返回登录
                </NuxtLink>
            </div>

            <!-- 底部链接 -->
            <div class="mt-8 flex items-center justify-between">
                <!-- 暗黑模式开关 -->
                <button @click="toggleTheme"
                    class="p-2 text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800">
                    <Sun v-if="isDark" class="w-5 h-5" />
                    <Moon v-else class="w-5 h-5" />
                </button>

                <div class="text-sm text-gray-500">
                    想起密码了？
                    <NuxtLink to="/login" class="text-primary hover:text-primary-hover font-bold hover:underline">
                        返回登录
                    </NuxtLink>
                </div>
            </div>

        </div>
    </div>
</template>

<style scoped>
.input-field {
    @apply w-full px-4 py-3 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all text-gray-900 dark:text-white placeholder-gray-400;
}
.domain-suffix {
    font-size: clamp(0.65rem, 2.5cqw, 0.875rem);
    container-type: inline-size;
}
</style>