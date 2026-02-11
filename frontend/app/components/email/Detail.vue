<script setup lang="ts">
import { ArrowLeft, Trash2, Archive, Star, Reply, Forward, MoreHorizontal, Mail, MailOpen, ReplyAll, Eye, Send, CheckCircle, XCircle, Loader2, RefreshCw, Paperclip, Download, Copy, Check, Tag, Plus, X, FileDown, FileText } from 'lucide-vue-next'
import { Menu, MenuButton, MenuItems, MenuItem } from '@headlessui/vue'

const { selectedEmailDetail, formatTime, toggleRead, removeEmail, startReply, startReplyAll, startForward, folders, currentFolderId, loadEmails, tags, loadTags, addTag, removeTag } = useEmails()
const { isComposeOpen } = useGlobalModal()
const { getTrackingStats, resendEmail, downloadAttachmentUrl, exportEmailUrl, token } = useApi()

// 验证码检测和复制
const detectedCode = ref<string | null>(null)
const codeCopied = ref(false)

// 检测邮件中的验证码（6位数字）
const detectVerificationCode = (email: any) => {
  if (!email) {
    detectedCode.value = null
    return
  }
  
  // 从邮件内容中提取验证码
  const content = email.body_text || email.body_html || ''
  
  // 匹配6位数字验证码（通常在特定上下文中）
  // 优先匹配：验证码是/为/：后面的6位数字
  const patterns = [
    /验证码[是为：:\s]*(\d{6})/,
    /code[:\s]*(\d{6})/i,
    /(\d{6})/  // 最后尝试匹配任意6位数字
  ]
  
  for (const pattern of patterns) {
    const match = content.match(pattern)
    if (match) {
      detectedCode.value = match[1]
      return
    }
  }
  
  detectedCode.value = null
}

// 复制验证码
const copyCode = async () => {
  if (!detectedCode.value) return
  
  try {
    await navigator.clipboard.writeText(detectedCode.value)
    codeCopied.value = true
    setTimeout(() => {
      codeCopied.value = false
    }, 2000)
  } catch (err) {
    console.error('复制失败:', err)
  }
}

// 监听邮件变化，检测验证码
watch(() => selectedEmailDetail.value, (email) => {
  detectVerificationCode(email)
  codeCopied.value = false
}, { immediate: true })

// 加载标签
onMounted(() => {
  loadTags()
})

// 处理添加标签
const handleAddTag = async (tagId: number) => {
  if (selectedEmailDetail.value) {
    await addTag(selectedEmailDetail.value.id, tagId)
  }
}

// 处理移除标签
const handleRemoveTag = async (tagId: number) => {
  if (selectedEmailDetail.value) {
    await removeTag(selectedEmailDetail.value.id, tagId)
  }
}

// 获取未使用的标签
const availableTags = computed(() => {
  if (!selectedEmailDetail.value?.tags) return tags.value
  const usedTagIds = selectedEmailDetail.value.tags.map((t: any) => t.id)
  return tags.value.filter(t => !usedTagIds.includes(t.id))
})

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

// 导出邮件
const exportEmail = (format: 'eml' | 'pdf') => {
  if (!selectedEmailDetail.value) return
  const url = exportEmailUrl(selectedEmailDetail.value.id, format)
  window.open(`${url}&token=${token.value}`, '_blank')
}
</script>

<template>
  <main class="flex-1 h-full email-detail-container flex flex-col min-w-0 relative">
    <template v-if="selectedEmailDetail">
      <!-- 顶部工具栏 -->
      <div class="h-16 border-b border-gray-200/50 dark:border-gray-800/50 flex items-center px-6 justify-between shrink-0">
        <div class="flex items-center gap-2">
          <button class="btn-icon" title="返回">
            <ArrowLeft class="w-5 h-5" />
          </button>
          <div class="w-px h-5 bg-gray-300 dark:bg-gray-600 mx-1"></div>
          <button class="btn-icon group" @click="handleToggleRead" :title="selectedEmailDetail.is_read ? '标记为未读' : '标记为已读'">
            <MailOpen v-if="selectedEmailDetail.is_read" class="w-5 h-5 group-hover:scale-110 transition-transform" />
            <Mail v-else class="w-5 h-5 group-hover:scale-110 transition-transform" />
          </button>
          <button class="btn-icon group" title="归档">
            <Archive class="w-5 h-5 group-hover:scale-110 transition-transform" />
          </button>
          <button class="btn-icon group hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/30" @click="handleDelete" title="删除">
            <Trash2 class="w-5 h-5 group-hover:scale-110 transition-transform" />
          </button>
        </div>
        
        <!-- 更多操作菜单 -->
        <Menu as="div" class="relative">
          <MenuButton class="btn-icon" title="更多操作（导出等）">
            <MoreHorizontal class="w-5 h-5" />
          </MenuButton>
          <transition
            enter-active-class="transition duration-100 ease-out"
            enter-from-class="transform scale-95 opacity-0"
            enter-to-class="transform scale-100 opacity-100"
            leave-active-class="transition duration-75 ease-in"
            leave-from-class="transform scale-100 opacity-100"
            leave-to-class="transform scale-95 opacity-0"
          >
            <MenuItems class="absolute right-0 mt-2 w-52 bg-white dark:bg-gray-800 rounded-xl shadow-xl shadow-gray-900/10 dark:shadow-black/30 border border-gray-200 dark:border-gray-700 py-1.5 z-50 focus:outline-none">
              <div class="px-4 py-2.5 text-xs font-semibold text-gray-500 dark:text-gray-400 border-b border-gray-100 dark:border-gray-700">
                导出邮件
              </div>
              <MenuItem v-slot="{ active }">
                <button
                  @click="exportEmail('eml')"
                  class="w-full text-left px-4 py-2.5 text-sm flex items-center gap-3 transition-colors group"
                  :class="active ? 'bg-gray-50 dark:bg-gray-700' : ''"
                >
                  <FileDown class="w-4 h-4 text-gray-500 group-hover:text-primary transition-colors" />
                  <span class="text-gray-700 dark:text-gray-200 group-hover:text-primary transition-colors">导出为 EML</span>
                </button>
              </MenuItem>
              <MenuItem v-slot="{ active }">
                <button
                  @click="exportEmail('pdf')"
                  class="w-full text-left px-4 py-2.5 text-sm flex items-center gap-3 transition-colors group"
                  :class="active ? 'bg-gray-50 dark:bg-gray-700' : ''"
                >
                  <FileText class="w-4 h-4 text-gray-500 group-hover:text-primary transition-colors" />
                  <span class="text-gray-700 dark:text-gray-200 group-hover:text-primary transition-colors">导出为 PDF</span>
                </button>
              </MenuItem>
            </MenuItems>
          </transition>
        </Menu>
      </div>

      <!-- 滚动内容区 -->
      <div class="flex-1 overflow-y-auto p-8 custom-scrollbar">
        <div class="max-w-4xl mx-auto">
          <!-- 邮件标题 -->
          <div class="flex items-start justify-between gap-4 mb-6">
            <h1 class="text-2xl font-bold text-gray-900 dark:text-white leading-tight flex-1">
              {{ selectedEmailDetail.subject }}
            </h1>
            
            <!-- 验证码快速复制 + 标签管理 -->
            <div class="flex items-center gap-2 shrink-0">
              <!-- 验证码复制按钮 -->
              <button v-if="detectedCode" @click="copyCode"
                class="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all"
                :class="codeCopied
                  ? 'bg-green-500 text-white'
                  : 'bg-gradient-to-r from-primary to-purple-500 text-white hover:shadow-md'">
                <Check v-if="codeCopied" class="w-3.5 h-3.5" />
                <Copy v-else class="w-3.5 h-3.5" />
                <span class="font-mono tracking-wider">{{ detectedCode }}</span>
              </button>
              <!-- 已有标签 -->
              <div v-for="tag in selectedEmailDetail.tags" :key="tag.id"
                class="flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium border"
                :style="{
                  backgroundColor: tag.color + '20',
                  color: tag.color,
                  borderColor: tag.color + '40'
                }">
                <span class="w-1.5 h-1.5 rounded-full" :style="{ backgroundColor: tag.color }"></span>
                {{ tag.name }}
                <button @click="handleRemoveTag(tag.id)" class="hover:bg-black/10 rounded-full p-0.5 transition-colors">
                  <X class="w-3 h-3" />
                </button>
              </div>

              <!-- 添加标签按钮 -->
              <Menu as="div" class="relative">
                <MenuButton class="flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors">
                  <Plus class="w-3 h-3" />
                  标签
                </MenuButton>
                <transition
                  enter-active-class="transition duration-100 ease-out"
                  enter-from-class="transform scale-95 opacity-0"
                  enter-to-class="transform scale-100 opacity-100"
                  leave-active-class="transition duration-75 ease-in"
                  leave-from-class="transform scale-100 opacity-100"
                  leave-to-class="transform scale-95 opacity-0"
                >
                  <MenuItems class="absolute right-0 mt-1 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 py-1 z-50 focus:outline-none">
                    <div v-if="availableTags.length === 0" class="px-4 py-2 text-xs text-gray-500 text-center">
                      无可用标签
                    </div>
                    <MenuItem v-for="tag in availableTags" :key="tag.id" v-slot="{ active }">
                      <button
                        @click="handleAddTag(tag.id)"
                        class="w-full text-left px-4 py-2 text-sm flex items-center gap-2"
                        :class="active ? 'bg-gray-50 dark:bg-gray-700' : ''"
                      >
                        <span class="w-2 h-2 rounded-full" :style="{ backgroundColor: tag.color }"></span>
                        <span class="text-gray-700 dark:text-gray-200">{{ tag.name }}</span>
                      </button>
                    </MenuItem>
                  </MenuItems>
                </transition>
              </Menu>
            </div>
          </div>

          <!-- 发件人卡片 - 改进样式 -->
          <div class="flex items-start gap-4 p-4 bg-gradient-to-r from-gray-50/50 to-transparent dark:from-gray-800/30 dark:to-transparent rounded-xl mb-8">
            <div class="w-14 h-14 rounded-full bg-gradient-to-br from-primary to-primary-hover flex items-center justify-center text-xl text-white font-bold shrink-0 shadow-lg shadow-primary/20 ring-2 ring-white dark:ring-gray-900">
              {{ getAvatar(selectedEmailDetail.sender) }}
            </div>
            <div class="flex-1 min-w-0 pt-1">
              <div class="flex items-center gap-2 mb-1">
                <span class="text-lg font-bold text-gray-900 dark:text-white">{{ selectedEmailDetail.sender }}</span>
              </div>
              <div class="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
                <p>{{ formatRecipients(selectedEmailDetail.recipients) }}</p>
                <p class="mt-1 flex items-center gap-2 text-xs text-gray-500 dark:text-gray-500">
                  <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                  </svg>
                  {{ formatTime(selectedEmailDetail.received_at) }}
                </p>
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

          <!-- 附件列表 - 改进样式 -->
          <div v-if="attachments.length" class="mb-8 p-5 bg-gradient-to-br from-blue-50/50 to-purple-50/30 dark:from-blue-900/10 dark:to-purple-900/10 border border-blue-100 dark:border-blue-900/30 rounded-xl">
            <div class="flex items-center gap-2 text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4">
              <div class="p-1.5 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                <Paperclip class="w-4 h-4 text-blue-600 dark:text-blue-400" />
              </div>
              <span>{{ attachments.length }} 个附件</span>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
              <button v-for="att in attachments" :key="att.id" @click="downloadAttachment(att.id)"
                class="flex items-center gap-3 px-4 py-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl
                       hover:shadow-md hover:border-primary dark:hover:border-primary transition-all duration-200 text-sm group">
                <div class="p-2 bg-gray-50 dark:bg-gray-700 rounded-lg group-hover:bg-primary/10 transition-colors">
                  <Download class="w-4 h-4 text-gray-500 group-hover:text-primary transition-colors" />
                </div>
                <div class="flex-1 min-w-0 text-left">
                  <p class="text-gray-800 dark:text-gray-200 font-medium truncate group-hover:text-primary transition-colors">{{ att.filename }}</p>
                  <p class="text-gray-400 text-xs mt-0.5">{{ formatFileSize(att.size) }}</p>
                </div>
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

      <!-- 底部浮动栏 - 改进样式 -->
      <div class="absolute bottom-8 right-8 flex gap-3 z-20">
        <button @click="handleForward"
          class="flex items-center gap-2.5 px-6 py-3 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300
                 rounded-2xl hover:bg-gray-50 dark:hover:bg-gray-700 active:scale-95
                 transition-all duration-200 text-sm font-semibold border-2 border-gray-200 dark:border-gray-700
                 shadow-lg hover:shadow-xl hover:-translate-y-0.5 group">
          <Forward class="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
          <span>转发</span>
        </button>
        <button @click="handleReplyAll"
          class="flex items-center gap-2.5 px-6 py-3 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300
                 rounded-2xl hover:bg-gray-50 dark:hover:bg-gray-700 active:scale-95
                 transition-all duration-200 text-sm font-semibold border-2 border-gray-200 dark:border-gray-700
                 shadow-lg hover:shadow-xl hover:-translate-y-0.5 group">
          <ReplyAll class="w-4 h-4 group-hover:-rotate-12 transition-transform" />
          <span>回复全部</span>
        </button>
        <button @click="handleReply"
          class="flex items-center gap-2.5 px-7 py-3 bg-gradient-to-r from-primary to-primary-hover text-white
                 rounded-2xl hover:shadow-2xl hover:shadow-primary/40 active:scale-95
                 transition-all duration-200 text-sm font-bold
                 hover:-translate-y-1 group ring-2 ring-primary/20">
          <Reply class="w-4 h-4 group-hover:-rotate-12 transition-transform" />
          <span>回复</span>
        </button>
      </div>
    </template>

    <!-- 空状态 - 改进样式 -->
    <template v-else>
      <div class="flex-1 flex flex-col items-center justify-center gap-4 text-gray-400 px-8">
        <div class="w-20 h-20 rounded-full bg-gradient-to-br from-gray-100 to-gray-50 dark:from-gray-800 dark:to-gray-900 flex items-center justify-center shadow-inner">
          <svg class="w-10 h-10 text-gray-300 dark:text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path>
          </svg>
        </div>
        <div class="text-center">
          <p class="text-lg font-semibold text-gray-600 dark:text-gray-400">选择一封邮件查看</p>
          <p class="text-sm text-gray-500 dark:text-gray-500 mt-1">从左侧列表中选择要阅读的邮件</p>
        </div>
      </div>
    </template>

    <!-- 删除确认对话框 - 改进样式 -->
    <CommonModal v-model="showDeleteConfirm" title="确认删除" width-class="w-full max-w-sm">
      <div class="flex items-start gap-3 py-2">
        <div class="w-10 h-10 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center shrink-0">
          <Trash2 class="w-5 h-5 text-red-500" />
        </div>
        <div>
          <p class="text-gray-800 dark:text-gray-200 font-medium">确定要将此邮件移到垃圾箱吗？</p>
          <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">此操作可以在垃圾箱中撤销</p>
        </div>
      </div>
      <template #footer>
        <button @click="showDeleteConfirm = false"
          class="px-5 py-2.5 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200
                 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-xl transition-all duration-200 font-medium">
          取消
        </button>
        <button @click="confirmDelete"
          class="px-5 py-2.5 bg-gradient-to-r from-red-500 to-red-600 text-white rounded-xl
                 hover:shadow-lg hover:shadow-red-500/30 transition-all duration-200 font-semibold
                 active:scale-95 flex items-center gap-2">
          <Trash2 class="w-4 h-4" />
          <span>删除</span>
        </button>
      </template>
    </CommonModal>
  </main>
</template>

<style scoped>
.btn-icon {
  @apply p-2.5 rounded-xl text-gray-500 dark:text-gray-400
         hover:bg-gray-100 dark:hover:bg-gray-800
         hover:text-gray-900 dark:hover:text-white
         transition-all duration-200 hover:scale-105 active:scale-95;
}

.btn-primary {
  @apply flex items-center gap-2.5 px-7 py-3
         bg-gradient-to-r from-primary to-primary-hover text-white
         rounded-xl hover:shadow-lg hover:shadow-primary/30
         transition-all duration-200 font-semibold
         active:scale-95 hover:-translate-y-0.5;
}

.btn-secondary {
  @apply flex items-center gap-2.5 px-6 py-3
         bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300
         rounded-xl hover:bg-gray-200 dark:hover:bg-gray-700
         transition-all duration-200 font-semibold
         hover:shadow-md active:scale-95;
}

/* 验证码按钮滑入动画 */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-up-enter-from,
.slide-up-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

/* 邮件内容区域平滑滚动 */
.email-detail-container {
  scroll-behavior: smooth;
}

/* 自定义滚动条 */
.email-detail-container ::-webkit-scrollbar {
  width: 8px;
}

.email-detail-container ::-webkit-scrollbar-track {
  background: transparent;
}

.email-detail-container ::-webkit-scrollbar-thumb {
  background: rgba(156, 163, 175, 0.3);
  border-radius: 4px;
  transition: background 0.2s;
}

.email-detail-container ::-webkit-scrollbar-thumb:hover {
  background: rgba(156, 163, 175, 0.5);
}

.dark .email-detail-container ::-webkit-scrollbar-thumb {
  background: rgba(75, 85, 99, 0.4);
}

.dark .email-detail-container ::-webkit-scrollbar-thumb:hover {
  background: rgba(75, 85, 99, 0.6);
}

/* 邮件内容样式覆盖 - 确保在暗色模式下可读 */
/* 覆盖邮件HTML中可能存在的白色/浅色背景 */
.prose :deep(div),
.prose :deep(p),
.prose :deep(table),
.prose :deep(td),
.prose :deep(th),
.prose :deep(span) {
  background-color: transparent !important;
  background: transparent !important;
}

/* 暗色模式下强制文字颜色 */
.dark .prose :deep(*) {
  color: inherit !important;
}

/* 确保链接在暗色模式下可见 */
.dark .prose :deep(a) {
  color: #60a5fa !important;
}

/* 表格边框在暗色模式下可见 */
.dark .prose :deep(table),
.dark .prose :deep(td),
.dark .prose :deep(th) {
  border-color: rgba(75, 85, 99, 0.5) !important;
}

/* 代码块在暗色模式下的背景 */
.dark .prose :deep(code),
.dark .prose :deep(pre) {
  background-color: rgba(39, 39, 42, 0.5) !important;
  color: #e5e7eb !important;
}
</style>