<script setup lang="ts">
import { HardDrive, Archive, Trash2, AlertTriangle, FileText, Image, Video } from 'lucide-vue-next'
</script>

<template>
    <div class="space-y-8">
        <h2 class="section-title">存储与配额</h2>

        <!-- 1. 空间使用概览卡片 -->
        <div class="card">
            <div class="flex items-center gap-4 mb-6">
                <div class="p-3 bg-blue-100 text-blue-600 dark:bg-blue-900/30 rounded-xl">
                    <HardDrive class="w-6 h-6" />
                </div>
                <div>
                    <div class="text-2xl font-bold text-gray-900 dark:text-white flex items-baseline gap-2">
                        2.4 GB
                        <span class="text-sm text-gray-500 font-normal">/ 10 GB</span>
                    </div>
                    <div class="text-sm text-gray-500">已使用 24% 的存储空间</div>
                </div>
            </div>

            <!-- 进度条 -->
            <div class="w-full bg-gray-100 dark:bg-gray-700 rounded-full h-4 mb-2 overflow-hidden flex">
                <!-- 邮件 (紫) -->
                <div class="bg-primary h-full" style="width: 15%" title="邮件"></div>
                <!-- 附件 (蓝) -->
                <div class="bg-blue-500 h-full" style="width: 8%" title="附件"></div>
                <!-- 垃圾 (红) -->
                <div class="bg-red-500 h-full" style="width: 1%" title="垃圾箱"></div>
            </div>

            <!-- 图例 -->
            <div class="flex gap-4 text-xs text-gray-500 mb-6">
                <div class="flex items-center gap-1.5">
                    <div class="w-2 h-2 rounded-full bg-primary"></div> 邮件 (1.5GB)
                </div>
                <div class="flex items-center gap-1.5">
                    <div class="w-2 h-2 rounded-full bg-blue-500"></div> 附件 (800MB)
                </div>
                <div class="flex items-center gap-1.5">
                    <div class="w-2 h-2 rounded-full bg-red-500"></div> 垃圾箱 (100MB)
                </div>
            </div>

            <!-- 分类统计 -->
            <div class="grid grid-cols-3 gap-4">
                <div class="stat-box">
                    <div class="flex items-center gap-2 mb-1 text-gray-500 text-xs">
                        <FileText class="w-3.5 h-3.5" /> 文档
                    </div>
                    <div class="font-bold text-gray-900 dark:text-white">450 MB</div>
                </div>
                <div class="stat-box">
                    <div class="flex items-center gap-2 mb-1 text-gray-500 text-xs">
                        <Image class="w-3.5 h-3.5" /> 图片
                    </div>
                    <div class="font-bold text-gray-900 dark:text-white">1.2 GB</div>
                </div>
                <div class="stat-box">
                    <div class="flex items-center gap-2 mb-1 text-gray-500 text-xs">
                        <Video class="w-3.5 h-3.5" /> 视频/其他
                    </div>
                    <div class="font-bold text-gray-900 dark:text-white">750 MB</div>
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
                <input type="checkbox" checked class="accent-primary w-5 h-5 cursor-pointer">
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
                <input type="checkbox" class="accent-primary w-5 h-5 cursor-pointer">
            </div>
        </div>

        <!-- 3. 扩容提示 -->
        <div
            class="bg-gradient-to-r from-primary/10 to-purple-500/10 border border-primary/20 rounded-xl p-4 flex items-start gap-3">
            <AlertTriangle class="w-5 h-5 text-primary shrink-0 mt-0.5" />
            <div>
                <h4 class="font-bold text-gray-900 dark:text-white text-sm">空间不足？</h4>
                <p class="text-xs text-gray-600 dark:text-gray-300 mt-1 mb-3">
                    升级到 Pro 套餐可获得 100GB 存储空间以及无限别名支持。
                </p>
                <button
                    class="text-xs bg-primary text-white px-3 py-1.5 rounded-lg hover:bg-primary-hover transition-colors">
                    查看升级方案
                </button>
            </div>
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

.stat-box {
    @apply bg-gray-50 dark:bg-gray-800 rounded-lg p-3 text-center border border-gray-100 dark:border-gray-700;
}
</style>