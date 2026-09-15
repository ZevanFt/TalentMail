<script setup lang="ts">
import { AlertTriangle, Home, RotateCcw } from 'lucide-vue-next'

const props = defineProps<{
  error: {
    statusCode?: number
    statusMessage?: string
    message?: string
  }
}>()

const { t } = useI18n()

useHead({ title: `${t('error.headTitle')} - ${t('common.appName')}` })

const errorInfo = computed(() => {
  const code = props.error?.statusCode || 500
  const map: Record<number, { titleKey: string; descKey: string }> = {
    404: { titleKey: 'error.notFound.title', descKey: 'error.notFound.desc' },
    403: { titleKey: 'error.forbidden.title', descKey: 'error.forbidden.desc' },
    500: { titleKey: 'error.serverError.title', descKey: 'error.serverError.desc' },
  }
  const entry = map[code]
  if (entry) {
    return { title: t(entry.titleKey), desc: t(entry.descKey) }
  }
  return {
    title: t('error.unknown.title'),
    desc: props.error?.message || t('error.unknown.desc'),
  }
})

const handleClearError = () => clearError({ redirect: '/' })
const handleRetry = () => clearError({ redirect: window.location.pathname })
</script>

<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-950 flex items-center justify-center p-6">
    <div class="text-center max-w-md">
      <!-- 错误码 -->
      <div class="text-7xl font-black text-gray-200 dark:text-gray-800 mb-4">
        {{ error?.statusCode || '?' }}
      </div>

      <!-- 图标 -->
      <AlertTriangle class="w-16 h-16 mx-auto mb-4 text-orange-400" />

      <!-- 标题 -->
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white mb-2">
        {{ errorInfo.title }}
      </h1>

      <!-- 描述 -->
      <p class="text-gray-500 dark:text-gray-400 mb-8">
        {{ errorInfo.desc }}
      </p>

      <!-- 操作按钮 -->
      <div class="flex items-center justify-center gap-3">
        <button @click="handleRetry"
          class="flex items-center gap-2 px-5 py-2.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors text-sm font-medium">
          <RotateCcw class="w-4 h-4" />
          {{ t('common.retry') }}
        </button>
        <button @click="handleClearError"
          class="flex items-center gap-2 px-5 py-2.5 bg-primary text-white rounded-xl hover:bg-primary-hover transition-colors text-sm font-medium shadow-lg shadow-primary/25">
          <Home class="w-4 h-4" />
          {{ t('error.goHome') }}
        </button>
      </div>
    </div>
  </div>
</template>
