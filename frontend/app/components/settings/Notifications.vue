<script setup lang="ts">
import { BellRing, Volume2, Smartphone } from 'lucide-vue-next'
</script>

<template>
    <div class="space-y-8">
        <h2 class="section-title">通知偏好</h2>

        <div
            class="bg-white dark:bg-bg-panelDark rounded-xl border border-gray-200 dark:border-border-dark divide-y divide-gray-100 dark:divide-gray-800">

            <!-- 桌面通知 -->
            <div class="p-6 flex items-center justify-between">
                <div class="flex gap-4">
                    <div class="p-2 bg-green-100 text-green-600 rounded-lg h-fit">
                        <BellRing class="w-5 h-5" />
                    </div>
                    <div>
                        <div class="font-bold text-gray-900 dark:text-white">桌面通知</div>
                        <div class="text-sm text-gray-500">收到新邮件时在浏览器显示弹窗</div>
                    </div>
                </div>
                <input type="checkbox" checked class="accent-primary w-5 h-5">
            </div>

            <!-- 提示音 -->
            <div class="p-6 flex items-center justify-between">
                <div class="flex gap-4">
                    <div class="p-2 bg-yellow-100 text-yellow-600 rounded-lg h-fit">
                        <Volume2 class="w-5 h-5" />
                    </div>
                    <div>
                        <div class="font-bold text-gray-900 dark:text-white">提示音效</div>
                        <div class="text-sm text-gray-500">播放 "Ding" 提示音</div>
                    </div>
                </div>
                <input type="checkbox" checked class="accent-primary w-5 h-5">
            </div>

            <!-- 账号池通知 -->
            <div class="p-6 flex items-center justify-between">
                <div class="flex gap-4">
                    <div class="p-2 bg-purple-100 text-purple-600 rounded-lg h-fit">
                        <Smartphone class="w-5 h-5" />
                    </div>
                    <div>
                        <div class="font-bold text-gray-900 dark:text-white">账号池验证码推送</div>
                        <div class="text-sm text-gray-500">当临时账号收到验证码时，发送系统级通知</div>
                    </div>
                </div>
                <input type="checkbox" class="accent-primary w-5 h-5">
            </div>

        </div>
    </div>
</template>

<style scoped>
.section-title {
    @apply text-2xl font-bold text-gray-900 dark:text-white mb-6;
}
</style>