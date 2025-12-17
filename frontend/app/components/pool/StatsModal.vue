<script setup lang="ts">
import { Mail, Zap, CheckCircle2 } from 'lucide-vue-next'
const { isStatsOpen } = useGlobalModal()
</script>

<template>
    <CommonModal v-model="isStatsOpen" title="账号池使用统计" widthClass="w-full max-w-3xl">
        <!-- 数据卡片 -->
        <div class="grid grid-cols-3 gap-4 mb-8">
            <div
                class="p-6 bg-purple-50 dark:bg-purple-900/10 rounded-2xl flex flex-col items-center justify-center text-center">
                <div class="text-3xl font-bold text-primary mb-1">3</div>
                <div class="text-xs text-gray-500 font-medium">总账号数</div>
            </div>
            <div
                class="p-6 bg-green-50 dark:bg-green-900/10 rounded-2xl flex flex-col items-center justify-center text-center">
                <div class="text-3xl font-bold text-green-500 mb-1">3</div>
                <div class="text-xs text-gray-500 font-medium">活跃账号</div>
            </div>
            <div
                class="p-6 bg-blue-50 dark:bg-blue-900/10 rounded-2xl flex flex-col items-center justify-center text-center">
                <div class="text-3xl font-bold text-blue-500 mb-1">3</div>
                <div class="text-xs text-gray-500 font-medium">今日验证码</div>
            </div>
        </div>

        <!-- 最近活动 -->
        <div>
            <h4 class="text-sm font-bold text-gray-900 dark:text-white mb-4">最近活动</h4>
            <div class="space-y-3">
                <div class="flex items-center justify-between text-sm">
                    <div class="flex items-center gap-3">
                        <div class="p-1.5 bg-gray-100 rounded-md">
                            <Mail class="w-4 h-4 text-gray-500" />
                        </div>
                        <span class="text-gray-700 dark:text-gray-300">test001@mymail.com</span>
                    </div>
                    <span class="text-gray-400 text-xs">刚刚</span>
                </div>
                <div class="flex items-center justify-between text-sm">
                    <div class="flex items-center gap-3">
                        <div class="p-1.5 bg-gray-100 rounded-md">
                            <Mail class="w-4 h-4 text-gray-500" />
                        </div>
                        <span class="text-gray-700 dark:text-gray-300">register02@mymail.com</span>
                    </div>
                    <span class="text-gray-400 text-xs">5分钟前</span>
                </div>
            </div>
        </div>
    </CommonModal>
</template>