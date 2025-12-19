<script setup lang="ts">
import { KeyRound, Smartphone, ShieldCheck, History, Laptop, Globe, X, Monitor, Trash2, LogOut } from 'lucide-vue-next'

const { changePassword, getLoginSessions, revokeSession, revokeAllSessions } = useApi()

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

onMounted(loadSessions)
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
                    <div class="icon-box bg-green-100 text-green-600 dark:bg-green-900/30">
                        <Smartphone class="w-5 h-5" />
                    </div>
                    <div>
                        <div class="font-bold text-gray-900 dark:text-white">两步验证 (2FA)</div>
                        <div class="text-sm text-gray-500 mt-0.5">使用 Authenticator App 进行二次确认</div>
                    </div>
                </div>
                <button class="btn-primary">立即启用</button>
            </div>

            <!-- 备用邮箱 -->
            <div class="p-6 flex items-center justify-between">
                <div class="flex items-center gap-4">
                    <div class="icon-box bg-blue-100 text-blue-600 dark:bg-blue-900/30">
                        <ShieldCheck class="w-5 h-5" />
                    </div>
                    <div>
                        <div class="font-bold text-gray-900 dark:text-white">安全辅助邮箱</div>
                        <div class="text-sm text-gray-500 mt-0.5">用于找回密码或接收安全通知</div>
                    </div>
                </div>
                <div class="text-sm text-gray-400 mr-4">未设置</div>
            </div>
        </div>

        <!-- 2. 最近活动设备 -->
        <div class="space-y-4">
            <div class="flex items-center justify-between">
                <h3 class="font-bold text-gray-900 dark:text-white flex items-center gap-2">
                    <History class="w-5 h-5 text-gray-500" />
                    最近登录设备
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
                    暂无登录记录
                </div>
                
                <!-- 会话列表 -->
                <template v-else>
                    <div v-for="(session, index) in sessions" :key="session.id"
                        class="p-4 flex items-center justify-between border-b border-gray-100 dark:border-gray-800 last:border-b-0"
                        :class="index === 0 ? 'bg-green-50/50 dark:bg-green-900/10' : ''">
                        <div class="flex items-center gap-4">
                            <component :is="getDeviceIcon(session.os)"
                                class="w-8 h-8"
                                :class="index === 0 ? 'text-green-600 dark:text-green-400' : 'text-gray-400'" />
                            <div>
                                <div class="font-bold text-gray-900 dark:text-white flex items-center gap-2">
                                    {{ session.browser || session.device_info || '未知设备' }}
                                    <span v-if="index === 0" class="px-2 py-0.5 bg-green-100 text-green-700 text-[10px] rounded-full">当前设备</span>
                                    <span v-if="!session.is_active" class="px-2 py-0.5 bg-gray-100 text-gray-500 text-[10px] rounded-full">已失效</span>
                                </div>
                                <div class="text-xs text-gray-500 mt-0.5 flex items-center gap-3">
                                    <span class="flex items-center gap-1">
                                        <Globe class="w-3 h-3" />
                                        {{ session.ip_address || '未知IP' }}
                                    </span>
                                    <span>{{ session.os || '未知系统' }}</span>
                                    <span>{{ formatTime(session.created_at) }}</span>
                                </div>
                            </div>
                        </div>
                        <button v-if="index !== 0 && session.is_active"
                            @click="handleRevokeSession(session.id)"
                            :disabled="revokingSession === session.id"
                            class="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                            title="撤销此会话">
                            <Trash2 class="w-4 h-4" />
                        </button>
                    </div>
                </template>
            </div>
            
            <p class="text-xs text-gray-400">
                显示最近 10 条登录记录。如发现异常登录，请立即修改密码。
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
</style>