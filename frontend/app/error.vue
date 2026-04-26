<script setup lang="ts">
import { AlertTriangle, Home, RotateCcw } from 'lucide-vue-next'

const props = defineProps<{
  error: {
    statusCode?: number
    statusMessage?: string
    message?: string
  }
}>()

useHead({ title: '出错了 - TalentMail' })

const errorInfo = computed(() => {
  const code = props.error?.statusCode || 500
  const map: Record<number, { title: string; desc: string }> = {
    404: { title: '页面不存在', desc: '您访问的页面可能已被移动或删除' },
    403: { title: '无权访问', desc: '您没有权限查看此页面' },
    500: { title: '服务器错误', desc: '服务器遇到了意外问题，请稍后重试' },
  }
  return map[code] || { title: '出了点问题', desc: props.error?.message || '发生了未知错误' }
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
          重试
        </button>
        <button @click="handleClearError"
          class="flex items-center gap-2 px-5 py-2.5 bg-primary text-white rounded-xl hover:bg-primary-hover transition-colors text-sm font-medium shadow-lg shadow-primary/25">
          <Home class="w-4 h-4" />
          返回首页
        </button>
      </div>
    </div>
  </div>
</template>
