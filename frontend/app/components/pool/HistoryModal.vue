<script setup lang="ts">
import { Plus, Trash2 } from 'lucide-vue-next'
const { isHistoryOpen } = useGlobalModal()
const { getPoolActivityLogs } = useApi()

interface ActivityLog {
    id: number
    action: string
    mailbox_email: string
    details: string | null
    created_at: string | null
}

const logs = ref<ActivityLog[]>([])
const loading = ref(false)

const loadLogs = async () => {
    loading.value = true
    try {
        const res = await getPoolActivityLogs()
        logs.value = res.items
    } catch (e) {
        console.error('加载日志失败', e)
    } finally {
        loading.value = false
    }
}

const formatTime = (dateStr: string | null) => {
    if (!dateStr) return '-'
    const date = new Date(dateStr)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    if (diff < 60000) return '刚刚'
    if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
    return date.toLocaleDateString('zh-CN') + ' ' + date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

const getActionText = (action: string) => action === 'create' ? '创建' : '删除'
const getActionColor = (action: string) => action === 'create' ? 'text-green-500 bg-green-50 dark:bg-green-900/20' : 'text-red-500 bg-red-50 dark:bg-red-900/20'

watch(isHistoryOpen, (val) => {
    if (val) loadLogs()
})
</script>

<template>
    <CommonModal v-model="isHistoryOpen" title="操作日志" widthClass="w-full max-w-2xl">
        <div v-if="loading" class="py-12 text-center text-gray-400">加载中...</div>
        <div v-else-if="logs.length === 0" class="py-12 text-center text-gray-400">暂无操作记录</div>
        <div v-else class="space-y-3">
            <div v-for="log in logs" :key="log.id"
                class="flex items-center justify-between p-4 border border-gray-100 dark:border-gray-700 rounded-xl">
                <div class="flex items-center gap-4">
                    <div class="w-10 h-10 rounded-full flex items-center justify-center" :class="getActionColor(log.action)">
                        <Plus v-if="log.action === 'create'" class="w-5 h-5" />
                        <Trash2 v-else class="w-5 h-5" />
                    </div>
                    <div>
                        <div class="font-medium text-gray-900 dark:text-white">
                            {{ getActionText(log.action) }} <span class="font-mono text-primary">{{ log.mailbox_email }}</span>
                        </div>
                        <div class="text-xs text-gray-500 mt-0.5">
                            {{ formatTime(log.created_at) }}
                            <span v-if="log.details" class="ml-2">· {{ log.details }}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </CommonModal>
</template>