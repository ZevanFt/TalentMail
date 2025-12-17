<script setup lang="ts">
import { Sun, Moon, Monitor, CheckCircle2 } from 'lucide-vue-next'
const { isDark, toggleTheme } = useTheme()

// 这里为了演示，我们假设还有一个 'system' 模式，
// 但实际 toggleTheme 目前只切换 true/false，所以这里主要处理 UI 交互
const selectMode = (mode: 'light' | 'dark') => {
    if ((mode === 'dark' && !isDark.value) || (mode === 'light' && isDark.value)) {
        toggleTheme()
    }
}
</script>

<template>
    <div class="space-y-8">
        <h2 class="section-title">外观主题</h2>

        <div class="grid grid-cols-2 gap-6">

            <!-- 浅色模式卡片 -->
            <div @click="selectMode('light')" class="group relative cursor-pointer">
                <div class="aspect-video rounded-xl border-2 transition-all overflow-hidden relative mb-3 bg-gray-100 flex items-center justify-center"
                    :class="!isDark ? 'border-primary ring-4 ring-primary/10' : 'border-gray-200 dark:border-gray-700 hover:border-primary/50'">
                    <!-- 模拟浅色 UI -->
                    <div class="w-3/4 h-3/4 bg-white rounded-lg shadow-sm flex flex-col p-2 gap-2">
                        <div class="w-1/3 h-2 bg-gray-100 rounded"></div>
                        <div
                            class="flex-1 bg-gray-50 rounded border border-dashed border-gray-200 flex items-center justify-center">
                            <Sun class="w-8 h-8 text-yellow-500" />
                        </div>
                    </div>

                    <!-- 选中角标 -->
                    <div v-if="!isDark" class="absolute top-3 right-3 text-primary">
                        <CheckCircle2 class="w-6 h-6 fill-white" />
                    </div>
                </div>
                <div
                    class="font-bold text-gray-900 dark:text-white group-hover:text-primary transition-colors text-center">
                    浅色模式
                </div>
            </div>

            <!-- 深色模式卡片 -->
            <div @click="selectMode('dark')" class="group relative cursor-pointer">
                <div class="aspect-video rounded-xl border-2 transition-all overflow-hidden relative mb-3 bg-gray-900 flex items-center justify-center"
                    :class="isDark ? 'border-primary ring-4 ring-primary/10' : 'border-gray-200 dark:border-gray-700 hover:border-primary/50'">
                    <!-- 模拟深色 UI -->
                    <div
                        class="w-3/4 h-3/4 bg-gray-800 rounded-lg shadow-inner flex flex-col p-2 gap-2 border border-gray-700">
                        <div class="w-1/3 h-2 bg-gray-700 rounded"></div>
                        <div
                            class="flex-1 bg-gray-900/50 rounded border border-dashed border-gray-700 flex items-center justify-center">
                            <Moon class="w-8 h-8 text-purple-400" />
                        </div>
                    </div>

                    <!-- 选中角标 -->
                    <div v-if="isDark" class="absolute top-3 right-3 text-primary">
                        <CheckCircle2 class="w-6 h-6 fill-gray-900" />
                    </div>
                </div>
                <div
                    class="font-bold text-gray-900 dark:text-white group-hover:text-primary transition-colors text-center">
                    深色模式
                </div>
            </div>

        </div>

        <!-- 更多选项 (跟随系统) -->
        <div class="p-4 rounded-xl bg-gray-50 dark:bg-bg-panelDark border border-gray-100 dark:border-gray-800 flex items-center justify-between opacity-50 cursor-not-allowed"
            title="暂未开发">
            <div class="flex items-center gap-3">
                <div class="p-2 bg-gray-200 dark:bg-gray-700 rounded-lg">
                    <Monitor class="w-5 h-5 text-gray-500 dark:text-gray-300" />
                </div>
                <div>
                    <div class="font-bold text-gray-900 dark:text-white">跟随系统设置</div>
                    <div class="text-xs text-gray-500">自动根据操作系统外观切换</div>
                </div>
            </div>
            <input type="checkbox" disabled class="toggle-checkbox">
        </div>

    </div>
</template>

<style scoped>
.section-title {
    @apply text-2xl font-bold text-gray-900 dark:text-white mb-6;
}
</style>