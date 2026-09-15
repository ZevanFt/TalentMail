<script setup lang="ts">
import { Shuffle } from 'lucide-vue-next'
const { isGenerateOpen } = useGlobalModal()
const { createPoolMailbox } = useApi()
const { baseDomain } = useConfig()
const { t } = useI18n()

const emit = defineEmits(['created'])

const prefix = ref('')
// purpose 发给后端，保持固定中文 value；展示走 i18n label
const purpose = ref('网站注册')
const autoVerify = ref(true)
const loading = ref(false)
const error = ref('')

const purposeOptions = computed(() => [
    { value: '网站注册', label: t('pool.createModal.purposes.signup') },
    { value: '社交媒体', label: t('pool.createModal.purposes.social') },
    { value: '开发测试', label: t('pool.createModal.purposes.dev') },
    { value: '其他', label: t('pool.createModal.purposes.other') },
])

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
        // 重置表单（purpose 保持后端约定的中文 value）
        prefix.value = ''
        purpose.value = '网站注册'
        autoVerify.value = true
    } catch (e: any) {
        error.value = e.data?.detail || t('pool.createModal.createFailed')
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
    <CommonModal v-model="isGenerateOpen" :title="t('pool.createModal.title')" widthClass="w-full max-w-lg">
        <div class="space-y-6 py-2">
            <!-- 错误提示 -->
            <div v-if="error" class="p-3 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm rounded-lg">
                {{ error }}
            </div>

            <!-- 账号前缀 -->
            <div class="space-y-2">
                <label class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ t('pool.createModal.prefixLabel') }}</label>
                <div class="flex gap-2">
                    <input v-model="prefix" type="text" :placeholder="t('pool.createModal.prefixPlaceholder')"
                        class="flex-1 px-4 py-2.5 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none">
                    <button @click="generateRandom" type="button"
                        class="px-3 py-2 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg text-gray-600 dark:text-gray-300 transition-colors">
                        <Shuffle class="w-4 h-4" />
                    </button>
                </div>
                <p class="text-xs text-gray-400">{{ t('pool.createModal.willGenerate', { example: prefix || 'random123', domain: baseDomain }) }}</p>
            </div>

            <!-- 用途标签 -->
            <div class="space-y-2">
                <label class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ t('pool.createModal.purposeLabel') }}</label>
                <select v-model="purpose"
                    class="w-full px-4 py-2.5 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none">
                    <option v-for="opt in purposeOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
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
                    <div class="font-medium text-sm text-gray-900 dark:text-white">{{ t('pool.createModal.autoVerifyTitle') }}</div>
                    <div class="text-xs text-gray-500 mt-0.5">{{ t('pool.createModal.autoVerifyHint') }}</div>
                </div>
            </div>
        </div>

        <template #footer>
            <button @click="handleClose" :disabled="loading"
                class="px-6 py-2.5 bg-gray-100 text-gray-600 hover:bg-gray-200 rounded-lg transition-colors font-medium disabled:opacity-50">
                {{ t('common.cancel') }}
            </button>
            <button @click="handleCreate" :disabled="loading"
                class="px-8 py-2.5 bg-primary text-white rounded-lg hover:bg-primary-hover shadow-lg shadow-primary/20 transition-all font-medium disabled:opacity-50">
                {{ loading ? t('pool.createModal.creating') : t('pool.createModal.generate') }}
            </button>
        </template>
    </CommonModal>
</template>
