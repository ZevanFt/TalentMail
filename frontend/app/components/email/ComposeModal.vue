<script setup lang="ts">
import { Paperclip, Send } from 'lucide-vue-next'
const { isComposeOpen } = useGlobalModal()
</script>

<template>
  <CommonModal v-model="isComposeOpen" title="新邮件" widthClass="w-full max-w-3xl">
    <div class="space-y-4">
      <!-- 收件人 -->
      <div>
        <input type="text" placeholder="收件人" class="w-full px-4 py-3 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all">
      </div>
      
      <!-- 主题 -->
      <div>
        <input type="text" placeholder="主题" class="w-full px-4 py-3 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all">
      </div>

      <!-- 内容区域 -->
      <div>
        <textarea 
          placeholder="内容..." 
          class="w-full h-64 px-4 py-3 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all resize-none custom-scrollbar"
        ></textarea>
      </div>
    </div>

    <template #footer>
      <button class="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 mr-auto">
        <Paperclip class="w-5 h-5" />
      </button>
      <button @click="isComposeOpen = false" class="flex items-center gap-2 px-6 py-2 bg-primary text-white rounded-lg hover:bg-primary-hover shadow-lg shadow-primary/20 transition-all font-medium">
        <Send class="w-4 h-4" /> 发送
      </button>
    </template>
  </CommonModal>
</template>