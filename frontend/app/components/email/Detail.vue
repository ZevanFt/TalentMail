<script setup lang="ts">
import { ArrowLeft, Trash2, Archive, Star, Reply, Forward, MoreHorizontal } from 'lucide-vue-next'
const { selectedEmailDetail, formatTime } = useEmails()

// 获取发件人首字母
const getAvatar = (sender: string) => {
  if (!sender) return '?'
  const match = sender.match(/^([^<]+)/) || sender.match(/<([^>]+)>/)
  const name = match?.[1]?.trim() || sender
  return name.charAt(0).toUpperCase()
}
</script>

<template>
  <main class="flex-1 h-full bg-white dark:bg-bg-dark flex flex-col min-w-0 relative">
    <template v-if="selectedEmailDetail">
      <!-- 顶部工具栏 -->
      <div class="h-14 border-b border-gray-100 dark:border-gray-800 flex items-center px-6 justify-between shrink-0">
        <div class="flex items-center gap-1">
          <button class="btn-icon">
            <ArrowLeft class="w-5 h-5" />
          </button>
          <div class="w-px h-4 bg-gray-200 dark:bg-gray-700 mx-2"></div>
          <button class="btn-icon">
            <Archive class="w-5 h-5" />
          </button>
          <button class="btn-icon hover:text-red-500 hover:bg-red-50">
            <Trash2 class="w-5 h-5" />
          </button>
        </div>
        <button class="btn-icon">
          <MoreHorizontal class="w-5 h-5" />
        </button>
      </div>

      <!-- 滚动内容区 -->
      <div class="flex-1 overflow-y-auto p-8 custom-scrollbar">
        <div class="max-w-4xl mx-auto">
          <!-- 邮件标题 -->
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white mb-6 leading-tight">
            {{ selectedEmailDetail.subject }}
          </h1>

          <!-- 发件人卡片 -->
          <div class="flex items-start gap-4 mb-8">
            <div class="w-12 h-12 rounded-full bg-primary flex items-center justify-center text-lg text-white font-medium shrink-0">
              {{ getAvatar(selectedEmailDetail.sender) }}
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-0.5">
                <span class="text-base font-bold text-gray-900 dark:text-white">{{ selectedEmailDetail.sender }}</span>
              </div>
              <div class="text-xs text-gray-500">
                收件人: {{ selectedEmailDetail.recipients }}
                <span class="ml-4">{{ formatTime(selectedEmailDetail.received_at) }}</span>
              </div>
            </div>
          </div>

          <!-- 分割线 -->
          <div class="border-t border-dashed border-gray-200 dark:border-gray-800 my-8"></div>

          <!-- 正文 -->
          <div v-if="selectedEmailDetail.body_html"
            class="prose prose-zinc dark:prose-invert max-w-none"
            v-html="selectedEmailDetail.body_html">
          </div>
          <div v-else
            class="prose prose-zinc dark:prose-invert max-w-none text-gray-700 dark:text-gray-300 whitespace-pre-line leading-7 text-base">
            {{ selectedEmailDetail.body_text }}
          </div>
        </div>
      </div>

      <!-- 底部浮动栏 -->
      <div class="absolute bottom-6 right-8 flex gap-3 z-20">
        <button class="flex items-center gap-2 px-5 py-2 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-full hover:bg-gray-50 dark:hover:bg-gray-700 transition-all text-sm font-medium border border-gray-200 dark:border-gray-700 shadow-sm hover:shadow-md">
          <Forward class="w-4 h-4" /> 转发
        </button>
        <button class="flex items-center gap-2 px-6 py-2 bg-primary text-white rounded-full hover:bg-primary-hover transition-all text-sm font-medium shadow-lg shadow-primary/30 hover:shadow-primary/50 hover:-translate-y-0.5">
          <Reply class="w-4 h-4" /> 回复
        </button>
      </div>
    </template>

    <!-- 空状态 -->
    <template v-else>
      <div class="flex-1 flex items-center justify-center text-gray-400">
        选择一封邮件查看
      </div>
    </template>
  </main>
</template>

<style scoped>
.btn-icon {
  @apply p-2 rounded-lg text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-white transition-all;
}

.btn-primary {
  @apply flex items-center gap-2 px-6 py-2.5 bg-primary text-white rounded-lg hover:bg-primary-hover transition-colors font-medium shadow-md shadow-primary/20;
}

.btn-secondary {
  @apply flex items-center gap-2 px-6 py-2.5 bg-gray-200 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-700 transition-colors font-medium;
}
</style>