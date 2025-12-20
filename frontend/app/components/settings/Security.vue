<script setup lang="ts">
import { KeyRound, Smartphone, ShieldCheck, History, Laptop, Globe, X, Monitor, Trash2, LogOut, Mail, Edit3, QrCode, Shield, ShieldOff } from 'lucide-vue-next'

const { changePassword, getLoginSessions, revokeSession, revokeAllSessions, getMe, sendRecoveryEmailCode, updateRecoveryEmail, get2FAStatus, setup2FA, enable2FA, disable2FA } = useApi()

// 用户信息
const user = ref<any>(null)
const loadingUser = ref(true)

const loadUser = async () => {
    loadingUser.value = true
    try {
        user.value = await getMe()
    } catch (e) {
        console.error('加载用户信息失败', e)
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

// 加载 2FA 状态
const load2FAStatus = async () => {
    loading2FA.value = true
    try {
        twoFAStatus.value = await get2FAStatus()
    } catch (e) {
        console.error('加载 2FA 状态失败', e)
    } finally {
        loading2FA.value = false
    }
}

// 加载登录会话
const loadSessions = async () => {
    loadingSessions.value = true
    try {
        sessions.value = await getLoginSessions(10)
    } catch (e) {
        console.error('加载登录会话失败', e)
    } finally {
        loadingSessions.value = false
    }
}

// 格式化时间
const formatTime = (dateStr: string | null) => {
    if (!dateStr) return '未知'
    const date = new Date(dateStr)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    
    if (diff < 60000) return '刚刚'
    if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`
    if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`
    if (diff < 604800000) return `${Math.floor(diff / 86400000)} 天前`
    
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
    if (!confirm('确定要撤销此登录会话吗？')) return
    revokingSession.value = sessionId
    try {
        await revokeSession(sessionId)
        sessions.value = sessions.value.filter(s => s.id !== sessionId)
    } catch (e) {
        console.error('撤销会话失败', e)
    } finally {
        revokingSession.value = null
    }
}

// 撤销所有会话
const handleRevokeAll = async () => {
    if (!confirm('确定要撤销所有登录会话吗？这将使所有设备退出登录。')) return
    try {
        await revokeAllSessions()
        await loadSessions()
    } catch (e) {
        console.error('撤销所有会话失败', e)
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
        recoveryEmailMessage.value = '请输入邮箱地址'
        recoveryEmailMessageType.value = 'error'
        return
    }
    
    // 简单的邮箱格式验证
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(recoveryEmailForm.email)) {
        recoveryEmailMessage.value = '请输入有效的邮箱地址'
        recoveryEmailMessageType.value = 'error'
        return
    }
    
    sendingRecoveryCode.value = true
    recoveryEmailMessage.value = ''
    
    try {
        await sendRecoveryEmailCode(recoveryEmailForm.email)
        recoveryEmailStep.value = 'verify'
        recoveryEmailMessage.value = '验证码已发送到您的邮箱'
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
        recoveryEmailMessage.value = e.data?.detail || '发送验证码失败'
        recoveryEmailMessageType.value = 'error'
    } finally {
        sendingRecoveryCode.value = false
    }
}

const handleUpdateRecoveryEmail = async () => {
    if (!recoveryEmailForm.code) {
        recoveryEmailMessage.value = '请输入验证码'
        recoveryEmailMessageType.value = 'error'
        return
    }
    
    if (recoveryEmailForm.code.length !== 6) {
        recoveryEmailMessage.value = '验证码为6位数字'
        recoveryEmailMessageType.value = 'error'
        return
    }
    
    recoveryEmailSaving.value = true
    recoveryEmailMessage.value = ''
    
    try {
        const result = await updateRecoveryEmail(recoveryEmailForm.email, recoveryEmailForm.code)
        recoveryEmailMessage.value = '辅助邮箱设置成功'
        recoveryEmailMessageType.value = 'success'
        
        // 更新用户信息
        if (user.value) {
            user.value.recovery_email = result.recovery_email
        }
        
        setTimeout(() => {
            showRecoveryEmailModal.value = false
        }, 1500)
    } catch (e: any) {
        recoveryEmailMessage.value = e.data?.detail || '设置辅助邮箱失败'
        recoveryEmailMessageType.value = 'error'
    } finally {
        recoveryEmailSaving.value = false
    }
}

// 清理定时器
onUnmounted(() => {
    if (recoveryCountdownTimer) {
        clearInterval(recoveryCountdownTimer)
    }
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
            twoFAMessage.value = e.data?.detail || '获取 2FA 设置信息失败'
            twoFAMessageType.value = 'error'
        } finally {
            twoFASaving.value = false
        }
    }
}

const handleEnable2FA = async () => {
    if (!twoFACode.value || twoFACode.value.length !== 6) {
        twoFAMessage.value = '请输入6位验证码'
        twoFAMessageType.value = 'error'
        return
    }
    
    twoFASaving.value = true
    twoFAMessage.value = ''
    
    try {
        await enable2FA(twoFACode.value)
        twoFAMessage.value = '两步验证已启用'
        twoFAMessageType.value = 'success'
        twoFAStatus.value.enabled = true
        
        setTimeout(() => {
            show2FAModal.value = false
        }, 1500)
    } catch (e: any) {
        twoFAMessage.value = e.data?.detail || '启用失败，请检查验证码'
        twoFAMessageType.value = 'error'
    } finally {
        twoFASaving.value = false
    }
}

const handleDisable2FA = async () => {
    if (!twoFACode.value || twoFACode.value.length !== 6) {
        twoFAMessage.value = '请输入6位验证码'
        twoFAMessageType.value = 'error'
        return
    }
    
    if (!twoFAPassword.value) {
        twoFAMessage.value = '请输入登录密码'
        twoFAMessageType.value = 'error'
        return
    }
    
    twoFASaving.value = true
    twoFAMessage.value = ''
    
    try {
        await disable2FA(twoFACode.value, twoFAPassword.value)
        twoFAMessage.value = '两步验证已禁用'
        twoFAMessageType.value = 'success'
        twoFAStatus.value.enabled = false
        
        setTimeout(() => {
            show2FAModal.value = false
        }, 1500)
    } catch (e: any) {
        twoFAMessage.value = e.data?.detail || '禁用失败，请检查验证码和密码'
        twoFAMessageType.value = 'error'
    } finally {
        twoFASaving.value = false
    }
}

const handleChangePassword = async () => {
    message.value = ''
    
    if (passwordForm.new !== passwordForm.confirm) {
        message.value = '两次输入的新密码不一致'
        messageType.value = 'error'
        return
    }
    
    if (passwordForm.new.length < 6) {
        message.value = '新密码至少需要6个字符'
        messageType.value = 'error'
        return
    }
    
    saving.value = true
    try {
        await changePassword(passwordForm.current, passwordForm.new)
        message.value = '密码修改成功'
        messageType.value = 'success'
        setTimeout(() => {
            showPasswordModal.value = false
        }, 1500)
    } catch (e: any) {
        message.value = e.data?.detail || '密码修改失败'
        messageType.value = 'error'
    } finally {
        saving.value = false
    }
}

onMounted(() => {
    loadSessions()
    loadUser()
    load2FAStatus()
})
</script>

<template>
    <div class="space-y-8">
        <h2 class="section-title">登录与安全</h2>

        <!-- 1. 核心认证设置 -->
        <div class="card divide-y divide-gray-100 dark:divide-gray-800">

            <!-- 修改密码 -->
            <div class="p-6 flex items-center justify-between">
                <div class="flex items-center gap-4">
                    <div class="icon-box bg-purple-100 text-purple-600 dark:bg-purple-900/30">
                        <KeyRound class="w-5 h-5" />
                    </div>
                    <div>
                        <div class="font-bold text-gray-900 dark:text-white">登录密码</div>
                        <div class="text-sm text-gray-500 mt-0.5">建议定期更换密码以保护账号安全</div>
                    </div>
                </div>
                <button @click="openPasswordModal" class="btn-secondary">修改密码</button>
            </div>

            <!-- 两步验证 -->
            <div class="p-6 flex items-center justify-between">
                <div class="flex items-center gap-4">
                    <div :class="['icon-box', twoFAStatus.enabled ? 'bg-green-100 text-green-600 dark:bg-green-900/30' : 'bg-gray-100 text-gray-600 dark:bg-gray-800']">
                        <Smartphone class="w-5 h-5" />
                    </div>
                    <div>
                        <div class="font-bold text-gray-900 dark:text-white">两步验证 (2FA)</div>
                        <div class="text-sm text-gray-500 mt-0.5">使用 Authenticator App 进行二次确认</div>
                    </div>
                </div>
                <div class="flex items-center gap-3">
                    <div v-if="loading2FA" class="text-sm text-gray-400">加载中...</div>
                    <template v-else>
                        <span v-if="twoFAStatus.enabled" class="px-2 py-0.5 bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 text-xs rounded-full">已启用</span>
                        <span v-else class="px-2 py-0.5 bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400 text-xs rounded-full">未启用</span>
                        <button @click="open2FASetupModal" :class="twoFAStatus.enabled ? 'btn-secondary' : 'btn-primary'">
                            {{ twoFAStatus.enabled ? '管理' : '立即启用' }}
                        </button>
                    </template>
                </div>
            </div>

            <!-- 备用邮箱 -->
            <div class="p-6 flex items-center justify-between">
                <div class="flex items-center gap-4">
                    <div class="icon-box bg-blue-100 text-blue-600 dark:bg-blue-900/30">
                        <Mail class="w-5 h-5" />
                    </div>
                    <div>
                        <div class="font-bold text-gray-900 dark:text-white">安全辅助邮箱</div>
                        <div class="text-sm text-gray-500 mt-0.5">用于找回密码或接收安全通知</div>
                    </div>
                </div>
                <div class="flex items-center gap-3">
                    <div v-if="loadingUser" class="text-sm text-gray-400">加载中...</div>
                    <template v-else>
                        <div v-if="user?.recovery_email" class="flex items-center gap-2">
                            <span class="text-sm text-gray-700 dark:text-gray-300 font-medium">{{ user.recovery_email }}</span>
                            <span class="px-2 py-0.5 bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 text-xs rounded-full">已绑定</span>
                        </div>
                        <div v-else class="text-sm text-gray-400">未设置</div>
                        <button @click="openRecoveryEmailModal" class="btn-secondary flex items-center gap-1.5">
                            <Edit3 class="w-4 h-4" />
                            {{ user?.recovery_email ? '修改' : '设置' }}
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
                    已登录设备
                </h3>
                <button v-if="sessions.length > 1" @click="handleRevokeAll" class="text-sm text-red-500 hover:text-red-600 flex items-center gap-1">
                    <LogOut class="w-4 h-4" />
                    退出所有设备
                </button>
            </div>

            <div class="card p-0 overflow-hidden">
                <!-- 加载中 -->
                <div v-if="loadingSessions" class="p-8 text-center text-gray-500">
                    加载中...
                </div>
                
                <!-- 无数据 -->
                <div v-else-if="sessions.length === 0" class="p-8 text-center text-gray-500">
                    暂无已登录设备
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
                                    {{ session.browser || session.device_info || '未知设备' }}
                                    <span v-if="session.is_current" class="px-2 py-0.5 bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 text-[10px] rounded-full">当前设备</span>
                                    <span v-if="!session.is_active" class="px-2 py-0.5 bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400 text-[10px] rounded-full">已失效</span>
                                </div>
                                <div class="text-xs text-gray-500 mt-0.5 flex items-center gap-3">
                                    <span class="flex items-center gap-1">
                                        <Globe class="w-3 h-3" />
                                        {{ session.ip_address || '未知IP' }}
                                    </span>
                                    <span>{{ session.os || '未知系统' }}</span>
                                    <span>最近活动：{{ formatTime(session.last_active_at || session.created_at) }}</span>
                                </div>
                            </div>
                        </div>
                        <button v-if="!session.is_current && session.is_active"
                            @click="handleRevokeSession(session.id)"
                            :disabled="revokingSession === session.id"
                            class="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                            title="退出此设备">
                            <Trash2 class="w-4 h-4" />
                        </button>
                    </div>
                </template>
            </div>
            
            <p class="text-xs text-gray-400">
                同一设备多次登录只显示一条记录。30天无活动的设备将自动清理。如发现异常设备，请立即退出并修改密码。
            </p>
        </div>

        <!-- 修改密码弹窗 -->
        <Teleport to="body">
            <div v-if="showPasswordModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                <div class="bg-white dark:bg-bg-panelDark rounded-2xl shadow-2xl w-full max-w-md">
                    <div class="flex items-center justify-between p-6 border-b border-gray-100 dark:border-gray-800">
                        <h3 class="text-lg font-bold text-gray-900 dark:text-white">修改密码</h3>
                        <button @click="showPasswordModal = false" class="p-1 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg">
                            <X class="w-5 h-5 text-gray-500" />
                        </button>
                    </div>
                    
                    <div class="p-6 space-y-4">
                        <div class="space-y-2">
                            <label class="text-sm font-medium text-gray-700 dark:text-gray-300">当前密码</label>
                            <input v-model="passwordForm.current" type="password" class="input-field" placeholder="输入当前密码">
                        </div>
                        <div class="space-y-2">
                            <label class="text-sm font-medium text-gray-700 dark:text-gray-300">新密码</label>
                            <input v-model="passwordForm.new" type="password" class="input-field" placeholder="输入新密码（至少6位）">
                        </div>
                        <div class="space-y-2">
                            <label class="text-sm font-medium text-gray-700 dark:text-gray-300">确认新密码</label>
                            <input v-model="passwordForm.confirm" type="password" class="input-field" placeholder="再次输入新密码">
                        </div>
                        
                        <div v-if="message" :class="['text-sm', messageType === 'success' ? 'text-green-600' : 'text-red-600']">
                            {{ message }}
                        </div>
                    </div>
                    
                    <div class="flex justify-end gap-3 p-6 border-t border-gray-100 dark:border-gray-800">
                        <button @click="showPasswordModal = false" class="btn-secondary">取消</button>
                        <button @click="handleChangePassword" :disabled="saving" class="btn-primary">
                            {{ saving ? '保存中...' : '确认修改' }}
                        </button>
                    </div>
                </div>
            </div>
        </Teleport>

        <!-- 辅助邮箱设置弹窗 -->
        <Teleport to="body">
            <div v-if="showRecoveryEmailModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                <div class="bg-white dark:bg-bg-panelDark rounded-2xl shadow-2xl w-full max-w-md">
                    <div class="flex items-center justify-between p-6 border-b border-gray-100 dark:border-gray-800">
                        <h3 class="text-lg font-bold text-gray-900 dark:text-white">
                            {{ user?.recovery_email ? '修改辅助邮箱' : '设置辅助邮箱' }}
                        </h3>
                        <button @click="showRecoveryEmailModal = false" class="p-1 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg">
                            <X class="w-5 h-5 text-gray-500" />
                        </button>
                    </div>
                    
                    <div class="p-6 space-y-4">
                        <!-- 步骤指示器 -->
                        <div class="flex items-center justify-center gap-2 mb-4">
                            <div class="flex items-center gap-2">
                                <div :class="['w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium',
                                    recoveryEmailStep === 'input' ? 'bg-primary text-white' : 'bg-green-500 text-white']">
                                    {{ recoveryEmailStep === 'input' ? '1' : '✓' }}
                                </div>
                                <span class="text-sm text-gray-600 dark:text-gray-400">输入邮箱</span>
                            </div>
                            <div class="w-8 h-0.5 bg-gray-200 dark:bg-gray-700"></div>
                            <div class="flex items-center gap-2">
                                <div :class="['w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium',
                                    recoveryEmailStep === 'verify' ? 'bg-primary text-white' : 'bg-gray-200 dark:bg-gray-700 text-gray-500']">
                                    2
                                </div>
                                <span class="text-sm text-gray-600 dark:text-gray-400">验证邮箱</span>
                            </div>
                        </div>

                        <!-- 步骤1: 输入邮箱 -->
                        <template v-if="recoveryEmailStep === 'input'">
                            <div class="space-y-2">
                                <label class="text-sm font-medium text-gray-700 dark:text-gray-300">新辅助邮箱</label>
                                <input v-model="recoveryEmailForm.email" type="email" class="input-field"
                                    placeholder="请输入您的辅助邮箱地址"
                                    @keyup.enter="sendRecoveryCode">
                                <p class="text-xs text-gray-500">请使用您能正常接收邮件的邮箱地址</p>
                            </div>
                        </template>

                        <!-- 步骤2: 验证邮箱 -->
                        <template v-else>
                            <div class="space-y-4">
                                <div class="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                                    <p class="text-sm text-blue-700 dark:text-blue-300">
                                        验证码已发送至 <span class="font-medium">{{ recoveryEmailForm.email }}</span>
                                    </p>
                                </div>
                                
                                <div class="space-y-2">
                                    <label class="text-sm font-medium text-gray-700 dark:text-gray-300">验证码</label>
                                    <input v-model="recoveryEmailForm.code" type="text" class="input-field text-center text-lg tracking-widest"
                                        placeholder="请输入6位验证码" maxlength="6"
                                        @keyup.enter="handleUpdateRecoveryEmail">
                                </div>
                                
                                <div class="flex justify-center">
                                    <button @click="sendRecoveryCode"
                                        :disabled="sendingRecoveryCode || recoveryCodeCountdown > 0"
                                        class="text-sm text-primary hover:text-primary-hover disabled:text-gray-400 disabled:cursor-not-allowed">
                                        {{ sendingRecoveryCode ? '发送中...' : recoveryCodeCountdown > 0 ? `${recoveryCodeCountdown}秒后重新发送` : '重新发送验证码' }}
                                    </button>
                                </div>
                            </div>
                        </template>
                        
                        <div v-if="recoveryEmailMessage" :class="['text-sm', recoveryEmailMessageType === 'success' ? 'text-green-600' : 'text-red-600']">
                            {{ recoveryEmailMessage }}
                        </div>
                    </div>
                    
                    <div class="flex justify-end gap-3 p-6 border-t border-gray-100 dark:border-gray-800">
                        <button @click="showRecoveryEmailModal = false" class="btn-secondary">取消</button>
                        <template v-if="recoveryEmailStep === 'input'">
                            <button @click="sendRecoveryCode" :disabled="sendingRecoveryCode || !recoveryEmailForm.email" class="btn-primary">
                                {{ sendingRecoveryCode ? '发送中...' : '发送验证码' }}
                            </button>
                        </template>
                        <template v-else>
                            <button @click="recoveryEmailStep = 'input'" class="btn-secondary">上一步</button>
                            <button @click="handleUpdateRecoveryEmail" :disabled="recoveryEmailSaving || !recoveryEmailForm.code" class="btn-primary">
                                {{ recoveryEmailSaving ? '保存中...' : '确认绑定' }}
                            </button>
                        </template>
                    </div>
                </div>
            </div>
        </Teleport>

        <!-- 2FA 设置弹窗 -->
        <Teleport to="body">
            <div v-if="show2FAModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                <div class="bg-white dark:bg-bg-panelDark rounded-2xl shadow-2xl w-full max-w-md">
                    <div class="flex items-center justify-between p-6 border-b border-gray-100 dark:border-gray-800">
                        <h3 class="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
                            <Shield v-if="twoFAStep !== 'disable'" class="w-5 h-5 text-green-500" />
                            <ShieldOff v-else class="w-5 h-5 text-red-500" />
                            {{ twoFAStep === 'disable' ? '禁用两步验证' : '设置两步验证' }}
                        </h3>
                        <button @click="show2FAModal = false" class="p-1 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg">
                            <X class="w-5 h-5 text-gray-500" />
                        </button>
                    </div>
                    
                    <div class="p-6 space-y-4">
                        <!-- 设置步骤：显示二维码 -->
                        <template v-if="twoFAStep === 'setup'">
                            <div v-if="twoFASaving" class="text-center py-8">
                                <div class="text-gray-500">正在生成二维码...</div>
                            </div>
                            <template v-else-if="twoFASetupData">
                                <div class="text-center space-y-4">
                                    <p class="text-sm text-gray-600 dark:text-gray-400">
                                        使用 Google Authenticator、Microsoft Authenticator 或其他 TOTP 应用扫描下方二维码
                                    </p>
                                    
                                    <!-- 二维码 -->
                                    <div class="flex justify-center">
                                        <img :src="twoFASetupData.qr_code" alt="2FA QR Code" class="w-48 h-48 rounded-lg border border-gray-200 dark:border-gray-700" />
                                    </div>
                                    
                                    <!-- 手动输入密钥 -->
                                    <div class="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                                        <p class="text-xs text-gray-500 mb-1">无法扫描？手动输入密钥：</p>
                                        <code class="text-sm font-mono text-gray-900 dark:text-white select-all">{{ twoFASetupData.secret }}</code>
                                    </div>
                                    
                                    <button @click="twoFAStep = 'verify'" class="btn-primary w-full">
                                        下一步：验证
                                    </button>
                                </div>
                            </template>
                        </template>
                        
                        <!-- 验证步骤：输入验证码 -->
                        <template v-else-if="twoFAStep === 'verify'">
                            <div class="space-y-4">
                                <p class="text-sm text-gray-600 dark:text-gray-400">
                                    请输入 Authenticator App 中显示的6位验证码，以完成设置
                                </p>
                                
                                <div class="space-y-2">
                                    <label class="text-sm font-medium text-gray-700 dark:text-gray-300">验证码</label>
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
                                        ⚠️ 禁用两步验证会降低账号安全性。请确认您要执行此操作。
                                    </p>
                                </div>
                                
                                <div class="space-y-2">
                                    <label class="text-sm font-medium text-gray-700 dark:text-gray-300">当前验证码</label>
                                    <input v-model="twoFACode" type="text" class="input-field text-center text-2xl tracking-[0.5em] font-mono"
                                        placeholder="000000" maxlength="6">
                                </div>
                                
                                <div class="space-y-2">
                                    <label class="text-sm font-medium text-gray-700 dark:text-gray-300">登录密码</label>
                                    <input v-model="twoFAPassword" type="password" class="input-field"
                                        placeholder="输入您的登录密码"
                                        @keyup.enter="handleDisable2FA">
                                </div>
                            </div>
                        </template>
                        
                        <div v-if="twoFAMessage" :class="['text-sm', twoFAMessageType === 'success' ? 'text-green-600' : 'text-red-600']">
                            {{ twoFAMessage }}
                        </div>
                    </div>
                    
                    <div class="flex justify-end gap-3 p-6 border-t border-gray-100 dark:border-gray-800">
                        <button @click="show2FAModal = false" class="btn-secondary">取消</button>
                        <template v-if="twoFAStep === 'verify'">
                            <button @click="twoFAStep = 'setup'" class="btn-secondary">上一步</button>
                            <button @click="handleEnable2FA" :disabled="twoFASaving || !twoFACode" class="btn-primary">
                                {{ twoFASaving ? '验证中...' : '启用两步验证' }}
                            </button>
                        </template>
                        <template v-else-if="twoFAStep === 'disable'">
                            <button @click="handleDisable2FA" :disabled="twoFASaving || !twoFACode || !twoFAPassword" class="btn-danger">
                                {{ twoFASaving ? '处理中...' : '确认禁用' }}
                            </button>
                        </template>
                    </div>
                </div>
            </div>
        </Teleport>
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