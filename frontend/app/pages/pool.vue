<script setup lang="ts">
import { Search, Plus, RefreshCw, Copy, Mail, History, BarChart, Trash2, Star, Box, ArrowLeft, Check } from 'lucide-vue-next'
const { isGenerateOpen, isHistoryOpen, isStatsOpen } = useGlobalModal()
const { getPoolMailboxes, getPoolMailboxEmails, deletePoolMailbox, getPoolStats, getMe, markPoolEmailRead } = useApi()
const router = useRouter()

definePageMeta({ layout: 'pool' })

// 权限检查
const hasAccess = ref(false)
const loading = ref(true)

// 数据
interface Mailbox {
    id: number
    email: string
    purpose: string | null
    auto_verify_codes: boolean
    is_active: boolean
    created_at: string
    unread_count: number
}

interface PoolEmail {
    id: number
    sender: string
    subject: string
    received_at: string | null
    is_read: boolean
    verification_code: string | null
}

const mailboxes = ref<Mailbox[]>([])
const selectedMailbox = ref<Mailbox | null>(null)
const emails = ref<PoolEmail[]>([])
const selectedEmail = ref<PoolEmail | null>(null)
const stats = ref({ active_mailboxes: 0, total_emails: 0 })
const searchQuery = ref('')
const copiedCode = ref<string | null>(null)

// 加载邮箱列表
const loadMailboxes = async () => {
    loading.value = true
    try {
        const res = await getPoolMailboxes()
        mailboxes.value = res.items
        if (res.items.length > 0 && !selectedMailbox.value) {
            selectedMailbox.value = res.items[0]
        }
    } catch (e: any) {
        if (e.statusCode === 403) {
            hasAccess.value = false
        }
        console.error('加载邮箱失败', e)
    } finally {
        loading.value = false
    }
}

// 加载邮件列表
const loadEmails = async () => {
    if (!selectedMailbox.value) {
        emails.value = []
        return
    }
    try {
        const res = await getPoolMailboxEmails(selectedMailbox.value.id)
        emails.value = res.items
        if (res.items.length > 0) {
            selectedEmail.value = res.items[0]
        } else {
            selectedEmail.value = null
        }
    } catch (e) {
        console.error('加载邮件失败', e)
    }
}

// 加载统计
const loadStats = async () => {
    try {
        stats.value = await getPoolStats()
    } catch (e) {
        console.error('加载统计失败', e)
    }
}

// 选择邮箱
const selectMailbox = (mailbox: Mailbox) => {
    selectedMailbox.value = mailbox
    loadEmails()
}

// 选择邮件并标记已读
const selectEmail = async (email: PoolEmail) => {
    selectedEmail.value = email
    if (!email.is_read) {
        try {
            await markPoolEmailRead(email.id)
            email.is_read = true
            // 更新未读数
            if (selectedMailbox.value && selectedMailbox.value.unread_count > 0) {
                selectedMailbox.value.unread_count--
            }
        } catch (e) {
            console.error('标记已读失败', e)
        }
    }
}

// 删除邮箱
const handleDelete = async (mailbox: Mailbox) => {
    if (!confirm(`确定删除 ${mailbox.email} 吗？`)) return
    try {
        await deletePoolMailbox(mailbox.id)
        mailboxes.value = mailboxes.value.filter(m => m.id !== mailbox.id)
        if (selectedMailbox.value?.id === mailbox.id) {
            selectedMailbox.value = mailboxes.value[0] || null
            loadEmails()
        }
        loadStats()
    } catch (e: any) {
        alert(e.data?.detail || '删除失败')
    }
}

// 复制验证码
const copyCode = async (code: string) => {
    await navigator.clipboard.writeText(code)
    copiedCode.value = code
    setTimeout(() => copiedCode.value = null, 2000)
}

// 复制邮箱地址
const copiedEmail = ref<string | null>(null)
const copyEmail = async (email: string) => {
    await navigator.clipboard.writeText(email)
    copiedEmail.value = email
    setTimeout(() => copiedEmail.value = null, 2000)
}

// 格式化时间
const formatTime = (dateStr: string | null) => {
    if (!dateStr) return '-'
    const date = new Date(dateStr)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    if (diff < 60000) return '刚刚'
    if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
    return date.toLocaleDateString('zh-CN')
}

// 获取邮箱首字母
const getInitial = (email: string) => email?.[0]?.toUpperCase() || '?'

// 获取发件人名称
const getSenderName = (sender: string) => sender?.split('<')[0]?.trim() || sender || '未知'

// 检查权限并加载数据
onMounted(async () => {
    try {
        const user = await getMe()
        hasAccess.value = user.pool_enabled || user.role === 'admin'
        if (hasAccess.value) {
            await Promise.all([loadMailboxes(), loadStats()])
        }
    } catch (e) {
        hasAccess.value = false
    } finally {
        loading.value = false
    }
})

// 监听邮箱变化
watch(selectedMailbox, () => {
    if (selectedMailbox.value) loadEmails()
})

// 监听创建弹窗关闭，刷新列表
watch(isGenerateOpen, (val) => {
    if (!val) {
        loadMailboxes()
        loadStats()
    }
})
</script>

<template>
    <div class="pool-page flex w-full h-full bg-white dark:bg-bg-dark overflow-hidden">
        <!-- 无权限提示 -->
        <div v-if="!loading && !hasAccess" class="flex-1 flex flex-col items-center justify-center text-gray-500">
            <Box class="w-20 h-20 opacity-20 mb-6" />
            <p class="text-xl font-medium mb-2">您没有账号池功能权限</p>
            <p class="text-sm">请联系管理员开通</p>
            <button @click="router.push('/')" class="mt-6 px-6 py-2 bg-primary text-white rounded-lg">返回首页</button>
        </div>

        <template v-else>
            <!-- 第一栏：账号列表 -->
            <div class="pool-sidebar w-64 h-full bg-gray-50/80 dark:bg-bg-panelDark border-r border-gray-200 dark:border-border-dark flex flex-col shrink-0">
                <!-- 顶部 Header -->
                <div class="h-14 flex items-center px-4 gap-3 border-b border-gray-200/50 dark:border-gray-800 shrink-0">
                    <button @click="router.push('/')" class="p-2 -ml-2 text-gray-500 hover:text-gray-900 dark:hover:text-white rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors">
                        <ArrowLeft class="w-5 h-5" />
                    </button>
                    <div class="font-bold text-gray-900 dark:text-white flex items-center gap-2">
                        <Box class="w-5 h-5 text-primary" />
                        账号池
                    </div>
                </div>

                <!-- 搜索 -->
                <div class="p-3 pb-2">
                    <div class="relative">
                        <Search class="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                        <input v-model="searchQuery" type="text" placeholder="搜索账号..."
                            class="w-full bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg py-1.5 pl-9 pr-4 text-xs focus:border-primary focus:ring-1 focus:ring-primary/20 outline-none transition-all">
                    </div>
                </div>

                <!-- 列表骨架屏 -->
                <div v-if="loading" class="flex-1 overflow-y-auto px-2 space-y-2 py-2">
                    <div v-for="i in 5" :key="i" class="p-3 rounded-xl animate-pulse">
                        <div class="flex items-center gap-3">
                            <div class="w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-700"></div>
                            <div class="flex-1 space-y-2">
                                <div class="h-3 bg-gray-200 dark:bg-gray-700 rounded w-32"></div>
                                <div class="h-2 bg-gray-200 dark:bg-gray-700 rounded w-20"></div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 列表 -->
                <div v-else class="flex-1 overflow-y-auto px-2 space-y-1 py-2 custom-scrollbar">
                    <div v-if="mailboxes.length === 0" class="p-4 text-center text-gray-400 text-sm">
                        暂无临时邮箱<br>点击右上角生成
                    </div>
                    <div v-for="mailbox in mailboxes.filter(m => !searchQuery || m.email.includes(searchQuery))" :key="mailbox.id" 
                        @click="selectMailbox(mailbox)"
                        class="p-3 rounded-xl cursor-pointer hover:bg-white dark:hover:bg-gray-800 transition-all border border-transparent hover:border-gray-200 dark:hover:border-gray-700 relative group"
                        :class="{ 'bg-white dark:bg-gray-800 shadow-sm border-gray-200 dark:border-gray-700': selectedMailbox?.id === mailbox.id }">
                        <div v-if="selectedMailbox?.id === mailbox.id" class="absolute left-0 top-3 bottom-3 w-1 bg-primary rounded-r-full"></div>
                        <div class="flex items-center gap-3 pl-2">
                            <div class="w-8 h-8 rounded-full bg-primary text-white flex items-center justify-center font-bold text-xs shrink-0">
                                {{ getInitial(mailbox.email) }}
                            </div>
                            <div class="flex-1 min-w-0">
                                <div class="flex items-center gap-2">
                                    <div class="text-sm font-bold text-gray-900 dark:text-white truncate">{{ mailbox.email }}</div>
                                    <span v-if="mailbox.unread_count > 0" class="px-1.5 py-0.5 bg-primary text-white text-[10px] font-bold rounded-full min-w-[18px] text-center">{{ mailbox.unread_count }}</span>
                                </div>
                                <div class="flex items-center justify-between mt-0.5">
                                    <span class="text-[10px] text-gray-400">{{ mailbox.purpose || '未分类' }}</span>
                                    <button @click.stop="handleDelete(mailbox)" class="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-100 dark:hover:bg-red-900/30 rounded text-red-500 transition-all">
                                        <Trash2 class="w-3 h-3" />
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 底部统计 -->
                <div class="p-3 border-t border-gray-200 dark:border-gray-800 flex justify-between text-[10px] text-gray-400 bg-gray-100/50 dark:bg-gray-900/50">
                    <span>{{ stats.active_mailboxes }} 个活跃账号</span>
                    <span>共 {{ stats.total_emails }} 封邮件</span>
                </div>
            </div>

            <!-- 第二栏：邮件列表 -->
            <div class="pool-email-list w-80 h-full border-r border-gray-200 dark:border-border-dark flex flex-col shrink-0">
                <div class="pool-email-header h-14 flex items-center justify-between px-5 border-b border-gray-100 dark:border-gray-800 shrink-0">
                    <div v-if="selectedMailbox" class="flex items-center gap-3 min-w-0">
                        <div class="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-white font-bold shrink-0 text-xs">
                            {{ getInitial(selectedMailbox.email) }}
                        </div>
                        <div class="min-w-0 flex items-center gap-2">
                            <div class="text-sm font-bold text-gray-900 dark:text-white truncate">{{ selectedMailbox.email }}</div>
                            <button @click="copyEmail(selectedMailbox.email)" class="text-gray-400 hover:text-primary transition-colors shrink-0">
                                <Check v-if="copiedEmail === selectedMailbox.email" class="w-4 h-4 text-green-500" />
                                <Copy v-else class="w-4 h-4" />
                            </button>
                        </div>
                    </div>
                    <button @click="loadEmails" class="text-gray-400 hover:text-primary transition-colors">
                        <RefreshCw class="w-4 h-4" />
                    </button>
                </div>

                <div class="flex-1 overflow-y-auto">
                    <div v-if="emails.length === 0" class="p-8 text-center text-gray-400 text-sm">
                        暂无邮件
                    </div>
                    <div v-for="email in emails" :key="email.id" @click="selectEmail(email)"
                        class="px-5 py-4 border-b border-gray-50 dark:border-gray-800 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors relative"
                        :class="{ 'bg-purple-50/40 dark:bg-gray-800/60': selectedEmail?.id === email.id }">
                        <div class="flex items-center justify-between mb-1">
                            <div class="flex items-center gap-2">
                                <div class="w-2 h-2 rounded-full bg-primary" v-if="!email.is_read"></div>
                                <div class="text-sm font-bold text-gray-900 dark:text-white truncate">{{ getSenderName(email.sender) }}</div>
                            </div>
                            <span class="text-xs text-gray-400">{{ formatTime(email.received_at) }}</span>
                        </div>
                        <div class="text-xs text-gray-500 mb-2 truncate">{{ email.subject }}</div>
                        <div v-if="email.verification_code" class="flex items-center gap-2">
                            <span class="px-2 py-0.5 bg-primary/10 text-primary text-xs font-bold font-mono rounded">{{ email.verification_code }}</span>
                            <button @click.stop="copyCode(email.verification_code)" class="text-gray-400 hover:text-primary">
                                <Check v-if="copiedCode === email.verification_code" class="w-3 h-3 text-green-500" />
                                <Copy v-else class="w-3 h-3" />
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 第三栏：详情 -->
            <div class="pool-detail flex-1 h-full flex flex-col min-w-0">
                <div class="pool-detail-header h-14 border-b border-gray-200 dark:border-border-dark flex items-center justify-end px-6 gap-3 shrink-0">
                    <button @click="isHistoryOpen = true" class="btn-tool">
                        <History class="w-4 h-4" /> 历史
                    </button>
                    <button @click="isStatsOpen = true" class="btn-tool">
                        <BarChart class="w-4 h-4" /> 统计
                    </button>
                    <button @click="isGenerateOpen = true"
                        class="flex items-center gap-2 px-4 py-1.5 bg-primary text-white rounded-lg hover:bg-primary-hover shadow-md shadow-primary/20 transition-all font-medium text-sm ml-2">
                        <Plus class="w-4 h-4" /> 生成临时邮箱
                    </button>
                </div>

                <div class="flex-1 p-10 overflow-y-auto flex flex-col">
                    <template v-if="selectedEmail">
                        <div class="flex items-start justify-between mb-10">
                            <div class="flex items-center gap-4">
                                <div class="w-14 h-14 rounded-full bg-primary flex items-center justify-center text-2xl text-white font-bold shadow-lg shadow-primary/20">
                                    {{ getInitial(getSenderName(selectedEmail.sender)) }}
                                </div>
                                <div>
                                    <div class="text-2xl font-bold text-gray-900 dark:text-white mb-1">{{ getSenderName(selectedEmail.sender) }}</div>
                                    <div class="text-sm text-gray-400">{{ formatTime(selectedEmail.received_at) }}</div>
                                </div>
                            </div>
                            <div class="flex gap-2">
                                <button class="icon-btn"><Star class="w-5 h-5" /></button>
                                <button class="icon-btn"><Trash2 class="w-5 h-5" /></button>
                            </div>
                        </div>
                        <div class="font-bold text-gray-900 dark:text-white mb-4">{{ selectedEmail.subject }}</div>
                        
                        <!-- 验证码展示 -->
                        <div v-if="selectedEmail.verification_code"
                            class="bg-purple-50/50 dark:bg-purple-900/10 border border-purple-100 dark:border-purple-900/30 rounded-2xl p-12 flex flex-col items-center justify-center relative overflow-hidden group border-dashed">
                            <div class="text-sm text-gray-500 mb-4">验证码 (已自动识别)</div>
                            <div class="text-7xl font-mono font-bold text-primary tracking-widest mb-8 drop-shadow-sm">{{ selectedEmail.verification_code }}</div>
                            <button @click="copyCode(selectedEmail.verification_code!)"
                                class="flex items-center gap-2 px-8 py-3 bg-primary text-white rounded-xl hover:bg-primary-hover shadow-xl shadow-primary/30 transition-all active:scale-95 text-lg font-medium">
                                <Check v-if="copiedCode === selectedEmail.verification_code" class="w-5 h-5" />
                                <Copy v-else class="w-5 h-5" />
                                {{ copiedCode === selectedEmail.verification_code ? '已复制' : '复制' }}
                            </button>
                        </div>
                        <div v-else class="bg-gray-50 dark:bg-gray-800/50 rounded-2xl p-8 text-center text-gray-500">
                            未检测到验证码
                        </div>
                    </template>
                    <template v-else>
                        <div class="flex-1 flex flex-col items-center justify-center text-gray-400">
                            <Mail class="w-20 h-20 opacity-10 mb-6" />
                            <p class="text-lg">选择一封邮件查看验证码</p>
                        </div>
                    </template>
                </div>
            </div>
        </template>

        <!-- 弹窗 -->
        <PoolCreateModal @created="loadMailboxes(); loadStats()" />
        <PoolHistoryModal />
        <PoolStatsModal />
    </div>
</template>

<style scoped>
.btn-tool {
    @apply flex items-center gap-2 px-3 py-1.5 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg text-sm transition-colors border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900;
}

.icon-btn {
    @apply p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg text-gray-400 transition-colors;
}
</style>