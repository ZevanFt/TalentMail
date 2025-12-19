<script setup lang="ts">
import { ArrowLeft, Trash2, Archive, Star, Reply, Forward, MoreHorizontal, Mail, MailOpen, ReplyAll, Eye, Send, CheckCircle, XCircle, Loader2, RefreshCw, Paperclip, Download } from 'lucide-vue-next'
const { selectedEmailDetail, formatTime, toggleRead, removeEmail, startReply, startReplyAll, startForward, folders, currentFolderId, loadEmails } = useEmails()
const { isComposeOpen } = useGlobalModal()
const { getTrackingStats, resendEmail, downloadAttachmentUrl, token } = useApi()

// 追踪统计
const trackingStats = ref<any>(null)
const loadingTracking = ref(false)

// 加载追踪统计
const loadTrackingStats = async (emailId: number) => {
  loadingTracking.value = true
  try {
    const res = await getTrackingStats(emailId)
    trackingStats.value = res.data
  } catch {
    trackingStats.value = null
  } finally {
    loadingTracking.value = false
  }
}

// 监听邮件变化，加载追踪统计
watch(() => selectedEmailDetail.value, (email) => {
  if (email?.is_tracked) {
    loadTrackingStats(email.id)
  } else {
    trackingStats.value = null
  }
}, { immediate: true })

// 切换已读状态
const handleToggleRead = () => {
  if (selectedEmailDetail.value) {
    toggleRead(selectedEmailDetail.value.id, !selectedEmailDetail.value.is_read)
  }
}

// 回复
const handleReply = () => {
  if (selectedEmailDetail.value) {
    startReply(selectedEmailDetail.value)
    isComposeOpen.value = true
  }
}

// 回复全部
const handleReplyAll = () => {
  if (selectedEmailDetail.value) {
    startReplyAll(selectedEmailDetail.value)
    isComposeOpen.value = true
  }
}

// 转发
const handleForward = () => {
  if (selectedEmailDetail.value) {
    startForward(selectedEmailDetail.value)
    isComposeOpen.value = true
  }
}

// 删除确认
const showDeleteConfirm = ref(false)
const handleDelete = () => {
  showDeleteConfirm.value = true
}
const confirmDelete = () => {
  if (selectedEmailDetail.value) {
    removeEmail(selectedEmailDetail.value.id)
  }
  showDeleteConfirm.value = false
}

// 获取发件人首字母
const getAvatar = (sender: string) => {
  if (!sender) return '?'
  const match = sender.match(/^([^<]+)/) || sender.match(/<([^>]+)>/)
  const name = match?.[1]?.trim() || sender
  return name.charAt(0).toUpperCase()
}

// 格式化收件人显示
const formatRecipients = (recipientsStr: string) => {
  if (!recipientsStr) return ''
  try {
    const data = JSON.parse(recipientsStr)
    const parts: string[] = []
    if (data.to?.length) {
      const toList = data.to.map((r: any) => r.name ? `${r.name} <${r.email}>` : r.email).join(', ')
      parts.push(`收件人: ${toList}`)
    }
    if (data.cc?.length) {
      const ccList = data.cc.map((r: any) => r.name ? `${r.name} <${r.email}>` : r.email).join(', ')
      parts.push(`抄送: ${ccList}`)
    }
    return parts.join(' | ')
  } catch {
    return `收件人: ${recipientsStr}`
  }
}

// 是否是已发送文件夹
const isSentFolder = computed(() => {
  const folder = folders.value.find(f => f.id === currentFolderId.value)
  return folder?.role === 'sent'
})

// 投递状态配置
const deliveryStatusConfig: Record<string, { icon: any; text: string; class: string }> = {
  pending: { icon: Loader2, text: '等待发送', class: 'text-gray-500 bg-gray-100 dark:bg-gray-800' },
  sending: { icon: Loader2, text: '发送中', class: 'text-blue-500 bg-blue-100 dark:bg-blue-900/30' },
  sent: { icon: Send, text: '已发送', class: 'text-green-600 bg-green-100 dark:bg-green-900/30' },
  delivered: { icon: CheckCircle, text: '已送达', class: 'text-green-600 bg-green-100 dark:bg-green-900/30' },
  failed: { icon: XCircle, text: '发送失败', class: 'text-red-500 bg-red-100 dark:bg-red-900/30' },
}

// 当前投递状态
const currentDeliveryStatus = computed(() => {
  const status = selectedEmailDetail.value?.delivery_status
  return status ? deliveryStatusConfig[status] : null
})

// 重新发送
const resending = ref(false)
const handleResend = async () => {
  if (!selectedEmailDetail.value || resending.value) return
  resending.value = true
  try {
    await resendEmail(selectedEmailDetail.value.id)
    // 刷新邮件列表
    if (currentFolderId.value) {
      await loadEmails(currentFolderId.value)
    }
  } finally {
    resending.value = false
  }
}

// 是否可以重新发送
const canResend = computed(() => {
  const status = selectedEmailDetail.value?.delivery_status
  return isSentFolder.value && (status === 'failed' || status === 'pending')
})

// 是否有真实的 HTML 内容（排除只有追踪像素的情况）
const hasRealHtmlContent = computed(() => {
  const html = selectedEmailDetail.value?.body_html
  if (!html) return false
  // 移除追踪像素后检查是否还有内容
  const withoutTracker = html.replace(/<img[^>]*track\/open[^>]*>/gi, '').trim()
  return withoutTracker.length > 0
})

// 附件
const attachments = computed(() => selectedEmailDetail.value?.attachments || [])

const formatFileSize = (bytes: number) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

const downloadAttachment = (id: number) => {
  const url = downloadAttachmentUrl(id)
  window.open(`${url}?token=${token.value}`, '_blank')
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
          <button class="btn-icon" @click="handleToggleRead" :title="selectedEmailDetail.is_read ? '标记为未读' : '标记为已读'">
            <MailOpen v-if="selectedEmailDetail.is_read" class="w-5 h-5" />
            <Mail v-else class="w-5 h-5" />
          </button>
          <button class="btn-icon">
            <Archive class="w-5 h-5" />
          </button>
          <button class="btn-icon hover:text-red-500 hover:bg-red-50" @click="handleDelete" title="删除">
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
                {{ formatRecipients(selectedEmailDetail.recipients) }}
                <span class="ml-4">{{ formatTime(selectedEmailDetail.received_at) }}</span>
              </div>
              <!-- 投递状态 + 追踪统计（仅已发送文件夹显示） -->
              <div v-if="isSentFolder && (currentDeliveryStatus || (selectedEmailDetail.is_tracked && trackingStats))" class="mt-2 flex items-center gap-3 text-xs flex-wrap">
                <!-- 投递状态 -->
                <span v-if="currentDeliveryStatus"
                  class="flex items-center gap-1 px-2 py-1 rounded-full"
                  :class="currentDeliveryStatus.class"
                  :title="selectedEmailDetail.delivery_error || ''">
                  <component :is="currentDeliveryStatus.icon"
                    class="w-3 h-3"
                    :class="{ 'animate-spin': selectedEmailDetail.delivery_status === 'sending' || selectedEmailDetail.delivery_status === 'pending' }" />
                  {{ currentDeliveryStatus.text }}
                </span>
                <!-- 重新发送按钮 -->
                <button v-if="canResend" @click="handleResend" :disabled="resending"
                  class="flex items-center gap-1 px-2 py-1 rounded-full bg-primary/10 text-primary hover:bg-primary/20 transition-colors">
                  <RefreshCw class="w-3 h-3" :class="{ 'animate-spin': resending }" />
                  {{ resending ? '发送中...' : '重新发送' }}
                </button>
                <!-- 追踪统计 -->
                <template v-if="selectedEmailDetail.is_tracked && trackingStats">
                  <span class="text-gray-300 dark:text-gray-600">→</span>
                  <span class="flex items-center gap-1 px-2 py-1 rounded-full" :class="trackingStats.open_count > 0 ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' : 'bg-gray-100 text-gray-500 dark:bg-gray-800'">
                    <Eye class="w-3 h-3" />
                    {{ trackingStats.open_count > 0 ? `对方已读 ${trackingStats.open_count} 次` : '对方未读' }}
                  </span>
                  <span v-if="trackingStats.last_opened_at" class="text-gray-400">
                    {{ formatTime(trackingStats.last_opened_at) }}
                  </span>
                </template>
              </div>
            </div>
          </div>

          <!-- 附件列表 -->
          <div v-if="attachments.length" class="mb-6 p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
            <div class="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 mb-3">
              <Paperclip class="w-4 h-4" />
              <span>{{ attachments.length }} 个附件</span>
            </div>
            <div class="flex flex-wrap gap-2">
              <button v-for="att in attachments" :key="att.id" @click="downloadAttachment(att.id)"
                class="flex items-center gap-2 px-3 py-2 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors text-sm">
                <Download class="w-4 h-4 text-gray-500" />
                <span class="text-gray-700 dark:text-gray-300">{{ att.filename }}</span>
                <span class="text-gray-400 text-xs">({{ formatFileSize(att.size) }})</span>
              </button>
            </div>
          </div>

          <!-- 分割线 -->
          <div class="border-t border-dashed border-gray-200 dark:border-gray-800 my-8"></div>

          <!-- 正文 -->
          <div v-if="hasRealHtmlContent"
            class="prose prose-zinc dark:prose-invert max-w-none"
            v-html="selectedEmailDetail.body_html">
          </div>
          <template v-else>
            <div v-if="selectedEmailDetail.body_text"
              class="prose prose-zinc dark:prose-invert max-w-none text-gray-700 dark:text-gray-300 whitespace-pre-line leading-7 text-base">
              {{ selectedEmailDetail.body_text }}
            </div>
            <div v-else class="text-gray-400 italic">
              (无正文内容)
            </div>
            <!-- 隐藏的追踪像素（确保追踪功能正常工作） -->
            <div v-if="selectedEmailDetail.body_html" v-html="selectedEmailDetail.body_html" class="hidden"></div>
          </template>
        </div>
      </div>

      <!-- 底部浮动栏 -->
      <div class="absolute bottom-6 right-8 flex gap-3 z-20">
        <button @click="handleForward" class="flex items-center gap-2 px-5 py-2 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-full hover:bg-gray-50 dark:hover:bg-gray-700 transition-all text-sm font-medium border border-gray-200 dark:border-gray-700 shadow-sm hover:shadow-md">
          <Forward class="w-4 h-4" /> 转发
        </button>
        <button @click="handleReplyAll" class="flex items-center gap-2 px-5 py-2 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-full hover:bg-gray-50 dark:hover:bg-gray-700 transition-all text-sm font-medium border border-gray-200 dark:border-gray-700 shadow-sm hover:shadow-md">
          <ReplyAll class="w-4 h-4" /> 回复全部
        </button>
        <button @click="handleReply" class="flex items-center gap-2 px-6 py-2 bg-primary text-white rounded-full hover:bg-primary-hover transition-all text-sm font-medium shadow-lg shadow-primary/30 hover:shadow-primary/50 hover:-translate-y-0.5">
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

    <!-- 删除确认对话框 -->
    <CommonModal v-model="showDeleteConfirm" title="确认删除" width-class="w-full max-w-sm">
      <p class="text-gray-600 dark:text-gray-300">确定要将此邮件移到垃圾箱吗？</p>
      <template #footer>
        <button @click="showDeleteConfirm = false" class="px-4 py-2 text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700 rounded-lg">
          取消
        </button>
        <button @click="confirmDelete" class="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600">
          删除
        </button>
      </template>
    </CommonModal>
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