<script setup lang="ts">
import { Shuffle, X } from 'lucide-vue-next'
const { isGenerateOpen } = useGlobalModal()
const autoVerify = ref(true)
</script>

<template>
    <CommonModal v-model="isGenerateOpen" title="生成临时邮箱" widthClass="w-full max-w-lg">
        <div class="space-y-6 py-2">
            <!-- 账号前缀 -->
            <div class="space-y-2">
                <label class="text-sm font-medium text-gray-700 dark:text-gray-300">账号前缀 (可选)</label>
                <div class="flex gap-2">
                    <input type="text" placeholder="留空则随机生成"
                        class="flex-1 px-4 py-2.5 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none">
                    <button
                        class="px-3 py-2 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg text-gray-600 dark:text-gray-300 transition-colors">
                        <Shuffle class="w-4 h-4" />
                        <span class="sr-only">随机</span>
                    </button>
                </div>
                <p class="text-xs text-gray-400">将自动生成如: random123@talenting.vip</p>
            </div>

            <!-- 用途标签 -->
            <div class="space-y-2">
                <label class="text-sm font-medium text-gray-700 dark:text-gray-300">用途标签</label>
                <select
                    class="w-full px-4 py-2.5 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none">
                    <option>网站注册</option>
                    <option>社交媒体</option>
                    <option>开发测试</option>
                </select>
            </div>

            <!-- 自动验证开关 -->
            <div class="flex items-start gap-3 p-4 bg-gray-50 dark:bg-gray-800/50 rounded-xl border border-gray-100 dark:border-gray-700 cursor-pointer"
                @click="autoVerify = !autoVerify">
                <div class="relative flex-shrink-0 mt-0.5">
                    <div
                        :class="`w-5 h-5 rounded border ${autoVerify ? 'bg-green-500 border-green-500' : 'border-gray-300'} flex items-center justify-center transition-colors`">
                        <svg v-if="autoVerify" class="w-3.5 h-3.5 text-white" fill="none" viewBox="0 0 24 24"
                            stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
                        </svg>
                    </div>
                </div>
                <div>
                    <div class="font-medium text-sm text-gray-900 dark:text-white">自动验证码识别</div>
                    <div class="text-xs text-gray-500 mt-0.5">收到验证码邮件将自动提取并高亮显示</div>
                </div>
            </div>
        </div>

        <template #footer>
            <button @click="isGenerateOpen = false"
                class="px-6 py-2.5 bg-gray-100 text-gray-600 hover:bg-gray-200 rounded-lg transition-colors font-medium">取消</button>
            <button @click="isGenerateOpen = false"
                class="px-8 py-2.5 bg-primary text-white rounded-lg hover:bg-primary-hover shadow-lg shadow-primary/20 transition-all font-medium">生成邮箱</button>
        </template>
    </CommonModal>
</template>