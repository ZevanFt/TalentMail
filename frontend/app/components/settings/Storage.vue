<script setup lang="ts">
import { HardDrive, Archive, Trash2, AlertTriangle, Mail, Crown, Ticket, Clock, Infinity } from 'lucide-vue-next'

const { getStorageStats, getSubscriptionStatus, redeemCode, getRedemptionHistory, getMe, updateMe } = useApi()

const loading = ref(true)
const stats = ref({
    storage_used_bytes: 0,
    storage_limit_bytes: 10 * 1024 * 1024 * 1024,
    email_count: 0,
    email_bytes: 0
})

// 订阅状态
const subscription = ref<any>(null)
const redeemCodeInput = ref('')
const redeeming = ref(false)
const redeemError = ref('')
const redeemSuccess = ref('')
const history = ref<any[]>([])
const showHistory = ref(false)

// 自动清理设置
const user = ref<any>(null)

const loadStats = async () => {
    try {
        stats.value = await getStorageStats()
    } catch (e: any) {
        console.error('加载存储统计失败', e)
    } finally {
        loading.value = false
    }
}

const loadSubscription = async () => {
    try {
        subscription.value = await getSubscriptionStatus()
    } catch (e: any) {
        console.error('加载订阅状态失败', e)
    }
}

const loadUser = async () => {
    try {
        user.value = await getMe()
    } catch (e) {
        console.error('加载用户信息失败', e)
    }
}

const loadHistory = async () => {
    try {
        history.value = await getRedemptionHistory()
    } catch (e) {
        console.error('加载兑换历史失败', e)
    }
}

const updateCleanSetting = async (key: string, value: boolean) => {
    if (!user.value) return
    const oldValue = user.value[key]
    user.value[key] = value
    try {
        await updateMe({ [key]: value })
    } catch (e) {
        console.error('更新设置失败', e)
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
        redeemError.value = e.data?.detail || '兑换失败'
    } finally {
        redeeming.value = false
    }
}

// 格式化字节
const formatBytes = (bytes: number) => {
    if (bytes === -1) return '无限'
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

const formatDate = (date: string | null) => {
    if (!date) return '-'
    return new Date(date).toLocaleDateString('zh-CN')
}

onMounted(async () => {
    await Promise.all([loadStats(), loadSubscription(), loadHistory(), loadUser()])
})
</script>

<template>
    <div class="space-y-8">
        <h2 class="section-title">存储与配额</h2>

        <div v-if="loading" class="text-gray-500">加载中...</div>

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
                                <span v-if="subscription.is_admin" class="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full">管理员</span>
                            </div>
                            <div class="text-sm text-gray-500">
                                <template v-if="subscription.is_admin">无限制</template>
                                <template v-else-if="subscription.expires_at">
                                    到期时间：{{ formatDate(subscription.expires_at) }}
                                    <span v-if="subscription.days_remaining !== null" class="text-primary">(剩余 {{ subscription.days_remaining }} 天)</span>
                                </template>
                                <template v-else>免费套餐</template>
                            </div>
                        </div>
                    </div>
                    <button @click="showHistory = !showHistory" class="text-sm text-primary hover:underline">
                        {{ showHistory ? '隐藏历史' : '兑换历史' }}
                    </button>
                </div>

                <!-- 配额使用情况 -->
                <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                    <div class="stat-box">
                        <div class="text-xs text-gray-500 mb-1">存储空间</div>
                        <div class="font-bold text-gray-900 dark:text-white text-sm">
                            {{ formatBytes(subscription.storage_used_bytes) }} /
                            <span :class="subscription.storage_quota_bytes === -1 ? 'text-purple-500' : ''">
                                {{ formatBytes(subscription.storage_quota_bytes) }}
                            </span>
                        </div>
                    </div>
                    <div class="stat-box">
                        <div class="text-xs text-gray-500 mb-1">临时邮箱</div>
                        <div class="font-bold text-gray-900 dark:text-white text-sm">
                            {{ subscription.current_temp_mailboxes }} /
                            <span :class="subscription.max_temp_mailboxes === -1 ? 'text-purple-500' : ''">
                                {{ subscription.max_temp_mailboxes === -1 ? '∞' : subscription.max_temp_mailboxes }}
                            </span>
                        </div>
                    </div>
                    <div class="stat-box">
                        <div class="text-xs text-gray-500 mb-1">别名数量</div>
                        <div class="font-bold text-gray-900 dark:text-white text-sm">
                            {{ subscription.current_aliases }} /
                            <span :class="subscription.max_aliases === -1 ? 'text-purple-500' : ''">
                                {{ subscription.max_aliases === -1 ? '∞' : subscription.max_aliases }}
                            </span>
                        </div>
                    </div>
                    <div class="stat-box">
                        <div class="text-xs text-gray-500 mb-1">域名数量</div>
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
                        <input v-model="redeemCodeInput" type="text" class="input-field flex-1" placeholder="输入兑换码激活/续费订阅" @keyup.enter="handleRedeem">
                        <button @click="handleRedeem" :disabled="redeeming || !redeemCodeInput.trim()" class="btn-primary flex items-center gap-2">
                            <Ticket class="w-4 h-4" />
                            {{ redeeming ? '兑换中...' : '兑换' }}
                        </button>
                    </div>
                    <div v-if="redeemError" class="text-red-500 text-sm mt-2">{{ redeemError }}</div>
                    <div v-if="redeemSuccess" class="text-green-500 text-sm mt-2">{{ redeemSuccess }}</div>
                </div>

                <!-- 兑换历史 -->
                <div v-if="showHistory && history.length > 0" class="border-t border-gray-100 dark:border-gray-800 pt-4 mt-4">
                    <h4 class="text-sm font-bold text-gray-700 dark:text-gray-300 mb-2">兑换历史</h4>
                    <div class="space-y-2 max-h-40 overflow-y-auto">
                        <div v-for="item in history" :key="item.code" class="flex justify-between text-sm text-gray-600 dark:text-gray-400">
                            <span class="font-mono">{{ item.code }}</span>
                            <span>{{ item.plan_name }} · {{ item.duration_days }}天 · {{ formatDate(item.used_at) }}</span>
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
                            <template v-if="subscription?.is_admin || subscription?.storage_quota_bytes === -1">无限存储空间</template>
                            <template v-else>已使用 {{ usagePercent }}% 的存储空间</template>
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
                        <div class="w-2 h-2 rounded-full bg-primary"></div> 邮件 ({{ formatBytes(stats.email_bytes) }})
                    </div>
                </div>

                <!-- 分类统计 -->
                <div class="grid grid-cols-2 gap-4">
                    <div class="stat-box">
                        <div class="flex items-center gap-2 mb-1 text-gray-500 text-xs">
                            <Mail class="w-3.5 h-3.5" /> 邮件数量
                        </div>
                        <div class="font-bold text-gray-900 dark:text-white">{{ stats.email_count }} 封</div>
                    </div>
                    <div class="stat-box">
                        <div class="flex items-center gap-2 mb-1 text-gray-500 text-xs">
                            <HardDrive class="w-3.5 h-3.5" /> 邮件占用
                        </div>
                        <div class="font-bold text-gray-900 dark:text-white">{{ formatBytes(stats.email_bytes) }}</div>
                    </div>
                </div>
            </div>

        <!-- 2. 自动清理规则 -->
        <div class="card space-y-6">
            <div class="flex items-center gap-2 mb-2">
                <h3 class="font-bold text-gray-900 dark:text-white">自动清理策略</h3>
                <span
                    class="text-xs bg-yellow-100 text-yellow-700 px-2 py-0.5 rounded border border-yellow-200">推荐开启</span>
            </div>

            <!-- 垃圾箱清理 -->
            <div
                class="flex items-center justify-between p-3 hover:bg-gray-50 dark:hover:bg-gray-800/50 rounded-lg transition-colors">
                <div class="flex gap-4">
                    <div class="p-2 bg-red-100 dark:bg-red-900/20 text-red-500 rounded-lg h-fit">
                        <Trash2 class="w-5 h-5" />
                    </div>
                    <div>
                        <div class="font-medium text-gray-900 dark:text-white">自动清空垃圾箱</div>
                        <div class="text-sm text-gray-500">永久删除超过 30 天的垃圾邮件</div>
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
                        <div class="font-medium text-gray-900 dark:text-white">历史邮件归档</div>
                        <div class="text-sm text-gray-500">自动归档 1 年前的旧邮件以节省收件箱空间</div>
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
                    <h4 class="font-bold text-gray-900 dark:text-white text-sm">空间不足？</h4>
                    <p class="text-xs text-gray-600 dark:text-gray-300 mt-1 mb-3">
                        升级套餐可获得更多存储空间和功能。请联系管理员获取兑换码。
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