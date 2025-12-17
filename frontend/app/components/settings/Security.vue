<script setup lang="ts">
import { KeyRound, Smartphone, ShieldCheck, History, Laptop, Globe } from 'lucide-vue-next'
</script>

<template>
    <div class="space-y-8">
        <h2 class="section-title">登录与安全</h2>

        <!-- 1. 核心认证设置 -->
        <div class="card divide-y divide-gray-100 dark:divide-gray-800">

            <!-- 修改密码 -->
            <div class="p-6 flex items-center justify-between">
                <div class="flex items-center gap-4">
                    <div class="icon-box bg-purple-100 text-purple-600 dark:bg-purple-900/30">
                        <KeyRound class="w-5 h-5" />
                    </div>
                    <div>
                        <div class="font-bold text-gray-900 dark:text-white">登录密码</div>
                        <div class="text-sm text-gray-500 mt-0.5">建议定期更换密码以保护账号安全</div>
                    </div>
                </div>
                <button class="btn-secondary">修改密码</button>
            </div>

            <!-- 两步验证 -->
            <div class="p-6 flex items-center justify-between">
                <div class="flex items-center gap-4">
                    <div class="icon-box bg-green-100 text-green-600 dark:bg-green-900/30">
                        <Smartphone class="w-5 h-5" />
                    </div>
                    <div>
                        <div class="font-bold text-gray-900 dark:text-white">两步验证 (2FA)</div>
                        <div class="text-sm text-gray-500 mt-0.5">使用 Authenticator App 进行二次确认</div>
                    </div>
                </div>
                <button class="btn-primary">立即启用</button>
            </div>

            <!-- 备用邮箱 -->
            <div class="p-6 flex items-center justify-between">
                <div class="flex items-center gap-4">
                    <div class="icon-box bg-blue-100 text-blue-600 dark:bg-blue-900/30">
                        <ShieldCheck class="w-5 h-5" />
                    </div>
                    <div>
                        <div class="font-bold text-gray-900 dark:text-white">安全辅助邮箱</div>
                        <div class="text-sm text-gray-500 mt-0.5">用于找回密码或接收安全通知</div>
                    </div>
                </div>
                <div class="text-sm text-gray-900 dark:text-white font-medium mr-4">re*****@gmail.com</div>
            </div>
        </div>

        <!-- 2. 最近活动设备 -->
        <div class="space-y-4">
            <h3 class="font-bold text-gray-900 dark:text-white flex items-center gap-2">
                <History class="w-5 h-5 text-gray-500" />
                最近登录设备
            </h3>

            <div class="card p-0 overflow-hidden">
                <!-- 当前设备 -->
                <div
                    class="p-4 flex items-center justify-between bg-green-50/50 dark:bg-green-900/10 border-b border-gray-100 dark:border-gray-800">
                    <div class="flex items-center gap-4">
                        <Laptop class="w-8 h-8 text-green-600 dark:text-green-400" />
                        <div>
                            <div class="font-bold text-gray-900 dark:text-white flex items-center gap-2">
                                Chrome on Windows
                                <span
                                    class="px-2 py-0.5 bg-green-100 text-green-700 text-[10px] rounded-full">当前设备</span>
                            </div>
                            <div class="text-xs text-gray-500 mt-0.5 flex items-center gap-2">
                                <Globe class="w-3 h-3" /> 192.168.1.1 · 新加坡 · 刚刚
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 其他设备 -->
                <div
                    class="p-4 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
                    <div class="flex items-center gap-4">
                        <Smartphone class="w-8 h-8 text-gray-400" />
                        <div>
                            <div class="font-bold text-gray-900 dark:text-white">Safari on iPhone 15</div>
                            <div class="text-xs text-gray-500 mt-0.5 flex items-center gap-2">
                                <Globe class="w-3 h-3" /> 203.11.22.33 · 美国 · 2小时前
                            </div>
                        </div>
                    </div>
                    <button class="text-red-500 hover:text-red-600 text-sm font-medium">下线</button>
                </div>
            </div>
        </div>

    </div>
</template>

<style scoped>
/* 通用样式 */
.section-title {
    @apply text-2xl font-bold text-gray-900 dark:text-white mb-6;
}

.card {
    @apply bg-white dark:bg-bg-panelDark rounded-xl border border-gray-200 dark:border-border-dark overflow-hidden;
}

.icon-box {
    @apply p-2.5 rounded-lg flex items-center justify-center;
}

.btn-primary {
    @apply px-4 py-1.5 bg-primary text-white text-sm rounded-lg hover:bg-primary-hover transition-colors shadow-sm shadow-primary/20;
}

.btn-secondary {
    @apply px-4 py-1.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-200 text-sm rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors;
}
</style>