<script setup lang="ts">
import { HardDrive, Archive, Trash2, AlertTriangle, Mail, Crown, Ticket, Clock, Infinity } from 'lucide-vue-next'

const { getStorageStats, getSubscriptionStatus, redeemCode, getRedemptionHistory, getMe, updateMe } = useApi()
const toast = useToast()
const { t } = useI18n()

const loading = ref(true)
const stats = ref({
    storage_used_bytes: 0,
    storage_limit_bytes: 10 * 1024 * 1024 * 1024,
    email_count: 0,
    email_bytes: 0
})

// 订阅状态
const subscription = ref<Subscription | null>(null)
const redeemCodeInput = ref('')
const redeeming = ref(false)
const redeemError = ref('')
const redeemSuccess = ref('')
const history = ref<any[]>([])
const showHistory = ref(false)

// 自动清理设置
const user = ref<AppUser | null>(null)

const loadStats = async () => {
    try {
        stats.value = await getStorageStats()
    } catch (e: any) {
        console.error('加载存储统计失败', e)
        toast.error(e.data?.detail || t('settings.storage.loadStatsFailed'))
    } finally {
        loading.value = false
    }
}

const loadSubscription = async () => {
    try {
        subscription.value = await getSubscriptionStatus()
    } catch (e: any) {
        console.error('加载订阅状态失败', e)
        toast.error(e.data?.detail || t('settings.storage.loadSubFailed'))
    }
}

const loadUser = async () => {
    try {
        user.value = await getMe()
    } catch (e: any) {
        console.error('加载用户信息失败', e)
        toast.error(e.data?.detail || t('settings.common.loadUserFailed'))
    }
}

const loadHistory = async () => {
    try {
        history.value = await getRedemptionHistory()
    } catch (e: any) {
        console.error('加载兑换历史失败', e)
        toast.error(e.data?.detail || t('settings.storage.loadHistoryFailed'))
    }
}

const updateCleanSetting = async (key: string, value: boolean) => {
    if (!user.value) return
    const oldValue = user.value[key]
    user.value[key] = value
    try {
        await updateMe({ [key]: value })
    } catch (e: any) {
        console.error('更新设置失败', e)
        toast.error(e.data?.detail || t('settings.storage.updateFailed'))
        user.value[key] = oldValue
    }
}

const handleRedeem = async () => {
    if (!redeemCodeInput.value.trim()) return
    redeeming.value = true
    redeemError.value = ''
    redeemSuccess.value = ''
    try {
        const result = await redeemCode(redeemCodeInput.value.trim())
        redeemSuccess.value = result.message
        redeemCodeInput.value = ''
        await loadSubscription()
        await loadHistory()
    } catch (e: any) {
        redeemError.value = e.data?.detail || t('settings.storage.redeemFailed')
    } finally {
        redeeming.value = false
    }
}

// 格式化字节
const formatBytes = (bytes: number) => {
    if (bytes === -1) return t('settings.storage.unlimitedBytes')
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

// 使用百分比
const usagePercent = computed(() => {
    if (subscription.value?.is_admin || subscription.value?.storage_quota_bytes === -1) return 0
    const limit = subscription.value?.storage_quota_bytes || stats.value.storage_limit_bytes
    return Math.round((stats.value.storage_used_bytes / limit) * 100)
})

// formatDate 来自 utils/format.ts (Nuxt 自动导入)

onMounted(async () => {
    await Promise.all([loadStats(), loadSubscription(), loadHistory(), loadUser()])
})
</script>

<template>
    <div class="space-y-8">
        <h2 class="section-title">{{ t('settings.tabs.storage') }}</h2>

        <div v-if="loading" class="text-gray-500">{{ t('settings.common.loading') }}</div>

        <template v-else>
            <!-- 0. 订阅状态卡片 -->
            <div class="card" v-if="subscription">
                <div class="flex items-center justify-between mb-4">
                    <div class="flex items-center gap-3">
                        <div :class="['p-3 rounded-xl', subscription.is_admin ? 'bg-purple-100 text-purple-600 dark:bg-purple-900/30' : subscription.has_subscription ? 'bg-yellow-100 text-yellow-600 dark:bg-yellow-900/30' : 'bg-gray-100 text-gray-600 dark:bg-gray-800']">
                            <Crown class="w-6 h-6" />
                        </div>
                        <div>
                            <div class="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
                                {{ subscription.plan?.name || 'Free' }}
                                <span v-if="subscription.is_admin" class="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full">{{ t('settings.storage.admin') }}</span>
                            </div>
                            <div class="text-sm text-gray-500">
                                <template v-if="subscription.is_admin">{{ t('settings.storage.unlimited') }}</template>
                                <template v-else-if="subscription.expires_at">
                                    {{ t('settings.storage.expiresAt', { date: formatDate(subscription.expires_at) }) }}
                                    <span v-if="subscription.days_remaining !== null" class="text-primary">{{ t('settings.storage.daysRemaining', { n: subscription.days_remaining }) }}</span>
                                </template>
                                <template v-else>{{ t('settings.storage.freePlan') }}</template>
                            </div>
                        </div>
                    </div>
                    <button @click="showHistory = !showHistory" class="text-sm text-primary hover:underline">
                        {{ showHistory ? t('settings.storage.hideHistory') : t('settings.storage.redemptionHistory') }}
                    </button>
                </div>

                <!-- 配额使用情况 -->
                <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                    <div class="stat-box">
                        <div class="text-xs text-gray-500 mb-1">{{ t('settings.storage.storageSpace') }}</div>
                        <div class="font-bold text-gray-900 dark:text-white text-sm">
                            {{ formatBytes(subscription.storage_used_bytes) }} /
                            <span :class="subscription.storage_quota_bytes === -1 ? 'text-purple-500' : ''">
                                {{ formatBytes(subscription.storage_quota_bytes) }}
                            </span>
                        </div>
                    </div>
                    <div class="stat-box">
                        <div class="text-xs text-gray-500 mb-1">{{ t('settings.storage.tempMailboxes') }}</div>
                        <div class="font-bold text-gray-900 dark:text-white text-sm">
                            {{ subscription.current_temp_mailboxes }} /
                            <span :class="subscription.max_temp_mailboxes === -1 ? 'text-purple-500' : ''">
                                {{ subscription.max_temp_mailboxes === -1 ? '∞' : subscription.max_temp_mailboxes }}
                            </span>
                        </div>
                    </div>
                    <div class="stat-box">
                        <div class="text-xs text-gray-500 mb-1">{{ t('settings.storage.aliases') }}</div>
                        <div class="font-bold text-gray-900 dark:text-white text-sm">
                            {{ subscription.current_aliases }} /
                            <span :class="subscription.max_aliases === -1 ? 'text-purple-500' : ''">
                                {{ subscription.max_aliases === -1 ? '∞' : subscription.max_aliases }}
                            </span>
                        </div>
                    </div>
                    <div class="stat-box">
                        <div class="text-xs text-gray-500 mb-1">{{ t('settings.storage.domains') }}</div>
                        <div class="font-bold text-gray-900 dark:text-white text-sm">
                            {{ subscription.current_domains }} /
                            <span :class="subscription.max_domains === -1 ? 'text-purple-500' : ''">
                                {{ subscription.max_domains === -1 ? '∞' : subscription.max_domains }}
                            </span>
                        </div>
                    </div>
                </div>

                <!-- 兑换码输入 -->
                <div class="border-t border-gray-100 dark:border-gray-800 pt-4">
                    <div class="flex gap-2">
                        <input v-model="redeemCodeInput" type="text" class="input-field flex-1" :placeholder="t('settings.storage.redeemPlaceholder')" @keyup.enter="handleRedeem">
                        <button @click="handleRedeem" :disabled="redeeming || !redeemCodeInput.trim()" class="btn-primary flex items-center gap-2">
                            <Ticket class="w-4 h-4" />
                            {{ redeeming ? t('settings.storage.redeeming') : t('settings.storage.redeem') }}
                        </button>
                    </div>
                    <div v-if="redeemError" class="text-red-500 text-sm mt-2">{{ redeemError }}</div>
                    <div v-if="redeemSuccess" class="text-green-500 text-sm mt-2">{{ redeemSuccess }}</div>
                </div>

                <!-- 兑换历史 -->
                <div v-if="showHistory && history.length > 0" class="border-t border-gray-100 dark:border-gray-800 pt-4 mt-4">
                    <h4 class="text-sm font-bold text-gray-700 dark:text-gray-300 mb-2">{{ t('settings.storage.redemptionHistory') }}</h4>
                    <div class="space-y-2 max-h-40 overflow-y-auto">
                        <div v-for="item in history" :key="item.code" class="flex justify-between text-sm text-gray-600 dark:text-gray-400">
                            <span class="font-mono">{{ item.code }}</span>
                            <span>{{ item.plan_name }} · {{ t('settings.storage.durationDays', { n: item.duration_days }) }} · {{ formatDate(item.used_at) }}</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 1. 空间使用概览卡片 -->
            <div class="card">
                <div class="flex items-center gap-4 mb-6">
                    <div class="p-3 bg-blue-100 text-blue-600 dark:bg-blue-900/30 rounded-xl">
                        <HardDrive class="w-6 h-6" />
                    </div>
                    <div>
                        <div class="text-2xl font-bold text-gray-900 dark:text-white flex items-baseline gap-2">
                            {{ formatBytes(stats.storage_used_bytes) }}
                            <span class="text-sm text-gray-500 font-normal">/ {{ formatBytes(subscription?.storage_quota_bytes || stats.storage_limit_bytes) }}</span>
                        </div>
                        <div class="text-sm text-gray-500">
                            <template v-if="subscription?.is_admin || subscription?.storage_quota_bytes === -1">{{ t('settings.storage.unlimitedStorage') }}</template>
                            <template v-else>{{ t('settings.storage.usedPercent', { n: usagePercent }) }}</template>
                        </div>
                    </div>
                </div>

                <!-- 进度条 -->
                <div v-if="!subscription?.is_admin && subscription?.storage_quota_bytes !== -1" class="w-full bg-gray-100 dark:bg-gray-700 rounded-full h-4 mb-2 overflow-hidden">
                    <div class="bg-primary h-full transition-all" :style="{ width: usagePercent + '%' }"></div>
                </div>

                <!-- 统计 -->
                <div class="flex gap-4 text-xs text-gray-500 mb-6">
                    <div class="flex items-center gap-1.5">
                        <div class="w-2 h-2 rounded-full bg-primary"></div> {{ t('settings.storage.mailUsage', { size: formatBytes(stats.email_bytes) }) }}
                    </div>
                </div>

                <!-- 分类统计 -->
                <div class="grid grid-cols-2 gap-4">
                    <div class="stat-box">
                        <div class="flex items-center gap-2 mb-1 text-gray-500 text-xs">
                            <Mail class="w-3.5 h-3.5" /> {{ t('settings.storage.emailCount') }}
                        </div>
                        <div class="font-bold text-gray-900 dark:text-white">{{ t('settings.storage.emailCountUnit', { n: stats.email_count }) }}</div>
                    </div>
                    <div class="stat-box">
                        <div class="flex items-center gap-2 mb-1 text-gray-500 text-xs">
                            <HardDrive class="w-3.5 h-3.5" /> {{ t('settings.storage.emailUsage') }}
                        </div>
                        <div class="font-bold text-gray-900 dark:text-white">{{ formatBytes(stats.email_bytes) }}</div>
                    </div>
                </div>
            </div>

        <!-- 2. 自动清理规则 -->
        <div class="card space-y-6">
            <div class="flex items-center gap-2 mb-2">
                <h3 class="font-bold text-gray-900 dark:text-white">{{ t('settings.storage.autoCleanTitle') }}</h3>
                <span
                    class="text-xs bg-yellow-100 text-yellow-700 px-2 py-0.5 rounded border border-yellow-200">{{ t('settings.storage.recommended') }}</span>
            </div>

            <!-- 垃圾箱清理 -->
            <div
                class="flex items-center justify-between p-3 hover:bg-gray-50 dark:hover:bg-gray-800/50 rounded-lg transition-colors">
                <div class="flex gap-4">
                    <div class="p-2 bg-red-100 dark:bg-red-900/20 text-red-500 rounded-lg h-fit">
                        <Trash2 class="w-5 h-5" />
                    </div>
                    <div>
                        <div class="font-medium text-gray-900 dark:text-white">{{ t('settings.storage.autoCleanTrash') }}</div>
                        <div class="text-sm text-gray-500">{{ t('settings.storage.autoCleanTrashDesc') }}</div>
                    </div>
                </div>
                <CommonToggle
                    :model-value="user?.auto_clean_trash ?? true"
                    @update:model-value="updateCleanSetting('auto_clean_trash', $event)"
                />
            </div>

            <!-- 邮件归档 -->
            <div
                class="flex items-center justify-between p-3 hover:bg-gray-50 dark:hover:bg-gray-800/50 rounded-lg transition-colors">
                <div class="flex gap-4">
                    <div class="p-2 bg-orange-100 dark:bg-orange-900/20 text-orange-500 rounded-lg h-fit">
                        <Archive class="w-5 h-5" />
                    </div>
                    <div>
                        <div class="font-medium text-gray-900 dark:text-white">{{ t('settings.storage.autoArchive') }}</div>
                        <div class="text-sm text-gray-500">{{ t('settings.storage.autoArchiveDesc') }}</div>
                    </div>
                </div>
                <CommonToggle
                    :model-value="user?.auto_archive_old ?? false"
                    @update:model-value="updateCleanSetting('auto_archive_old', $event)"
                />
            </div>
        </div>

            <!-- 3. 扩容提示 -->
            <div v-if="usagePercent > 80 && !subscription?.is_admin"
                class="bg-gradient-to-r from-primary/10 to-purple-500/10 border border-primary/20 rounded-xl p-4 flex items-start gap-3">
                <AlertTriangle class="w-5 h-5 text-primary shrink-0 mt-0.5" />
                <div>
                    <h4 class="font-bold text-gray-900 dark:text-white text-sm">{{ t('settings.storage.lowSpaceTitle') }}</h4>
                    <p class="text-xs text-gray-600 dark:text-gray-300 mt-1 mb-3">
                        {{ t('settings.storage.lowSpaceDesc') }}
                    </p>
                </div>
            </div>
        </template>
    </div>
</template>

<style scoped>
.section-title {
    @apply text-2xl font-bold text-gray-900 dark:text-white mb-6;
}

.card {
    @apply bg-white dark:bg-bg-panelDark rounded-xl border border-gray-200 dark:border-border-dark p-6;
}

.stat-box {
    @apply bg-gray-50 dark:bg-gray-800 rounded-lg p-3 text-center border border-gray-100 dark:border-gray-700;
}

.input-field {
    @apply px-3 py-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all text-gray-900 dark:text-white;
}

.btn-primary {
    @apply px-4 py-2 bg-primary text-white text-sm rounded-lg hover:bg-primary-hover transition-colors shadow-sm shadow-primary/20 disabled:opacity-50;
}
</style>