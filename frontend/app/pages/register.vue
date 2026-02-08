<script setup lang="ts">
import { Mail, ArrowLeft, ArrowRight, Check, Loader2 } from 'lucide-vue-next'

definePageMeta({ layout: false })

const { login, sendVerificationCode, verifyCode, registerWithVerification } = useApi()
const router = useRouter()
const config = useConfig()

// 步骤：1=邮箱验证, 2=填写信息
const step = ref(1)

const form = reactive({
    // 步骤1：邮箱验证
    verificationEmail: '',
    verificationCode: '',
    // 步骤2：注册信息
    displayName: '',
    emailPrefix: '',
    password: '',
    inviteCode: ''
})

const loading = ref(false)
const sendingCode = ref(false)
const verifyingCode = ref(false)
const error = ref('')
const success = ref('')
const countdown = ref(0)
const codeVerified = ref(false)

// 倒计时
let countdownTimer: ReturnType<typeof setInterval> | null = null

const startCountdown = () => {
    countdown.value = 60
    countdownTimer = setInterval(() => {
        countdown.value--
        if (countdown.value <= 0) {
            if (countdownTimer) clearInterval(countdownTimer)
        }
    }, 1000)
}

// 发送验证码
const handleSendCode = async () => {
    if (!form.verificationEmail) {
        error.value = '请输入邮箱地址'
        return
    }
    
    error.value = ''
    success.value = ''
    sendingCode.value = true
    
    try {
        await sendVerificationCode(form.verificationEmail, 'register')
        success.value = '验证码已发送到您的邮箱'
        startCountdown()
    } catch (e: any) {
        error.value = e.data?.detail || '发送验证码失败，请重试'
    } finally {
        sendingCode.value = false
    }
}

// 验证验证码
const handleVerifyCode = async () => {
    if (!form.verificationCode) {
        error.value = '请输入验证码'
        return
    }
    
    error.value = ''
    verifyingCode.value = true
    
    try {
        await verifyCode(form.verificationEmail, form.verificationCode, 'register')
        codeVerified.value = true
        success.value = '验证成功！'
        // 自动进入下一步
        setTimeout(() => {
            step.value = 2
            success.value = ''
        }, 1000)
    } catch (e: any) {
        error.value = e.data?.detail || '验证码错误'
    } finally {
        verifyingCode.value = false
    }
}

// 注册
const handleRegister = async () => {
    error.value = ''
    loading.value = true
    
    try {
        const email = `${form.emailPrefix}@${config.baseDomain}`
        
        await registerWithVerification({
            email,
            password: form.password,
            invite_code: form.inviteCode,
            verification_email: form.verificationEmail,
            verification_code: form.verificationCode
        })
        
        await login(email, form.password)
        router.push('/')
    } catch (e: any) {
        error.value = e.data?.detail || '注册失败，请重试'
    } finally {
        loading.value = false
    }
}

// 返回上一步
const goBack = () => {
    step.value = 1
    error.value = ''
    success.value = ''
}

onUnmounted(() => {
    if (countdownTimer) clearInterval(countdownTimer)
})
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

            <!-- 步骤指示器 -->
            <div class="flex items-center justify-center mb-6">
                <div class="flex items-center">
                    <div :class="[
                        'w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-colors',
                        step >= 1 ? 'bg-primary text-white' : 'bg-gray-200 dark:bg-gray-700 text-gray-500'
                    ]">
                        <Check v-if="codeVerified" class="w-4 h-4" />
                        <span v-else>1</span>
                    </div>
                    <div :class="[
                        'w-12 h-1 mx-2 transition-colors',
                        step >= 2 ? 'bg-primary' : 'bg-gray-200 dark:bg-gray-700'
                    ]"></div>
                    <div :class="[
                        'w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-colors',
                        step >= 2 ? 'bg-primary text-white' : 'bg-gray-200 dark:bg-gray-700 text-gray-500'
                    ]">
                        2
                    </div>
                </div>
            </div>

            <!-- 错误提示 -->
            <div v-if="error" class="mb-4 p-3 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm rounded-lg">
                {{ error }}
            </div>

            <!-- 成功提示 -->
            <div v-if="success" class="mb-4 p-3 bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400 text-sm rounded-lg">
                {{ success }}
            </div>

            <!-- 步骤1：邮箱验证 -->
            <div v-if="step === 1" class="space-y-5">
                <div class="text-center mb-4">
                    <p class="text-sm text-gray-600 dark:text-gray-400">
                        请先验证您的外部邮箱地址
                    </p>
                </div>

                <!-- 外部邮箱 -->
                <div class="space-y-2">
                    <label class="text-sm font-medium text-gray-700 dark:text-gray-300">验证邮箱</label>
                    <input 
                        v-model="form.verificationEmail" 
                        type="email" 
                        placeholder="请输入您的邮箱地址" 
                        class="input-field"
                        :disabled="codeVerified"
                        required
                    >
                    <p class="text-xs text-gray-400">我们将发送验证码到此邮箱</p>
                </div>

                <!-- 验证码输入 -->
                <div class="space-y-2">
                    <label class="text-sm font-medium text-gray-700 dark:text-gray-300">验证码</label>
                    <div class="flex gap-2">
                        <input 
                            v-model="form.verificationCode" 
                            type="text" 
                            placeholder="6位验证码" 
                            class="input-field flex-1"
                            maxlength="6"
                            :disabled="codeVerified"
                        >
                        <button 
                            type="button"
                            @click="handleSendCode"
                            :disabled="sendingCode || countdown > 0 || codeVerified"
                            class="px-4 py-3 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 text-sm font-medium rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
                        >
                            <Loader2 v-if="sendingCode" class="w-4 h-4 animate-spin" />
                            <span v-else-if="countdown > 0">{{ countdown }}s</span>
                            <span v-else>发送验证码</span>
                        </button>
                    </div>
                </div>

                <!-- 验证按钮 -->
                <button 
                    v-if="!codeVerified"
                    type="button"
                    @click="handleVerifyCode"
                    :disabled="verifyingCode || !form.verificationCode"
                    class="w-full bg-gradient-to-r from-primary to-purple-600 hover:from-primary-hover hover:to-purple-700 text-white font-bold py-3 rounded-xl shadow-lg shadow-primary/25 transition-all active:scale-[0.98] disabled:opacity-50 flex items-center justify-center gap-2"
                >
                    <Loader2 v-if="verifyingCode" class="w-4 h-4 animate-spin" />
                    <span>{{ verifyingCode ? '验证中...' : '验证' }}</span>
                </button>

                <!-- 已验证，进入下一步 -->
                <button 
                    v-else
                    type="button"
                    @click="step = 2"
                    class="w-full bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white font-bold py-3 rounded-xl shadow-lg shadow-green-500/25 transition-all active:scale-[0.98] flex items-center justify-center gap-2"
                >
                    <Check class="w-4 h-4" />
                    <span>验证成功，下一步</span>
                    <ArrowRight class="w-4 h-4" />
                </button>
            </div>

            <!-- 步骤2：填写注册信息 -->
            <form v-else @submit.prevent="handleRegister" class="space-y-5">
                <!-- 返回按钮 -->
                <button 
                    type="button"
                    @click="goBack"
                    class="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
                >
                    <ArrowLeft class="w-4 h-4" />
                    <span>返回上一步</span>
                </button>

                <!-- 已验证的邮箱 -->
                <div class="p-3 bg-green-50 dark:bg-green-900/20 rounded-lg flex items-center gap-2">
                    <Check class="w-4 h-4 text-green-600 dark:text-green-400" />
                    <span class="text-sm text-green-600 dark:text-green-400">已验证: {{ form.verificationEmail }}</span>
                </div>

                <!-- 邀请码 -->
                <input v-model="form.inviteCode" type="text" placeholder="邀请码" class="input-field" required>

                <!-- 用户名 -->
                <input v-model="form.displayName" type="text" placeholder="显示名称（可选）" class="input-field">

                <!-- 邮箱 (组合输入框) -->
                <div class="space-y-2">
                    <label class="text-sm font-medium text-gray-700 dark:text-gray-300">TalentMail 邮箱地址</label>
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
                    class="w-full bg-gradient-to-r from-primary to-purple-600 hover:from-primary-hover hover:to-purple-700 text-white font-bold py-3 rounded-xl shadow-lg shadow-primary/25 transition-all active:scale-[0.98] mt-2 disabled:opacity-50 flex items-center justify-center gap-2">
                    <Loader2 v-if="loading" class="w-4 h-4 animate-spin" />
                    <span>{{ loading ? '注册中...' : '完成注册' }}</span>
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

/* 覆盖浏览器自动填充样式 - 浅色模式 */
input:-webkit-autofill,
input:-webkit-autofill:hover,
input:-webkit-autofill:focus,
input:-webkit-autofill:active {
    -webkit-box-shadow: 0 0 0 1000px rgb(255, 255, 255) inset !important;
    -webkit-text-fill-color: rgb(17, 24, 39) !important;
    caret-color: rgb(17, 24, 39) !important;
    transition: background-color 5000s ease-in-out 0s !important;
}

/* 覆盖浏览器自动填充样式 - 暗色模式 */
:global(html.dark) input:-webkit-autofill,
:global(html.dark) input:-webkit-autofill:hover,
:global(html.dark) input:-webkit-autofill:focus,
:global(html.dark) input:-webkit-autofill:active {
    -webkit-box-shadow: 0 0 0 1000px rgb(17, 24, 39) inset !important;
    -webkit-text-fill-color: rgb(255, 255, 255) !important;
    caret-color: rgb(255, 255, 255) !important;
    transition: background-color 5000s ease-in-out 0s !important;
}
</style>