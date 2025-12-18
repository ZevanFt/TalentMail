<script setup lang="ts">
import { Shuffle } from 'lucide-vue-next'
const { isGenerateOpen } = useGlobalModal()
const { createPoolMailbox } = useApi()

const emit = defineEmits(['created'])

const prefix = ref('')
const purpose = ref('网站注册')
const autoVerify = ref(true)
const loading = ref(false)
const error = ref('')

const purposeOptions = ['网站注册', '社交媒体', '开发测试', '其他']

const generateRandom = () => {
    const chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
    prefix.value = Array.from({ length: 8 }, () => chars[Math.floor(Math.random() * chars.length)]).join('')
}

const handleCreate = async () => {
    loading.value = true
    error.value = ''
    try {
        await createPoolMailbox({
            prefix: prefix.value || undefined,
            purpose: purpose.value,
            auto_verify_codes: autoVerify.value
        })
        isGenerateOpen.value = false
        emit('created')
        // 重置表单
        prefix.value = ''
        purpose.value = '网站注册'
        autoVerify.value = true
    } catch (e: any) {
        error.value = e.data?.detail || '创建失败'
    } finally {
        loading.value = false
    }
}

const handleClose = () => {
    isGenerateOpen.value = false
    error.value = ''
}
</script>

<template>
    <CommonModal v-model="isGenerateOpen" title="生成临时邮箱" widthClass="w-full max-w-lg">
        <div class="space-y-6 py-2">
            <!-- 错误提示 -->
            <div v-if="error" class="p-3 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm rounded-lg">
                {{ error }}
            </div>

            <!-- 账号前缀 -->
            <div class="space-y-2">
                <label class="text-sm font-medium text-gray-700 dark:text-gray-300">账号前缀 (可选)</label>
                <div class="flex gap-2">
                    <input v-model="prefix" type="text" placeholder="留空则随机生成"
                        class="flex-1 px-4 py-2.5 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none">
                    <button @click="generateRandom" type="button"
                        class="px-3 py-2 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg text-gray-600 dark:text-gray-300 transition-colors">
                        <Shuffle class="w-4 h-4" />
                    </button>
                </div>
                <p class="text-xs text-gray-400">将自动生成如: {{ prefix || 'random123' }}@talenting.test</p>
            </div>

            <!-- 用途标签 -->
            <div class="space-y-2">
                <label class="text-sm font-medium text-gray-700 dark:text-gray-300">用途标签</label>
                <select v-model="purpose"
                    class="w-full px-4 py-2.5 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none">
                    <option v-for="opt in purposeOptions" :key="opt" :value="opt">{{ opt }}</option>
                </select>
            </div>

            <!-- 自动验证开关 -->
            <div class="flex items-start gap-3 p-4 bg-gray-50 dark:bg-gray-800/50 rounded-xl border border-gray-100 dark:border-gray-700 cursor-pointer"
                @click="autoVerify = !autoVerify">
                <div class="relative flex-shrink-0 mt-0.5">
                    <div :class="['w-5 h-5 rounded border flex items-center justify-center transition-colors',
                        autoVerify ? 'bg-green-500 border-green-500' : 'border-gray-300 dark:border-gray-600']">
                        <svg v-if="autoVerify" class="w-3.5 h-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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
            <button @click="handleClose" :disabled="loading"
                class="px-6 py-2.5 bg-gray-100 text-gray-600 hover:bg-gray-200 rounded-lg transition-colors font-medium disabled:opacity-50">
                取消
            </button>
            <button @click="handleCreate" :disabled="loading"
                class="px-8 py-2.5 bg-primary text-white rounded-lg hover:bg-primary-hover shadow-lg shadow-primary/20 transition-all font-medium disabled:opacity-50">
                {{ loading ? '创建中...' : '生成邮箱' }}
            </button>
        </template>
    </CommonModal>
</template>