<script setup lang="ts">
import { PenTool, Calendar, Server, ToggleLeft, ToggleRight, Plus } from 'lucide-vue-next'
const autoReply = ref(false)
</script>

<template>
    <div class="space-y-8">
        <h2 class="section-title">邮件设置</h2>

        <!-- 1. 签名管理 -->
        <section class="card">
            <div class="card-header">
                <div class="flex items-center gap-3">
                    <div class="icon-box bg-blue-100 text-blue-600 dark:bg-blue-900/30">
                        <PenTool class="w-5 h-5" />
                    </div>
                    <div>
                        <h3 class="font-bold text-gray-900 dark:text-white">邮件签名</h3>
                        <p class="text-xs text-gray-500">发送邮件时自动附加的内容</p>
                    </div>
                </div>
                <button class="btn-secondary text-xs">
                    <Plus class="w-3 h-3 mr-1" /> 新增签名
                </button>
            </div>

            <!-- 模拟富文本编辑器 -->
            <div class="mt-4 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
                <div
                    class="bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-3 py-2 flex gap-3 text-gray-500">
                    <span class="font-bold cursor-pointer hover:text-gray-800">B</span>
                    <span class="italic cursor-pointer hover:text-gray-800">I</span>
                    <span class="underline cursor-pointer hover:text-gray-800">U</span>
                </div>
                <textarea class="w-full h-24 p-3 bg-white dark:bg-gray-900 outline-none text-sm resize-none"
                    placeholder="在此输入您的签名..."></textarea>
            </div>
        </section>

        <!-- 2. 自动回复 -->
        <section class="card">
            <div class="card-header">
                <div class="flex items-center gap-3">
                    <div class="icon-box bg-purple-100 text-purple-600 dark:bg-purple-900/30">
                        <Calendar class="w-5 h-5" />
                    </div>
                    <div>
                        <h3 class="font-bold text-gray-900 dark:text-white">自动回复 / 休假模式</h3>
                        <p class="text-xs text-gray-500">在特定时间段自动回复收到的邮件</p>
                    </div>
                </div>
                <button @click="autoReply = !autoReply" :class="autoReply ? 'text-primary' : 'text-gray-400'">
                    <ToggleRight v-if="autoReply" class="w-8 h-8" />
                    <ToggleLeft v-else class="w-8 h-8" />
                </button>
            </div>

            <div v-if="autoReply" class="mt-4 space-y-3 pt-4 border-t border-gray-100 dark:border-gray-800">
                <div class="grid grid-cols-2 gap-4">
                    <div class="space-y-1">
                        <label class="text-xs text-gray-500">开始时间</label>
                        <input type="date" class="input-field">
                    </div>
                    <div class="space-y-1">
                        <label class="text-xs text-gray-500">结束时间</label>
                        <input type="date" class="input-field">
                    </div>
                </div>
                <textarea class="input-field h-20" placeholder="自动回复内容：您好，我现在不在办公室..."></textarea>
            </div>
        </section>

        <!-- 3. 服务器设置 -->
        <section class="card">
            <div class="card-header">
                <div class="flex items-center gap-3">
                    <div class="icon-box bg-orange-100 text-orange-600 dark:bg-orange-900/30">
                        <Server class="w-5 h-5" />
                    </div>
                    <div>
                        <h3 class="font-bold text-gray-900 dark:text-white">POP / IMAP / SMTP</h3>
                        <p class="text-xs text-gray-500">配置第三方客户端连接</p>
                    </div>
                </div>
            </div>
            <div class="mt-4 space-y-4">
                <div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
                    <div class="text-sm font-medium dark:text-white">启用 IMAP 服务</div>
                    <div class="text-green-500 text-sm font-bold">已开启</div>
                </div>
                <div class="text-xs text-gray-500 font-mono bg-gray-100 dark:bg-gray-900 p-3 rounded select-all">
                    IMAP Server: mail.talenting.vip (Port: 993)<br>
                    SMTP Server: mail.talenting.vip (Port: 465)
                </div>
            </div>
        </section>
    </div>
</template>

<style scoped>
/* 通用样式，建议提取到全局 CSS，这里为了方便直接写 */
.section-title {
    @apply text-2xl font-bold text-gray-900 dark:text-white mb-6;
}

.card {
    @apply bg-white dark:bg-bg-panelDark rounded-xl border border-gray-200 dark:border-border-dark p-6;
}

.card-header {
    @apply flex items-center justify-between;
}

.icon-box {
    @apply p-2 rounded-lg;
}

.input-field {
    @apply w-full px-4 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none text-sm dark:text-white transition-all;
}

.btn-secondary {
    @apply px-3 py-1.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors flex items-center text-gray-700 dark:text-gray-300;
}
</style>