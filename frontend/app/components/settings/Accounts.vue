<script setup lang="ts">
import { User, Plus, MoreHorizontal, Copy } from 'lucide-vue-next'
</script>

<template>
    <div class="space-y-8">
        <div class="flex justify-between items-center">
            <h2 class="section-title mb-0">多账号管理</h2>
            <button
                class="bg-primary text-white px-4 py-2 rounded-lg text-sm hover:bg-primary-hover flex items-center gap-2">
                <Plus class="w-4 h-4" /> 添加账号
            </button>
        </div>

        <!-- 主账号 -->
        <div class="card border-primary/30 relative overflow-hidden">
            <div class="absolute top-0 right-0 bg-primary text-white text-xs px-2 py-1 rounded-bl-lg">当前</div>
            <div class="flex items-center gap-4">
                <div
                    class="w-12 h-12 rounded-full bg-primary flex items-center justify-center text-white text-xl font-bold">
                    T</div>
                <div>
                    <div class="font-bold text-gray-900 dark:text-white text-lg">Talent</div>
                    <div class="text-gray-500">me@talenting.vip</div>
                </div>
            </div>
        </div>

        <!-- 别名管理 -->
        <div class="card">
            <h3 class="font-bold text-gray-900 dark:text-white mb-4">邮件别名 (Aliases)</h3>
            <div class="space-y-3">
                <div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <div class="flex items-center gap-3">
                        <span class="text-sm font-mono dark:text-gray-300">support@talenting.vip</span>
                        <span
                            class="bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300 text-[10px] px-1.5 py-0.5 rounded">工作</span>
                    </div>
                    <button class="text-gray-400 hover:text-red-500">
                        <MoreHorizontal class="w-4 h-4" />
                    </button>
                </div>
                <div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <div class="flex items-center gap-3">
                        <span class="text-sm font-mono dark:text-gray-300">shop@talenting.vip</span>
                        <span
                            class="bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300 text-[10px] px-1.5 py-0.5 rounded">购物</span>
                    </div>
                    <button class="text-gray-400 hover:text-red-500">
                        <MoreHorizontal class="w-4 h-4" />
                    </button>
                </div>
            </div>
            <button
                class="mt-4 w-full py-2 border border-dashed border-gray-300 dark:border-gray-600 text-gray-500 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 text-sm transition-colors">
                + 添加新别名
            </button>
        </div>
    </div>
</template>

<style scoped>
.section-title {
    @apply text-2xl font-bold text-gray-900 dark:text-white mb-6;
}

.card {
    @apply bg-white dark:bg-bg-panelDark rounded-xl border border-gray-200 dark:border-border-dark p-6;
}
</style>