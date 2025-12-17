<script setup lang="ts">
import { Star } from 'lucide-vue-next'
const { emails, selectedEmailId } = useEmails()
</script>

<template>
  <!-- 修改点：w-80 (320px) 保持不变，这是标准列表宽度 -->
  <div
    class="w-80 h-full bg-white dark:bg-bg-panelDark border-r border-gray-200 dark:border-border-dark flex flex-col shrink-0">
    <!-- 内容保持不变... -->
    <div
      class="px-4 py-3 text-xs font-bold text-gray-500 dark:text-gray-400 border-b border-gray-100 dark:border-gray-800">
      收件箱 (12)
    </div>

    <div class="flex-1 overflow-y-auto">
      <div v-for="email in emails" :key="email.id" @click="selectedEmailId = email.id"
        class="px-4 py-3 border-b border-gray-50 dark:border-gray-800 cursor-pointer transition-all hover:bg-gray-50 dark:hover:bg-gray-800/50 relative group"
        :class="{ 'bg-blue-50/30 dark:bg-gray-800': selectedEmailId === email.id }">
        <!-- 内容保持不变... -->
        <div v-if="selectedEmailId === email.id" class="absolute left-0 top-0 bottom-0 w-[3px] bg-primary"></div>
        <div class="flex justify-between items-start mb-0.5">
          <div class="flex items-center gap-2.5">
            <div
              :class="`w-8 h-8 rounded-full ${email.color} flex items-center justify-center text-xs text-white font-bold shadow-sm`">
              {{ email.avatar }}
            </div>
            <div class="min-w-0">
              <div class="text-sm font-bold text-gray-900 dark:text-white leading-tight truncate">
                {{ email.from }}
              </div>
            </div>
          </div>
          <span class="text-[10px] text-gray-400 font-medium">{{ email.time }}</span>
        </div>
        <div class="flex items-center justify-between mt-1">
          <div class="text-xs font-semibold text-gray-700 dark:text-gray-300 truncate pr-2">{{ email.subject }}</div>
          <Star v-if="email.starred" class="w-3 h-3 fill-yellow-400 text-yellow-400 shrink-0" />
        </div>
        <p class="text-xs text-gray-500 dark:text-gray-400 line-clamp-2 mt-1 leading-relaxed">{{ email.snippet }}</p>
      </div>
    </div>
  </div>
</template>