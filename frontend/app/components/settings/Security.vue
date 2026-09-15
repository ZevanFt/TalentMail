<script setup lang="ts">
import { KeyRound, Smartphone, ShieldCheck, History, Laptop, Globe, X, Monitor, Trash2, LogOut, Mail, Edit3, QrCode, Shield, ShieldOff } from 'lucide-vue-next'

const { changePassword, getLoginSessions, revokeSession, revokeAllSessions, getMe, sendRecoveryEmailCode, updateRecoveryEmail, get2FAStatus, setup2FA, enable2FA, disable2FA, listAppPasswords, createAppPassword, revokeAppPassword } = useApi()
const toast = useToast()
const { confirm: confirmDialog } = useConfirmDialog()
const { t } = useI18n()

// 用户信息
const user = ref<AppUser | null>(null)
const loadingUser = ref(true)

const loadUser = async () => {
    loadingUser.value = true
    try {
        user.value = await getMe()
    } catch (e: any) {
        console.error('加载用户信息失败', e)
        toast.error(e.data?.detail || t('settingsSecurity.common.loadUserFailed'))
    } finally {
        loadingUser.value = false
    }
}

const showPasswordModal = ref(false)
const saving = ref(false)
const message = ref('')
const messageType = ref<'success' | 'error'>('success')

// 登录会话
interface LoginSession {
    id: number
    device_info: string | null
    browser: string | null
    os: string | null
    ip_address: string | null
    location: string | null
    is_active: boolean
    created_at: string | null
    last_active_at: string | null
    is_current: boolean
}

const sessions = ref<LoginSession[]>([])
const loadingSessions = ref(true)
const revokingSession = ref<number | null>(null)

const passwordForm = reactive({
    current: '',
    new: '',
    confirm: ''
})

// 辅助邮箱设置
const showRecoveryEmailModal = ref(false)
const recoveryEmailStep = ref<'input' | 'verify'>('input')
const recoveryEmailForm = reactive({
    email: '',
    code: ''
})
const recoveryEmailSaving = ref(false)
const recoveryEmailMessage = ref('')
const recoveryEmailMessageType = ref<'success' | 'error'>('success')
const sendingRecoveryCode = ref(false)
const recoveryCodeCountdown = ref(0)
let recoveryCountdownTimer: ReturnType<typeof setInterval> | null = null

// 2FA 设置
const show2FAModal = ref(false)
const twoFAStep = ref<'setup' | 'verify' | 'disable'>('setup')
const twoFAStatus = ref({ enabled: false, has_secret: false })
const twoFASetupData = ref<{ secret: string; qr_code: string; provisioning_uri: string } | null>(null)
const twoFACode = ref('')
const twoFAPassword = ref('')
const twoFASaving = ref(false)
const twoFAMessage = ref('')
const twoFAMessageType = ref<'success' | 'error'>('success')
const loading2FA = ref(false)

// 应用专用密码（CalDAV）
interface AppPasswordRow {
    id: number
    name: string
    prefix: string
    last_used_at?: string | null
    created_at?: string | null
}
const appPasswords = ref<AppPasswordRow[]>([])
const loadingAppPasswords = ref(false)
const showAppPasswordModal = ref(false)
const appPasswordName = ref('')
const appPasswordCreating = ref(false)
const newAppPassword = ref('')
const copiedAppPassword = ref(false)

const loadAppPasswords = async () => {
    loadingAppPasswords.value = true
    try {
        appPasswords.value = await listAppPasswords()
    } catch (e: any) {
        console.error(e)
    } finally {
        loadingAppPasswords.value = false
    }
}

const handleCreateAppPassword = async () => {
    if (!appPasswordName.value.trim()) return
    appPasswordCreating.value = true
    try {
        const res = await createAppPassword(appPasswordName.value.trim())
        newAppPassword.value = res.password
        await loadAppPasswords()
    } catch (e: any) {
        toast.error(e?.data?.detail || t('settingsSecurity.appPasswords.createFailed'))
    } finally {
        appPasswordCreating.value = false
    }
}

const closeAppPasswordModal = () => {
    showAppPasswordModal.value = false
    appPasswordName.value = ''
    newAppPassword.value = ''
    copiedAppPassword.value = false
}

const copyAppPassword = async () => {
    try {
        await navigator.clipboard.writeText(newAppPassword.value)
        copiedAppPassword.value = true
        toast.success(t('settingsSecurity.appPasswords.copied'))
    } catch {
        toast.error(t('settingsSecurity.appPasswords.copyFailed'))
    }
}

const handleRevokeAppPassword = async (row: AppPasswordRow) => {
    const ok = await confirmDialog({
        title: t('settingsSecurity.appPasswords.revokeTitle'),
        message: t('settingsSecurity.appPasswords.revokeConfirm', { name: row.name }),
        confirmText: t('common.delete'),
        cancelText: t('common.cancel'),
    })
    if (!ok) return
    try {
        await revokeAppPassword(row.id)
        toast.success(t('settingsSecurity.appPasswords.revoked'))
        await loadAppPasswords()
    } catch (e: any) {
        toast.error(e?.data?.detail || t('settingsSecurity.appPasswords.revokeFailed'))
    }
}

// 加载 2FA 状态
const load2FAStatus = async () => {
    loading2FA.value = true
    try {
        twoFAStatus.value = await get2FAStatus()
    } catch (e: any) {
        console.error('加载 2FA 状态失败', e)
        toast.error(e.data?.detail || t('settingsSecurity.security.load2faFailed'))
    } finally {
        loading2FA.value = false
    }
}

// 加载登录会话
const loadSessions = async () => {
    loadingSessions.value = true
    try {
        sessions.value = await getLoginSessions(10)
    } catch (e: any) {
        console.error('加载登录会话失败', e)
        toast.error(e.data?.detail || t('settingsSecurity.security.loadSessionsFailed'))
    } finally {
        loadingSessions.value = false
    }
}

// 格式化时间
const formatTime = (dateStr: string | null) => {
    if (!dateStr) return t('settingsSecurity.security.unknown')
    const date = new Date(dateStr)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    
    if (diff < 60000) return t('settingsSecurity.common.justNow')
    if (diff < 3600000) return t('settingsSecurity.common.minutesAgo', { n: Math.floor(diff / 60000) })
    if (diff < 86400000) return t('settingsSecurity.common.hoursAgo', { n: Math.floor(diff / 3600000) })
    if (diff < 604800000) return t('settingsSecurity.common.daysAgo', { n: Math.floor(diff / 86400000) })
    
    return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

// 获取设备图标
const getDeviceIcon = (os: string | null) => {
    if (!os) return Monitor
    const osLower = os.toLowerCase()
    if (osLower.includes('windows') || osLower.includes('mac') || osLower.includes('linux')) return Laptop
    if (osLower.includes('android') || osLower.includes('ios') || osLower.includes('iphone')) return Smartphone
    return Monitor
}

// 撤销单个会话
const handleRevokeSession = async (sessionId: number) => {
    const ok = await confirmDialog({ message: t('settingsSecurity.security.revokeSessionConfirm'), type: 'warning' })
    if (!ok) return
    revokingSession.value = sessionId
    try {
        await revokeSession(sessionId)
        sessions.value = sessions.value.filter(s => s.id !== sessionId)
    } catch (e: any) {
        console.error('撤销会话失败', e)
        toast.error(e.data?.detail || t('settingsSecurity.security.revokeSessionFailed'))
    } finally {
        revokingSession.value = null
    }
}

// 撤销所有会话
const handleRevokeAll = async () => {
    const ok = await confirmDialog({ message: t('settingsSecurity.security.revokeAllConfirm'), type: 'danger' })
    if (!ok) return
    try {
        await revokeAllSessions()
        await loadSessions()
    } catch (e: any) {
        console.error('撤销所有会话失败', e)
        toast.error(e.data?.detail || t('settingsSecurity.security.revokeAllFailed'))
    }
}

const openPasswordModal = () => {
    passwordForm.current = ''
    passwordForm.new = ''
    passwordForm.confirm = ''
    message.value = ''
    showPasswordModal.value = true
}

// 辅助邮箱相关函数
const openRecoveryEmailModal = () => {
    recoveryEmailForm.email = ''
    recoveryEmailForm.code = ''
    recoveryEmailStep.value = 'input'
    recoveryEmailMessage.value = ''
    recoveryCodeCountdown.value = 0
    showRecoveryEmailModal.value = true
}

const sendRecoveryCode = async () => {
    if (!recoveryEmailForm.email) {
        recoveryEmailMessage.value = t('settingsSecurity.security.emailRequired')
        recoveryEmailMessageType.value = 'error'
        return
    }
    
    // 简单的邮箱格式验证
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(recoveryEmailForm.email)) {
        recoveryEmailMessage.value = t('settingsSecurity.security.emailInvalid')
        recoveryEmailMessageType.value = 'error'
        return
    }
    
    sendingRecoveryCode.value = true
    recoveryEmailMessage.value = ''
    
    try {
        await sendRecoveryEmailCode(recoveryEmailForm.email)
        recoveryEmailStep.value = 'verify'
        recoveryEmailMessage.value = t('settingsSecurity.security.codeSent')
        recoveryEmailMessageType.value = 'success'
        
        // 开始倒计时
        recoveryCodeCountdown.value = 60
        recoveryCountdownTimer = setInterval(() => {
            recoveryCodeCountdown.value--
            if (recoveryCodeCountdown.value <= 0) {
                if (recoveryCountdownTimer) {
                    clearInterval(recoveryCountdownTimer)
                    recoveryCountdownTimer = null
                }
            }
        }, 1000)
    } catch (e: any) {
        recoveryEmailMessage.value = e.data?.detail || t('settingsSecurity.security.sendCodeFailed')
        recoveryEmailMessageType.value = 'error'
    } finally {
        sendingRecoveryCode.value = false
    }
}

const handleUpdateRecoveryEmail = async () => {
    if (!recoveryEmailForm.code) {
        recoveryEmailMessage.value = t('settingsSecurity.security.codeRequired')
        recoveryEmailMessageType.value = 'error'
        return
    }
    
    if (recoveryEmailForm.code.length !== 6) {
        recoveryEmailMessage.value = t('settingsSecurity.security.codeSixDigits')
        recoveryEmailMessageType.value = 'error'
        return
    }
    
    recoveryEmailSaving.value = true
    recoveryEmailMessage.value = ''
    
    try {
        const result = await updateRecoveryEmail(recoveryEmailForm.email, recoveryEmailForm.code)
        recoveryEmailMessage.value = t('settingsSecurity.security.recoveryEmailSaved')
        recoveryEmailMessageType.value = 'success'
        
        // 更新用户信息
        if (user.value) {
            user.value.recovery_email = result.recovery_email
        }
        
        safeTimeout(() => {
            showRecoveryEmailModal.value = false
        }, 1500)
    } catch (e: any) {
        recoveryEmailMessage.value = e.data?.detail || t('settingsSecurity.security.setRecoveryEmailFailed')
        recoveryEmailMessageType.value = 'error'
    } finally {
        recoveryEmailSaving.value = false
    }
}

// 收集所有 setTimeout 以便统一清理
const pendingTimers: ReturnType<typeof setTimeout>[] = []
const safeTimeout = (fn: () => void, ms: number) => {
    const id = setTimeout(fn, ms)
    pendingTimers.push(id)
    return id
}

// 清理定时器
onUnmounted(() => {
    if (recoveryCountdownTimer) {
        clearInterval(recoveryCountdownTimer)
    }
    pendingTimers.forEach(clearTimeout)
})

// 2FA 相关函数
const open2FASetupModal = async () => {
    twoFACode.value = ''
    twoFAPassword.value = ''
    twoFAMessage.value = ''
    twoFASetupData.value = null
    
    if (twoFAStatus.value.enabled) {
        // 已启用，显示禁用界面
        twoFAStep.value = 'disable'
        show2FAModal.value = true
    } else {
        // 未启用，开始设置流程
        twoFAStep.value = 'setup'
        show2FAModal.value = true
        
        // 获取设置数据
        twoFASaving.value = true
        try {
            twoFASetupData.value = await setup2FA()
        } catch (e: any) {
            twoFAMessage.value = e.data?.detail || t('settingsSecurity.security.setup2faFailed')
            twoFAMessageType.value = 'error'
        } finally {
            twoFASaving.value = false
        }
    }
}

const handleEnable2FA = async () => {
    if (!twoFACode.value || twoFACode.value.length !== 6) {
        twoFAMessage.value = t('settingsSecurity.security.enterSixDigitCode')
        twoFAMessageType.value = 'error'
        return
    }
    
    twoFASaving.value = true
    twoFAMessage.value = ''
    
    try {
        await enable2FA(twoFACode.value)
        twoFAMessage.value = t('settingsSecurity.security.twoFAEnabled')
        twoFAMessageType.value = 'success'
        twoFAStatus.value.enabled = true

        safeTimeout(() => {
            show2FAModal.value = false
        }, 1500)
    } catch (e: any) {
        twoFAMessage.value = e.data?.detail || t('settingsSecurity.security.enable2faFailed')
        twoFAMessageType.value = 'error'
    } finally {
        twoFASaving.value = false
    }
}

const handleDisable2FA = async () => {
    if (!twoFACode.value || twoFACode.value.length !== 6) {
        twoFAMessage.value = t('settingsSecurity.security.enterSixDigitCode')
        twoFAMessageType.value = 'error'
        return
    }
    
    if (!twoFAPassword.value) {
        twoFAMessage.value = t('settingsSecurity.security.passwordRequired')
        twoFAMessageType.value = 'error'
        return
    }
    
    twoFASaving.value = true
    twoFAMessage.value = ''
    
    try {
        await disable2FA(twoFACode.value, twoFAPassword.value)
        twoFAMessage.value = t('settingsSecurity.security.twoFADisabled')
        twoFAMessageType.value = 'success'
        twoFAStatus.value.enabled = false

        safeTimeout(() => {
            show2FAModal.value = false
        }, 1500)
    } catch (e: any) {
        twoFAMessage.value = e.data?.detail || t('settingsSecurity.security.disable2faFailed')
        twoFAMessageType.value = 'error'
    } finally {
        twoFASaving.value = false
    }
}

const handleChangePassword = async () => {
    message.value = ''
    
    if (passwordForm.new !== passwordForm.confirm) {
        message.value = t('settingsSecurity.security.passwordMismatch')
        messageType.value = 'error'
        return
    }
    
    if (passwordForm.new.length < 6) {
        message.value = t('settingsSecurity.security.passwordTooShort')
        messageType.value = 'error'
        return
    }
    
    saving.value = true
    try {
        await changePassword(passwordForm.current, passwordForm.new)
        message.value = t('settingsSecurity.security.passwordChanged')
        messageType.value = 'success'
        safeTimeout(() => {
            showPasswordModal.value = false
        }, 1500)
    } catch (e: any) {
        message.value = e.data?.detail || t('settingsSecurity.security.passwordChangeFailed')
        messageType.value = 'error'
    } finally {
        saving.value = false
    }
}

onMounted(() => {
    loadSessions()
    loadUser()
    load2FAStatus()
    loadAppPasswords()
})
</script>

<template>
    <div class="space-y-8">
        <h2 class="section-title">{{ t('settingsSecurity.security.title') }}</h2>

        <!-- 1. 核心认证设置 -->
        <div class="card bg-white dark:bg-bg-panelDark divide-y divide-gray-100 dark:divide-gray-800">

            <!-- 修改密码 -->
            <div class="p-6 flex items-center justify-between">
                <div class="flex items-center gap-4">
                    <div class="icon-box bg-purple-100 text-purple-600 dark:bg-purple-900/30">
                        <KeyRound class="w-5 h-5" />
                    </div>
                    <div>
                        <div class="font-bold text-gray-900 dark:text-white">{{ t('settingsSecurity.security.loginPassword') }}</div>
                        <div class="text-sm text-gray-500 mt-0.5">{{ t('settingsSecurity.security.loginPasswordDesc') }}</div>
                    </div>
                </div>
                <button @click="openPasswordModal" class="btn-secondary">{{ t('settingsSecurity.security.changePassword') }}</button>
            </div>

            <!-- 两步验证 -->
            <div class="p-6 flex items-center justify-between">
                <div class="flex items-center gap-4">
                    <div :class="['icon-box', twoFAStatus.enabled ? 'bg-green-100 text-green-600 dark:bg-green-900/30' : 'bg-gray-100 text-gray-600 dark:bg-gray-800']">
                        <Smartphone class="w-5 h-5" />
                    </div>
                    <div>
                        <div class="font-bold text-gray-900 dark:text-white">{{ t('settingsSecurity.security.twoFA') }}</div>
                        <div class="text-sm text-gray-500 mt-0.5">{{ t('settingsSecurity.security.twoFADesc') }}</div>
                    </div>
                </div>
                <div class="flex items-center gap-3">
                    <div v-if="loading2FA" class="text-sm text-gray-400">{{ t('common.loading') }}</div>
                    <template v-else>
                        <span v-if="twoFAStatus.enabled" class="px-2 py-0.5 bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 text-xs rounded-full">{{ t('settingsSecurity.security.enabled') }}</span>
                        <span v-else class="px-2 py-0.5 bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400 text-xs rounded-full">{{ t('settingsSecurity.security.notEnabled') }}</span>
                        <button @click="open2FASetupModal" :class="twoFAStatus.enabled ? 'btn-secondary' : 'btn-primary'">
                            {{ twoFAStatus.enabled ? t('settingsSecurity.security.manage') : t('settingsSecurity.security.enableNow') }}
                        </button>
                    </template>
                </div>
            </div>

            <!-- 应用专用密码（CalDAV） -->
            <div class="p-6 space-y-4">
                <div class="flex items-center justify-between">
                    <div class="flex items-center gap-4">
                        <div class="icon-box bg-amber-100 text-amber-600 dark:bg-amber-900/30">
                            <KeyRound class="w-5 h-5" />
                        </div>
                        <div>
                            <div class="font-bold text-gray-900 dark:text-white">{{ t('settingsSecurity.appPasswords.title') }}</div>
                            <div class="text-sm text-gray-500 mt-0.5">{{ t('settingsSecurity.appPasswords.desc') }}</div>
                        </div>
                    </div>
                    <button class="btn-primary" @click="showAppPasswordModal = true">
                        {{ t('settingsSecurity.appPasswords.create') }}
                    </button>
                </div>
                <div v-if="loadingAppPasswords" class="text-sm text-gray-400">{{ t('common.loading') }}</div>
                <div v-else-if="appPasswords.length === 0" class="text-sm text-gray-400">
                    {{ t('settingsSecurity.appPasswords.empty') }}
                </div>
                <div v-else class="divide-y divide-gray-100 dark:divide-gray-700/60">
                    <div v-for="row in appPasswords" :key="row.id"
                        class="flex items-center justify-between gap-3 py-2.5 text-sm">
                        <div class="min-w-0">
                            <div class="font-medium text-gray-900 dark:text-white truncate">{{ row.name }}</div>
                            <div class="text-xs text-gray-400 font-mono">
                                {{ row.prefix }}••••
                                <span v-if="row.last_used_at"> · {{ t('settingsSecurity.appPasswords.lastUsed') }} {{ new Date(row.last_used_at).toLocaleString() }}</span>
                            </div>
                        </div>
                        <button class="btn-secondary text-xs shrink-0" @click="handleRevokeAppPassword(row)">
                            {{ t('settingsSecurity.appPasswords.revoke') }}
                        </button>
                    </div>
                </div>
            </div>

            <!-- 备用邮箱 -->
            <div class="p-6 flex items-center justify-between">
                <div class="flex items-center gap-4">
                    <div class="icon-box bg-blue-100 text-blue-600 dark:bg-blue-900/30">
                        <Mail class="w-5 h-5" />
                    </div>
                    <div>
                        <div class="font-bold text-gray-900 dark:text-white">{{ t('settingsSecurity.security.recoveryEmail') }}</div>
                        <div class="text-sm text-gray-500 mt-0.5">{{ t('settingsSecurity.security.recoveryEmailDesc') }}</div>
                    </div>
                </div>
                <div class="flex items-center gap-3">
                    <div v-if="loadingUser" class="text-sm text-gray-400">{{ t('common.loading') }}</div>
                    <template v-else>
                        <div v-if="user?.recovery_email" class="flex items-center gap-2">
                            <span class="text-sm text-gray-700 dark:text-gray-300 font-medium">{{ user.recovery_email }}</span>
                            <span class="px-2 py-0.5 bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 text-xs rounded-full">{{ t('settingsSecurity.security.bound') }}</span>
                        </div>
                        <div v-else class="text-sm text-gray-400">{{ t('settingsSecurity.security.notSet') }}</div>
                        <button @click="openRecoveryEmailModal" class="btn-secondary flex items-center gap-1.5">
                            <Edit3 class="w-4 h-4" />
                            {{ user?.recovery_email ? t('settingsSecurity.security.change') : t('settingsSecurity.security.setup') }}
                        </button>
                    </template>
                </div>
            </div>
        </div>

        <!-- 2. 已登录设备 -->
        <div class="space-y-4">
            <div class="flex items-center justify-between">
                <h3 class="font-bold text-gray-900 dark:text-white flex items-center gap-2">
                    <Monitor class="w-5 h-5 text-gray-500" />
                    {{ t('settingsSecurity.security.loggedInDevices') }}
                </h3>
                <button v-if="sessions.length > 1" @click="handleRevokeAll" class="text-sm text-red-500 hover:text-red-600 flex items-center gap-1">
                    <LogOut class="w-4 h-4" />
                    {{ t('settingsSecurity.security.logoutAllDevices') }}
                </button>
            </div>

            <div class="card bg-white dark:bg-bg-panelDark p-0 overflow-hidden">
                <!-- 加载中 -->
                <div v-if="loadingSessions" class="p-8 text-center text-gray-500">
                    {{ t('common.loading') }}
                </div>
                
                <!-- 无数据 -->
                <div v-else-if="sessions.length === 0" class="p-8 text-center text-gray-500">
                    {{ t('settingsSecurity.security.noSessions') }}
                </div>
                
                <!-- 会话列表 -->
                <template v-else>
                    <div v-for="(session, index) in sessions" :key="session.id"
                        class="p-4 flex items-center justify-between border-b border-gray-100 dark:border-gray-800 last:border-b-0"
                        :class="session.is_current ? 'bg-green-50/50 dark:bg-green-900/10' : ''">
                        <div class="flex items-center gap-4">
                            <component :is="getDeviceIcon(session.os)"
                                class="w-8 h-8"
                                :class="session.is_current ? 'text-green-600 dark:text-green-400' : 'text-gray-400'" />
                            <div>
                                <div class="font-bold text-gray-900 dark:text-white flex items-center gap-2">
                                    {{ session.browser || session.device_info || t('settingsSecurity.security.unknownDevice') }}
                                    <span v-if="session.is_current" class="px-2 py-0.5 bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 text-[10px] rounded-full">{{ t('settingsSecurity.security.currentDevice') }}</span>
                                    <span v-if="!session.is_active" class="px-2 py-0.5 bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400 text-[10px] rounded-full">{{ t('settingsSecurity.security.inactive') }}</span>
                                </div>
                                <div class="text-xs text-gray-500 mt-0.5 flex items-center gap-3">
                                    <span class="flex items-center gap-1">
                                        <Globe class="w-3 h-3" />
                                        {{ session.ip_address || t('settingsSecurity.security.unknownIp') }}
                                    </span>
                                    <span>{{ session.os || t('settingsSecurity.security.unknownOs') }}</span>
                                    <span>{{ t('settingsSecurity.security.lastActive') }}{{ formatTime(session.last_active_at || session.created_at) }}</span>
                                </div>
                            </div>
                        </div>
                        <button v-if="!session.is_current && session.is_active"
                            @click="handleRevokeSession(session.id)"
                            :disabled="revokingSession === session.id"
                            class="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                            :title="t('settingsSecurity.security.logoutThisDevice')">
                            <Trash2 class="w-4 h-4" />
                        </button>
                    </div>
                </template>
            </div>
            
            <p class="text-xs text-gray-400">
                {{ t('settingsSecurity.security.sessionsHint') }}
            </p>
        </div>

        <!-- 修改密码弹窗 -->
        <CommonModal v-model="showPasswordModal" :title="t('settingsSecurity.security.changePassword')" width-class="w-full max-w-md">
            <div class="space-y-4">
                <div class="space-y-2">
                    <label class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ t('settingsSecurity.security.currentPassword') }}</label>
                    <input v-model="passwordForm.current" type="password" class="input-field" :placeholder="t('settingsSecurity.security.currentPasswordPlaceholder')">
                </div>
                <div class="space-y-2">
                    <label class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ t('settingsSecurity.security.newPassword') }}</label>
                    <input v-model="passwordForm.new" type="password" class="input-field" :placeholder="t('settingsSecurity.security.newPasswordPlaceholder')">
                    <CommonPasswordStrength :password="passwordForm.new" />
                </div>
                <div class="space-y-2">
                    <label class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ t('settingsSecurity.security.confirmNewPassword') }}</label>
                    <input v-model="passwordForm.confirm" type="password" class="input-field" :placeholder="t('settingsSecurity.security.confirmNewPasswordPlaceholder')">
                </div>
                <div v-if="message" :class="['text-sm', messageType === 'success' ? 'text-green-600' : 'text-red-600']">
                    {{ message }}
                </div>
            </div>
            <template #footer>
                <button @click="showPasswordModal = false" class="btn-secondary">{{ t('common.cancel') }}</button>
                <button @click="handleChangePassword" :disabled="saving" class="btn-primary">
                    {{ saving ? t('settingsSecurity.common.saving') : t('settingsSecurity.security.confirmChange') }}
                </button>
            </template>
        </CommonModal>

        <!-- 辅助邮箱设置弹窗 -->
        <CommonModal v-model="showRecoveryEmailModal" :title="user?.recovery_email ? t('settingsSecurity.security.changeRecoveryTitle') : t('settingsSecurity.security.setupRecoveryTitle')" width-class="w-full max-w-md">
            <div class="space-y-4">
                <!-- 步骤指示器 -->
                <div class="flex items-center justify-center gap-2 mb-4">
                    <div class="flex items-center gap-2">
                        <div :class="['w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium',
                            recoveryEmailStep === 'input' ? 'bg-primary text-white' : 'bg-green-500 text-white']">
                            {{ recoveryEmailStep === 'input' ? '1' : '✓' }}
                        </div>
                        <span class="text-sm text-gray-600 dark:text-gray-400">{{ t('settingsSecurity.security.stepInputEmail') }}</span>
                    </div>
                    <div class="w-8 h-0.5 bg-gray-200 dark:bg-gray-700"></div>
                    <div class="flex items-center gap-2">
                        <div :class="['w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium',
                            recoveryEmailStep === 'verify' ? 'bg-primary text-white' : 'bg-gray-200 dark:bg-gray-700 text-gray-500']">
                            2
                        </div>
                        <span class="text-sm text-gray-600 dark:text-gray-400">{{ t('settingsSecurity.security.stepVerifyEmail') }}</span>
                    </div>
                </div>

                <!-- 步骤1: 输入邮箱 -->
                <template v-if="recoveryEmailStep === 'input'">
                    <div class="space-y-2">
                        <label class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ t('settingsSecurity.security.newRecoveryEmail') }}</label>
                        <input v-model="recoveryEmailForm.email" type="email" class="input-field"
                            :placeholder="t('settingsSecurity.security.recoveryEmailPlaceholder')"
                            @keyup.enter="sendRecoveryCode">
                        <p class="text-xs text-gray-500">{{ t('settingsSecurity.security.recoveryEmailHint') }}</p>
                    </div>
                </template>

                <!-- 步骤2: 验证邮箱 -->
                <template v-else>
                    <div class="space-y-4">
                        <div class="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                            <p class="text-sm text-blue-700 dark:text-blue-300">
                                {{ t('settingsSecurity.security.codeSentTo') }}<span class="font-medium">{{ recoveryEmailForm.email }}</span>
                            </p>
                        </div>
                        <div class="space-y-2">
                            <label class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ t('settingsSecurity.security.verificationCode') }}</label>
                            <input v-model="recoveryEmailForm.code" type="text" class="input-field text-center text-lg tracking-widest"
                                :placeholder="t('settingsSecurity.security.enterSixDigitCode')" maxlength="6"
                                @keyup.enter="handleUpdateRecoveryEmail">
                        </div>
                        <div class="flex justify-center">
                            <button @click="sendRecoveryCode"
                                :disabled="sendingRecoveryCode || recoveryCodeCountdown > 0"
                                class="text-sm text-primary hover:text-primary-hover disabled:text-gray-400 disabled:cursor-not-allowed">
                                {{ sendingRecoveryCode ? t('settingsSecurity.security.sending') : recoveryCodeCountdown > 0 ? t('settingsSecurity.security.resendIn', { n: recoveryCodeCountdown }) : t('settingsSecurity.security.resendCode') }}
                            </button>
                        </div>
                    </div>
                </template>

                <div v-if="recoveryEmailMessage" :class="['text-sm', recoveryEmailMessageType === 'success' ? 'text-green-600' : 'text-red-600']">
                    {{ recoveryEmailMessage }}
                </div>
            </div>
            <template #footer>
                <button @click="showRecoveryEmailModal = false" class="btn-secondary">{{ t('common.cancel') }}</button>
                <template v-if="recoveryEmailStep === 'input'">
                    <button @click="sendRecoveryCode" :disabled="sendingRecoveryCode || !recoveryEmailForm.email" class="btn-primary">
                        {{ sendingRecoveryCode ? t('settingsSecurity.security.sending') : t('settingsSecurity.security.sendCode') }}
                    </button>
                </template>
                <template v-else>
                    <button @click="recoveryEmailStep = 'input'" class="btn-secondary">{{ t('settingsSecurity.security.prevStep') }}</button>
                    <button @click="handleUpdateRecoveryEmail" :disabled="recoveryEmailSaving || !recoveryEmailForm.code" class="btn-primary">
                        {{ recoveryEmailSaving ? t('settingsSecurity.common.saving') : t('settingsSecurity.security.confirmBind') }}
                    </button>
                </template>
            </template>
        </CommonModal>

        <!-- 2FA 设置弹窗 -->
        <CommonModal v-model="show2FAModal" :title="twoFAStep === 'disable' ? t('settingsSecurity.security.disableTitle') : t('settingsSecurity.security.setupTitle')">
            <template #header-actions>
                <Shield v-if="twoFAStep !== 'disable'" class="w-5 h-5 text-green-500" />
                <ShieldOff v-else class="w-5 h-5 text-red-500" />
            </template>

            <!-- 设置步骤：显示二维码 -->
            <template v-if="twoFAStep === 'setup'">
                <div v-if="twoFASaving" class="text-center py-8">
                    <div class="text-gray-500">{{ t('settingsSecurity.security.generatingQr') }}</div>
                </div>
                <template v-else-if="twoFASetupData">
                    <div class="text-center space-y-4">
                        <p class="text-sm text-gray-600 dark:text-gray-400">
                            {{ t('settingsSecurity.security.scanHint') }}
                        </p>

                        <!-- 二维码 -->
                        <div class="flex justify-center">
                            <img :src="twoFASetupData.qr_code" alt="2FA QR Code" class="w-48 h-48 rounded-lg border border-gray-200 dark:border-gray-700" />
                        </div>

                        <!-- 手动输入密钥 -->
                        <div class="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                            <p class="text-xs text-gray-500 mb-1">{{ t('settingsSecurity.security.manualKeyHint') }}</p>
                            <code class="text-sm font-mono text-gray-900 dark:text-white select-all">{{ twoFASetupData.secret }}</code>
                        </div>

                        <button @click="twoFAStep = 'verify'" class="btn-primary w-full">
                            {{ t('settingsSecurity.security.nextVerify') }}
                        </button>
                    </div>
                </template>
            </template>

            <!-- 验证步骤：输入验证码 -->
            <template v-else-if="twoFAStep === 'verify'">
                <div class="space-y-4">
                    <p class="text-sm text-gray-600 dark:text-gray-400">
                        {{ t('settingsSecurity.security.verifyHint') }}
                    </p>

                    <div class="space-y-2">
                        <label class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ t('settingsSecurity.security.verificationCode') }}</label>
                        <input v-model="twoFACode" type="text" class="input-field text-center text-2xl tracking-[0.5em] font-mono"
                            placeholder="000000" maxlength="6"
                            @keyup.enter="handleEnable2FA">
                    </div>
                </div>
            </template>

            <!-- 禁用步骤 -->
            <template v-else-if="twoFAStep === 'disable'">
                <div class="space-y-4">
                    <div class="p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
                        <p class="text-sm text-red-700 dark:text-red-300">
                            {{ t('settingsSecurity.security.disableWarning') }}
                        </p>
                    </div>

                    <div class="space-y-2">
                        <label class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ t('settingsSecurity.security.currentCode') }}</label>
                        <input v-model="twoFACode" type="text" class="input-field text-center text-2xl tracking-[0.5em] font-mono"
                            placeholder="000000" maxlength="6">
                    </div>

                    <div class="space-y-2">
                        <label class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ t('settingsSecurity.security.loginPassword') }}</label>
                        <input v-model="twoFAPassword" type="password" class="input-field"
                            :placeholder="t('settingsSecurity.security.loginPasswordPlaceholder')"
                            @keyup.enter="handleDisable2FA">
                    </div>
                </div>
            </template>

            <div v-if="twoFAMessage" :class="['text-sm mt-4', twoFAMessageType === 'success' ? 'text-green-600' : 'text-red-600']">
                {{ twoFAMessage }}
            </div>

            <template #footer>
                <button @click="show2FAModal = false" class="btn-secondary">{{ t('common.cancel') }}</button>
                <template v-if="twoFAStep === 'verify'">
                    <button @click="twoFAStep = 'setup'" class="btn-secondary">{{ t('settingsSecurity.security.prevStep') }}</button>
                    <button @click="handleEnable2FA" :disabled="twoFASaving || !twoFACode" class="btn-primary">
                        {{ twoFASaving ? t('settingsSecurity.security.verifying') : t('settingsSecurity.security.enableTwoFA') }}
                    </button>
                </template>
                <template v-else-if="twoFAStep === 'disable'">
                    <button @click="handleDisable2FA" :disabled="twoFASaving || !twoFACode || !twoFAPassword" class="btn-danger">
                        {{ twoFASaving ? t('settingsSecurity.security.processing') : t('settingsSecurity.security.confirmDisable') }}
                    </button>
                </template>
            </template>
        </CommonModal>

        <!-- 应用专用密码创建 -->
        <CommonModal v-model="showAppPasswordModal" :title="t('settingsSecurity.appPasswords.createTitle')" @update:model-value="v => { if (!v) closeAppPasswordModal() }">
            <div class="space-y-4">
                <template v-if="!newAppPassword">
                    <div class="space-y-2">
                        <label class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ t('settingsSecurity.appPasswords.nameLabel') }}</label>
                        <input v-model="appPasswordName" type="text" class="input-field" maxlength="100"
                            :placeholder="t('settingsSecurity.appPasswords.namePlaceholder')" @keyup.enter="handleCreateAppPassword">
                    </div>
                    <p class="text-xs text-gray-400">{{ t('settingsSecurity.appPasswords.caldavHint') }}</p>
                </template>
                <template v-else>
                    <div class="p-3 bg-amber-50 dark:bg-amber-900/20 rounded-lg">
                        <p class="text-sm text-amber-800 dark:text-amber-200 mb-2">{{ t('settingsSecurity.appPasswords.saveOnce') }}</p>
                        <code class="text-sm font-mono text-gray-900 dark:text-white select-all break-all">{{ newAppPassword }}</code>
                    </div>
                    <button class="btn-secondary w-full" @click="copyAppPassword">
                        {{ copiedAppPassword ? t('settingsSecurity.appPasswords.copied') : t('settingsSecurity.appPasswords.copy') }}
                    </button>
                </template>
            </div>
            <template #footer>
                <template v-if="!newAppPassword">
                    <button class="btn-secondary" @click="closeAppPasswordModal">{{ t('common.cancel') }}</button>
                    <button class="btn-primary" :disabled="appPasswordCreating || !appPasswordName.trim()" @click="handleCreateAppPassword">
                        {{ appPasswordCreating ? t('settings.common.saving') : t('settingsSecurity.appPasswords.create') }}
                    </button>
                </template>
                <template v-else>
                    <button class="btn-primary" @click="closeAppPasswordModal">{{ t('common.confirm') }}</button>
                </template>
            </template>
        </CommonModal>
    </div>
</template>

<style scoped>
.section-title {
    @apply text-2xl font-bold text-gray-900 dark:text-white mb-6;
}

.card {
    @apply bg-white dark:bg-bg-panelDark rounded-xl border border-gray-200 dark:border-border-dark overflow-hidden;
}

.icon-box {
    @apply p-2.5 rounded-lg flex items-center justify-center;
}

.input-field {
    @apply w-full px-4 py-2.5 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all text-gray-900 dark:text-white text-sm;
}

.btn-primary {
    @apply px-4 py-1.5 bg-primary text-white text-sm rounded-lg hover:bg-primary-hover transition-colors shadow-sm shadow-primary/20 disabled:opacity-50;
}

.btn-secondary {
    @apply px-4 py-1.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-200 text-sm rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors;
}

.btn-danger {
    @apply px-4 py-1.5 bg-red-500 text-white text-sm rounded-lg hover:bg-red-600 transition-colors shadow-sm shadow-red-500/20 disabled:opacity-50;
}
</style>