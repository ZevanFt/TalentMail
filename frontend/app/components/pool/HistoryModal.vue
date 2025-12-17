<script setup lang="ts">
import { Copy, Clock } from 'lucide-vue-next'
const { isHistoryOpen } = useGlobalModal()

const history = [
    { id: 1, service: 'Steam', code: '847291', email: 'test001@mymail.com', time: '刚刚' },
    { id: 2, service: 'Discord', code: '582034', email: 'test001@mymail.com', time: '2分钟前' },
    { id: 3, service: 'Twitter', code: 'KC84HT', email: 'test001@mymail.com', time: '10分钟前' },
]
</script>

<template>
    <CommonModal v-model="isHistoryOpen" title="验证码历史记录" widthClass="w-full max-w-2xl">
        <div class="space-y-3">
            <div v-for="item in history" :key="item.id"
                class="flex items-center justify-between p-4 border border-gray-100 dark:border-gray-700 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
                <div class="flex items-center gap-4">
                    <div
                        class="w-10 h-10 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center text-gray-500">
                        {{ item.service[0] }}
                    </div>
                    <div>
                        <div class="font-bold text-gray-900 dark:text-white">{{ item.service }}</div>
                        <div class="text-xs text-gray-500 mt-0.5">{{ item.time }} · {{ item.email }}</div>
                    </div>
                </div>

                <div class="flex items-center gap-3">
                    <div
                        class="px-3 py-1 bg-purple-50 dark:bg-purple-900/20 text-primary font-bold font-mono rounded-md">
                        {{ item.code }}
                    </div>
                    <button
                        class="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors">
                        <Copy class="w-4 h-4" />
                    </button>
                </div>
            </div>
        </div>
    </CommonModal>
</template>