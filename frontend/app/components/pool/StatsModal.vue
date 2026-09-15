<script setup lang="ts">
import { Mail, Inbox, MailOpen, Calendar } from 'lucide-vue-next'
const { isStatsOpen } = useGlobalModal()
const { getPoolStats } = useApi()
const toast = useToast()
const { t } = useI18n()

interface Stats {
    total_mailboxes: number
    active_mailboxes: number
    total_emails: number
    unread_emails: number
    today_emails: number
    recent_emails: Array<{
        id: number
        mailbox: string
        sender: string
        subject: string
        received_at: string | null
    }>
}

const stats = ref<Stats | null>(null)
const loading = ref(false)

const loadStats = async () => {
    loading.value = true
    try {
        stats.value = await getPoolStats()
    } catch (e: any) {
        console.error('加载统计失败', e)
        toast.error(e.data?.detail || t('pool.loadStatsFailed'))
    } finally {
        loading.value = false
    }
}

const formatTime = (dateStr: string | null) => {
    if (!dateStr) return '-'
    const date = new Date(dateStr)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    if (diff < 60000) return t('pool.justNow')
    if (diff < 3600000) return t('pool.minutesAgo', { n: Math.floor(diff / 60000) })
    if (diff < 86400000) return t('pool.hoursAgo', { n: Math.floor(diff / 3600000) })
    return date.toLocaleDateString()
}

const getSenderName = (sender: string) => sender?.split('<')[0]?.trim() || sender || t('pool.unknown')

watch(isStatsOpen, (val) => {
    if (val) loadStats()
})
</script>

<template>
    <CommonModal v-model="isStatsOpen" :title="t('pool.statsModal.title')" widthClass="w-full max-w-3xl">
        <!-- 加载中 -->
        <div v-if="loading" class="py-12 text-center text-gray-400">{{ t('common.loading') }}</div>

        <template v-else-if="stats">
            <!-- 数据卡片 -->
            <div class="grid grid-cols-4 gap-4 mb-8">
                <div class="p-5 bg-purple-50 dark:bg-purple-900/10 rounded-2xl flex flex-col items-center justify-center text-center">
                    <Inbox class="w-6 h-6 text-primary mb-2" />
                    <div class="text-2xl font-bold text-primary mb-1">{{ stats.active_mailboxes }}</div>
                    <div class="text-xs text-gray-500">{{ t('pool.statsModal.activeMailboxes') }}</div>
                </div>
                <div class="p-5 bg-blue-50 dark:bg-blue-900/10 rounded-2xl flex flex-col items-center justify-center text-center">
                    <Mail class="w-6 h-6 text-blue-500 mb-2" />
                    <div class="text-2xl font-bold text-blue-500 mb-1">{{ stats.total_emails }}</div>
                    <div class="text-xs text-gray-500">{{ t('pool.statsModal.totalEmails') }}</div>
                </div>
                <div class="p-5 bg-orange-50 dark:bg-orange-900/10 rounded-2xl flex flex-col items-center justify-center text-center">
                    <MailOpen class="w-6 h-6 text-orange-500 mb-2" />
                    <div class="text-2xl font-bold text-orange-500 mb-1">{{ stats.unread_emails }}</div>
                    <div class="text-xs text-gray-500">{{ t('pool.unread') }}</div>
                </div>
                <div class="p-5 bg-green-50 dark:bg-green-900/10 rounded-2xl flex flex-col items-center justify-center text-center">
                    <Calendar class="w-6 h-6 text-green-500 mb-2" />
                    <div class="text-2xl font-bold text-green-500 mb-1">{{ stats.today_emails }}</div>
                    <div class="text-xs text-gray-500">{{ t('pool.statsModal.todayEmails') }}</div>
                </div>
            </div>

            <!-- 最近活动 -->
            <div>
                <h4 class="text-sm font-bold text-gray-900 dark:text-white mb-4">{{ t('pool.statsModal.recentEmails') }}</h4>
                <div v-if="stats.recent_emails.length === 0" class="text-center text-gray-400 py-8">
                    {{ t('pool.statsModal.empty') }}
                </div>
                <div v-else class="space-y-3">
                    <div v-for="email in stats.recent_emails" :key="email.id" class="flex items-center justify-between text-sm p-3 bg-gray-50 dark:bg-gray-800/50 rounded-xl">
                        <div class="flex items-center gap-3 min-w-0 flex-1">
                            <div class="p-2 bg-white dark:bg-gray-700 rounded-lg shrink-0">
                                <Mail class="w-4 h-4 text-gray-500" />
                            </div>
                            <div class="min-w-0 flex-1">
                                <div class="text-gray-900 dark:text-white font-medium truncate">{{ getSenderName(email.sender) }}</div>
                                <div class="text-xs text-gray-400 truncate">{{ email.mailbox }}</div>
                            </div>
                        </div>
                        <span class="text-gray-400 text-xs shrink-0 ml-4">{{ formatTime(email.received_at) }}</span>
                    </div>
                </div>
            </div>
        </template>
    </CommonModal>
</template>
