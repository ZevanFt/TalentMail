<script setup lang="ts">
import { Star, RefreshCw, Loader2 } from 'lucide-vue-next'

const { emails, selectedEmailId, folders, currentFolderId, loading, syncing, loadFolders, loadEmails, loadEmailDetail, sync, formatTime } = useEmails()

// 当前文件夹
const currentFolder = computed(() => folders.value.find(f => f.id === currentFolderId.value))

// 获取发件人首字母
const getAvatar = (sender: string) => {
  if (!sender) return '?'
  const match = sender.match(/^([^<]+)/) || sender.match(/<([^>]+)>/)
  const name = match?.[1]?.trim() || sender
  return name.charAt(0).toUpperCase()
}

// 选择邮件
const selectEmail = (id: number) => {
  selectedEmailId.value = id
  loadEmailDetail(id)
}

// 初始化加载（只在有 token 时）
const { token } = useApi()
onMounted(async () => {
  if (token.value) {
    await loadFolders()
    await loadEmails()
  }
})
</script>

<template>
  <div class="w-80 h-full bg-white dark:bg-bg-panelDark border-r border-gray-200 dark:border-border-dark flex flex-col shrink-0">
    <!-- 标题栏 -->
    <div class="px-4 py-3 text-xs font-bold text-gray-500 dark:text-gray-400 border-b border-gray-100 dark:border-gray-800 flex items-center justify-between">
      <span>{{ currentFolder?.name || '收件箱' }} ({{ emails.length }})</span>
      <button @click="sync" :disabled="syncing" class="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded">
        <Loader2 v-if="syncing" class="w-4 h-4 animate-spin" />
        <RefreshCw v-else class="w-4 h-4" />
      </button>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="flex-1 flex items-center justify-center">
      <Loader2 class="w-6 h-6 animate-spin text-gray-400" />
    </div>

    <!-- 空状态 -->
    <div v-else-if="emails.length === 0" class="flex-1 flex items-center justify-center text-gray-400 text-sm">
      暂无邮件
    </div>

    <!-- 邮件列表 -->
    <div v-else class="flex-1 overflow-y-auto">
      <div v-for="email in emails" :key="email.id" @click="selectEmail(email.id)"
        class="px-4 py-3 border-b border-gray-50 dark:border-gray-800 cursor-pointer transition-all hover:bg-gray-50 dark:hover:bg-gray-800/50 relative group"
        :class="{ 'bg-blue-50/30 dark:bg-gray-800': selectedEmailId === email.id, 'font-semibold': !email.is_read }">
        <div v-if="selectedEmailId === email.id" class="absolute left-0 top-0 bottom-0 w-[3px] bg-primary"></div>
        <div class="flex justify-between items-start mb-0.5">
          <div class="flex items-center gap-2.5">
            <div class="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-xs text-white font-bold shadow-sm">
              {{ getAvatar(email.sender) }}
            </div>
            <div class="min-w-0">
              <div class="text-sm font-bold text-gray-900 dark:text-white leading-tight truncate">
                {{ email.sender }}
              </div>
            </div>
          </div>
          <span class="text-[10px] text-gray-400 font-medium">{{ formatTime(email.received_at) }}</span>
        </div>
        <div class="flex items-center justify-between mt-1">
          <div class="text-xs font-semibold text-gray-700 dark:text-gray-300 truncate pr-2">{{ email.subject }}</div>
          <Star v-if="email.is_starred" class="w-3 h-3 fill-yellow-400 text-yellow-400 shrink-0" />
        </div>
        <p class="text-xs text-gray-500 dark:text-gray-400 line-clamp-2 mt-1 leading-relaxed">{{ email.snippet }}</p>
      </div>
    </div>
  </div>
</template>