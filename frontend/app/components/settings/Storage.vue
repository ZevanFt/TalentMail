<script setup lang="ts">
import { HardDrive, Archive, Trash2, AlertTriangle, Mail } from 'lucide-vue-next'

const { getStorageStats } = useApi()

const loading = ref(true)
const stats = ref({
    storage_used_bytes: 0,
    storage_limit_bytes: 10 * 1024 * 1024 * 1024,
    email_count: 0,
    email_bytes: 0
})

const loadStats = async () => {
    try {
        stats.value = await getStorageStats()
    } catch (e: any) {
        console.error('加载存储统计失败', e)
    } finally {
        loading.value = false
    }
}

// 格式化字节
const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

// 使用百分比
const usagePercent = computed(() => {
    return Math.round((stats.value.storage_used_bytes / stats.value.storage_limit_bytes) * 100)
})

onMounted(loadStats)
</script>

<template>
    <div class="space-y-8">
        <h2 class="section-title">存储与配额</h2>

        <div v-if="loading" class="text-gray-500">加载中...</div>

        <template v-else>
            <!-- 1. 空间使用概览卡片 -->
            <div class="card">
                <div class="flex items-center gap-4 mb-6">
                    <div class="p-3 bg-blue-100 text-blue-600 dark:bg-blue-900/30 rounded-xl">
                        <HardDrive class="w-6 h-6" />
                    </div>
                    <div>
                        <div class="text-2xl font-bold text-gray-900 dark:text-white flex items-baseline gap-2">
                            {{ formatBytes(stats.storage_used_bytes) }}
                            <span class="text-sm text-gray-500 font-normal">/ {{ formatBytes(stats.storage_limit_bytes) }}</span>
                        </div>
                        <div class="text-sm text-gray-500">已使用 {{ usagePercent }}% 的存储空间</div>
                    </div>
                </div>

                <!-- 进度条 -->
                <div class="w-full bg-gray-100 dark:bg-gray-700 rounded-full h-4 mb-2 overflow-hidden">
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
            <div v-if="usagePercent > 80"
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
</style>